#!/usr/bin/env python3

import os
import sys
import json
import re
import time
import socket
import logging
import threading
from datetime import datetime

import RNS

# Configuration
APP_NAME = "atak"
ASPECT = "cot"
ANNOUNCE_INTERVAL = 60  # 1 minute
PEER_TIMEOUT = 300      # 5 minutes
STARTUP_DELAY = 10      # 10 seconds for LoRa radio

# Retry Configuration
PACKET_TIMEOUT = 5      # seconds to wait for delivery proof
MAX_RETRIES = 3         # maximum number of retry attempts

class ReticulumHandler:
    def __init__(self):
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("ReticulumHandler")
        
        # File paths
        self.node_modes_path = "/home/natak/reticulum_mesh/mesh_controller/node_modes.json"
        self.identity_map_path = "/home/natak/reticulum_mesh/identity_handler/identity_map.json"
        self.incoming_dir = "/home/natak/reticulum_mesh/tak_transmission/shared/incoming"
        self.pending_dir = "/home/natak/reticulum_mesh/tak_transmission/shared/pending"
        self.processing_dir = "/home/natak/reticulum_mesh/tak_transmission/shared/processing"
        self.sent_buffer_dir = "/home/natak/reticulum_mesh/tak_transmission/shared/sent_buffer"
        
        # Ensure directories exist
        os.makedirs(self.incoming_dir, exist_ok=True)
        os.makedirs(self.pending_dir, exist_ok=True)
        os.makedirs(self.processing_dir, exist_ok=True)
        os.makedirs(self.sent_buffer_dir, exist_ok=True)
        
        # Runtime state
        self.hostname = socket.gethostname()
        self.peer_map = {}  # hostname -> destination
        self.last_seen = {} # hostname -> timestamp
        self.packet_map = {} # packet_hash -> filename
        self.should_quit = False
        self.message_loops_running = False
        self.message_threads = []
        
        # Initialize Reticulum with startup delay
        self.logger.info(f"Initializing Reticulum (waiting {STARTUP_DELAY}s for LoRa radio)...")
        time.sleep(STARTUP_DELAY)
        self.reticulum = RNS.Reticulum()
        
        # Create our identity
        self.identity = RNS.Identity()
        
        # Create our destination
        self.destination = RNS.Destination(
            self.identity,
            RNS.Destination.IN,
            RNS.Destination.SINGLE,
            APP_NAME,
            ASPECT
        )
        
        # Set up packet callback and enable proofs
        self.destination.set_packet_callback(self.message_received)
        self.destination.set_proof_strategy(RNS.Destination.PROVE_ALL)
        
        # Set up announce handler
        self.announce_handler = AnnounceHandler(
            aspect_filter=f"{APP_NAME}.{ASPECT}",
            parent=self
        )
        RNS.Transport.register_announce_handler(self.announce_handler)
        
        # Announce our presence
        self.destination.announce(app_data=self.hostname.encode())
        self.logger.info(f"Reticulum Handler running with destination: {RNS.prettyhexrep(self.destination.hash)}")
        
        # Start announce thread
        self.announce_thread = threading.Thread(target=self.announce_loop, daemon=True)
        self.announce_thread.start()
        
        # Start node mode monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_node_modes, daemon=True)
        self.monitor_thread.start()

    def announce_loop(self):
        """Periodically announce our presence"""
        while not self.should_quit:
            time.sleep(ANNOUNCE_INTERVAL)
            try:
                self.destination.announce(app_data=self.hostname.encode())
                self.logger.debug(f"Sent periodic announce")
            except Exception as e:
                self.logger.error(f"Error sending announce: {e}")

    def monitor_node_modes(self):
        """Monitor node_modes.json for non-WIFI nodes"""
        while not self.should_quit:
            try:
                non_wifi_nodes = self.get_non_wifi_nodes()
                
                # Clean up stale peers
                current_time = time.time()
                for hostname in list(self.last_seen.keys()):
                    if current_time - self.last_seen[hostname] > PEER_TIMEOUT:
                        self.logger.info(f"Removing stale peer: {hostname}")
                        self.last_seen.pop(hostname, None)
                        self.peer_map.pop(hostname, None)
                
                # Start or stop message loops based on non-WIFI nodes
                if non_wifi_nodes and not self.message_loops_running:
                    self.start_message_loops()
                elif not non_wifi_nodes and self.message_loops_running:
                    self.stop_message_loops()
                    
                # Sleep briefly before checking again
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Error monitoring node modes: {e}")
                time.sleep(5)

    def get_non_wifi_nodes(self):
        """Get list of MAC addresses for nodes not in WIFI mode"""
        try:
            with open(self.node_modes_path, 'r') as f:
                node_modes = json.load(f)
                return [mac for mac, data in node_modes.items() if data.get('mode') != 'WIFI']
        except Exception as e:
            self.logger.error(f"Error reading node_modes.json: {e}")
            return []

    def get_hostname_for_mac(self, mac_address):
        """Get hostname for a MAC address from identity_map.json"""
        try:
            with open(self.identity_map_path, 'r') as f:
                identity_map = json.load(f)
                node_data = identity_map.get('nodes', {}).get(mac_address, {})
                return node_data.get('hostname')
        except Exception as e:
            self.logger.error(f"Error reading identity_map.json: {e}")
            return None

    def start_message_loops(self):
        """Start outgoing and incoming message loops"""
        if self.message_loops_running:
            return
            
        self.logger.info("Starting message loops")
        self.message_loops_running = True
        
        # Start outgoing message thread
        outgoing_thread = threading.Thread(target=self.outgoing_message_loop, daemon=True)
        outgoing_thread.start()
        self.message_threads.append(outgoing_thread)

    def stop_message_loops(self):
        """Stop message loops"""
        if not self.message_loops_running:
            return
            
        self.logger.info("Stopping message loops")
        self.message_loops_running = False
        self.message_threads = []

    def outgoing_message_loop(self):
        """Process outgoing messages from pending directory"""
        while self.message_loops_running and not self.should_quit:
            try:
                # Get list of .zst files in pending directory
                pending_files = [f for f in os.listdir(self.pending_dir) if f.endswith('.zst')]
                
                if not pending_files:
                    time.sleep(1)
                    continue
                
                # Sort by timestamp (assuming filename contains timestamp)
                pending_files.sort()
                oldest_file = pending_files[0]
                
                # Move file to processing directory
                pending_path = os.path.join(self.pending_dir, oldest_file)
                processing_path = os.path.join(self.processing_dir, oldest_file)
                
                # Atomic move
                os.rename(pending_path, processing_path)
                
                # Get non-WIFI nodes
                non_wifi_macs = self.get_non_wifi_nodes()
                
                # Get hostnames for non-WIFI nodes
                target_hostnames = []
                for mac in non_wifi_macs:
                    hostname = self.get_hostname_for_mac(mac)
                    if hostname:
                        target_hostnames.append(hostname)
                
                # Send file to each target
                with open(processing_path, 'rb') as f:
                    file_data = f.read()
                    
                    for hostname in target_hostnames:
                        if hostname in self.peer_map:
                            dest = self.peer_map[hostname]
                            self.logger.info(f"Sending {oldest_file} to {hostname}")
                            
                            # Create outgoing destination
                            outgoing_dest = RNS.Destination(
                                dest,
                                RNS.Destination.OUT,
                                RNS.Destination.SINGLE,
                                APP_NAME,
                                ASPECT
                            )
                            
                            # Enable proofs on this outgoing destination
                            outgoing_dest.set_proof_strategy(RNS.Destination.PROVE_ALL)
                            
                            # Send packet with proof tracking
                            packet = RNS.Packet(outgoing_dest, file_data)
                            receipt = packet.send()
                            if receipt:
                                self.logger.info(f"Sent {oldest_file} to {hostname} (packet {RNS.prettyhexrep(receipt.hash)})")
                                
                                # Track packet
                                self.packet_map[receipt.hash] = oldest_file
                                
                                # Set callbacks with configured timeout
                                receipt.set_timeout(PACKET_TIMEOUT)
                                receipt.set_delivery_callback(self.delivery_confirmed)
                                receipt.set_timeout_callback(self.delivery_failed)
                # Move to sent_buffer after sending to all targets
                sent_path = os.path.join(self.sent_buffer_dir, oldest_file)
                os.rename(processing_path, sent_path)
                
            except Exception as e:
                self.logger.error(f"Error processing outgoing message: {e}")
                time.sleep(1)

    def message_received(self, data, packet):
        """Handle incoming messages"""
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"incoming_{timestamp}.zst"
            file_path = os.path.join(self.incoming_dir, filename)
            
            # Write data to file
            with open(file_path, 'wb') as f:
                f.write(data)
                
            self.logger.info(f"Received message, saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error processing incoming message: {e}")

    def delivery_confirmed(self, receipt):
        """Handle successful delivery confirmation"""
        self.logger.info(f"Got proof for packet {RNS.prettyhexrep(receipt.hash)} in {receipt.get_rtt():.3f}s")
        
        # Get filename and remove from sent_buffer
        filename = self.packet_map.pop(receipt.hash, None)
        if filename:
            sent_path = os.path.join(self.sent_buffer_dir, filename)
            if os.path.exists(sent_path):
                os.remove(sent_path)
                self.logger.info(f"Successfully delivered {filename}, removed from sent_buffer")

    def delivery_failed(self, receipt):
        """Handle delivery timeout"""
        self.logger.info(f"No proof received for packet {RNS.prettyhexrep(receipt.hash)} after {PACKET_TIMEOUT}s")
        
        # Get filename and move back to pending for retry
        filename = self.packet_map.pop(receipt.hash, None)
        if filename:
            sent_path = os.path.join(self.sent_buffer_dir, filename)
            
            # Check if this is already a retry
            retry_count = 1
            retry_match = re.search(r'_retry(\d+)\.zst$', filename)
            if retry_match:
                retry_count = int(retry_match.group(1)) + 1
                # Remove the old retry suffix
                base_filename = re.sub(r'_retry\d+\.zst$', '.zst', filename)
            else:
                # First retry
                base_filename = filename
                
            # Check max retries
            if retry_count > MAX_RETRIES:
                self.logger.error(f"Max retries ({MAX_RETRIES}) reached for {filename}, dropping packet")
                if os.path.exists(sent_path):
                    os.remove(sent_path)
                return
                
            # Add retry counter to filename
            new_filename = base_filename.replace('.zst', f'_retry{retry_count}.zst')
            pending_path = os.path.join(self.pending_dir, new_filename)
            
            if os.path.exists(sent_path):
                # Move back to pending with updated filename
                os.rename(sent_path, pending_path)
                self.logger.info(f"Moved {filename} to {new_filename} for retry {retry_count}/{MAX_RETRIES}")

    def run(self):
        """Main program loop"""
        try:
            self.logger.info("Reticulum Handler running, press Ctrl+C to exit")
            while not self.should_quit:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Exiting...")
            self.should_quit = True

class AnnounceHandler:
    def __init__(self, aspect_filter=None, parent=None):
        """Initialize the announce handler"""
        self.aspect_filter = aspect_filter
        self.parent = parent
        self.logger = logging.getLogger("AnnounceHandler")

    def received_announce(self, destination_hash, announced_identity, app_data):
        """Handle incoming announces from other nodes"""
        try:
            if app_data:
                hostname = app_data.decode() if isinstance(app_data, bytes) else str(app_data)
                
                # Store destination and update last seen time
                self.parent.peer_map[hostname] = announced_identity
                self.parent.last_seen[hostname] = time.time()
                
                self.logger.info(f"Updated peer: {hostname} ({RNS.prettyhexrep(destination_hash)})")
        except Exception as e:
            self.logger.error(f"Error processing announce: {e}")

def main():
    """Main entry point"""
    try:
        handler = ReticulumHandler()
        handler.run()
    except KeyboardInterrupt:
        print("")
        sys.exit(0)

if __name__ == "__main__":
    main()
