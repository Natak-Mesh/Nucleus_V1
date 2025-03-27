#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
from pathlib import Path

import RNS

# Configuration
OUTPUT_PATH = "/home/natak/reticulum_mesh/rns_stats/rns_status.json"
UPDATE_INTERVAL = 10  # seconds
APP_NAME = "atak"
ASPECT = "cot"

class RNSMonitor:
    def __init__(self, config_path=None, output_path=OUTPUT_PATH):
        """Initialize the RNS Monitor"""
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("RNSMonitor")
        
        # Store configuration
        self.output_path = output_path
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        # Connect to the existing Reticulum instance
        self.reticulum = RNS.Reticulum(config_path)
        
        # Set up announce handler
        self.announce_handler = AnnounceHandler(
            aspect_filter=f"{APP_NAME}.{ASPECT}",
            parent=self
        )
        RNS.Transport.register_announce_handler(self.announce_handler)
        
        self.logger.info("RNS Monitor initialized")

    def collect_and_write_status(self):
        """Collect status information and write to file"""
        try:
            # Build status data structure
            status = {
                "timestamp": int(time.time()),
                "peers": {}
            }
            
            # Add peer information from announce handler
            for dest_hash, peer_info in self.announce_handler.known_peers.items():
                status["peers"][dest_hash] = peer_info.copy()
                
                # Convert destination hash to bytes for API calls
                try:
                    # Strip angle brackets if present
                    clean_hash = dest_hash.strip('<>')
                    dest_hash_bytes = bytes.fromhex(clean_hash)
                    
                    # Add path information if available
                    if RNS.Transport.has_path(dest_hash_bytes):
                        status["peers"][dest_hash]["hops"] = RNS.Transport.hops_to(dest_hash_bytes)
                        
                        next_hop = RNS.Transport.next_hop(dest_hash_bytes)
                        if next_hop:
                            status["peers"][dest_hash]["next_hop"] = RNS.prettyhexrep(next_hop)
                        
                        next_hop_interface = RNS.Transport.next_hop_interface(dest_hash_bytes)
                        if next_hop_interface:
                            status["peers"][dest_hash]["next_hop_interface"] = str(next_hop_interface)
                except Exception as e:
                    self.logger.error(f"Error getting path info for {dest_hash}: {e}")
            
            # Write status atomically using a temporary file
            temp_file = self.output_path + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(status, f, indent=2)
            
            # Atomic rename
            os.rename(temp_file, self.output_path)
            self.logger.debug("Status file updated")
            
        except Exception as e:
            self.logger.error(f"Error collecting status: {e}")

    def run(self):
        """Main program loop"""
        self.logger.info(f"RNS Monitor running, writing status to {self.output_path}")
        try:
            while True:
                self.collect_and_write_status()
                time.sleep(UPDATE_INTERVAL)
        except KeyboardInterrupt:
            self.logger.info("Exiting...")

class AnnounceHandler:
    def __init__(self, aspect_filter=None, parent=None):
        """Initialize the announce handler"""
        self.aspect_filter = aspect_filter
        self.parent = parent
        self.known_peers = {}
        self.logger = logging.getLogger("AnnounceHandler")

    def received_announce(self, destination_hash, announced_identity, app_data, announce_packet_hash=None):
        """Handle incoming announces from other nodes"""
        try:
            # Convert destination hash to string representation
            dest_hash_str = RNS.prettyhexrep(destination_hash)
            
            # Create or update peer info
            peer_info = {
                "last_seen": int(time.time())
            }
            
            # Add app data if present (contains hostname)
            if app_data:
                try:
                    hostname = app_data.decode() if isinstance(app_data, bytes) else str(app_data)
                    peer_info["hostname"] = hostname
                except:
                    pass
            
            # Add RSSI and SNR information if available
            if announce_packet_hash and self.parent and self.parent.reticulum.is_connected_to_shared_instance:
                rssi = self.parent.reticulum.get_packet_rssi(announce_packet_hash)
                snr = self.parent.reticulum.get_packet_snr(announce_packet_hash)
                
                if rssi is not None:
                    peer_info["rssi"] = rssi
                    self.logger.debug(f"RSSI for {dest_hash_str}: {rssi} dBm")
                
                if snr is not None:
                    peer_info["snr"] = snr
                    self.logger.debug(f"SNR for {dest_hash_str}: {snr} dB")
            
            # Store or update peer information
            self.known_peers[dest_hash_str] = peer_info
            
            self.logger.debug(f"Updated peer: {dest_hash_str}")
        except Exception as e:
            self.logger.error(f"Error processing announce: {e}")

def main():
    """Main entry point"""
    try:
        # Parse command line arguments for config path
        config_path = None
        if len(sys.argv) > 1:
            config_path = sys.argv[1]
        
        # Create and run monitor
        monitor = RNSMonitor(config_path)
        monitor.run()
    except KeyboardInterrupt:
        print("")
        sys.exit(0)

if __name__ == "__main__":
    main()
