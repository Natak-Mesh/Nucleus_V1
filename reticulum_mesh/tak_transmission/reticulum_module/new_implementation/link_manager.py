#!/usr/bin/env python3

"""
Link manager module for the Reticulum handler.
Handles link establishment, monitoring, and maintenance.
"""

import threading
import time
import RNS

from . import config
from . import logger

class LinkManager:
    """
    Manages Reticulum links to peers.
    
    This includes:
    - Establishing and re-establishing links
    - Monitoring link health and status
    - Managing link callbacks and events
    """
    
    def __init__(self, identity=None, peer_discovery=None):
        """
        Initialize the link manager
        
        Args:
            identity (RNS.Identity): Our node's identity
            peer_discovery (PeerDiscovery): Reference to peer discovery module
        """
        self.logger = logger.get_logger("LinkManager")
        
        # Store identity and peer discovery reference
        self.identity = identity
        self.peer_discovery = peer_discovery
        
        # Runtime state
        self.node_links = {}      # hostname -> link object
        self.link_to_hostname = {} # Direct link object to hostname mapping
        
        # Control flags
        self.should_quit = False
        
        # Callbacks
        self.on_incoming_packet_callback = None
        self.on_link_established_callback = None
        self.on_link_closed_callback = None
        
        # Start link monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_links, daemon=True)
        self.monitor_thread.start()
    
    def set_on_incoming_packet_callback(self, callback):
        """Set callback for incoming packets on any link"""
        self.on_incoming_packet_callback = callback
    
    def set_on_link_established_callback(self, callback):
        """Set callback for when a link is established"""
        self.on_link_established_callback = callback
    
    def set_on_link_closed_callback(self, callback):
        """Set callback for when a link is closed"""
        self.on_link_closed_callback = callback
    
    def establish_link(self, hostname):
        """
        Establish a link to a specific node
        
        Args:
            hostname (str): The hostname of the node to connect to
            
        Returns:
            bool: True if link establishment started, False otherwise
        """
        try:
            # Get peer identity from discovery
            if self.peer_discovery is None:
                self.logger.error(f"Cannot establish link to {hostname}: No peer discovery module")
                return False
            
            # Get the peer's identity
            peer_identity = self.peer_discovery.get_peer_identity(hostname)
            if peer_identity is None:
                self.logger.warning(f"Cannot establish link to unknown peer: {hostname}")
                return False
            
            # Log that we're starting the link establishment
            self.logger.info(f"Starting link establishment to node: {hostname}")
            
            # Create outgoing destination
            outgoing_dest = RNS.Destination(
                peer_identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                config.APP_NAME,
                config.ASPECT
            )
            
            # Create link with callbacks
            link = RNS.Link(
                outgoing_dest, 
                established_callback=lambda l: self.outgoing_link_established(l, hostname),
                closed_callback=lambda l: self.link_closed(l)
            )
            
            # Adjust the keepalive interval to maintain the link better
            link.KEEPALIVE = config.LINK_KEEPALIVE
            
            # Enable physical layer statistics tracking if available
            link.track_phy_stats(True)
            
            # Store link in our map - use a special marker to indicate "establishing"
            self.node_links[hostname] = link
            self.link_to_hostname[link] = hostname
            
            self.logger.info(f"Link establishment process started for node: {hostname}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error establishing link to {hostname}: {e}")
            return False
    
    def establish_links_to_non_wifi_nodes(self):
        """
        Establish links to all known non-WiFi nodes
        
        Returns:
            int: Number of link establishment attempts started
        """
        count = 0
        
        if self.peer_discovery is None:
            self.logger.error("Cannot establish links: No peer discovery module")
            return 0
        
        # Get non-WiFi nodes
        non_wifi_macs = self.peer_discovery.get_non_wifi_nodes()
        
        # For each non-WiFi MAC, get the hostname and establish a link
        for mac in non_wifi_macs:
            hostname = self.peer_discovery.get_hostname_for_mac(mac)
            
            if hostname and hostname not in self.node_links:
                if self.establish_link(hostname):
                    count += 1
        
        return count
    
    def is_link_active(self, hostname):
        """
        Check if a link to a hostname is active
        
        Args:
            hostname (str): The hostname to check
            
        Returns:
            bool: True if link is active, False otherwise
        """
        if hostname not in self.node_links:
            return False
        
        link = self.node_links[hostname]
        
        # Check if link is active
        if hasattr(link, 'status'):
            return link.status == RNS.Link.ACTIVE
        
        return False
    
    def get_link_stats(self, hostname):
        """
        Get statistics for a link
        
        Args:
            hostname (str): The hostname to get stats for
            
        Returns:
            dict: Dictionary of link statistics, or None if link not found
        """
        if hostname not in self.node_links:
            return None
        
        link = self.node_links[hostname]
        stats = {}
        
        # Collect various link stats
        try:
            if hasattr(link, 'get_age'):
                stats['age'] = link.get_age()
            
            if hasattr(link, 'inactive_for'):
                stats['inactive'] = link.inactive_for()
            
            if hasattr(link, 'get_mtu'):
                stats['mtu'] = link.get_mtu()
                
            if hasattr(link, 'get_expected_rate'):
                stats['rate'] = link.get_expected_rate()
            
            if hasattr(link, 'get_rssi') and link.get_rssi() is not None:
                stats['rssi'] = link.get_rssi()
                
            if hasattr(link, 'get_snr') and link.get_snr() is not None:
                stats['snr'] = link.get_snr()
                
            if hasattr(link, 'status'):
                stats['active'] = (link.status == RNS.Link.ACTIVE)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting link stats for {hostname}: {e}")
            return {}
    
    def send_data(self, hostname, data):
        """
        Send data over an established link
        
        Args:
            hostname (str): The hostname to send to
            data (bytes): The data to send
            
        Returns:
            tuple: (success, receipt) - success is boolean, receipt is the packet receipt or None
        """
        # Check if we have a link to this hostname
        if hostname not in self.node_links:
            self.logger.warning(f"Cannot send data: No link to {hostname}")
            return False, None
        
        link = self.node_links[hostname]
        
        # Make sure the link is established before sending
        if not hasattr(link, 'status') or link.status != RNS.Link.ACTIVE:
            self.logger.warning(f"Cannot send data: Link to {hostname} is not active")
            return False, None
        
        try:
            # Create packet with data
            packet = RNS.Packet(link, data)
            
            # Send packet and get receipt
            receipt = packet.send()
            
            if receipt:
                self.logger.info(f"Sent {len(data)} bytes to {hostname}")
                return True, receipt
            else:
                self.logger.warning(f"Failed to send packet to {hostname}")
                return False, None
                
        except Exception as e:
            self.logger.error(f"Error sending data over link to {hostname}: {e}")
            return False, None
    
    def tear_down_link(self, hostname):
        """
        Tear down a link to a specific hostname
        
        Args:
            hostname (str): The hostname to disconnect from
            
        Returns:
            bool: True if successful, False otherwise
        """
        if hostname not in self.node_links:
            self.logger.warning(f"Cannot tear down link: No link to {hostname}")
            return False
        
        link = self.node_links[hostname]
        
        try:
            # Remove from our mappings
            self.node_links.pop(hostname, None)
            self.link_to_hostname.pop(link, None)
            
            # Tear down the link
            link.teardown()
            self.logger.info(f"Tore down link to {hostname}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error tearing down link to {hostname}: {e}")
            return False
    
    def monitor_links(self):
        """Thread function to monitor link status and health"""
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
                            # Get link stats
                            stats = self.get_link_stats(hostname)
                            
                            if stats:
                                # Format stats string
                                stats_parts = []
                                if 'age' in stats:
                                    stats_parts.append(f"Age: {stats['age']:.1f}s")
                                if 'inactive' in stats:
                                    stats_parts.append(f"Inactive: {stats['inactive']:.1f}s")
                                if 'mtu' in stats:
                                    stats_parts.append(f"MTU: {stats['mtu']}")
                                if 'rate' in stats:
                                    stats_parts.append(f"Rate: {stats['rate']:.2f} bps")
                                if 'rssi' in stats:
                                    stats_parts.append(f"RSSI: {stats['rssi']} dBm")
                                if 'snr' in stats:
                                    stats_parts.append(f"SNR: {stats['snr']} dB")
                                
                                # Join stats with commas
                                stats_str = ", ".join(stats_parts)
                                
                                # Log link status
                                status_str = "ACTIVE" if stats.get('active', False) else "NOT ACTIVE"
                                self.logger.info(f"Link to {hostname}: {status_str} [{stats_str}]")
                                
                                # If link is not active but should be, try to re-establish
                                if not stats.get('active', False):
                                    self.logger.warning(f"Link to {hostname} is not active, attempting to re-establish")
                                    
                                    # Remove from our mappings
                                    self.node_links.pop(hostname, None)
                                    self.link_to_hostname.pop(link, None)
                                    
                                    # Try to establish a new link
                                    self.establish_link(hostname)
                            else:
                                self.logger.warning(f"Link to {hostname} has no stats available")
                        except Exception as e:
                            self.logger.error(f"Error checking link to {hostname}: {e}")
                
                # Sleep between link status checks
                time.sleep(config.LINK_MONITOR_INTERVAL)  
                
            except Exception as e:
                self.logger.error(f"Error in link monitoring: {e}")
                time.sleep(60)  # In case of error, still wait before trying again
    
    def outgoing_link_established(self, link, hostname):
        """
        Callback when an outgoing link is established
        
        Args:
            link (RNS.Link): The established link
            hostname (str): The hostname this link is connected to
        """
        try:
            self.logger.info(f"LINK_ESTABLISHED: Outgoing link to {hostname}")
            
            # IMPORTANT: Store the link-to-hostname mapping right away
            # This is critical for proper packet source identification
            self.link_to_hostname[link] = hostname
            
            # Set packet callback for the link
            link.set_packet_callback(self.link_packet_received)
            
            # Explicitly identify ourselves to the remote peer
            self.logger.info(f"Identifying to remote peer {hostname}")
            link.identify(self.identity)
            
            # Call the callback if set
            if self.on_link_established_callback:
                self.on_link_established_callback(link, hostname, is_outgoing=True)
                
        except Exception as e:
            self.logger.error(f"Error in outgoing link established callback: {e}")
    
    def incoming_link_established(self, link):
        """
        Callback when an incoming link is established
        
        Args:
            link (RNS.Link): The established link
        """
        try:
            # Try to find hostname if possible
            hostname = "unknown"
            source_hash = "unknown"
            
            # Check by destination hash
            if hasattr(link, 'destination') and hasattr(link.destination, 'hash'):
                source_hash = RNS.prettyhexrep(link.destination.hash)
                
                # Try to find hostname through peer discovery
                if self.peer_discovery:
                    hostname = self.peer_discovery.get_hostname_from_hash(source_hash)
            
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
            
            # Store in our mappings
            if hostname != "unknown":
                self.node_links[hostname] = link
                self.link_to_hostname[link] = hostname
            
            # Call the callback if set
            if self.on_link_established_callback:
                self.on_link_established_callback(link, hostname, is_outgoing=False)
                
        except Exception as e:
            self.logger.error(f"Error in incoming link established callback: {e}")
    
    def remote_peer_identified(self, link, identity):
        """
        Callback when a remote peer has identified itself on a link
        
        Args:
            link (RNS.Link): The link the peer identified on
            identity (RNS.Identity): The identity of the remote peer
        """
        try:
            # Convert identity hash to string
            identity_hash = RNS.prettyhexrep(identity.hash)
            self.logger.info(f"Remote peer identified with hash: {identity_hash}")
            
            # TODO: This part will be revisited after discussing identity mapping
            
            # Placeholder functionality - look up hostname
            hostname = None
            
            # First check our link map
            if link in self.link_to_hostname:
                hostname = self.link_to_hostname[link]
            
            # If still unknown, check with peer discovery
            if hostname is None and self.peer_discovery:
                hostname = self.peer_discovery.get_hostname_from_hash(identity_hash)
            
            # If still unknown, use hash as a temporary identifier
            if hostname is None:
                short_hash = identity_hash[:8]
                hostname = f"node-{short_hash}"
                self.logger.info(f"Assigning temporary hostname {hostname} to newly identified peer")
            
            # Store in mappings if not already there
            if hostname not in self.node_links:
                self.node_links[hostname] = link
            
            if link not in self.link_to_hostname:
                self.link_to_hostname[link] = hostname
            
            self.logger.info(f"REMOTE_IDENTIFIED: Peer on link identified as {hostname}")
            
            # Update peer in discovery if available
            if self.peer_discovery:
                if hostname in self.peer_discovery.peer_map:
                    # Update existing peer
                    self.peer_discovery.update_peer(hostname, identity)
                else:
                    # Add new peer
                    self.peer_discovery.add_peer(hostname, identity)
                
        except Exception as e:
            self.logger.error(f"Error in remote peer identification: {e}")
    
    def link_closed(self, link):
        """
        Callback when a link is closed
        
        Args:
            link (RNS.Link): The link that closed
        """
        try:
            # Find the hostname associated with this link
            hostname = self.link_to_hostname.get(link, "unknown")
            
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
            
            self.logger.info(f"LINK_CLOSED: Link with {hostname} closed (Age: {link_age}, Inactive: {inactive_time})")
            
            # Clean up mappings
            self.link_to_hostname.pop(link, None)
            
            if hostname != "unknown":
                self.node_links.pop(hostname, None)
                
                # Call the callback if set
                if self.on_link_closed_callback:
                    self.on_link_closed_callback(link, hostname)
                
                # Try to re-establish the link if it's a non-WiFi node
                if self.peer_discovery:
                    non_wifi_macs = self.peer_discovery.get_non_wifi_nodes()
                    for mac in non_wifi_macs:
                        if self.peer_discovery.get_hostname_for_mac(mac) == hostname:
                            self.logger.info(f"Attempting to re-establish link to non-WiFi node: {hostname}")
                            self.establish_link(hostname)
                            break
                
        except Exception as e:
            self.logger.error(f"Error in link closed callback: {e}")
    
    def link_packet_received(self, data, packet):
        """
        Handle a packet received over a link
        
        Args:
            data (bytes): The packet data
            packet (RNS.Packet): The packet object
        """
        try:
            # Find the source hostname
            hostname = "unknown"
            
            # Check link-to-hostname mapping first
            if packet.link in self.link_to_hostname:
                hostname = self.link_to_hostname[packet.link]
            
            # If hostname is still unknown but we have peer discovery, try to find it
            if hostname == "unknown" and self.peer_discovery and hasattr(packet, 'source_hash'):
                source_hash = RNS.prettyhexrep(packet.source_hash)
                hostname = self.peer_discovery.get_hostname_from_hash(source_hash)
            
            # Get source hash if available
            source_hash = RNS.prettyhexrep(packet.source_hash) if hasattr(packet, 'source_hash') else "unknown"
            
            # Get packet size
            data_size = len(data)
            
            # Log physical layer stats if available
            phy_stats = ""
            if hasattr(packet, "rssi") and packet.rssi is not None:
                phy_stats += f" [RSSI {packet.rssi} dBm]"
            if hasattr(packet, "snr") and packet.snr is not None:
                phy_stats += f" [SNR {packet.snr} dB]"
            
            # Log link quality if available
            link_quality = ""
            if hasattr(packet.link, "get_q") and packet.link.get_q() is not None:
                link_quality = f" [Link Quality {packet.link.get_q():.2f}]"
            
            # Log link MTU if available
            link_mtu = ""
            if hasattr(packet.link, "get_mtu") and packet.link.get_mtu() is not None:
                link_mtu = f" [Link MTU {packet.link.get_mtu()} bytes]"
            
            self.logger.info(f"LINK_DATA_RECEIVED: Size={data_size} bytes, Source={hostname}({source_hash}){phy_stats}{link_quality}{link_mtu}")
            
            # Call the callback if set
            if self.on_incoming_packet_callback:
                self.on_incoming_packet_callback(data, packet, hostname)
                
        except Exception as e:
            self.logger.error(f"Error processing incoming packet: {e}")
    
    def shutdown(self):
        """Gracefully tear down all links and stop monitoring"""
        self.should_quit = True
        
        # Tear down all links
        for hostname, link in list(self.node_links.items()):
            try:
                self.logger.info(f"Tearing down link to {hostname} during shutdown")
                link.teardown()
            except Exception as e:
                self.logger.error(f"Error tearing down link to {hostname}: {e}")
        
        # Clear mappings
        self.node_links.clear()
        self.link_to_hostname.clear()
