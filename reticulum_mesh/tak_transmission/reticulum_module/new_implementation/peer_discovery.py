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
    """
    Simple peer discovery and tracking for Reticulum.
    """
    
    def __init__(self, identity, destination):
        """
        Initialize peer discovery
        
        Args:
            identity (RNS.Identity): Our node's identity
            destination (RNS.Destination): Our destination object
        """
        self.logger = logger.get_logger("PeerDiscovery")
        
        # Basic state
        self.identity = identity
        self.destination = destination
        self.hostname = socket.gethostname()
        
        # Bidirectional mapping
        self.peer_map = {}              # hostname -> identity
        self.identity_to_hostname = {}  # identity hash string -> hostname
        self.last_seen = {}             # hostname -> timestamp

        # Create fresh peer status file
        self.update_peer_status_file()
        
        # Set up announce handler
        self.announce_handler = AnnounceHandler(
            aspect_filter=f"{config.APP_NAME}.{config.ASPECT}",
            parent=self
        )
        RNS.Transport.register_announce_handler(self.announce_handler)
        
        # Announce immediately
        self.announce_presence()
        
        # Start periodic announcer if needed
        self.should_quit = False
        self.announce_thread = threading.Thread(target=self.announce_loop, daemon=True)
        self.announce_thread.start()
    
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
    
    def add_peer(self, hostname, identity, destination_hash=None):
        """
        Add a peer to our map
        
        Args:
            hostname (str): The hostname of the peer
            identity (RNS.Identity): The identity of the peer
            destination_hash (bytes, optional): Not used in simplified version
        """
        if hostname != self.hostname:  # Don't add ourselves
            if hostname in self.peer_map:
                self.logger.info(f"Updating peer: {hostname}")
            else:
                self.logger.info(f"Adding peer: {hostname}")
            
            # Store hostname -> identity mapping
            self.peer_map[hostname] = identity
            
            # Store identity -> hostname mapping
            identity_str = str(identity)
            self.identity_to_hostname[identity_str] = hostname
            
            # Update last seen timestamp
            self.last_seen[hostname] = time.time()
            
            # Update peer status file
            self.update_peer_status_file()
    
    def get_peer_identity(self, hostname):
        """
        Get a peer's identity
        
        Args:
            hostname (str): The hostname to look up
            
        Returns:
            RNS.Identity: The peer's identity, or None if not found
        """
        return self.peer_map.get(hostname)
    
    def get_hostname_by_identity(self, identity):
        """
        Get a hostname from an identity
        
        Args:
            identity: RNS.Identity object or string representation of identity
            
        Returns:
            str: Hostname, or None if not found
        """
        identity_str = str(identity)
        return self.identity_to_hostname.get(identity_str)
    
    def clean_stale_peers(self):
        """Remove stale peers that haven't been seen recently"""
        current_time = time.time()
        removed_peers = []
        
        for hostname in list(self.last_seen.keys()):
            if current_time - self.last_seen[hostname] > config.PEER_TIMEOUT:
                self.logger.info(f"Removing stale peer: {hostname}")
                
                # Remove from both mappings
                if hostname in self.peer_map:
                    identity = self.peer_map[hostname]
                    identity_str = str(identity)
                    self.identity_to_hostname.pop(identity_str, None)
                    self.peer_map.pop(hostname, None)
                
                self.last_seen.pop(hostname, None)
                removed_peers.append(hostname)
        
        # Update peer status file after cleaning
        self.update_peer_status_file()
        
        return removed_peers
    
    def update_peer_status_file(self):
        """Update the peer_discovery.json file with current peer status"""
        try:
            status = {
                "timestamp": int(time.time()),
                "peers": {}
            }
            
            # Add all current peers
            for hostname, identity in self.peer_map.items():
                status["peers"][hostname] = {
                    "destination_hash": RNS.Identity.truncated_hash(identity.get_public_key()).hex(),
                    "last_seen": int(self.last_seen[hostname])
                }
            
            # Write to file
            json_path = f"{config.BASE_DIR}/tak_transmission/reticulum_module/new_implementation/peer_discovery.json"
            with open(json_path, "w") as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error updating peer status file: {e}")

    def shutdown(self):
        """Shutdown peer discovery"""
        self.should_quit = True
        RNS.Transport.deregister_announce_handler(self.announce_handler)


class AnnounceHandler:
    """Handler for Reticulum announcements from other nodes"""
    
    def __init__(self, aspect_filter=None, parent=None):
        """
        Initialize the announce handler
        
        Args:
            aspect_filter (str): Filter for specific aspects
            parent (PeerDiscovery): Parent discovery object
        """
        self.aspect_filter = aspect_filter
        self.parent = parent
        self.logger = logger.get_logger("AnnounceHandler")
    
    def received_announce(self, destination_hash, announced_identity, app_data):
        """
        Handle incoming announces from other nodes
        
        Args:
            destination_hash (bytes): Hash of the source destination
            announced_identity (RNS.Identity): Identity from the announce
            app_data (bytes): Application data in the announce
        """
        try:
            if app_data:
                # Extract hostname from app_data
                hostname = None
                try:
                    if isinstance(app_data, bytes):
                        hostname = app_data.decode('utf-8')
                    else:
                        hostname = str(app_data)
                except:
                    self.logger.warning(f"Could not decode app_data in announce")
                    return
                
                if hostname:
                    if hostname == self.parent.hostname:
                        return  # Skip our own announces
                        
                    identity_str = str(announced_identity)
                    self.logger.info(f"Received announce from {hostname} [{identity_str[:8]}...]")
                    
                    # Check if we've seen this peer before
                    is_new_peer = hostname not in self.parent.peer_map
                    
                    # Add or update peer
                    self.parent.add_peer(hostname, announced_identity, destination_hash)
                    
                    # If this is a new peer, announce ourselves back after a short delay
                    if is_new_peer:
                        self.logger.info(f"New peer discovered: {hostname}")
                        def announce_back():
                            time.sleep(random.uniform(0.5, 1.5))
                            self.parent.announce_presence()
                        threading.Thread(target=announce_back, daemon=True).start()
                        
        except Exception as e:
            self.logger.error(f"Error processing announce: {e}")
