#!/usr/bin/env python3

"""
Peer discovery module for the Reticulum handler.
Handles peer announcements, discovery, and tracking.
"""

import threading
import time
import random
import socket
import json
import os
import RNS

from . import config
from . import logger

class PeerDiscovery:
    """
    Manages peer discovery and tracking.
    
    This includes:
    - Announcing our presence on the network
    - Tracking peers we've discovered
    - Maintaining peer identity mappings
    """
    
    def __init__(self, identity, destination):
        """
        Initialize the peer discovery module
        
        Args:
            identity (RNS.Identity): Our node's identity
            destination (RNS.Destination): Our destination object
        """
        self.logger = logger.get_logger("PeerDiscovery")
        
        # Store identity and destination
        self.identity = identity
        self.destination = destination
        
        # Runtime state
        self.hostname = socket.gethostname()
        self.peer_map = {}  # hostname -> identity
        self.last_seen = {} # hostname -> timestamp
        
        # Bidirectional identity mapping
        self.identity_hash_to_hostname = {}  # Identity hash -> hostname
        self.hostname_to_identity_hash = {}  # hostname -> Identity hash
        self.dest_hash_to_hostname = {}      # Destination hash -> hostname
        self.hostname_to_dest_hash = {}      # hostname -> Destination hash
        
        # Control flags
        self.should_quit = False
        
        # Set up announce handler
        self.announce_handler = AnnounceHandler(
            aspect_filter=f"{config.APP_NAME}.{config.ASPECT}",
            parent=self
        )
        RNS.Transport.register_announce_handler(self.announce_handler)
        
        # Start announce thread
        self.announce_thread = threading.Thread(target=self.announce_loop, daemon=True)
        self.announce_thread.start()
        
        # Start JSON export thread if configured
        if hasattr(config, 'PEER_STATUS_PATH'):
            self.json_thread = threading.Thread(target=self.json_export_loop, daemon=True)
            self.json_thread.start()
        
        # Announce immediately
        self.announce_presence()
    
    def announce_loop(self):
        """Periodically announce our presence"""
        while not self.should_quit:
            time.sleep(config.ANNOUNCE_INTERVAL)
            self.announce_presence()
    
    def json_export_loop(self):
        """Periodically export peer data to JSON"""
        while not self.should_quit:
            try:
                self.export_to_json()
                time.sleep(30)  # Export every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in JSON export: {e}")
                time.sleep(60)  # On error, wait longer before retrying
    
    def announce_presence(self):
        """Announce our presence to the network"""
        try:
            self.destination.announce(app_data=self.hostname.encode())
            self.logger.debug(f"Sent announce: {self.hostname}")
        except Exception as e:
            self.logger.error(f"Error sending announce: {e}")
    
    def add_peer(self, hostname, identity, destination_hash=None):
        """
        Add a peer to our peer map with bidirectional mappings
        
        Args:
            hostname (str): The hostname of the peer
            identity (RNS.Identity): The identity of the peer
            destination_hash (bytes, optional): The hash of the peer's destination
        """
        self.logger.info(f"Adding peer: {hostname}")
        
        # Store in peer map and update last seen timestamp
        self.peer_map[hostname] = identity
        self.last_seen[hostname] = time.time()
        
        # Store identity hash mapping bidirectionally
        if hasattr(identity, 'hash'):
            identity_hash = RNS.prettyhexrep(identity.hash)
            self.identity_hash_to_hostname[identity_hash] = hostname
            self.hostname_to_identity_hash[hostname] = identity_hash
            self.logger.debug(f"Added identity hash mapping: {identity_hash} <-> {hostname}")
        
        # Store destination hash mapping bidirectionally if provided
        if destination_hash is not None:
            dest_hash = RNS.prettyhexrep(destination_hash)
            self.dest_hash_to_hostname[dest_hash] = hostname
            self.hostname_to_dest_hash[hostname] = dest_hash
            self.logger.debug(f"Added destination hash mapping: {dest_hash} <-> {hostname}")
    
    def update_peer(self, hostname, identity=None, reset_last_seen=True):
        """
        Update a peer's last seen time and optionally its identity
        
        Args:
            hostname (str): The hostname of the peer
            identity (RNS.Identity, optional): New identity if changed
            reset_last_seen (bool): Whether to update the last seen timestamp
        
        Returns:
            bool: True if successful, False if peer not found
        """
        # Check if peer exists
        if hostname not in self.peer_map:
            return False
        
        # Update identity if provided
        if identity is not None:
            old_identity = self.peer_map[hostname]
            
            # Check if identity changed
            if old_identity.get_public_key() != identity.get_public_key():
                self.logger.info(f"Identity changed for {hostname}")
                self.peer_map[hostname] = identity
                
                # Update identity hash mappings bidirectionally
                if hasattr(identity, 'hash'):
                    # Remove old mapping if it exists
                    if hostname in self.hostname_to_identity_hash:
                        old_hash = self.hostname_to_identity_hash[hostname]
                        self.identity_hash_to_hostname.pop(old_hash, None)
                    
                    # Add new mapping
                    identity_hash = RNS.prettyhexrep(identity.hash)
                    self.identity_hash_to_hostname[identity_hash] = hostname
                    self.hostname_to_identity_hash[hostname] = identity_hash
                    
                # Return True to indicate identity changed
                return True
        
        # Update last seen time if requested
        if reset_last_seen:
            self.last_seen[hostname] = time.time()
            
        return False  # Identity did not change
    
    def get_peer_identity(self, hostname):
        """
        Get a peer's identity
        
        Args:
            hostname (str): The hostname to look up
            
        Returns:
            RNS.Identity: The peer's identity, or None if not found
        """
        return self.peer_map.get(hostname)
    
    def get_peer_by_any_hash(self, hash_str):
        """
        Find a peer by any type of hash
        
        Args:
            hash_str (str): The hash string to look up
            
        Returns:
            tuple: (hostname, identity) if found, or (None, None) if not found
        """
        # Try identity hash first
        hostname = self.identity_hash_to_hostname.get(hash_str)
        if hostname:
            return hostname, self.peer_map.get(hostname)
            
        # Then try destination hash
        hostname = self.dest_hash_to_hostname.get(hash_str)
        if hostname:
            return hostname, self.peer_map.get(hostname)
            
        return None, None
    
    def get_hostname_from_hash(self, hash_str):
        """
        Get a hostname from a hash
        
        Args:
            hash_str (str): The hash string to look up
            
        Returns:
            str: The hostname, or None if not found
        """
        # First check the identity hash map
        if hash_str in self.identity_hash_to_hostname:
            return self.identity_hash_to_hostname[hash_str]
        
        # Then check the destination hash map
        if hash_str in self.dest_hash_to_hostname:
            return self.dest_hash_to_hostname[hash_str]
        
        return None
    
    def clean_stale_peers(self):
        """
        Remove stale peers that haven't been seen recently
        
        Returns:
            list: List of hostnames that were removed
        """
        removed_peers = []
        current_time = time.time()
        
        for hostname in list(self.last_seen.keys()):
            if current_time - self.last_seen[hostname] > config.PEER_TIMEOUT:
                self.logger.info(f"Removing stale peer: {hostname}")
                
                # Remove from peer map and last seen
                self.last_seen.pop(hostname, None)
                
                # Remove identity hash mappings
                if hostname in self.hostname_to_identity_hash:
                    identity_hash = self.hostname_to_identity_hash[hostname]
                    self.identity_hash_to_hostname.pop(identity_hash, None)
                    self.hostname_to_identity_hash.pop(hostname, None)
                
                # Remove destination hash mappings
                if hostname in self.hostname_to_dest_hash:
                    dest_hash = self.hostname_to_dest_hash[hostname]
                    self.dest_hash_to_hostname.pop(dest_hash, None)
                    self.hostname_to_dest_hash.pop(hostname, None)
                
                # Remove from peer map
                if hostname in self.peer_map:
                    self.peer_map.pop(hostname, None)
                
                removed_peers.append(hostname)
        
        return removed_peers
    
    def export_to_json(self):
        """Export peer information to JSON file for IPC"""
        try:
            if not hasattr(config, 'PEER_STATUS_PATH'):
                return
                
            # Create output data structure
            output = {
                "last_updated": int(time.time()),
                "peers": {}
            }
            
            # Add data for each peer
            for hostname, identity in self.peer_map.items():
                if hostname in self.last_seen:
                    peer_data = {
                        "last_seen": self.last_seen[hostname]
                    }
                    
                    if hostname in self.hostname_to_identity_hash:
                        peer_data["identity_hash"] = self.hostname_to_identity_hash[hostname]
                        
                    if hostname in self.hostname_to_dest_hash:
                        peer_data["destination_hash"] = self.hostname_to_dest_hash[hostname]
                    
                    output["peers"][hostname] = peer_data
            
            # Write to file (atomic)
            directory = os.path.dirname(config.PEER_STATUS_PATH)
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                
            temp_path = f"{config.PEER_STATUS_PATH}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(output, f, indent=2)
                
            os.replace(temp_path, config.PEER_STATUS_PATH)
            
            self.logger.debug(f"Exported peer status to {config.PEER_STATUS_PATH}")
            
        except Exception as e:
            self.logger.error(f"Error exporting peer status to JSON: {e}")
    
    def shutdown(self):
        """Gracefully shutdown peer discovery"""
        self.should_quit = True
        
        # Export one last time before shutting down
        if hasattr(config, 'PEER_STATUS_PATH'):
            try:
                self.export_to_json()
            except:
                pass


class AnnounceHandler:
    """
    Handler for Reticulum announcements from other nodes
    """
    
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
        self.known_peers = set()  # Track peers we've seen
    
    def received_announce(self, destination_hash, announced_identity, app_data):
        """
        Handle incoming announces from other nodes
        
        Args:
            destination_hash (bytes): Hash of the source destination
            announced_identity (RNS.Identity): Identity from the announce
            app_data (bytes): Application data in the announce
        """
        try:
            # Check if this is a new peer we haven't seen before
            is_new_peer = destination_hash not in self.known_peers
            
            # Store the peer hash
            self.known_peers.add(destination_hash)
            
            if app_data:
                # Process the announce data to extract hostname
                hostname = None
                try:
                    if isinstance(app_data, bytes):
                        hostname = app_data.decode('utf-8')
                    else:
                        hostname = str(app_data)
                except:
                    self.logger.warning(f"Could not decode app_data in announce from {RNS.prettyhexrep(destination_hash)}")
                    return
                
                if hostname:
                    self.logger.info(f"Received announce from {hostname} ({RNS.prettyhexrep(destination_hash)})")
                    
                    # Store in parent's peer map
                    self.parent.add_peer(hostname, announced_identity, destination_hash)
                    
                    # If new peer, respond with our own announce after a delay
                    if is_new_peer:
                        self.logger.info(f"New peer discovered: {hostname}")
                        
                        # Send our own announce after a small random delay
                        def delayed_announce():
                            delay = random.uniform(0.5, 2.0)
                            self.logger.info(f"Sending announce after {delay:.1f}s delay")
                            time.sleep(delay)
                            self.parent.announce_presence()
                            self.logger.info(f"Announce sent in response to peer discovery")
                        
                        # Start announce thread
                        thread = threading.Thread(target=delayed_announce, daemon=True)
                        thread.start()
                else:
                    self.logger.warning(f"Received announce with empty hostname from {RNS.prettyhexrep(destination_hash)}")
            else:
                self.logger.warning(f"Received announce with no app_data from {RNS.prettyhexrep(destination_hash)}")
        
        except Exception as e:
            self.logger.error(f"Error processing announce: {e}")
