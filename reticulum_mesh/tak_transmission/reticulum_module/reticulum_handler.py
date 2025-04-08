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

import RNS

# Configuration
APP_NAME = "atak"
ASPECT = "cot"
ANNOUNCE_INTERVAL = 60  # 1 minute
PEER_TIMEOUT = 300      # 5 minutes
STARTUP_DELAY = 10      # 10 seconds for LoRa radio
LINK_TIMEOUT = 600      # 10 minutes link inactivity timeout

# Retry Configuration
PACKET_TIMEOUT = 20      # seconds to wait for delivery proof
MAX_RETRIES = 3         # maximum number of retry attempts

class ReticulumHandler:
    def __init__(self):
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("ReticulumHandler")
        
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
                
                # Create outgoing destination
                outgoing_dest = RNS.Destination(
                    dest,
                    RNS.Destination.OUT,
                    RNS.Destination.SINGLE,
                    APP_NAME,
                    ASPECT
                )
                
                # Create link
                link = RNS.Link(outgoing_dest)
                link.set_link_established_callback(self.outgoing_link_established)
                link.set_link_closed_callback(self.link_closed)
                
                # Store link in our map
                self.node_links[hostname] = link
                
                self.logger.info(f"Establishing link to node: {hostname}")
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
        if hasattr(link, 'destination') and hasattr(link.destination, 'hash'):
            for h, dest in self.peer_map.items():
                if hasattr(dest, 'hash') and dest.hash == link.destination.hash:
                    hostname = h
                    break
                    
        self.logger.info(f"LINK_ESTABLISHED: Incoming link from {hostname}")
        # Set callbacks for the link
        link.set_link_closed_callback(self.link_closed)
        link.set_packet_callback(self.link_packet_received)

    def link_closed(self, link):
        """Callback when a link is closed"""
        # Find the hostname associated with this link
        hostname = None
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
            # Try to find hostname for the source if possible
            hostname = "unknown"
            if hasattr(packet, 'source_hash'):
                for h, dest in self.peer_map.items():
                    if hasattr(dest, 'hash') and dest.hash == packet.source_hash:
                        hostname = h
                        break
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"incoming_{timestamp}.zst"
            file_path = os.path.join(self.incoming_dir, filename)
            
            # Get source information if available
            source_hash = RNS.prettyhexrep(packet.source_hash) if hasattr(packet, 'source_hash') else "unknown"
            data_size = len(data)
            
            self.logger.info(f"LINK_DATA_RECEIVED: Size={data_size} bytes, Source={hostname}({source_hash}), Time={datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            
            # Write data to file
            with open(file_path, 'wb') as f:
                f.write(data)
                
            self.logger.info(f"SAVED: Message saved to {filename}")
            
            # Check if we have a link to this hostname
            if hostname != "unknown" and hostname in self.node_links:
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
        except Exception as e:
            self.logger.error(f"Error processing incoming message: {e}")

    def send_data_over_link(self, link, data, hostname, filename):
        """Send data over an established link"""
        try:
            packet = RNS.Packet(link, data)
            packet.send()
            self.logger.info(f"SENT: {filename} to {hostname} at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            return True
        except Exception as e:
            self.logger.error(f"Error sending data over link: {e}")
            return False

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
            # Try to find hostname for the source if possible
            hostname = "unknown"
            if hasattr(packet, 'source_hash'):
                for h, dest in self.peer_map.items():
                    if hasattr(dest, 'hash') and dest.hash == packet.source_hash:
                        hostname = h
                        break
            
            # Get source information if available
            source_hash = RNS.prettyhexrep(packet.source_hash) if hasattr(packet, 'source_hash') else "unknown"
            data_size = len(data)
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"incoming_{timestamp}.zst"
            file_path = os.path.join(self.incoming_dir, filename)
            
            # Write data to file
            with open(file_path, 'wb') as f:
                f.write(data)
            
            self.logger.info(f"INCOMING: Size={data_size} bytes, Source={hostname}({source_hash}), Time={datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
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
        self.hostname_identities = {}  # Track identities per hostname

    def received_announce(self, destination_hash, announced_identity, app_data):
        """Handle incoming announces from other nodes"""
        try:
            # Check if this is a new peer we haven't seen before
            is_new_peer = destination_hash not in self.known_peers
            
            # Store the peer hash
            self.known_peers.add(destination_hash)
            
            if app_data:
                hostname = app_data.decode() if isinstance(app_data, bytes) else str(app_data)
                
                # Check if the identity for this hostname has changed
                identity_changed = False
                if hostname in self.hostname_identities:
                    # Compare the identity public key to detect changes
                    old_identity = self.hostname_identities[hostname]
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
                
                # Store the identity for this hostname
                self.hostname_identities[hostname] = announced_identity
                
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
