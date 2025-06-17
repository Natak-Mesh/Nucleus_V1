#!/usr/bin/env python3

import json
import os
import subprocess
import time
from datetime import datetime

class SimplifiedOGMMonitor:
    def __init__(self):
        self.status_file = "/home/natak/mesh/ogm_monitor/node_status.json"
        self.local_mac = self.get_local_mac()
        print(f"OGM Monitor starting (local MAC: {self.local_mac})")
        print("Press Ctrl+C to exit")
    
    def get_local_mac(self):
        """Get local MAC from wlan1 interface"""
        try:
            result = subprocess.run(['cat', '/sys/class/net/wlan1/address'], 
                                  capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def get_batman_status(self):
        """Parse batctl o output"""
        try:
            output = subprocess.check_output(['sudo', 'batctl', 'o'], 
                                           universal_newlines=True)
            nodes = {}
            
            for line in output.split('\n'):
                if ' * ' in line:
                    parts = line.strip().split()
                    mac = parts[1]
                    
                    # Skip local node
                    if mac == self.local_mac:
                        continue
                    
                    last_seen = float(parts[2].replace('s', ''))
                    
                    # Extract throughput from parentheses
                    start = line.find('(') + 1
                    end = line.find(')')
                    throughput = float(line[start:end].strip())
                    
                    # Get nexthop
                    nexthop = line[end+1:].split()[0]
                    
                    nodes[mac] = {
                        'last_seen': last_seen,
                        'throughput': throughput,
                        'nexthop': nexthop
                    }
            
            return nodes
        except Exception as e:
            print(f"Error reading batman status: {e}")
            return {}
    
    def write_status(self, nodes):
        """Write node status to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
            
            status = {
                "timestamp": int(time.time()),
                "nodes": nodes
            }
            
            # Write atomically
            temp_file = self.status_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(status, f, indent=2)
            os.rename(temp_file, self.status_file)
            
            # Print status
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"[{current_time}] Found {len(nodes)} nodes")
            for mac, info in nodes.items():
                print(f"  {mac}: last_seen={info['last_seen']:.1f}s, "
                      f"throughput={info['throughput']:.1f}, nexthop={info['nexthop']}")
                      
        except Exception as e:
            print(f"Error writing status: {e}")
    
    def run(self):
        """Main monitoring loop"""
        try:
            while True:
                nodes = self.get_batman_status()
                self.write_status(nodes)
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")

if __name__ == "__main__":
    monitor = SimplifiedOGMMonitor()
    monitor.run()
