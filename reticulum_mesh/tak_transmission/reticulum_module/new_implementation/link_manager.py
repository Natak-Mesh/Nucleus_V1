#!/usr/bin/env python3

import os
import json
import time
import threading
import RNS
import config
import logger

class LinkHandler:
    """Handler for link callbacks"""
    
    def __init__(self, parent, hostname):
        """
        Initialize the link handler
        
        Args:
            parent (LinkManager): Parent link manager
            hostname (str): Hostname this handler is for
        """
        self.parent = parent
        self.hostname = hostname
        self.logger = logger.get_logger("LinkHandler")
    
    def link_established(self, link):
        """Handle link established event"""
        self.logger.info(f"Link established to {self.hostname}")
    
    def link_closed(self, link):
        """Handle link closed event"""
        self.logger.info(f"Link closed to {self.hostname}")


class LinkManager:
    def __init__(self, identity):
        """Initialize the link manager with an RNS identity."""
        self.logger = logger.get_logger("LinkManager")
        self.identity = identity
        self.active_links = {}  # destination_hash -> (Link, hostname)
        self.running = True
        self.monitor_thread = None

    def start(self):
        """Start the link manager monitoring thread."""
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop(self):
        """Stop the link manager and cleanup."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        for dest_hash in list(self.active_links.keys()):
            self._remove_link(dest_hash)

    def _monitor_loop(self):
        """Main monitoring loop."""
        self.logger.info("Link manager monitor loop started")
        while self.running:
            try:
                self._check_peers()
                self._update_link_status()
                time.sleep(config.LINK_MONITOR_INTERVAL)
            except Exception as e:
                self.logger.error(f"Error in link manager monitor loop: {e}")

    def _check_peers(self):
        """Check peer_discovery.json and maintain links."""
        try:
            self.logger.info("Checking peers from peer_discovery.json")
            with open(os.path.join(os.path.dirname(__file__), "peer_discovery.json"), 'r') as f:
                peer_data = json.load(f)

            current_time = time.time()
            
            # Check for new or updated peers
            for hostname, peer in peer_data.get('peers', {}).items():
                self.logger.info(f"Processing peer {hostname} with hash {peer['destination_hash']}")
                dest_hash = peer['destination_hash']
                last_seen = peer['last_seen']

                # Skip old peers
                if current_time - last_seen > config.PEER_TIMEOUT:
                    continue

                # Establish link if needed
                if dest_hash not in self.active_links:
                    self.logger.info(f"No active link for {hostname}, attempting to establish one")
                    self._establish_link(dest_hash, hostname)

            # Remove stale peers
            for dest_hash in list(self.active_links.keys()):
                hostname = self.active_links[dest_hash][1]
                if hostname not in peer_data.get('peers', {}):
                    self._remove_link(dest_hash)

        except FileNotFoundError:
            self.logger.warning("peer_discovery.json not found")
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON in peer_discovery.json")
        except Exception as e:
            self.logger.error(f"Error checking peers: {e}")

    def _establish_link(self, dest_hash, hostname):
        """Establish a new link to a peer."""
        try:
            # Convert hash to bytes
            dest_hash_bytes = bytes.fromhex(dest_hash)
            
            # Check if we have a path
            has_path = RNS.Transport.has_path(dest_hash_bytes)
            self.logger.info(f"Path check for {hostname}: {'EXISTS' if has_path else 'NO PATH'}")
            
            if not has_path:
                self.logger.info(f"No path to {hostname}, skipping link establishment")
                return

            # Now recall the peer's identity
            peer_identity = RNS.Identity.recall(dest_hash_bytes)
            if not peer_identity:
                self.logger.error(f"Could not recall identity for {hostname}")
                return

            # Create outgoing destination
            outgoing_dest = RNS.Destination(
                peer_identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                config.APP_NAME,
                config.ASPECT
            )

            # Create link handler for callbacks
            handler = LinkHandler(self, hostname)

            # Create link with outgoing destination
            link = RNS.Link(
                outgoing_dest,
                established_callback=handler.link_established,
                closed_callback=handler.link_closed
            )
            self.active_links[dest_hash] = (link, hostname)
            self.logger.info(f"Link setup initiated to {hostname}")

        except Exception as e:
            self.logger.error(f"Error establishing link to {hostname}: {e}")

    def _update_link_status(self):
        """Update link_status.json with current link states."""
        try:
            status_data = {
                "timestamp": time.time(),
                "links": {}
            }

            for dest_hash, (link, hostname) in self.active_links.items():
                status_data["links"][dest_hash] = {
                    "link_id": str(link),
                    "status": self._get_link_status(link),
                    "hostname": hostname
                }

            os.makedirs(os.path.dirname(config.LINK_STATUS_PATH), exist_ok=True)
            with open(config.LINK_STATUS_PATH, 'w') as f:
                json.dump(status_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error updating link status: {e}")

    def _remove_link(self, dest_hash):
        """Remove a link and clean up."""
        if dest_hash in self.active_links:
            link, hostname = self.active_links[dest_hash]
            link.teardown()
            del self.active_links[dest_hash]
            self.logger.info(f"Removed link to {hostname}")

    def link_established(self, link):
        """Handle incoming link established event"""
        try:
            # Get source hash if available
            source_hash = RNS.prettyhexrep(link.destination.hash) if hasattr(link, 'destination') and hasattr(link.destination, 'hash') else "unknown"
            self.logger.info(f"Incoming link established from {source_hash}")
            
            # Create handler for this link
            handler = LinkHandler(self, source_hash)
            
            # Set up callbacks
            link.set_link_closed_callback(handler.link_closed)
            link.set_packet_callback(handler.link_established)
            
            # Store in active links if not already there
            if source_hash not in self.active_links:
                self.active_links[source_hash] = (link, source_hash)
                self.logger.info(f"Added incoming link from {source_hash} to active links")
            else:
                self.logger.info(f"Link from {source_hash} already in active links")
            
        except Exception as e:
            self.logger.error(f"Error handling incoming link: {e}")

    def _get_link_status(self, link):
        """Get the string representation of a link's status."""
        status_map = {
            RNS.Link.PENDING: "PENDING",
            RNS.Link.HANDSHAKE: "HANDSHAKE",
            RNS.Link.ACTIVE: "ACTIVE",
            RNS.Link.STALE: "STALE",
            RNS.Link.CLOSED: "CLOSED"
        }
        return status_map.get(link.status, "UNKNOWN")
