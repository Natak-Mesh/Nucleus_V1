#!/usr/bin/env python3

import RNS
from . import config
from . import logger

class LinkManager:
    def __init__(self, identity, peer_discovery):
        self.logger = logger.get_logger("LinkManager")
        self.identity = identity
        self.peer_discovery = peer_discovery
        self.links = {}
        self.logger.info("Link Manager initialized")
    
    def establish_link(self, hostname):
        # Skip if we already have a link to this peer
        if hostname in self.links:
            return True
        
        # Get peer identity
        peer_identity = self.peer_discovery.get_peer_identity(hostname)
        if not peer_identity:
            return False
        
        try:
            # Create destination
            destination = RNS.Destination(
                peer_identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                config.APP_NAME,
                config.ASPECT
            )
            
            # Create link
            link = RNS.Link(destination)
            
            # Set callbacks
            link.set_link_established_callback(lambda l: self._on_link_established(hostname, l))
            link.set_link_closed_callback(lambda l: self._on_link_closed(hostname, l))
            link.set_packet_callback(self._on_packet)
            
            # Enable physical stats tracking
            link.track_phy_stats(True)
            
            # Store link
            self.links[hostname] = link
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error establishing link to {hostname}: {e}")
            return False
    
    def establish_links_to_all_known_peers(self):
        for hostname in list(self.peer_discovery.peer_map.keys()):
            if hostname != self.peer_discovery.hostname:
                self.establish_link(hostname)
    
    def _on_link_established(self, hostname, link):
        self.logger.info(f"Link established: {RNS.prettyhexrep(link.link_id)}")
        link.identify(self.identity)
    
    def _on_link_closed(self, hostname, link):
        self.logger.info(f"Link closed: {RNS.prettyhexrep(link.link_id)}")
        if hostname in self.links:
            self.links.pop(hostname)
    
    def _on_packet(self, data, packet):
        pass
    
    def incoming_link_established(self, link):
        link_id = RNS.prettyhexrep(link.link_id)
        temp_name = f"incoming_{link_id[:8]}"
        
        # Store with temporary name
        self.links[temp_name] = link
        
        # Setup callbacks
        link.track_phy_stats(True)
        link.set_packet_callback(self._on_packet)
        link.set_link_closed_callback(lambda l: self._on_link_closed(temp_name, l))
        link.set_remote_identified_callback(self._on_remote_identified)
    
    def _on_remote_identified(self, link, identity):
        identity_str = str(identity)
        self.logger.info(f"Remote peer identified: {identity_str}")
        
        # Find temporary name for this link
        temp_name = None
        for hostname, stored_link in list(self.links.items()):
            if stored_link == link:
                temp_name = hostname
                break
        
        # Look up hostname by identity
        real_hostname = self.peer_discovery.get_hostname_by_identity(identity)
        
        # Update mapping if found
        if real_hostname and temp_name and temp_name.startswith("incoming_"):
            self.links[real_hostname] = link
            self.links.pop(temp_name)
    
    def print_link_status(self):
        if not self.links:
            self.logger.info("No active links")
            return
            
        self.logger.info("Current link status:")
        for hostname, link in list(self.links.items()):
            if link.status == RNS.Link.ACTIVE:
                self.logger.info(f"  Link to {hostname}: Status=active, RTT={link.rtt}, RSSI={link.get_rssi()}, SNR={link.get_snr()}")
            elif link.status == RNS.Link.PENDING:
                self.logger.info(f"  Link to {hostname}: Status=pending")
            else:
                self.logger.info(f"  Link to {hostname}: Status={link.status}")
    
    def shutdown(self):
        self.logger.info("Shutting down link manager")
        for hostname, link in list(self.links.items()):
            try:
                link.teardown()
            except Exception as e:
                self.logger.error(f"Error tearing down link to {hostname}: {e}")
