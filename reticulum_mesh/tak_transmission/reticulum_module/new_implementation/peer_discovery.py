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
        self.peer_map = {}  # hostname -> destination
        self.last_seen = {} # hostname -> timestamp
        
        # Identity mapping
        self.hash_to_hostname = {}  # Hash to hostname mapping
        self.identity_hash_to_hostname = {}  # Identity hash to hostname mapping
        
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
    
    def add_peer(self, hostname, identity, destination_hash=None):
        """
        Add a peer to our peer map
        
        Args:
            hostname (str): The hostname of the peer
            identity (RNS.Identity): The identity of the peer
            destination_hash (bytes, optional): The hash of the peer's destination
        """
        self.logger.info(f"Adding peer: {hostname}")
        
        # Store in peer map and update last seen timestamp
        self.peer_map[hostname] = identity
        self.last_seen[hostname] = time.time()
        
        # Store identity hash mapping
        if hasattr(identity, 'hash'):
            identity_hash = RNS.prettyhexrep(identity.hash)
            self.identity_hash_to_hostname[identity_hash] = hostname
            self.logger.debug(f"Added identity hash mapping: {identity_hash} -> {hostname}")
        
        # Store destination hash mapping if provided
        if destination_hash is not None:
            source_hash = RNS.prettyhexrep(destination_hash)
            self.hash_to_hostname[source_hash] = hostname
            self.logger.debug(f"Added destination hash mapping: {source_hash} -> {hostname}")
    
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
                
                # Update identity hash mapping
                if hasattr(identity, 'hash'):
                    identity_hash = RNS.prettyhexrep(identity.hash)
                    self.identity_hash_to_hostname[identity_hash] = hostname
                    
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
        if hash_str in self.hash_to_hostname:
            return self.hash_to_hostname[hash_str]
        
        return None
    
    def get_hostname_for_mac(self, mac_address):
        """
        Get hostname for a MAC address from identity_map.json
        
        Args:
            mac_address (str): The MAC address to look up
            
        Returns:
            str: The hostname, or None if not found
        """
        try:
            with open(config.IDENTITY_MAP_PATH, 'r') as f:
                identity_map = json.load(f)
                node_data = identity_map.get('nodes', {}).get(mac_address, {})
                return node_data.get('hostname')
        except Exception as e:
            self.logger.error(f"Error reading identity_map.json: {e}")
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
                
                # Remove from peer map
                if hostname in self.peer_map:
                    # Get identity hash before removing
                    if hasattr(self.peer_map[hostname], 'hash'):
                        identity_hash = RNS.prettyhexrep(self.peer_map[hostname].hash)
                        # Remove from identity hash map
                        self.identity_hash_to_hostname.pop(identity_hash, None)
                    
                    # Remove from peer map
                    self.peer_map.pop(hostname, None)
                
                # Find and remove from hash map
                hashes_to_remove = []
                for hash_str, h in self.hash_to_hostname.items():
                    if h == hostname:
                        hashes_to_remove.append(hash_str)
                
                for hash_str in hashes_to_remove:
                    self.hash_to_hostname.pop(hash_str, None)
                
                removed_peers.append(hostname)
        
        return removed_peers
    
    def get_non_wifi_nodes(self):
        """
        Get list of MAC addresses for nodes not in WIFI mode
        
        Returns:
            list: List of MAC addresses
        """
        try:
            with open(config.NODE_MODES_PATH, 'r') as f:
                node_modes = json.load(f)
                return [mac for mac, data in node_modes.items() if data.get('mode') != 'WIFI']
        except Exception as e:
            self.logger.error(f"Error reading node_modes.json: {e}")
            return []
    
    def shutdown(self):
        """Gracefully shutdown peer discovery"""
        self.should_quit = True


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
                # TODO: Identity mapping implementation to be discussed and revisited
                # The remainder of this method will handle processing of announces,
                # associating identity hashes with hostnames, and tracking peer activity
                
                # Placeholder for now - we'll revisit the identity mapping logic
                hostname = app_data.decode() if isinstance(app_data, bytes) else str(app_data)
                self.logger.info(f"Received announce from {hostname} ({RNS.prettyhexrep(destination_hash)})")
                
                # Basic tracking - will be expanded later
                if hostname:
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
        
        except Exception as e:
            self.logger.error(f"Error processing announce: {e}")
