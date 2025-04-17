#!/usr/bin/env python3

"""
Simple peer discovery module for Reticulum.
"""

import time
import socket
import threading
import random
import json
import RNS

import config
import logger

class PeerDiscovery:
    """Simple peer discovery and tracking for Reticulum."""
    
    def __init__(self):
        """Initialize peer discovery"""
        self.logger = logger.get_logger("PeerDiscovery", "peer_discovery.log")
        
        # Clean up on startup
        self.cleanup_on_startup()
        
        # Initialize RNS
        RNS.Reticulum()
        
        # Create identity and destination
        self.identity = RNS.Identity()
        self.destination = RNS.Destination(
            self.identity,
            RNS.Destination.IN,  # Direction - we want to receive announces
            RNS.Destination.SINGLE,  # Type - for single destination encryption
            config.APP_NAME,  # From your config
            config.ASPECT  # From your config as separate aspect
        )
        
        # Configure destination to automatically prove all received packets
        self.destination.set_proof_strategy(RNS.Destination.PROVE_ALL)
        self.logger.info("Set destination to automatically prove all packets")
        
        self.hostname = socket.gethostname()
        
        # Store peer info
        self.peer_map = {}  # hostname -> {identity, destination_hash}
        self.last_seen = {} # hostname -> timestamp
        
        # Create fresh peer status file
        self.update_peer_status_file()
        
        # Set up announce handler
        self.announce_handler = AnnounceHandler(
            aspect_filter=f"{config.APP_NAME}.{config.ASPECT}",
            parent=self
        )
        RNS.Transport.register_announce_handler(self.announce_handler)
        
        # Start periodic announcer
        self.should_quit = False
        self.announce_thread = threading.Thread(target=self.announce_loop, daemon=True)
        self.announce_thread.start()
        
        # Announce immediately
        self.announce_presence()
    
    def announce_loop(self):
        """Periodically announce our presence"""
        while not self.should_quit:
            time.sleep(config.ANNOUNCE_INTERVAL)
            self.announce_presence()
    
    def announce_presence(self):
        """Announce our presence to the network"""
        try:
            self.destination.announce(app_data=self.hostname.encode())
            self.logger.debug(f"Sent announce: {self.hostname}")
        except Exception as e:
            self.logger.error(f"Error sending announce: {e}")
    
    def add_peer(self, hostname, identity, destination_hash):
        """Add or update a peer"""
        if hostname != self.hostname:  # Don't add ourselves
            if hostname in self.peer_map:
                self.logger.info(f"Updating peer: {hostname}")
            else:
                self.logger.info(f"Adding peer: {hostname}")
            
            # Store peer info
            self.peer_map[hostname] = {
                'identity': identity,
                'destination_hash': destination_hash
            }
            
            # Update last seen timestamp
            self.last_seen[hostname] = time.time()
            
            # Update peer status file
            self.update_peer_status_file()
            self.logger.info(f"Current peer map after add_peer: {self.peer_map}")
    
    def get_peer_identity(self, hostname):
        """Get a peer's identity"""
        peer_data = self.peer_map.get(hostname)
        return peer_data['identity'] if peer_data else None
    
    def clean_stale_peers(self):
        """Remove stale peers that haven't been seen recently"""
        current_time = time.time()
        removed = []
        
        for hostname in list(self.last_seen.keys()):
            if current_time - self.last_seen[hostname] > config.PEER_TIMEOUT:
                self.logger.info(f"Removing stale peer: {hostname}")
                self.peer_map.pop(hostname, None)
                self.last_seen.pop(hostname, None)
                removed.append(hostname)
        
        if removed:
            self.update_peer_status_file()
        
        return removed
    
    def update_peer_status_file(self):
        """Update the peer status file"""
        try:
            status = {
                "timestamp": int(time.time()),
                "peers": {}
            }
            
            for hostname, peer_data in self.peer_map.items():
                status["peers"][hostname] = {
                    "destination_hash": peer_data['destination_hash'].hex(),
                    "last_seen": int(self.last_seen[hostname])
                }
            
            json_path = f"{config.BASE_DIR}/tak_transmission/reticulum_module/new_implementation/peer_discovery.json"
            with open(json_path, "w") as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error updating peer status file: {e}")

    def cleanup_on_startup(self):
        """Clean up all stored peer data on startup"""
        self.logger.info("Cleaning up peer data on startup")
        
        # Reset peer tracking
        self.peer_map = {}
        self.last_seen = {}
        
        # Create fresh peer status file with empty peers
        status = {
            "timestamp": int(time.time()),
            "peers": {}
        }
        
        try:
            json_path = f"{config.BASE_DIR}/tak_transmission/reticulum_module/new_implementation/peer_discovery.json"
            with open(json_path, "w") as f:
                json.dump(status, f, indent=2)
            self.logger.info("Created fresh peer_discovery.json")
            self.logger.info(f"Peer map after cleanup: {self.peer_map}")
        except Exception as e:
            self.logger.error(f"Error creating fresh peer status file: {e}")

    def shutdown(self):
        """Shutdown peer discovery"""
        self.should_quit = True
        RNS.Transport.deregister_announce_handler(self.announce_handler)


class AnnounceHandler:
    """Handler for Reticulum announcements"""
    
    def __init__(self, aspect_filter=None, parent=None):
        self.aspect_filter = aspect_filter
        self.parent = parent
        self.logger = logger.get_logger("AnnounceHandler", "peer_discovery.log")
    
    def received_announce(self, destination_hash, announced_identity, app_data):
        """Handle incoming announces"""
        try:
            if app_data:
                # Extract hostname from app_data
                try:
                    hostname = app_data.decode('utf-8') if isinstance(app_data, bytes) else str(app_data)
                except:
                    self.logger.warning("Could not decode app_data in announce")
                    return
                
                if hostname and hostname != self.parent.hostname:
                    identity_str = str(announced_identity)
                    self.logger.info(f"Received announce from {hostname} [{identity_str[:8]}...]")
                    
                    # Add or update peer
                    is_new = hostname not in self.parent.peer_map
                    self.parent.add_peer(hostname, announced_identity, destination_hash)
                    
                    # Announce back to new peers after short delay
                    if is_new:
                        self.logger.info(f"New peer discovered: {hostname}")
                        def announce_back():
                            time.sleep(random.uniform(0.5, 1.5))
                            self.parent.announce_presence()
                        threading.Thread(target=announce_back, daemon=True).start()
                        
        except Exception as e:
            self.logger.error(f"Error processing announce: {e}")
