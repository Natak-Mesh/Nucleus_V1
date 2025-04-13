#!/usr/bin/env python3

import os
import json
import time
import RNS
import config
import logger

class LinkManager:
    def __init__(self, peer_discovery):
        """Initialize the link manager."""
        self.logger = logger.get_logger("LinkManager")
        self.active_outgoing_links = {}  # hostname -> Link for outgoing connections
        self.active_incoming_links = []  # List of incoming links
        
        # Set up callback for incoming connections on the node's IN destination
        peer_discovery.destination.set_link_established_callback(self._incoming_link_established)

    def _check_peers(self):
        """Check peer_discovery.json and establish links."""
        try:
            # Read peer_discovery.json
            with open(os.path.join(os.path.dirname(__file__), "peer_discovery.json"), 'r') as f:
                peer_data = json.load(f)

            current_time = time.time()
            
            # Process each peer
            for hostname, peer in peer_data.get('peers', {}).items():
                # Skip old peers
                if current_time - peer['last_seen'] > config.PEER_TIMEOUT:
                    continue

                # Skip if we already have an outgoing link
                if hostname in self.active_outgoing_links:
                    continue

                # Get destination hash and convert to bytes
                dest_hash = bytes.fromhex(peer['destination_hash'])

                # Check if we have a path
                if not RNS.Transport.has_path(dest_hash):
                    self.logger.info(f"No path to {hostname}, requesting...")
                    RNS.Transport.request_path(dest_hash)
                    continue

                # Get peer identity
                peer_identity = RNS.Identity.recall(dest_hash)
                if not peer_identity:
                    self.logger.error(f"Could not recall identity for {hostname}")
                    continue

                # Create destination
                destination = RNS.Destination(
                    peer_identity,
                    RNS.Destination.OUT,
                    RNS.Destination.SINGLE,
                    config.APP_NAME,
                    config.ASPECT
                )

                # Create link
                self.logger.info(f"Establishing link to {hostname}")
                link = RNS.Link(
                    destination,
                    established_callback=lambda l, h=hostname: self._link_established(l, h),
                    closed_callback=lambda l, h=hostname: self._link_closed(l, h)
                )
                self.active_outgoing_links[hostname] = link

        except Exception as e:
            self.logger.error(f"Error checking peers: {e}")

    def _incoming_link_established(self, link):
        """Handle incoming link establishment."""
        self.logger.info("Incoming link established")
        # Set callbacks for the incoming link
        link.set_link_closed_callback(lambda l: self._incoming_link_closed(l))
        # Store the incoming link
        self.active_incoming_links.append(link)

    def _incoming_link_closed(self, link):
        """Handle incoming link closed."""
        self.logger.info("Incoming link closed")
        # Remove the link from active incoming links
        if link in self.active_incoming_links:
            self.active_incoming_links.remove(link)

    def _link_established(self, link, hostname):
        """Handle outgoing link established."""
        self.logger.info(f"Link established to {hostname}")

    def _link_closed(self, link, hostname):
        """Handle link closed."""
        self.logger.info(f"Link closed to {hostname}")
        if hostname in self.active_outgoing_links:
            del self.active_outgoing_links[hostname]

    def start(self):
        """Start checking for peers."""
        while True:
            try:
                self._check_peers()
                time.sleep(config.LINK_MONITOR_INTERVAL)
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                time.sleep(5)  # Wait a bit on error

    def stop(self):
        """Stop and clean up links."""
        # Clean up outgoing links
        for hostname, link in list(self.active_outgoing_links.items()):
            link.teardown()
            del self.active_outgoing_links[hostname]
        
        # Clean up incoming links
        for link in self.active_incoming_links:
            link.teardown()
        self.active_incoming_links.clear()
