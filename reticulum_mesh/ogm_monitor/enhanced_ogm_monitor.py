#!/usr/bin/env python3

import json
import os
import subprocess
import time
from datetime import datetime

class EnhancedOGMMonitor:
    # Configuration parameters (from original mesh_controller)
    FAILURE_THRESHOLD = 3.0    # seconds without OGMs to consider a failure
    FAILURE_COUNT = 3          # consecutive failures to switch to LORA
    RECOVERY_COUNT = 10        # consecutive good readings to switch back to WIFI
    
    # Local node information - exclude from monitoring
    LOCAL_NODE_MAC = "00:c0:ca:b6:92:c0"  # takNode1
    
    # File paths
    HOSTNAME_MAP_PATH = "/home/natak/mesh/hostname_mapping.json"
    STATUS_FILE_PATH = "/home/natak/reticulum_mesh/ogm_monitor/node_status.json"
    
    def __init__(self):
        """Initialize the enhanced OGM monitor"""
        # Set up logging
        self.setup_logging()
        
        # Initialize nodes status tracking
        self.node_status = {}
        
        self.logger.info("Enhanced OGM Monitor starting")
        self.logger.info(f"Reading hostname mapping from: {self.HOSTNAME_MAP_PATH}")
        self.logger.info(f"Writing status to: {self.STATUS_FILE_PATH}")
        self.logger.info("\nMonitoring mesh status (Press Ctrl+C to exit)...")
        
    def setup_logging(self):
        """Set up basic console logging"""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("EnhancedOGMMonitor")
    
    def load_hostname_mapping(self):
        """Load the hostname mapping file"""
        try:
            with open(self.HOSTNAME_MAP_PATH, 'r') as f:
                hostname_mapping = json.load(f)
                return hostname_mapping
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading hostname mapping: {e}")
            return {}
    
    def load_existing_status(self):
        """Load existing node status if available"""
        try:
            if os.path.exists(self.STATUS_FILE_PATH):
                with open(self.STATUS_FILE_PATH, 'r') as f:
                    status_data = json.load(f)
                    return status_data.get("nodes", {})
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return {}
    
    def get_batman_status(self):
        """Run batctl and parse best paths"""
        try:
            # Run batctl originators command - EXACT COPY FROM ORIGINAL
            output = subprocess.check_output(['sudo', 'batctl', 'o'], 
                                         universal_newlines=True)
            
            current_time = time.strftime('%H:%M:%S')
            print(f"\n[{current_time}] Updating status...")
            
            # Parse output
            nodes = {}
            for line in output.split('\n'):
                if ' * ' in line:
                    # Use string operations instead of splitting
                    parts = line.strip().split()
                    mac = parts[1]  # MAC address after *
                    
                    # Skip local node
                    if mac == self.LOCAL_NODE_MAC:
                        continue
                    
                    # Extract last_seen (remove 's' suffix)
                    last_seen = float(parts[2].replace('s', ''))
                    
                    # Extract throughput (find value between parentheses)
                    start = line.find('(') + 1
                    end = line.find(')')
                    throughput = float(line[start:end].strip())
                    
                    # Get nexthop (after throughput parentheses)
                    nexthop = line[end+1:].split()[0]
                    
                    nodes[mac] = {
                        'last_seen': last_seen,
                        'throughput': throughput,
                        'nexthop': nexthop
                    }
            
            return {
                'timestamp': int(time.time()),
                'nodes': nodes
            }
        except Exception as e:
            print(f"Error getting batman status: {e}")
            return None
    
    def update_node_status(self):
        """Update the status of all nodes"""
        # Get hostname mapping (authorized nodes)
        hostname_nodes = self.load_hostname_mapping()
        
        # Load existing status (to preserve counters, etc.)
        existing_status = self.load_existing_status()
        
        # Get current Batman status
        batman_status = self.get_batman_status()
        
        # Check if we have valid Batman status
        if batman_status is None:
            return None  # Return None if Batman status failed
        
        batman_nodes = batman_status.get('nodes', {})
        timestamp = batman_status.get('timestamp', int(time.time()))
        
        # Initialize new status with all nodes from identity map
        node_status = {}
        
        # Process all nodes from hostname mapping (except local node)
        for mac, node_info in hostname_nodes.items():
            # Skip local node
            if mac == self.LOCAL_NODE_MAC:
                continue
                
            # Start with hostname mapping information
            node_data = {
                "hostname": node_info.get("hostname", "unknown"),
                "ip": node_info.get("ip", "unknown"),
            }
            
            # Initialize or preserve counters
            if mac in existing_status:
                node_data["failure_count"] = existing_status[mac].get("failure_count", 0)
                node_data["good_count"] = existing_status[mac].get("good_count", 0)
                node_data["mode"] = existing_status[mac].get("mode", "WIFI")
            else:
                node_data["failure_count"] = 0
                node_data["good_count"] = 0
                node_data["mode"] = "WIFI"  # Default to WiFi
            
            # Update with Batman status if available
            if mac in batman_nodes:
                batman_info = batman_nodes[mac]
                node_data["last_seen"] = batman_info["last_seen"]
                node_data["throughput"] = batman_info["throughput"]
                node_data["nexthop"] = batman_info["nexthop"]
                
                # Update counters based on current status
                if batman_info["last_seen"] > self.FAILURE_THRESHOLD:
                    node_data["failure_count"] += 1
                    node_data["good_count"] = 0
                    if node_data["failure_count"] >= self.FAILURE_COUNT:
                        node_data["mode"] = "LORA"
                else:
                    node_data["good_count"] += 1
                    node_data["failure_count"] = 0
                    if node_data["good_count"] >= self.RECOVERY_COUNT:
                        node_data["mode"] = "WIFI"
            else:
                # Node not seen in Batman, set conservative values
                node_data["last_seen"] = 999.0  # Large value to indicate not seen
                node_data["throughput"] = 0
                node_data["nexthop"] = "unknown"
                
                # Update counters for unseen nodes
                node_data["failure_count"] += 1
                node_data["good_count"] = 0
                if node_data["failure_count"] >= self.FAILURE_COUNT:
                    node_data["mode"] = "LORA"
            
            # Add to status collection
            node_status[mac] = node_data
        
        # Format and return complete status
        return {
            "timestamp": timestamp,
            "nodes": node_status
        }
    
    def write_status(self, status):
        """Write status atomically using a temporary file"""
        if status:  # Only write if status is valid (not None)
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.STATUS_FILE_PATH), exist_ok=True)
                
                # Write to temp file
                temp_file = self.STATUS_FILE_PATH + '.tmp'
                with open(temp_file, 'w') as f:
                    json.dump(status, f, indent=2)
                
                # Atomic rename
                os.rename(temp_file, self.STATUS_FILE_PATH)
                
                # Print status summary
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"[{current_time}] Updated node status")
                
                # Print mode info for each node
                for mac, info in status["nodes"].items():
                    mode_str = info["mode"]
                    mode_color = '\033[92m' if mode_str == 'WIFI' else '\033[93m'  # Green for WIFI, Yellow for LORA
                    
                    if "last_seen" in info:
                        print(f"  {info['hostname']} ({mac}): last_seen={info.get('last_seen', 999.0):.1f}s, "
                              f"mode={mode_color}{mode_str}\033[0m "
                              f"[fail={info['failure_count']}, good={info['good_count']}]")
                    else:
                        print(f"  {info['hostname']} ({mac}): OFFLINE, "
                              f"mode={mode_color}{mode_str}\033[0m "
                              f"[fail={info['failure_count']}, good={info['good_count']}]")
                
            except Exception as e:
                print(f"Error writing status: {e}")
    
    def run(self):
        """Main loop to continuously monitor and update status"""
        try:
            print("Enhanced OGM Monitor running - updates every 1 second (matching BATMAN OGM interval)")
            print("Press Ctrl+C to exit")
            
            while True:
                # Update and write status
                status = self.update_node_status()
                self.write_status(status)
                
                # Wait before next update - matches BATMAN's OGM interval
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")

def main():
    """Main entry point"""
    monitor = EnhancedOGMMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
