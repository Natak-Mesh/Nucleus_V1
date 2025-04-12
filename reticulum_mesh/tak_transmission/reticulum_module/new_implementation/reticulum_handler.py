#!/usr/bin/env python3

"""
Main Reticulum handler module.
This is the primary entry point that coordinates all components.
"""

import os
import sys
import time
import socket
import threading
import RNS

from . import config
from . import logger
from .file_manager import FileManager
from .peer_discovery import PeerDiscovery
from .link_manager import LinkManager
from .packet_manager import PacketManager

class ReticulumHandler:
    """
    Main handler for Reticulum mesh networking.
    
    This class coordinates between the different modules:
    - File management for incoming and outgoing data
    - Peer discovery and tracking
    - Link establishment and maintenance
    - Packet sending and receipt with retry support
    - Monitoring node modes for non-WiFi connections
    """
    
    def __init__(self):
        """Initialize the Reticulum handler"""
        # Set up logging
        self.logger = logger.get_logger("ReticulumHandler", "handler.log")
        self.logger.info("Initializing Reticulum Handler")
        
        # Runtime state
        self.hostname = socket.gethostname()
        self.should_quit = False
        self.message_loops_running = False
        self.message_threads = []
        
        # Initialize components
        self.file_manager = FileManager()
        
        # Initialize Reticulum with startup delay
        self.logger.info(f"Initializing Reticulum (waiting {config.STARTUP_DELAY}s for LoRa radio)...")
        time.sleep(config.STARTUP_DELAY)
        self.reticulum = RNS.Reticulum()
        
        # Create our identity
        self.identity = RNS.Identity()
        
        # Create our destination
        self.destination = RNS.Destination(
            self.identity,
            RNS.Destination.IN,
            RNS.Destination.SINGLE,
            config.APP_NAME,
            config.ASPECT
        )
        
        # Set up packet callback and enable proofs
        self.destination.set_packet_callback(self.message_received)
        self.destination.set_proof_strategy(RNS.Destination.PROVE_ALL)
        
        # Set up link callback
        self.destination.set_link_established_callback(self.link_established)
        
        # Initialize other modules
        self.peer_discovery = PeerDiscovery(self.identity, self.destination)
        self.link_manager = LinkManager(self.identity, self.peer_discovery)
        self.packet_manager = PacketManager(self.file_manager, self.link_manager)
        
        # Set up link manager callbacks
        self.link_manager.set_on_incoming_packet_callback(self.packet_manager.handle_incoming_packet)
        
        # Announce our presence
        self.peer_discovery.announce_presence()
        self.logger.info(f"Reticulum Handler running with destination: {RNS.prettyhexrep(self.destination.hash)}")
        
        # Start node mode monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_node_modes, daemon=True)
        self.monitor_thread.start()
    
    def message_received(self, data, packet):
        """
        Callback when a message is received directly to our destination
        
        Args:
            data (bytes): The packet data
            packet (RNS.Packet): The packet object
        """
        try:
            # Try to find source hostname
            source_hostname = "unknown"
            
            # If we have source hash, try to find the hostname
            if hasattr(packet, 'source_hash'):
                source_hash = RNS.prettyhexrep(packet.source_hash)
                source_hostname = self.peer_discovery.get_hostname_from_hash(source_hash)
            
            # Handle the incoming data via the packet manager
            self.packet_manager.handle_incoming_packet(data, packet, source_hostname)
            
        except Exception as e:
            self.logger.error(f"Error processing incoming message: {e}")
    
    def link_established(self, link):
        """
        Callback when an incoming link is established to our destination
        
        Args:
            link (RNS.Link): The established link
        """
        try:
            # Pass to the link manager
            self.link_manager.incoming_link_established(link)
        except Exception as e:
            self.logger.error(f"Error handling link established: {e}")
    
    def monitor_node_modes(self):
        """Monitor node_modes.json for non-WIFI nodes and manage links accordingly"""
        while not self.should_quit:
            try:
                # Clean up stale peers
                self.peer_discovery.clean_stale_peers()
                
                # Get non-WiFi nodes
                non_wifi_nodes = self.peer_discovery.get_non_wifi_nodes()
                
                # Start or stop message loops based on non-WIFI nodes
                if non_wifi_nodes and not self.message_loops_running:
                    self.start_message_loops()
                elif not non_wifi_nodes and self.message_loops_running:
                    self.stop_message_loops()
                    
                # Establish links to non-WiFi nodes
                self.link_manager.establish_links_to_non_wifi_nodes()
                    
                # Sleep briefly before checking again
                time.sleep(config.NODE_MONITOR_INTERVAL)
            except Exception as e:
                self.logger.error(f"Error monitoring node modes: {e}")
                time.sleep(config.NODE_MONITOR_INTERVAL)
    
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
                # Get list of files in pending directory
                pending_files = self.file_manager.get_pending_files()
                
                if not pending_files:
                    time.sleep(1)
                    continue
                
                # Process oldest file
                oldest_file = pending_files[0]
                
                # Move file to processing
                success, processing_path = self.file_manager.move_to_processing(oldest_file)
                
                if not success:
                    self.logger.warning(f"Failed to move {oldest_file} to processing")
                    time.sleep(1)
                    continue
                
                # Get non-WIFI nodes
                non_wifi_macs = self.peer_discovery.get_non_wifi_nodes()
                
                # Get hostnames for non-WIFI nodes
                target_hostnames = []
                for mac in non_wifi_macs:
                    hostname = self.peer_discovery.get_hostname_for_mac(mac)
                    if hostname:
                        target_hostnames.append(hostname)
                
                if not target_hostnames:
                    self.logger.warning("No non-WiFi nodes to send data to")
                    # Remove file from processing directory
                    self.file_manager.remove_processing_file(oldest_file)
                    continue
                
                # Read file data
                success, file_data = self.file_manager.read_processing_file(oldest_file)
                
                if not success or not file_data:
                    self.logger.error(f"Failed to read file data for {oldest_file}")
                    time.sleep(1)
                    continue
                
                # Track whether file was sent to at least one target
                sent_to_at_least_one = False
                
                # Process each target
                for hostname in target_hostnames:
                    # Send data using packet manager
                    self.logger.info(f"Sending {oldest_file} to {hostname}")
                    success, _ = self.packet_manager.send_data(hostname, file_data, oldest_file)
                    
                    if success:
                        sent_to_at_least_one = True
                    else:
                        self.logger.warning(f"Failed to send {oldest_file} to {hostname}")
                        
                        # Try to establish a link if missing
                        if not self.link_manager.is_link_active(hostname):
                            self.logger.info(f"Attempting to establish link to {hostname}")
                            self.link_manager.establish_link(hostname)
                
                # Remove file from processing directory
                self.file_manager.remove_processing_file(oldest_file)
                
            except Exception as e:
                self.logger.error(f"Error processing outgoing message: {e}")
                time.sleep(1)
    
    def run(self):
        """Main program loop"""
        try:
            self.logger.info("Reticulum Handler running, press Ctrl+C to exit")
            while not self.should_quit:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Exiting...")
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown all components"""
        self.should_quit = True
        
        # Shutdown components in reverse order of initialization
        if hasattr(self, 'packet_manager'):
            self.packet_manager.shutdown()
            
        if hasattr(self, 'link_manager'):
            self.link_manager.shutdown()
            
        if hasattr(self, 'peer_discovery'):
            self.peer_discovery.shutdown()
            
        self.logger.info("Reticulum Handler shutdown complete")

def main():
    """Main entry point"""
    try:
        handler = ReticulumHandler()
        handler.run()
    except KeyboardInterrupt:
        print("")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
