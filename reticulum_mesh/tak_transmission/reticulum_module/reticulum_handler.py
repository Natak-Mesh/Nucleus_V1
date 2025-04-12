#!/usr/bin/env python3

import os
import sys
import json
import re
import time
import socket
import logging
import threading
import random
from datetime import datetime
import shutil

import RNS

# Configuration
APP_NAME = "atak"
ASPECT = "cot"
ANNOUNCE_INTERVAL = 60  # 1 minute
PEER_TIMEOUT = 300      # 5 minutes
STARTUP_DELAY = 10      # 10 seconds for LoRa radio
LINK_TIMEOUT = 600      # 10 minutes link inactivity timeout

# Link keepalive interval (in seconds)
# Default RNS.Link.KEEPALIVE is 360
LINK_KEEPALIVE = 120    # 2 minutes - more frequent keepalives for better link maintenance

class ReticulumHandler:
    def __init__(self):
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("ReticulumHandler")
        
        # Retry mechanism configuration
        self.RETRY_INITIAL_DELAY = 60    # seconds (1 minute) - Base delay for first retry
        self.RETRY_BACKOFF_FACTOR = 2    # Multiplier for delay increase (doubles each time)
        self.RETRY_MAX_DELAY = 900       # seconds (15 minutes) - Maximum allowed delay between retries
        self.RETRY_JITTER = 0.3          # +/- 30% randomness added to calculated delay
        self.RETRY_MAX_ATTEMPTS = 5      # Max number of retry attempts before giving up
        self.RETRY_RATE_LIMIT = 1        # Max number of retries per second
        
        # Add file handler for packet logs
        log_dir = "/home/natak/reticulum_mesh/logs"
        os.makedirs(log_dir, exist_ok=True)
        packet_log_file = os.path.join(log_dir, "packet_logs.log")
        
        # Custom file handler that maintains last 100 lines
        class RotatingHandler(logging.FileHandler):
            def __init__(self, filename, mode='a', encoding=None, delay=False, max_lines=100):
                super().__init__(filename, mode, encoding, delay)
                self.max_lines = max_lines
                
            def emit(self, record):
                try:
                    # Read existing lines
                    lines = []
                    if os.path.exists(self.baseFilename):
                        with open(self.baseFilename, 'r') as f:
                            lines = f.readlines()
                    
                    # Add new line
                    lines.append(self.format(record) + '\n')
                    
                    # Keep only last max_lines
                    lines = lines[-self.max_lines:]
                    
                    # Write back to file
                    with open(self.baseFilename, 'w') as f:
                        f.writelines(lines)
                except Exception:
                    self.handleError(record)
        
        # Use custom handler that maintains last 100 lines
        file_handler = RotatingHandler(packet_log_file, max_lines=100)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
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
        self.node_links = {}  # hostname -> link object
        self.link_to_hostname = {}  # Direct link object to hostname mapping
        self.hash_to_hostname = {}  # Hash to hostname mapping
        self.identity_hash_to_hostname = {}  # Identity hash to hostname mapping  
        self.should_quit = False
        self.message_loops_running = False
        self.message_threads = []
        
        # Retry mechanism state
        self.message_retry_queue = {}  # For tracking messages awaiting proof/retry
        self.retry_lock = threading.Lock()  # Thread safety for retry queue
        self.last_retry_time = 0  # For rate limiting retries
        self.buffer_refs = {}  # Maps packet_id -> {count, nodes} for reference counting
        
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
        
        # Set up link callback
        self.destination.set_link_established_callback(self.link_established)
        
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
        
        # Start link monitoring thread
        self.link_monitor_thread = threading.Thread(target=self.monitor_links, daemon=True)
        self.link_monitor_thread.start()
        
        # Start establishing links to known nodes
        self.establish_all_links()

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
                        
                        # Tear down any link to this stale peer
                        if hostname in self.node_links:
                            self.logger.info(f"Tearing down link to stale peer: {hostname}")
                            try:
                                self.node_links[hostname].teardown()
                            except Exception as e:
                                self.logger.error(f"Error tearing down link: {e}")
                            self.node_links.pop(hostname, None)
                
                # Start or stop message loops based on non-WIFI nodes
                if non_wifi_nodes and not self.message_loops_running:
                    self.start_message_loops()
                elif not non_wifi_nodes and self.message_loops_running:
                    self.stop_message_loops()
                    
                # Ensure we have links to all non-WiFi nodes
                for mac in non_wifi_nodes:
                    hostname = self.get_hostname_for_mac(mac)
                    if hostname and hostname in self.peer_map and hostname not in self.node_links:
                        self.establish_link_to_node(hostname)
                    
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

    def monitor_links(self):
        """Periodically monitor link status and health"""
        # Wait a bit before starting to monitor links
        time.sleep(30)
        
        while not self.should_quit:
            try:
                # Check all active links
                if self.node_links:
                    self.logger.info("=== LINK STATUS REPORT ===")
                    self.logger.info(f"Active Links: {len(self.node_links)}")
                    
                    for hostname, link in list(self.node_links.items()):
                        try:
                            # Check if link is active
                            if hasattr(link, 'status'):
                                status_str = "ACTIVE" if link.status == RNS.Link.ACTIVE else "NOT ACTIVE"
                                
                                # Collect link stats
                                stats = []
                                
                                if hasattr(link, 'get_age'):
                                    stats.append(f"Age: {link.get_age():.1f}s")
                                
                                if hasattr(link, 'inactive_for'):
                                    stats.append(f"Inactive: {link.inactive_for():.1f}s")
                                
                                if hasattr(link, 'get_mtu'):
                                    stats.append(f"MTU: {link.get_mtu()}")
                                    
                                if hasattr(link, 'get_expected_rate'):
                                    stats.append(f"Rate: {link.get_expected_rate():.2f} bps")
                                
                                if hasattr(link, 'get_rssi') and link.get_rssi() is not None:
                                    stats.append(f"RSSI: {link.get_rssi()} dBm")
                                    
                                if hasattr(link, 'get_snr') and link.get_snr() is not None:
                                    stats.append(f"SNR: {link.get_snr()} dB")
                                
                                # Join stats with commas
                                stats_str = ", ".join(stats)
                                
                                # Log link status
                                self.logger.info(f"Link to {hostname}: {status_str} [{stats_str}]")
                                
                                # If link is not active but should be, try to re-establish
                                if link.status != RNS.Link.ACTIVE and hostname in self.peer_map:
                                    self.logger.warning(f"Link to {hostname} is not active, attempting to re-establish")
                                    # Remove the old link
                                    self.node_links.pop(hostname, None)
                                    # Try to establish a new link
                                    self.establish_link_to_node(hostname)
                            else:
                                self.logger.warning(f"Link to {hostname} has no status attribute")
                        except Exception as e:
                            self.logger.error(f"Error checking link to {hostname}: {e}")
                
                # Sleep between link status checks
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in link monitoring: {e}")
                time.sleep(60)  # In case of error, still wait before trying again

    def establish_all_links(self):
        """Establish links to all known non-WiFi nodes"""
        self.logger.info("Establishing links to all known non-WiFi nodes")
        non_wifi_nodes = self.get_non_wifi_nodes()
        for mac in non_wifi_nodes:
            hostname = self.get_hostname_for_mac(mac)
            if hostname and hostname in self.peer_map and hostname not in self.node_links:
                self.establish_link_to_node(hostname)

    def establish_link_to_node(self, hostname):
        """Establish a link to a specific node"""
        try:
            if hostname in self.peer_map:
                dest = self.peer_map[hostname]
                
                # Log that we're starting the link establishment
                self.logger.info(f"Starting link establishment to node: {hostname}")
                
                # Create outgoing destination
                outgoing_dest = RNS.Destination(
                    dest,
                    RNS.Destination.OUT,
                    RNS.Destination.SINGLE,
                    APP_NAME,
                    ASPECT
                )
                
                # Create link with keepalive settings
                link = RNS.Link(
                    outgoing_dest, 
                    established_callback=self.outgoing_link_established,
                    closed_callback=self.link_closed
                )
                
                # Adjust the keepalive interval to maintain the link better
                link.KEEPALIVE = LINK_KEEPALIVE
                
                # Enable physical layer statistics tracking if available
                link.track_phy_stats(True)
                
                # Store link in our map - use a special marker to indicate "establishing"
                self.node_links[hostname] = link
                
                self.logger.info(f"Link establishment process started for node: {hostname}")
                return True
            else:
                self.logger.warning(f"Cannot establish link to unknown peer: {hostname}")
                return False
        except Exception as e:
            self.logger.error(f"Error establishing link to {hostname}: {e}")
            return False

    def outgoing_link_established(self, link):
        """Callback when an outgoing link is established"""
        # Find the hostname associated with this link
        hostname = None
        for h, l in self.node_links.items():
            if l == link:
                hostname = h
                break
        
        if hostname:
            self.logger.info(f"LINK_ESTABLISHED: Outgoing link to {hostname}")
            
            # IMPORTANT: Store the link-to-hostname mapping right away
            # This is critical for proper packet source identification
            self.link_to_hostname[link] = hostname
            
            # Also store destination hash mapping if available
            if hasattr(link, 'destination') and hasattr(link.destination, 'hash'):
                source_hash = RNS.prettyhexrep(link.destination.hash) 
                self.hash_to_hostname[source_hash] = hostname
            
            # Explicitly identify ourselves to the remote peer
            self.logger.info(f"Identifying to remote peer {hostname}")
            link.identify(self.identity)
            
            self.check_pending_files_for_node(hostname)
        else:
            self.logger.warning("LINK_ESTABLISHED: Outgoing link to unknown node")
            
    def check_pending_files_for_node(self, hostname):
        """Check for pending files to send to a specific node"""
        try:
            if hostname not in self.node_links:
                self.logger.warning(f"Cannot check pending files: No active link to {hostname}")
                return
                
            link = self.node_links[hostname]
            
            # Get list of .zst files in pending directory
            pending_files = [f for f in os.listdir(self.pending_dir) if f.endswith('.zst')]
            
            if pending_files:
                self.logger.info(f"Found {len(pending_files)} files to process for {hostname}")
                
                # Sort by timestamp (assuming filename contains timestamp)
                pending_files.sort()
                
                for filename in pending_files:
                    # Move file to processing directory
                    pending_path = os.path.join(self.pending_dir, filename)
                    processing_path = os.path.join(self.processing_dir, filename)
                    
                    # Atomic move
                    os.rename(pending_path, processing_path)
                    
                    # Send file over link
                    with open(processing_path, 'rb') as f:
                        file_data = f.read()
                        
                        file_size = len(file_data)
                        timestamp_from_filename = filename.split('_')[1].split('.')[0] if '_' in filename else 'unknown'
                        
                        self.logger.info(f"SEND DETAILS: File={filename}, Size={file_size} bytes, To={hostname}, TimestampFromFilename={timestamp_from_filename}")
                        
                        # Send packet over the established link
                        self.send_data_over_link(link, file_data, hostname, filename)
                        
                    # Remove file from processing directory
                    os.remove(processing_path)
            else:
                self.logger.debug(f"No pending files for {hostname}")
        except Exception as e:
            self.logger.error(f"Error checking pending files for {hostname}: {e}")

    def link_established(self, link):
        """Callback when an incoming link is established"""
        # Try to find hostname if possible
        hostname = "unknown"
        source_hash = "unknown"
        
        # Check by destination hash
        if hasattr(link, 'destination') and hasattr(link.destination, 'hash'):
            source_hash = RNS.prettyhexrep(link.destination.hash)
            
            # Now try to find hostname
            for h, dest in self.peer_map.items():
                if hasattr(dest, 'hash') and dest.hash == link.destination.hash:
                    hostname = h
                    # Store the mappings right away
                    self.link_to_hostname[link] = hostname
                    self.hash_to_hostname[source_hash] = hostname
                    break
        
        # Log detailed link information
        if hostname != "unknown":
            self.logger.info(f"LINK_ESTABLISHED: Incoming link from {hostname} ({source_hash})")
        else:
            self.logger.info(f"LINK_ESTABLISHED: Incoming link from unknown peer ({source_hash})")
            
        # Set callbacks for the link
        link.set_link_closed_callback(self.link_closed)
        link.set_packet_callback(self.link_packet_received)
        
        # Set callback for when remote peer identifies itself
        link.set_remote_identified_callback(self.remote_peer_identified)

    def remote_peer_identified(self, link, identity):
        """Callback when a remote peer has identified itself on a link"""
        try:
            identity_hash = RNS.prettyhexrep(identity.hash)
            self.logger.info(f"Remote peer identified with hash: {identity_hash}")
            
            # First try to find existing hostname for this identity
            hostname = None
            for h, dest in self.peer_map.items():
                if dest == identity:
                    hostname = h
                    self.logger.info(f"Recognized peer identity for {h}")
                    break
            
            # If hostname still unknown but we have destination hash, try that
            if hostname is None and hasattr(link, 'destination') and hasattr(link.destination, 'hash'):
                source_hash = RNS.prettyhexrep(link.destination.hash)
                for h, dest in self.peer_map.items():
                    if hasattr(dest, 'hash') and dest.hash == link.destination.hash:
                        hostname = h
                        self.logger.info(f"Matched peer by destination hash: {h}")
                        break
            
            # If still unknown, use the hash as a temporary identifier
            if hostname is None:
                short_hash = identity_hash[:8]
                hostname = f"node-{short_hash}"
                self.logger.info(f"Assigning temporary hostname {hostname} to newly identified peer")
            
            # Update peer map with this identity
            self.peer_map[hostname] = identity
            self.last_seen[hostname] = time.time()
            
            # Store a mapping between the identity hash and hostname
            if not hasattr(self, 'identity_hash_to_hostname'):
                self.identity_hash_to_hostname = {}
            self.identity_hash_to_hostname[identity_hash] = hostname
            
            # Also store a mapping between link and hostname
            if not hasattr(self, 'link_to_hostname'):
                self.link_to_hostname = {}
            self.link_to_hostname[link] = hostname
            
            # And update any existing mapping from destination hash
            if hasattr(link, 'destination') and hasattr(link.destination, 'hash'):
                dest_hash = RNS.prettyhexrep(link.destination.hash)
                if not hasattr(self, 'hash_to_hostname'):
                    self.hash_to_hostname = {}
                self.hash_to_hostname[dest_hash] = hostname
            
            self.logger.info(f"REMOTE_IDENTIFIED: Peer on link identified as {hostname}")
                
        except Exception as e:
            self.logger.error(f"Error in remote peer identification: {e}")

    def link_closed(self, link):
        """Callback when a link is closed"""
        # Find the hostname associated with this link
        hostname = None
        
        # Check if we have it in our link mapping
        if link in self.link_to_hostname:
            hostname = self.link_to_hostname[link]
            # Clean up the mapping
            self.link_to_hostname.pop(link, None)
        
        # If not found in direct mapping, search node_links
        if hostname is None:
            for h, l in self.node_links.items():
                if l == link:
                    hostname = h
                    self.node_links.pop(h, None)
                    break
        
        # Get link age if available
        link_age = "unknown"
        try:
            if hasattr(link, 'get_age'):
                link_age = f"{link.get_age():.1f}s"
        except Exception:
            pass
            
        # Get inactive time if available
        inactive_time = "unknown"
        try:
            if hasattr(link, 'inactive_for'):
                inactive_time = f"{link.inactive_for():.1f}s"
        except Exception:
            pass
        
        if hostname:
            self.logger.info(f"LINK_CLOSED: Link with {hostname} closed (Age: {link_age}, Inactive: {inactive_time})")
            # Try to re-establish the link if the peer is still known
            if hostname in self.peer_map and hostname in self.last_seen:
                self.logger.info(f"Attempting to re-establish link to: {hostname}")
                self.establish_link_to_node(hostname)
        else:
            self.logger.info(f"LINK_CLOSED: Link with unknown node closed (Age: {link_age}, Inactive: {inactive_time})")

    def link_packet_received(self, data, packet):
        """Handle a packet received over a link"""
        try:
            # Try to find the hostname using our various mappings
            hostname = "unknown"
            
            # First check for remote identity and lookup hostname
            remote_id = packet.link.get_remote_identity()
            if remote_id is not None:
                # Try to find hostname in peer_map
                for h, identity in self.peer_map.items():
                    if identity == remote_id:
                        hostname = h
                        break
            
            # If that fails, try using link mapping
            if hostname == "unknown" and hasattr(self, 'link_to_hostname') and packet.link in self.link_to_hostname:
                hostname = self.link_to_hostname[packet.link]
                self.logger.debug(f"Found hostname {hostname} from link map")
            
            # If that fails, try using remote identity with hash mapping
            if hostname == "unknown" and hasattr(packet.link, "get_remote_identity") and packet.link.get_remote_identity() is not None:
                remote_identity = packet.link.get_remote_identity()
                identity_hash = RNS.prettyhexrep(remote_identity.hash)
                
                # Check our identity hash map first (faster)
                if hasattr(self, 'identity_hash_to_hostname') and identity_hash in self.identity_hash_to_hostname:
                    hostname = self.identity_hash_to_hostname[identity_hash]
                    self.logger.debug(f"Found hostname {hostname} from identity hash map")
                else:
                    # Fall back to searching peer_map
                    for h, dest in self.peer_map.items():
                        if dest == remote_identity:
                            hostname = h
                            # Update our mapping for future use
                            if not hasattr(self, 'identity_hash_to_hostname'):
                                self.identity_hash_to_hostname = {}
                            self.identity_hash_to_hostname[identity_hash] = hostname
                            self.logger.debug(f"Found hostname {hostname} from peer_map")
                            break
            
            # Last resort: try source hash
            if hostname == "unknown" and hasattr(packet, 'source_hash'):
                source_hash = RNS.prettyhexrep(packet.source_hash)
                
                # Check our hash map first
                if hasattr(self, 'hash_to_hostname') and source_hash in self.hash_to_hostname:
                    hostname = self.hash_to_hostname[source_hash]
                    self.logger.debug(f"Found hostname {hostname} from hash map")
                else:
                    # Fall back to searching node_links
                    for h, link in self.node_links.items():
                        if link and hasattr(link, 'destination') and hasattr(link.destination, 'hash'):
                            if link.destination.hash == packet.source_hash:
                                hostname = h
                                # Store for future lookups
                                if not hasattr(self, 'hash_to_hostname'):
                                    self.hash_to_hostname = {}
                                self.hash_to_hostname[source_hash] = hostname
                                self.logger.debug(f"Found hostname {hostname} from node_links")
                                break
            
            # Get source information if available
            source_hash = RNS.prettyhexrep(packet.source_hash) if hasattr(packet, 'source_hash') else "unknown"
            data_size = len(data)
            
            # Update our link mapping if not already done
            if hostname != "unknown" and hasattr(self, 'link_to_hostname') and packet.link not in self.link_to_hostname:
                self.link_to_hostname[packet.link] = hostname
            
            # Log physical layer stats if available
            phy_stats = ""
            if hasattr(packet, "rssi") and packet.rssi is not None:
                phy_stats += f" [RSSI {packet.rssi} dBm]"
            if hasattr(packet, "snr") and packet.snr is not None:
                phy_stats += f" [SNR {packet.snr} dB]"
            
            # Log packet quality if available
            link_quality = ""
            if hasattr(packet.link, "get_q") and packet.link.get_q() is not None:
                link_quality = f" [Link Quality {packet.link.get_q():.2f}]"
            
            # Log link MTU if available
            link_mtu = ""
            if hasattr(packet.link, "get_mtu") and packet.link.get_mtu() is not None:
                link_mtu = f" [Link MTU {packet.link.get_mtu()} bytes]"
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"incoming_{timestamp}.zst"
            file_path = os.path.join(self.incoming_dir, filename)
            
            self.logger.info(f"LINK_DATA_RECEIVED: Size={data_size} bytes, Source={hostname}({source_hash}), Time={datetime.now().strftime('%H:%M:%S.%f')[:-3]}{phy_stats}{link_quality}{link_mtu}")
            
            # Write data to file
            with open(file_path, 'wb') as f:
                f.write(data)
            
            # Extract packet ID from filename timestamp
            packet_id = timestamp
            
            # Log with improved format that matches direct packet receipt
            self.logger.info(f"PACKET RECEIVED: #{packet_id} from {hostname}")
            self.logger.info(f"SAVED: Message saved to {filename}")
            
            # Check for pending files to send in response
            # This helps with bidirectional communication and acknowledgments
            if hostname != "unknown" and hostname in self.node_links:
                # Use a small delay to allow the packet processing to complete before checking
                # for pending messages, improves packet flow when messages are going both ways
                def check_pending_delayed():
                    time.sleep(0.1)
                    self.check_pending_files_for_node(hostname)
                
                # Start thread to check pending files
                thread = threading.Thread(target=check_pending_delayed, daemon=True)
                thread.start()
        except Exception as e:
            self.logger.error(f"Error processing incoming message: {e}")

    def packet_delivered(self, receipt, hostname, packet_id):
        """Callback when a packet has been delivered and proof received"""
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
                if tracking_key in self.message_retry_queue:
                    buffer_path = self.message_retry_queue[tracking_key]['buffer_path']
                    # Remove from retry queue
                    self.message_retry_queue.pop(tracking_key, None)
                    
                # Update buffer reference count
                if packet_id in self.buffer_refs:
                    # Remove this node from the set
                    self.buffer_refs[packet_id]['nodes'].discard(hostname)
                    # Decrement count
                    self.buffer_refs[packet_id]['count'] -= 1
                    
                    # Only delete buffer file if no more references
                    if self.buffer_refs[packet_id]['count'] <= 0:
                        # All nodes have confirmed delivery, safe to delete
                        if buffer_path and os.path.exists(buffer_path):
                            try:
                                os.remove(buffer_path)
                                self.logger.debug(f"Removed buffer file for packet {packet_id} - all nodes confirmed delivery")
                            except Exception as e:
                                self.logger.error(f"Error removing buffer file: {e}")
                        
                        # Clean up reference tracking
                        self.buffer_refs.pop(packet_id, None)
                    else:
                        nodes_left = len(self.buffer_refs[packet_id]['nodes'])
                        self.logger.debug(f"Buffer file for packet {packet_id} still needed by {nodes_left} node(s)")
        except Exception as e:
            self.logger.error(f"Error in packet delivery callback: {e}")
    
    def packet_delivery_timeout(self, receipt, hostname, packet_id):
        """Callback when a packet delivery times out"""
        try:
            # Check if this packet was already confirmed delivered
            tracking_key = f"{hostname}_{packet_id}"
            
            with self.retry_lock:
                # Skip timeout processing if the entry no longer exists in the queue
                # (which would mean it was already confirmed delivered)
                if tracking_key not in self.message_retry_queue:
                    return
            
            # Log the delivery failure
            self.logger.info(f"DELIVERY_FAILED: No proof received for packet {packet_id} to {hostname}")
            
            # Check if the link is still active
            link_active = False
            link = None
            
            if hostname in self.node_links:
                link = self.node_links[hostname]
                if hasattr(link, 'status') and link.status == RNS.Link.ACTIVE:
                    link_active = True
            
            # Generate tracking key for this packet
            tracking_key = f"{hostname}_{packet_id}"
            
            # Check if we need to retry
            with self.retry_lock:
                if tracking_key in self.message_retry_queue:
                    entry = self.message_retry_queue[tracking_key]
                    
                    # Increment retry attempts
                    entry['retry_attempts'] += 1
                    
                    # Log retry status
                    self.logger.info(f"RETRY_STATUS: Attempt {entry['retry_attempts']} of {self.RETRY_MAX_ATTEMPTS} for {packet_id} to {hostname}")
                    
                    # Check if max retries reached
                    if entry['retry_attempts'] >= self.RETRY_MAX_ATTEMPTS:
                        self.logger.warning(f"RETRY_MAX_EXCEEDED: Packet {packet_id} to {hostname} failed after {self.RETRY_MAX_ATTEMPTS} attempts")
                        
                        # Remove from retry queue
                        self.message_retry_queue.pop(tracking_key, None)
                        
                        # Update buffer reference count
                        if packet_id in self.buffer_refs:
                            # Remove this node from the set
                            self.buffer_refs[packet_id]['nodes'].discard(hostname)
                            # Decrement count
                            self.buffer_refs[packet_id]['count'] -= 1
                            
                            # Only delete buffer file if no more references
                            if self.buffer_refs[packet_id]['count'] <= 0:
                                # All nodes have either confirmed or exceeded max retries
                                if os.path.exists(entry['buffer_path']):
                                    try:
                                        os.remove(entry['buffer_path'])
                                        self.logger.debug(f"Removed buffer file for packet {packet_id} - all nodes completed")
                                    except Exception as e:
                                        self.logger.error(f"Error removing buffer file: {e}")
                                
                                # Clean up reference tracking
                                self.buffer_refs.pop(packet_id, None)
                            else:
                                nodes_left = len(self.buffer_refs[packet_id]['nodes'])
                                self.logger.debug(f"Buffer file for packet {packet_id} still needed by {nodes_left} node(s)")
                    
                    # Otherwise schedule retry
                    elif link_active:
                        # Calculate next retry time with exponential backoff
                        delay = min(
                            self.RETRY_INITIAL_DELAY * (self.RETRY_BACKOFF_FACTOR ** (entry['retry_attempts'] - 1)),
                            self.RETRY_MAX_DELAY
                        )
                        # Add jitter
                        jitter_factor = 1.0 + random.uniform(-self.RETRY_JITTER, self.RETRY_JITTER)
                        delay = delay * jitter_factor
                        
                        entry['next_retry_time'] = time.time() + delay
                        entry['status'] = 'pending_retry'
                        
                        self.logger.info(f"RETRY_SCHEDULED: Packet {packet_id} to {hostname} - Attempt {entry['retry_attempts']} of {self.RETRY_MAX_ATTEMPTS} scheduled in {delay:.1f}s")
                        
                        # Start retry thread if not already running
                        if not hasattr(self, 'retry_thread') or not self.retry_thread.is_alive():
                            self.retry_thread = threading.Thread(target=self.retry_processing_loop, daemon=True)
                            self.retry_thread.start()
                            self.logger.debug("Started retry processing thread")
                    else:
                        # Link is not active, mark as pending but without a retry time
                        # We'll retry when the link becomes active again
                        entry['status'] = 'pending_retry'
                        entry['next_retry_time'] = None
                        self.logger.warning(f"RETRY_DEFERRED: Link to {hostname} is not active, retry for packet {packet_id} deferred")
            
            # Log link status - this is important to diagnose if the automatic resend is working
            if link_active:
                # Get link information if available
                link_info = ""
                try:
                    if hasattr(link, 'get_age'):
                        link_info += f" [Age {link.get_age():.1f}s]"
                    if hasattr(link, 'inactive_for'):
                        link_info += f" [Inactive {link.inactive_for():.1f}s]"
                    if hasattr(link, 'get_mtu'):
                        link_info += f" [MTU {link.get_mtu()}]"
                except Exception:
                    pass
                
                self.logger.info(f"LINK_STATUS: Link to {hostname} is ACTIVE{link_info}, automatic resend should occur")
            else:
                self.logger.warning(f"LINK_STATUS: Link to {hostname} is NOT ACTIVE, automatic resend will not occur")
                
                # If we have a path to the destination but no active link, try to re-establish
                if hostname in self.peer_map and hasattr(self.peer_map[hostname], 'hash'):
                    dest_hash = self.peer_map[hostname].hash
                    if RNS.Transport.has_path(dest_hash):
                        self.logger.info(f"Path exists to {hostname}, attempting to re-establish link")
                        self.establish_link_to_node(hostname)
        except Exception as e:
            self.logger.error(f"Error in packet timeout callback: {e}")
    
    def send_data_over_link(self, link, data, hostname, filename):
        """Send data over an established link"""
        try:
            # Make sure the link is established before sending
            if not hasattr(link, 'status') or link.status != RNS.Link.ACTIVE:
                self.logger.warning(f"Cannot send data: Link to {hostname} is not active")
                return False
            
            # Extract packet ID from filename if available
            packet_id = "unknown"
            if "_" in filename:
                parts = filename.split("_")
                if len(parts) > 1:
                    packet_id = parts[1].split(".")[0]
            
            # Simple hash for tracking, without using full content hash which causes errors
            short_hash = str(hash(data) % 10000).zfill(4)
            
            # Get link statistics before sending
            link_stats = ""
            try:
                if hasattr(link, 'get_mtu'):
                    link_stats += f" [MTU {link.get_mtu()}]"
                if hasattr(link, 'get_expected_rate'):
                    link_stats += f" [Rate {link.get_expected_rate():.2f} bps]"
                if hasattr(link, 'get_rssi') and link.get_rssi() is not None:
                    link_stats += f" [RSSI {link.get_rssi()} dBm]"
                if hasattr(link, 'get_snr') and link.get_snr() is not None:
                    link_stats += f" [SNR {link.get_snr()} dB]"
            except Exception:
                pass
            
            # Create packet with data
            packet = RNS.Packet(link, data)
            
            # Initialize basic packet tracking
            if not hasattr(self, 'packet_tracking'):
                self.packet_tracking = {}
                self.last_cleanup_time = time.time()
            
            # Simple tracking cleanup
            current_time = time.time()
            if current_time - self.last_cleanup_time > 60:  # Clean up every minute
                self.last_cleanup_time = current_time
                # Create a safe copy of keys for iteration
                keys = list(self.packet_tracking.keys())
                for key in keys:
                    if key in self.packet_tracking and current_time - self.packet_tracking[key]['timestamp'] > 600:
                        self.packet_tracking.pop(key, None)
            
            # Generate a unique key combining hostname and packet_id
            tracking_key = f"{hostname}_{packet_id}"
            
            # Check if this might be a resend
            if tracking_key in self.packet_tracking:
                # We've seen this packet ID before, check if it's a resend
                old_data_hash = self.packet_tracking[tracking_key]['data_hash']
                if old_data_hash == short_hash:
                    self.logger.info(f"DETECTED_RESEND: Packet {packet_id} to {hostname} [Hash: {short_hash}]")
                else:
                    self.logger.info(f"REUSED_ID: Packet {packet_id} to {hostname} has same ID but different content")
            
            # Store packet info for future reference
            self.packet_tracking[tracking_key] = {
                'data_hash': short_hash,
                'timestamp': current_time,
                'size': len(data)
            }
            
            # Save a copy of the file to the buffer directory for potential retries
            buffer_path = os.path.join(self.sent_buffer_dir, filename)
            try:
                with open(buffer_path, 'wb') as f:
                    f.write(data)
            except Exception as e:
                self.logger.error(f"Error saving file to buffer: {e}")
                # Continue anyway - we'll just not have retry capability for this packet
            
            # Send packet and get receipt
            self.logger.info(f"SENDING: {filename} to {hostname}{link_stats}")
            receipt = packet.send()
            
            if receipt:
                # Set callbacks for packet delivery status tracking
                receipt.set_delivery_callback(lambda r: self.packet_delivered(r, hostname, packet_id))
                receipt.set_timeout_callback(lambda r: self.packet_delivery_timeout(r, hostname, packet_id))
                
                # Add to message retry queue
                with self.retry_lock:
                    # Track the packet_id to hostname mapping for buffer reference counting
                    if packet_id not in self.buffer_refs:
                        self.buffer_refs[packet_id] = {'count': 0, 'nodes': set()}
                    
                    self.buffer_refs[packet_id]['count'] += 1
                    self.buffer_refs[packet_id]['nodes'].add(hostname)
                    
                    self.message_retry_queue[tracking_key] = {
                        'hostname': hostname,
                        'filename': filename,
                        'buffer_path': buffer_path,
                        'initial_send_time': time.time(),
                        'retry_attempts': 0,
                        'next_retry_time': None,  # None when awaiting proof
                        'status': 'awaiting_proof',
                        'receipt_hash': receipt.hash if hasattr(receipt, 'hash') else None
                    }
                
                # Let Reticulum handle the timeout period automatically
                self.logger.info(f"SENT: {filename} to {hostname} at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                return True
            else:
                # If send failed, clean up buffer file
                if os.path.exists(buffer_path):
                    try:
                        os.remove(buffer_path)
                    except Exception as e:
                        self.logger.error(f"Error removing buffer file after failed send: {e}")
                
                self.logger.warning(f"Failed to send packet: {filename} to {hostname}")
                return False
        except Exception as e:
            self.logger.error(f"Error sending data over link: {e}")
            return False

    def retry_processing_loop(self):
        """Process messages in the retry queue"""
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
                    for key, entry in self.message_retry_queue.items():
                        if entry['status'] == 'pending_retry' and entry['next_retry_time'] is not None:
                            pending_retries = True
                            if entry['next_retry_time'] <= current_time:
                                retry_candidates.append((key, entry))
                
                # If no pending retries at all, exit the loop
                if not pending_retries:
                    self.logger.debug("No pending retries, exiting retry processing loop")
                    break
                
                # If no ready retries, sleep and check again
                if not retry_candidates:
                    time.sleep(1)
                    continue
                
                # Sort by next_retry_time
                retry_candidates.sort(key=lambda x: x[1]['next_retry_time'])
                
                # Process each candidate
                for key, entry in retry_candidates:
                    hostname = entry['hostname']
                    filename = entry['filename']
                    buffer_path = entry['buffer_path']
                    
                    # Check if we need to rate limit
                    if time.time() - self.last_retry_time < (1.0 / self.RETRY_RATE_LIMIT):
                        # Rate limiting in effect, sleep until we can send again
                        sleep_time = (1.0 / self.RETRY_RATE_LIMIT) - (time.time() - self.last_retry_time)
                        time.sleep(sleep_time)
                    
                    # Check if the link is active
                    link_active = False
                    link = None
                    
                    if hostname in self.node_links:
                        link = self.node_links[hostname]
                        if hasattr(link, 'status') and link.status == RNS.Link.ACTIVE:
                            link_active = True
                    
                    # Only retry if the link is active
                    if link_active:
                        # Get packet ID from filename if available
                        packet_id = "unknown"
                        if "_" in filename:
                            parts = filename.split("_")
                            if len(parts) > 1:
                                packet_id = parts[1].split(".")[0]
                                
                        # Check if the buffer file exists
                        if not os.path.exists(buffer_path):
                            self.logger.warning(f"RETRY_FILE_MISSING: Buffer file for packet {packet_id} to {hostname} not found")
                            
                            # Update buffer reference tracking and remove from retry queue
                            with self.retry_lock:
                                if key in self.message_retry_queue:  # Check again in case it was removed
                                    self.message_retry_queue.pop(key, None)
                                
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
                        
                        # Read the data from the buffer file
                        try:
                            with open(buffer_path, 'rb') as f:
                                data = f.read()
                                
                            # Send the packet
                            packet = RNS.Packet(link, data)
                            receipt = packet.send()
                            
                            if receipt:
                                # Update last retry time for rate limiting
                                self.last_retry_time = time.time()
                                
                                # Set callbacks for packet delivery status tracking
                                receipt.set_delivery_callback(lambda r: self.packet_delivered(r, hostname, packet_id))
                                receipt.set_timeout_callback(lambda r: self.packet_delivery_timeout(r, hostname, packet_id))
                                
                                # Update the retry queue entry
                                with self.retry_lock:
                                    if key in self.message_retry_queue:  # Check again in case it was removed
                                        self.message_retry_queue[key]['status'] = 'awaiting_proof'
                                        self.message_retry_queue[key]['next_retry_time'] = None
                                        self.message_retry_queue[key]['receipt_hash'] = receipt.hash if hasattr(receipt, 'hash') else None
                                
                                self.logger.info(f"RETRY_SENT: Packet {packet_id} to {hostname}, attempt {entry['retry_attempts']} of {self.RETRY_MAX_ATTEMPTS}")
                            else:
                                self.logger.warning(f"RETRY_FAILED: Failed to resend packet {packet_id} to {hostname}")
                                
                                # Link might be having issues, back off a bit
                                with self.retry_lock:
                                    if key in self.message_retry_queue:  # Check again in case it was removed
                                        self.message_retry_queue[key]['next_retry_time'] = time.time() + 10  # Short delay before retrying
                                        
                        except Exception as e:
                            self.logger.error(f"Error processing retry for packet {packet_id} to {hostname}: {e}")
                            
                            # Backoff on error
                            with self.retry_lock:
                                if key in self.message_retry_queue:  # Check again in case it was removed
                                    self.message_retry_queue[key]['next_retry_time'] = time.time() + 30  # Longer delay on error
                    else:
                        # Link is not active, defer retry
                        self.logger.debug(f"Deferring retry for packet to {hostname} - link not active")
                        
                        # Mark pending but without a time to check later when link is active
                        with self.retry_lock:
                            if key in self.message_retry_queue:  # Check again in case it was removed
                                self.message_retry_queue[key]['next_retry_time'] = None
                
                # Sleep a bit before checking for more retries
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in retry processing loop: {e}")
                time.sleep(5)  # Longer sleep on error
        
        self.logger.debug("Retry processing loop ended")
    
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
                
                # Read file data once
                with open(processing_path, 'rb') as f:
                    file_data = f.read()
                
                # Track whether file was sent to at least one target
                sent_to_at_least_one = False
                
                # Process each target
                for hostname in target_hostnames:
                    # Check if we have an established link to this hostname
                    if hostname in self.node_links:
                        link = self.node_links[hostname]
                        
                        self.logger.info(f"Sending {oldest_file} to {hostname} via established link")
                        
                        # Send data over the established link
                        if self.send_data_over_link(link, file_data, hostname, oldest_file):
                            sent_to_at_least_one = True
                    else:
                        # If no link exists yet, try to establish one
                        if hostname in self.peer_map:
                            self.logger.info(f"No link to {hostname}, establishing one...")
                            if self.establish_link_to_node(hostname):
                                # If we successfully establish a link, we'll let the
                                # outgoing_link_established callback handle sending
                                # data from the pending directory
                                sent_to_at_least_one = True
                        # No else clause - if we can't establish a link, we don't send to this node
                
                # Remove file from processing directory
                os.remove(processing_path)
                
                # If we couldn't send to any target, put the file back in pending
                if target_hostnames and not sent_to_at_least_one:
                    self.logger.warning(f"Could not send file to any target, will retry later: {oldest_file}")
                    # We don't need to actually put it back since it will be picked up
                    # in the next loop iteration from the pending directory
                
            except Exception as e:
                self.logger.error(f"Error processing outgoing message: {e}")
                time.sleep(1)
                
    def message_received(self, data, packet):
        """Handle incoming messages"""
        try:
            # Get source information and try to identify the source
            hostname = "unknown"
            source_hash = "unknown"
            
            if hasattr(packet, 'source_hash'):
                source_hash = RNS.prettyhexrep(packet.source_hash)
                
                # Try our hash map first
                if hasattr(self, 'hash_to_hostname') and source_hash in self.hash_to_hostname:
                    hostname = self.hash_to_hostname[source_hash]
                    self.logger.debug(f"Found hostname {hostname} from hash map")
                else:
                    # Fall back to searching peer_map
                    for h, dest in self.peer_map.items():
                        if hasattr(dest, 'hash') and dest.hash == packet.source_hash:
                            hostname = h
                            # Store for future lookups
                            if not hasattr(self, 'hash_to_hostname'):
                                self.hash_to_hostname = {}
                            self.hash_to_hostname[source_hash] = hostname
                            break
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"incoming_{timestamp}.zst"
            file_path = os.path.join(self.incoming_dir, filename)
            
            # Write data to file
            with open(file_path, 'wb') as f:
                f.write(data)
            
            # Extract packet ID from filename timestamp
            packet_id = timestamp
            
            # Log with improved format
            self.logger.info(f"PACKET RECEIVED: #{packet_id} from {hostname} ({source_hash})")
            self.logger.info(f"SAVED: Message saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error processing incoming message: {e}")

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
        self.known_peers = set()  # We'll use this to track peers we've seen

    def received_announce(self, destination_hash, announced_identity, app_data):
        """Handle incoming announces from other nodes"""
        try:
            # Check if this is a new peer we haven't seen before
            is_new_peer = destination_hash not in self.known_peers
            
            # Store the peer hash
            self.known_peers.add(destination_hash)
            
            if app_data:
                hostname = app_data.decode() if isinstance(app_data, bytes) else str(app_data)
                
                # Check if the identity has changed from what we have stored
                identity_changed = False
                if hostname in self.parent.peer_map:
                    old_identity = self.parent.peer_map[hostname]
                    if old_identity.get_public_key() != announced_identity.get_public_key():
                        self.logger.info(f"Identity changed for {hostname}, treating as new peer")
                        identity_changed = True
                        # If we have a link to this node, tear it down since the identity changed
                        if hostname in self.parent.node_links:
                            self.logger.info(f"Tearing down link to node with changed identity: {hostname}")
                            try:
                                self.parent.node_links[hostname].teardown()
                            except Exception as e:
                                self.logger.error(f"Error tearing down link: {e}")
                            self.parent.node_links.pop(hostname, None)
                
                # Store destination and update last seen time
                self.parent.peer_map[hostname] = announced_identity
                self.parent.last_seen[hostname] = time.time()
                
                self.logger.info(f"Updated peer: {hostname} ({RNS.prettyhexrep(destination_hash)})")
                
                # If we don't have a link to this node but should, establish one
                if hostname not in self.parent.node_links:
                    # Check if this node is currently in non-WiFi mode
                    non_wifi_nodes = self.parent.get_non_wifi_nodes()
                    for mac in non_wifi_nodes:
                        if self.parent.get_hostname_for_mac(mac) == hostname:
                            self.logger.info(f"Establishing link to announced non-WiFi node: {hostname}")
                            self.parent.establish_link_to_node(hostname)
                            break
                
                # If this is a new peer or the identity changed, respond with our own announce after a delay
                if is_new_peer or identity_changed:
                    self.logger.info(f"New peer or changed identity discovered: {hostname}")
                    
                    # Send our own announce after a small random delay
                    def delayed_announce():
                        delay = random.uniform(0.5, 2.0)
                        self.logger.info(f"Sending announce after {delay:.1f}s delay")
                        time.sleep(delay)
                        self.parent.destination.announce(app_data=self.parent.hostname.encode())
                        self.logger.info(f"Announce sent in response to peer discovery")
                    
                    # Start announce thread
                    thread = threading.Thread(target=delayed_announce, daemon=True)
                    thread.start()
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
