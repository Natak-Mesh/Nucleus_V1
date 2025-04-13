#!/usr/bin/env python3

"""
Simple test program for peer discovery functionality.
This demonstrates the basic peer discovery mechanism between nodes.
"""

import RNS
import time
import config
import logger
from peer_discovery import PeerDiscovery

def main():
    # Initialize RNS (will use existing config)
    RNS.Reticulum()
    
    # Create identity and destination
    identity = RNS.Identity()
    destination = RNS.Destination(
        identity,
        RNS.Destination.IN,  # Direction - we want to receive announces
        RNS.Destination.SINGLE,  # Type - for single destination encryption
        config.APP_NAME,  # From your config
        config.ASPECT  # From your config as separate aspect
    )
    
    # Initialize peer discovery - this will automatically:
    # - Set up the announce handler
    # - Start periodic announces (every ANNOUNCE_INTERVAL seconds)
    # - Handle peer tracking
    # - Clean stale peers (after PEER_TIMEOUT seconds)
    peer_discovery = PeerDiscovery(identity, destination)
    
    try:
        while True:
            time.sleep(10)  # Keep program running
            
    except KeyboardInterrupt:
        print("\nShutting down peer discovery...")
        peer_discovery.shutdown()

if __name__ == "__main__":
    main()
