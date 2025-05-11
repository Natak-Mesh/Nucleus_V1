#!/usr/bin/env python3

"""
Test script to run all required components in sequence:
1. enhanced_ogm_monitor.py (for node status)
2. peer_discovery.py (for destination handling)
3. packet_manager.py (for packet handling)
4. atak_handler.py (for ATAK integration)
"""

import subprocess
import time
import threading
import RNS
import config
import logger
from peer_discovery import PeerDiscovery
from packet_manager import PacketManager

def main():
    print("Starting components...")
    
    # Start OGM monitor with output redirected
    print("Starting OGM Monitor...")
    ogm_process = subprocess.Popen(
        ['python3', '/home/natak/reticulum_mesh/ogm_monitor/enhanced_ogm_monitor.py'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)  # Wait for OGM monitor to initialize
    
    # Initialize peer discovery
    print("Starting Peer Discovery...")
    peer_discovery = PeerDiscovery()
    
    # Initialize packet manager with peer discovery
    print("Starting Packet Manager...")
    packet_manager = PacketManager(peer_discovery)
    packet_manager_thread = threading.Thread(target=packet_manager.run)
    packet_manager_thread.daemon = True
    packet_manager_thread.start()
    
    # Wait for LoRa radio initialization
    print(f"Waiting {config.STARTUP_DELAY} seconds for LoRa radio initialization...")
    time.sleep(config.STARTUP_DELAY)
    
    # Start ATAK handler as subprocess
    print("Starting ATAK Handler...")
    atak_process = subprocess.Popen(
        ['python3', '/home/natak/reticulum_mesh/tak_transmission/atak_module/atak_handler.py']
    )
    
    print("All components started. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down components...")
        ogm_process.terminate()
        ogm_process.wait()
        atak_process.terminate()
        atak_process.wait()
        peer_discovery.shutdown()
        packet_manager.stop()
        print("All components stopped.")

if __name__ == "__main__":
    main()
