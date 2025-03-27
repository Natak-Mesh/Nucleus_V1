#!/usr/bin/env python3

import json
import os
import subprocess
import time

def get_batman_status():
    """Run batctl and parse best paths"""
    try:
        # Run batctl originators command
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

def write_status(status, filename='status.json'):
    """Write status atomically using a temporary file"""
    if status:
        try:
            # Write to temp file
            temp_file = filename + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(status, f, indent=2)
            
            # Atomic rename
            os.rename(temp_file, filename)
            
            # Print node info
            print("Current nodes:")
            for mac, info in status['nodes'].items():
                print(f"  {mac}: last_seen={info['last_seen']}s, throughput={info['throughput']}, nexthop={info['nexthop']}")
        except Exception as e:
            print(f"Error writing status: {e}")

def main():
    print("OGM Monitor starting - updates every 1 second (matching BATMAN OGM interval)")
    print("Press Ctrl+C to exit")
    while True:
        # Get and write status
        status = get_batman_status()
        write_status(status)
        
        # Wait before next update - matches BATMAN's OGM interval
        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
