#!/usr/bin/env python3

"""
Packet manager module for the Reticulum handler.
Handles packet sending, receiving, and retry mechanism.
"""

import os
import threading
import time
import random
from datetime import datetime
import RNS

from . import config
from . import logger

class PacketManager:
    """
    Manages packet operations for the Reticulum handler.
    
    This includes:
    - Sending packets with delivery tracking
    - Managing packet retry mechanism
    - Processing received packets
    """
    
    def __init__(self, file_manager=None, link_manager=None):
        """
        Initialize the packet manager
        
        Args:
            file_manager (FileManager): Reference to file manager module
            link_manager (LinkManager): Reference to link manager module
        """
        self.logger = logger.get_logger("PacketManager")
        
        # Store references to other modules
        self.file_manager = file_manager
        self.link_manager = link_manager
        
        # Retry state
        self.retry_queue = {}     # tracking_key -> retry info
        self.retry_lock = threading.Lock()  # Thread safety for retry queue
        self.last_retry_time = 0  # For rate limiting retries
        self.buffer_refs = {}     # packet_id -> {count, nodes} for reference counting
        
        # Control flags
        self.should_quit = False
        
        # Start retry thread
        self.retry_thread = None  # We'll start this when needed
    
    def start_retry_thread(self):
        """Start the retry processing thread if not already running"""
        if self.retry_thread is None or not self.retry_thread.is_alive():
            self.retry_thread = threading.Thread(target=self.retry_processing_loop, daemon=True)
            self.retry_thread.start()
            self.logger.debug("Started retry processing thread")
    
    def send_data(self, hostname, data, filename):
        """
        Send data to a specific hostname with retry support
        
        Args:
            hostname (str): The hostname to send to
            data (bytes): The data to send
            filename (str): The filename for buffer reference
            
        Returns:
            tuple: (success, tracking_id) - success is boolean, tracking_id for tracking
        """
        # Check if link manager is available
        if self.link_manager is None:
            self.logger.error(f"Cannot send data: No link manager available")
            return False, None
        
        # Generate unique packet ID from filename if available
        packet_id = "unknown"
        if "_" in filename:
            parts = filename.split("_")
            if len(parts) > 1:
                packet_id = parts[1].split(".")[0]
        else:
            # Use timestamp as packet ID
            packet_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        try:
            # Save to buffer for potential retries
            buffer_saved = False
            buffer_path = None
            
            if self.file_manager:
                buffer_saved, buffer_path = self.file_manager.save_to_buffer(data, filename)
            
            # Try to send the packet
            success, receipt = self.link_manager.send_data(hostname, data)
            
            if success and receipt:
                # Generate tracking key
                tracking_key = f"{hostname}_{packet_id}"
                
                # Set callbacks for packet delivery status tracking
                receipt.set_delivery_callback(lambda r: self.packet_delivered(r, hostname, packet_id))
                receipt.set_timeout_callback(lambda r: self.packet_delivery_timeout(r, hostname, packet_id))
                
                # Add to retry queue and buffer references if we saved to buffer
                if buffer_saved:
                    with self.retry_lock:
                        # Track the packet_id to hostname mapping for buffer reference counting
                        if packet_id not in self.buffer_refs:
                            self.buffer_refs[packet_id] = {'count': 0, 'nodes': set()}
                        
                        self.buffer_refs[packet_id]['count'] += 1
                        self.buffer_refs[packet_id]['nodes'].add(hostname)
                        
                        self.retry_queue[tracking_key] = {
                            'hostname': hostname,
                            'filename': filename,
                            'buffer_path': buffer_path,
                            'initial_send_time': time.time(),
                            'retry_attempts': 0,
                            'next_retry_time': None,  # None when awaiting proof
                            'status': 'awaiting_proof',
                            'receipt_hash': receipt.hash if hasattr(receipt, 'hash') else None
                        }
                
                self.logger.info(f"SENT: {filename} to {hostname}")
                return True, tracking_key
            
            else:
                # If send failed, clean up buffer file
                if buffer_saved and buffer_path and self.file_manager:
                    self.file_manager.delete_buffer_file(buffer_path)
                
                self.logger.warning(f"Failed to send packet: {filename} to {hostname}")
                return False, None
                
        except Exception as e:
            self.logger.error(f"Error sending data to {hostname}: {e}")
            return False, None
    
    def packet_delivered(self, receipt, hostname, packet_id):
        """
        Callback when a packet has been delivered and proof received
        
        Args:
            receipt (RNS.PacketReceipt): The packet receipt object
            hostname (str): The hostname the packet was sent to
            packet_id (str): The ID of the packet
        """
        try:
            # Get the round-trip time
            rtt = receipt.get_rtt()
            self.logger.info(f"DELIVERY_CONFIRMED: Got proof from {hostname} for packet {packet_id} in {rtt:.2f}s")
            
            # Format for packet log display
            self.logger.info(f"DELIVERY_CONFIRMED: #{packet_id} → {hostname} ({rtt:.2f}s)")
            
            # Clean up any retry entries for this packet
            tracking_key = f"{hostname}_{packet_id}"
            buffer_path = None
            
            with self.retry_lock:
                # Get buffer path before removing from queue
                if tracking_key in self.retry_queue:
                    buffer_path = self.retry_queue[tracking_key]['buffer_path']
                    # Remove from retry queue
                    self.retry_queue.pop(tracking_key, None)
                    
                # Update buffer reference count
                if packet_id in self.buffer_refs:
                    # Remove this node from the set
                    self.buffer_refs[packet_id]['nodes'].discard(hostname)
                    # Decrement count
                    self.buffer_refs[packet_id]['count'] -= 1
                    
                    # Only delete buffer file if no more references
                    if self.buffer_refs[packet_id]['count'] <= 0 and buffer_path and self.file_manager:
                        # All nodes have confirmed delivery, safe to delete
                        self.file_manager.delete_buffer_file(buffer_path)
                        self.logger.debug(f"Removed buffer file for packet {packet_id} - all nodes confirmed delivery")
                        
                        # Clean up reference tracking
                        self.buffer_refs.pop(packet_id, None)
                    elif buffer_path:
                        nodes_left = len(self.buffer_refs[packet_id]['nodes'])
                        self.logger.debug(f"Buffer file for packet {packet_id} still needed by {nodes_left} node(s)")
                        
        except Exception as e:
            self.logger.error(f"Error in packet delivery callback: {e}")
    
    def packet_delivery_timeout(self, receipt, hostname, packet_id):
        """
        Callback when a packet delivery times out
        
        Args:
            receipt (RNS.PacketReceipt): The packet receipt object
            hostname (str): The hostname the packet was sent to
            packet_id (str): The ID of the packet
        """
        try:
            # Check if this packet was already confirmed delivered
            tracking_key = f"{hostname}_{packet_id}"
            already_confirmed = False
            
            with self.retry_lock:
                # Check if entry no longer exists in the queue (already confirmed delivered)
                if tracking_key not in self.retry_queue:
                    already_confirmed = True
            
            # Only log and handle retry logic if not already confirmed
            if not already_confirmed:
                # Log the delivery failure
                self.logger.info(f"DELIVERY_FAILED: No proof received for packet {packet_id} to {hostname}")
            
            # Check if the link is still active
            link_active = False
            if self.link_manager:
                link_active = self.link_manager.is_link_active(hostname)
            
            # Only process retry logic if packet is still in the queue
            if not already_confirmed:
                # Process retry for this packet
                with self.retry_lock:
                    if tracking_key in self.retry_queue:
                        entry = self.retry_queue[tracking_key]
                        
                        # Increment retry attempts
                        entry['retry_attempts'] += 1
                        
                        # Log retry status
                        self.logger.info(f"RETRY_STATUS: Attempt {entry['retry_attempts']} of {config.RETRY_MAX_ATTEMPTS} for {packet_id} to {hostname}")
                        
                        # Check if max retries reached
                        if entry['retry_attempts'] >= config.RETRY_MAX_ATTEMPTS:
                            self.logger.warning(f"RETRY_MAX_EXCEEDED: Packet {packet_id} to {hostname} failed after {config.RETRY_MAX_ATTEMPTS} attempts")
                            
                            # Remove from retry queue
                            self.retry_queue.pop(tracking_key, None)
                            
                            # Update buffer reference count
                            if packet_id in self.buffer_refs:
                                # Remove this node from the set
                                self.buffer_refs[packet_id]['nodes'].discard(hostname)
                                # Decrement count
                                self.buffer_refs[packet_id]['count'] -= 1
                                
                                # Only delete buffer file if no more references
                                if self.buffer_refs[packet_id]['count'] <= 0 and self.file_manager:
                                    # All nodes have either confirmed or exceeded max retries
                                    if os.path.exists(entry['buffer_path']):
                                        self.file_manager.delete_buffer_file(entry['buffer_path'])
                                        self.logger.debug(f"Removed buffer file for packet {packet_id} - all nodes completed")
                                    
                                    # Clean up reference tracking
                                    self.buffer_refs.pop(packet_id, None)
                                else:
                                    nodes_left = len(self.buffer_refs[packet_id]['nodes'])
                                    self.logger.debug(f"Buffer file for packet {packet_id} still needed by {nodes_left} node(s)")
                        
                        # Otherwise schedule retry
                        elif link_active:
                            # Calculate next retry time with exponential backoff
                            delay = min(
                                config.RETRY_INITIAL_DELAY * (config.RETRY_BACKOFF_FACTOR ** (entry['retry_attempts'] - 1)),
                                config.RETRY_MAX_DELAY
                            )
                            # Add jitter
                            jitter_factor = 1.0 + random.uniform(-config.RETRY_JITTER, config.RETRY_JITTER)
                            delay = delay * jitter_factor
                            
                            entry['next_retry_time'] = time.time() + delay
                            entry['status'] = 'pending_retry'
                            
                            self.logger.info(f"RETRY_SCHEDULED: Packet {packet_id} to {hostname} - Attempt {entry['retry_attempts']} of {config.RETRY_MAX_ATTEMPTS} scheduled in {delay:.1f}s")
                            
                            # Start retry thread if not already running
                            self.start_retry_thread()
                        else:
                            # Link is not active, mark as pending but without a retry time
                            # We'll retry when the link becomes active again
                            entry['status'] = 'pending_retry'
                            entry['next_retry_time'] = None
                            self.logger.warning(f"RETRY_DEFERRED: Link to {hostname} is not active, retry for packet {packet_id} deferred")
            
            # Log link status if not already confirmed
            if not already_confirmed:
                if link_active:
                    self.logger.info(f"LINK_STATUS: Link to {hostname} is ACTIVE, automatic resend should occur")
                else:
                    self.logger.warning(f"LINK_STATUS: Link to {hostname} is NOT ACTIVE, automatic resend will not occur")
                    
                    # Try to re-establish the link
                    if self.link_manager:
                        self.logger.info(f"Attempting to re-establish link to {hostname}")
                        self.link_manager.establish_link(hostname)
                        
        except Exception as e:
            self.logger.error(f"Error in packet timeout callback: {e}")
    
    def retry_processing_loop(self):
        """Thread function for processing message retries"""
        self.logger.info("Starting retry processing loop")
        
        # Keep running until there are no more pending retries
        while not self.should_quit:
            try:
                retry_candidates = []
                
                # Find all packets due for retry
                with self.retry_lock:
                    current_time = time.time()
                    
                    # Check if there are any pending retries
                    pending_retries = False
                    for key, entry in self.retry_queue.items():
                        if entry['status'] == 'pending_retry' and entry['next_retry_time'] is not None:
                            pending_retries = True
                            if entry['next_retry_time'] <= current_time:
                                retry_candidates.append((key, entry))
                
                # If no pending retries at all, exit the loop
                if not pending_retries:
                    self.logger.debug("No pending retries, exiting retry processing loop")
                    self.retry_thread = None
                    break
                
                # If no ready retries, sleep and check again
                if not retry_candidates:
                    time.sleep(config.RETRY_CHECK_INTERVAL)
                    continue
                
                # Sort by next_retry_time
                retry_candidates.sort(key=lambda x: x[1]['next_retry_time'])
                
                # Process each candidate
                for key, entry in retry_candidates:
                    hostname = entry['hostname']
                    filename = entry['filename']
                    buffer_path = entry['buffer_path']
                    
                    # Check if we need to rate limit
                    if time.time() - self.last_retry_time < (1.0 / config.RETRY_RATE_LIMIT):
                        # Rate limiting in effect, sleep until we can send again
                        sleep_time = (1.0 / config.RETRY_RATE_LIMIT) - (time.time() - self.last_retry_time)
                        time.sleep(sleep_time)
                    
                    # Check if the link is active
                    link_active = False
                    if self.link_manager:
                        link_active = self.link_manager.is_link_active(hostname)
                    
                    # Only retry if the link is active
                    if link_active:
                        # Get packet ID from the tracking key
                        packet_id = key.split('_')[1] if '_' in key else "unknown"
                                
                        # Check if the buffer file exists
                        if not self.file_manager or not buffer_path or not self.file_manager.delete_buffer_file(buffer_path):
                            self.logger.warning(f"RETRY_FILE_MISSING: Buffer file for packet {packet_id} to {hostname} not found")
                            
                            # Update buffer reference tracking and remove from retry queue
                            with self.retry_lock:
                                if key in self.retry_queue:  # Check again in case it was removed
                                    self.retry_queue.pop(key, None)
                                
                                # Update buffer reference count
                                if packet_id in self.buffer_refs:
                                    # Remove this node from the set
                                    self.buffer_refs[packet_id]['nodes'].discard(hostname)
                                    # Decrement count
                                    self.buffer_refs[packet_id]['count'] -= 1
                                    
                                    # If nothing else is using this buffer reference, clean it up
                                    if self.buffer_refs[packet_id]['count'] <= 0:
                                        self.buffer_refs.pop(packet_id, None)
                                        self.logger.debug(f"Cleared buffer references for packet {packet_id} - no nodes remaining")
                            
                            continue
                        
                        # Read the data from the buffer file and send it
                        success, data = self.file_manager.read_processing_file(os.path.basename(buffer_path))
                        
                        if success and data:
                            # Send the data
                            if self.link_manager:
                                success, receipt = self.link_manager.send_data(hostname, data)
                                
                                if success and receipt:
                                    # Update last retry time for rate limiting
                                    self.last_retry_time = time.time()
                                    
                                    # Set callbacks for packet delivery status tracking
                                    receipt.set_delivery_callback(lambda r: self.packet_delivered(r, hostname, packet_id))
                                    receipt.set_timeout_callback(lambda r: self.packet_delivery_timeout(r, hostname, packet_id))
                                    
                                    # Update the retry queue entry
                                    with self.retry_lock:
                                        if key in self.retry_queue:  # Check again in case it was removed
                                            self.retry_queue[key]['status'] = 'awaiting_proof'
                                            self.retry_queue[key]['next_retry_time'] = None
                                            self.retry_queue[key]['receipt_hash'] = receipt.hash if hasattr(receipt, 'hash') else None
                                    
                                    self.logger.info(f"RETRY_SENT: Packet {packet_id} to {hostname}, attempt {entry['retry_attempts']} of {config.RETRY_MAX_ATTEMPTS}")
                                else:
                                    self.logger.warning(f"RETRY_FAILED: Failed to resend packet {packet_id} to {hostname}")
                                    
                                    # Link might be having issues, back off a bit
                                    with self.retry_lock:
                                        if key in self.retry_queue:  # Check again in case it was removed
                                            self.retry_queue[key]['next_retry_time'] = time.time() + 10  # Short delay before retrying
                            else:
                                self.logger.error(f"Cannot retry: No link manager available")
                        else:
                            self.logger.error(f"Failed to read buffer file data for packet {packet_id}")
                            
                            # Remove entry on error
                            with self.retry_lock:
                                if key in self.retry_queue:
                                    self.retry_queue.pop(key, None)
                    else:
                        # Link is not active, defer retry
                        self.logger.debug(f"Deferring retry for packet to {hostname} - link not active")
                        
                        # Mark pending but without a time to check later when link is active
                        with self.retry_lock:
                            if key in self.retry_queue:  # Check again in case it was removed
                                self.retry_queue[key]['next_retry_time'] = None
                
                # Sleep a bit before checking for more retries
                time.sleep(config.RETRY_CHECK_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Error in retry processing loop: {e}")
                time.sleep(5)  # Longer sleep on error
        
        self.logger.debug("Retry processing loop ended")
    
    def handle_incoming_packet(self, data, packet, source_hostname):
        """
        Handle an incoming packet
        
        Args:
            data (bytes): The packet data
            packet (RNS.Packet): The packet object
            source_hostname (str): The source hostname
        """
        try:
            # Get source hash if available
            source_hash = RNS.prettyhexrep(packet.source_hash) if hasattr(packet, 'source_hash') else "unknown"
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Save to file
            if self.file_manager:
                success, filename = self.file_manager.save_incoming_file(data, source_hostname)
                
                if success:
                    # Extract packet ID from filename timestamp
                    packet_id = timestamp
                    
                    # Log with improved format
                    self.logger.info(f"PACKET RECEIVED: #{packet_id} from {source_hostname} ({source_hash})")
                else:
                    self.logger.error(f"Failed to save incoming packet from {source_hostname}")
            else:
                self.logger.error(f"Cannot save packet: No file manager available")
                
        except Exception as e:
            self.logger.error(f"Error handling incoming packet: {e}")
    
    def shutdown(self):
        """Gracefully shutdown packet manager"""
        self.should_quit = True
