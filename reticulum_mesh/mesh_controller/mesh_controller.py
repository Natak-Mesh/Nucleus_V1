#!/usr/bin/env python3

import json
import os
import time
from datetime import datetime

class MeshController:
    # Configuration parameters
    FAILURE_THRESHOLD = 3.0    # seconds without OGMs to consider a failure
    FAILURE_COUNT = 3         # consecutive failures to switch to LORA
    RECOVERY_COUNT = 10       # consecutive good readings to switch back to WIFI
    
    # File paths
    STATUS_FILE = '/home/natak/reticulum_mesh/ogm_monitor/status.json'
    MODES_FILE = '/home/natak/reticulum_mesh/mesh_controller/node_modes.json'
    
    def __init__(self):
        print("\nMesh Status Controller Starting")
        print(f"Reading OGM data from: {self.STATUS_FILE}")
        print(f"Writing mode data to: {self.MODES_FILE}")
        print("\nMonitoring mesh status (Press Ctrl+C to exit)...")
        print("\nNode Status:")
        print("-" * 80)
    
    def read_status(self):
        try:
            with open(self.STATUS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"\nError: Status file not found at {self.STATUS_FILE}")
            return None
        except json.JSONDecodeError:
            print(f"\nError: Invalid JSON in status file")
            return None
    
    def read_node_modes(self):
        try:
            with open(self.MODES_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def update(self):
        status_data = self.read_status()
        if not status_data:
            return
        
        # Read current node modes and counts
        stored_data = self.read_node_modes()
        current_time = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{current_time}] Current Status:")
        
        for mac, node_data in status_data['nodes'].items():
            # Initialize state if not present or invalid
            if mac not in stored_data or not isinstance(stored_data[mac], dict):
                stored_data[mac] = {
                    'mode': 'WIFI',
                    'failure_count': 0,
                    'good_count': 0
                }
            
            # Update counts based on current status
            if node_data['last_seen'] > self.FAILURE_THRESHOLD:
                stored_data[mac]['failure_count'] += 1
                stored_data[mac]['good_count'] = 0
                if stored_data[mac]['failure_count'] >= self.FAILURE_COUNT:
                    stored_data[mac]['mode'] = 'LORA'
            else:
                stored_data[mac]['good_count'] += 1
                stored_data[mac]['failure_count'] = 0
                if stored_data[mac]['good_count'] >= self.RECOVERY_COUNT:
                    stored_data[mac]['mode'] = 'WIFI'
            
            # Print status with color coding
            mode_color = '\033[92m' if stored_data[mac]['mode'] == 'WIFI' else '\033[93m'
            print(f"{mac}: last_seen={node_data['last_seen']:.1f}s, "
                  f"mode={mode_color}{stored_data[mac]['mode']}\033[0m "
                  f"[fail={stored_data[mac]['failure_count']}, "
                  f"good={stored_data[mac]['good_count']}]")
        
        self.write_status(stored_data, self.MODES_FILE)

    def write_status(self, node_modes, filename):
        """Write status atomically using a temporary file"""
        try:
            # Write to temp file
            temp_file = filename + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(node_modes, f, indent=2)
            
            # Atomic rename
            os.rename(temp_file, filename)
            
        except Exception as e:
            print(f"Error writing status: {e}")

def main():
    controller = MeshController()
    try:
        while True:
            controller.update()
            time.sleep(1)  # Match OGM monitor update interval
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == '__main__':
    main()
