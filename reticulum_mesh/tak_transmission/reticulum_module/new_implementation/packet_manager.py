#!/usr/bin/env python3

"""
##############################################################################
#                                                                            #
#                          !!! IMPORTANT NOTE !!!                            #
#                                                                            #
#  Destination Handling:                                                     #
#  - PeerDiscovery creates and owns the IN destination                      #
#  - PacketManager must access it through peer_discovery.destination        #
#  - NEVER create new destinations or get through RNS.Reticulum.get_instance #
#  - This ensures we use the same destination PeerDiscovery announced       #
#                                                                            #
##############################################################################
"""

import RNS
from . import config
from . import logger

class PacketManager:
    def __init__(self, peer_discovery=None):
        self.peer_discovery = peer_discovery
        self.logger = logger.get_logger("PacketManager")

    def send_data(self, hostname, data):
        """Send data to a specific hostname"""
        # Get peer identity from peer_discovery
        peer_identity = self.peer_discovery.get_peer_identity(hostname)
        if not peer_identity:
            self.logger.error(f"Cannot send data: No identity found for {hostname}")
            return False

        # Create outbound destination for this peer
        destination = RNS.Destination(
            peer_identity,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            config.APP_NAME,
            config.ASPECT
        )

        # Create and send packet
        packet = RNS.Packet(destination, data)
        success = packet.send()

        if success:
            # Set up basic retry on failure
            packet.set_delivery_callback(lambda r: self.logger.info(f"Packet delivered to {hostname}"))
            packet.set_timeout_callback(lambda r: self.logger.warning(f"Packet to {hostname} failed, should retry"))
            return True

        self.logger.error(f"Failed to send packet to {hostname}")
        return False
