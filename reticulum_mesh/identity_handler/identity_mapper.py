#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
from pathlib import Path

# File paths
HOSTNAME_MAP_PATH = "/home/natak/mesh/hostname_mapping.json"
IDENTITY_MAP_PATH = "/home/natak/reticulum_mesh/identity_handler/identity_map.json"

class IdentityMapper:
    def __init__(self):
        """Initialize the identity mapper service"""
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("IdentityMapper")
        
        # Always start with empty mapping on reboot
        self.mapping = {"nodes": {}}
        
        # Initial load of hostname mapping
        self.load_hostname_mapping()
        
        self.logger.info("Identity Mapper running")

    def load_hostname_mapping(self):
        """Load the hostname mapping file"""
        try:
            if os.path.exists(HOSTNAME_MAP_PATH):
                with open(HOSTNAME_MAP_PATH, 'r') as f:
                    hostname_map = json.load(f)
                    
                # Update our mapping with hostname info
                for mac, info in hostname_map.items():
                    if mac not in self.mapping["nodes"]:
                        self.mapping["nodes"][mac] = {
                            "hostname": info["hostname"],
                            "ip": info["ip"]
                        }
                    else:
                        self.mapping["nodes"][mac].update({
                            "hostname": info["hostname"],
                            "ip": info["ip"]
                        })
                
                self.write_identity_map()
                self.logger.info("Loaded hostname mapping")
            else:
                self.logger.warning(f"Hostname mapping file not found at {HOSTNAME_MAP_PATH}")
        except Exception as e:
            self.logger.error(f"Error loading hostname mapping: {e}")

    def write_identity_map(self):
        """Write the identity mapping file using atomic operation"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(IDENTITY_MAP_PATH), exist_ok=True)
            
            # Write to temp file first
            temp_file = IDENTITY_MAP_PATH + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(self.mapping, f, indent=2)
            
            # Atomic rename
            os.rename(temp_file, IDENTITY_MAP_PATH)
            self.logger.debug("Identity map updated")
        except Exception as e:
            self.logger.error(f"Error writing identity map: {e}")

    def run(self):
        """Main program loop"""
        try:
            self.logger.info("Identity Mapper running, press Ctrl+C to exit")
            while True:
                # Check for hostname mapping changes periodically
                self.load_hostname_mapping()
                time.sleep(10)
                
        except KeyboardInterrupt:
            self.logger.info("Exiting...")

def main():
    """Main entry point"""
    try:
        mapper = IdentityMapper()
        mapper.run()
    except KeyboardInterrupt:
        print("")
        sys.exit(0)

if __name__ == "__main__":
    main()
