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
    # Initialize peer discovery - this will automatically:
    # - Create identity and destination
    # - Set up the announce handler
    # - Start periodic announces (every ANNOUNCE_INTERVAL seconds)
    # - Handle peer tracking
    # - Clean stale peers (after PEER_TIMEOUT seconds)
    peer_discovery = PeerDiscovery()
    
    try:
        while True:
            time.sleep(10)  # Keep program running
            
    except KeyboardInterrupt:
        print("\nShutting down peer discovery...")
        peer_discovery.shutdown()

if __name__ == "__main__":
    main()
