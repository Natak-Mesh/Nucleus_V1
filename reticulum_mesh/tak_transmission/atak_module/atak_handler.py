#!/usr/bin/env python3

"""
ATAKHandler handles compression and transmission of TAK Protocol packets.
"""

import os
import socket
import struct
import time
import hashlib
import threading
import json
from collections import deque
from typing import Dict, Tuple
from utils.compression import compress_cot_packet, decompress_cot_packet

# MulticastSocketManager from atak_relay_resilient.py
class MulticastSocketManager:
    def __init__(self):
        """Initialize the socket manager with persistent sockets"""
        self.sockets = {}  # (addr, port) -> socket
        self.lock = threading.Lock()
        self.setup_persistent_sockets()

    def get_br0_ip(self):
        """Get the IP address of the br0 interface"""
        try:
            import subprocess
            output = subprocess.check_output("ip -4 addr show br0 | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'", shell=True).decode().strip()
            if output:
                return output
        except Exception as e:
            print(f"Error getting br0 IP: {e}")
        return None

    def setup_persistent_sockets(self):
        """Set up persistent UDP sockets for ATAK multicast addresses"""
        with self.lock:
            # Close any existing sockets first
            self.cleanup_sockets()
            
            br0_ip = self.get_br0_ip()
            if br0_ip:
                print(f"Using br0 interface with IP {br0_ip} for multicast")
            else:
                print("Warning: Could not determine br0 IP address")
            
            for addr, port in zip(MULTICAST_ADDRS, MULTICAST_PORTS):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
                    sock.setblocking(False)
                    
                    if br0_ip:
                        sock.bind((br0_ip, 0))
                    
                    self.sockets[(addr, port)] = sock
                    print(f"Created persistent socket for {addr}:{port}")
                except Exception as e:
                    print(f"Error creating socket for {addr}:{port}: {e}")

    def send_packet(self, data: bytes, addr: str, port: int) -> bool:
        """Send a packet using the persistent socket"""
        with self.lock:
            sock = self.sockets.get((addr, port))
            if not sock:
                # Socket missing - try to recreate
                self.setup_persistent_sockets()
                sock = self.sockets.get((addr, port))
                if not sock:
                    return False

            try:
                sock.sendto(data, (addr, port))
                return True
            except BlockingIOError:
                # Would block - try again next cycle
                return False
            except Exception as e:
                print(f"Send error to {addr}:{port}: {e}")
                # Socket error - mark for recreation
                self.cleanup_socket(addr, port)
                return False

    def cleanup_socket(self, addr: str, port: int):
        """Clean up a specific socket"""
        try:
            sock = self.sockets.pop((addr, port), None)
            if sock:
                sock.close()
        except Exception:
            pass

    def cleanup_sockets(self):
        """Clean up all sockets"""
        for (addr, port) in list(self.sockets.keys()):
            self.cleanup_socket(addr, port)

# ATAK multicast addresses and ports
# Both output (send) and input (receive) ports
MULTICAST_ADDRS = ["224.10.10.1", "224.10.10.1", "239.2.3.1", "239.2.3.1", "239.5.5.55", "239.5.5.55"]
MULTICAST_PORTS = [17012, 17013, 6969, 6970, 7171, 7172]

# Define which ports are for output (locally generated packets)
OUTPUT_PORTS = [17012, 6969, 7171]

class ATAKHandler:
    def __init__(self, shared_dir: str = "/home/natak/reticulum_mesh/tak_transmission/shared"):
        """Initialize handler"""
        # Socket handling
        self.sockets: Dict[Tuple[str, int], socket.socket] = {}
        self.lock = threading.Lock()
        
        # Directory setup
        self.pending_dir = f"{shared_dir}/pending"
        self.incoming_dir = f"{shared_dir}/incoming"
        self.processing_dir = f"{shared_dir}/processing"
        os.makedirs(self.pending_dir, exist_ok=True)
        os.makedirs(self.incoming_dir, exist_ok=True)
        os.makedirs(self.processing_dir, exist_ok=True)
            
        # Deduplication setup
        self.MAX_RECENT_PACKETS = 1000
        self.recent_packets = deque(maxlen=self.MAX_RECENT_PACKETS)
        
        # Node modes path
        self.node_modes_path = "/home/natak/reticulum_mesh/mesh_controller/node_modes.json"
        
        # Set up multicast sockets for receiving
        self.setup_multicast_sockets()
        
        # Set up socket manager for sending
        self.socket_manager = MulticastSocketManager()
        
    def get_br0_ip(self):
        """Get the IP address of the br0 interface"""
        try:
            import subprocess
            output = subprocess.check_output("ip -4 addr show br0 | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'", shell=True).decode().strip()
            if output:
                return output
        except Exception as e:
            print(f"Error getting br0 IP: {e}")
        return None
    
    def setup_multicast_sockets(self) -> None:
        """Set up UDP sockets for ATAK multicast"""
        # Get the IP address of the br0 interface
        br0_ip = self.get_br0_ip()
        if br0_ip:
            print(f"Using br0 interface with IP {br0_ip} for multicast")
        else:
            print("Warning: Could not determine br0 IP address, falling back to INADDR_ANY")
            
        for addr, port in zip(MULTICAST_ADDRS, MULTICAST_PORTS):
            try:
                # Create socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('', port))
                
                # Add socket to multicast group
                if br0_ip:
                    # Use br0 interface explicitly
                    mreq = struct.pack("4s4s", socket.inet_aton(addr), socket.inet_aton(br0_ip))
                else:
                    # Fall back to INADDR_ANY (though this will likely fail on some nodes)
                    mreq = struct.pack("4sl", socket.inet_aton(addr), socket.INADDR_ANY)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                
                self.sockets[(addr, port)] = sock
                print(f"SETUP: Listening on {addr}:{port}")
            except Exception as e:
                print(f"ERROR: Failed to setup socket for {addr}:{port}: {e}")

    def is_duplicate(self, data: bytes) -> bool:
        """Check if packet has been seen recently"""
        packet_hash = hashlib.md5(data).hexdigest()
        if packet_hash in self.recent_packets:
            print(f"HASH: Found duplicate packet with hash {packet_hash}")
            return True
        print(f"HASH: New packet with hash {packet_hash}")
        self.recent_packets.append(packet_hash)
        return False
    
    def get_non_wifi_nodes(self):
        """Get list of MAC addresses for nodes not in WIFI mode"""
        try:
            with open(self.node_modes_path, 'r') as f:
                node_modes = json.load(f)
                return [mac for mac, data in node_modes.items() if data.get('mode') != 'WIFI']
        except Exception as e:
            print(f"ERROR: Reading node_modes.json: {e}")
            return []
            
    def cleanup_shared_directories(self):
        """Clean up all files in shared directories when no nodes are in LoRa mode"""
        try:
            # Clean pending directory
            for filename in os.listdir(self.pending_dir):
                path = os.path.join(self.pending_dir, filename)
                os.remove(path)
                print(f"CLEANUP: Removed {path}")
                
            # Clean incoming directory
            for filename in os.listdir(self.incoming_dir):
                path = os.path.join(self.incoming_dir, filename)
                os.remove(path)
                print(f"CLEANUP: Removed {path}")
                
            # Clean processing directory
            for filename in os.listdir(self.processing_dir):
                path = os.path.join(self.processing_dir, filename)
                os.remove(path)
                print(f"CLEANUP: Removed {path}")
                
            print("CLEANUP: All shared directories cleaned")
        except Exception as e:
            print(f"ERROR: Cleaning shared directories: {e}")
    
    def process_packet(self, data: bytes, packet_id: str = None, source_addr: str = None, source_port: int = None) -> None:
        """Process an ATAK packet for transmission"""
        try:
            # Compress data using zstd
            print(f"OUTGOING PACKET: {packet_id} - Received {len(data)} bytes from {source_addr}:{source_port}")
            compressed = compress_cot_packet(data)
            outgoing_hash = hashlib.md5(compressed).hexdigest()
            print(f"HASH CHECK: Outgoing compressed data hash: {outgoing_hash}")
            if not compressed:
                print("ERROR: Compression failed")
                return
            print(f"COMPRESS: Result {len(compressed)} bytes")
            
            # Check for duplicates before writing
            if self.is_duplicate(compressed):
                return
            
            # Only forward packets from output ports (locally generated)
            if source_port not in OUTPUT_PORTS:
                print(f"SKIPPING: Remote packet from input port {source_port}")
                return
            else:
                print(f"FORWARDING: Local packet from output port {source_port}")
            
            # Check if any nodes are in non-WIFI mode
            non_wifi_nodes = self.get_non_wifi_nodes()
            if non_wifi_nodes:
                # Write to pending directory
                timestamp = str(int(time.time() * 1000))
                path = f"{self.pending_dir}/packet_{timestamp}.zst"
                
                with open(path, 'wb') as f:
                    f.write(compressed)
                print(f"WRITE: {path} ({len(compressed)} bytes)")
            else:
                # Skip writing if all nodes are in WIFI mode
                print("SKIP: Not writing to pending (all nodes in WIFI mode)")
                # Clean up directories
                self.cleanup_shared_directories()
                
        except Exception as e:
            print(f"ERROR: Processing packet failed: {e}")

    def forward_to_atak(self, data: bytes) -> None:
        """Forward packet to ATAK multicast addresses (input ports only)"""
        success_count = 0
        
        # Define input ports (non-output ports)
        INPUT_PORTS = [17013, 6970, 7172]
        
        # Only forward to input ports
        for i, (addr, port) in enumerate(zip(MULTICAST_ADDRS, MULTICAST_PORTS)):
            if port in INPUT_PORTS:
                if self.socket_manager.send_packet(data, addr, port):
                    success_count += 1
                    print(f"FORWARD: {len(data)} bytes to {addr}:{port} (input port)")
        
        print(f"Successfully forwarded to {success_count}/{len(INPUT_PORTS)} input multicast addresses")

    def process_incoming(self) -> None:
        """Process packets in the incoming directory"""
        try:
            for filename in os.listdir(self.incoming_dir):
                if not filename.endswith('.zst'):
                    continue
                    
                path = f"{self.incoming_dir}/{filename}"
                try:
                    print(f"INCOMING PACKET: Processing {filename}")
                    # Read compressed data
                    with open(path, 'rb') as f:
                        compressed = f.read()
                    print(f"READ: {filename} ({len(compressed)} bytes)")
                    incoming_hash = hashlib.md5(compressed).hexdigest()
                    print(f"HASH CHECK: Incoming compressed data hash: {incoming_hash}")
                    
                    # Check for duplicates
                    if self.is_duplicate(compressed):
                        os.remove(path)
                        continue
                    
                    # Decompress and forward
                    print(f"DECOMPRESS: {len(compressed)} bytes")
                    decompressed = decompress_cot_packet(compressed)
                    if decompressed:
                        print(f"DECOMPRESS: Result {len(decompressed)} bytes")
                        self.forward_to_atak(decompressed)
                        os.remove(path)
                    else:
                        print(f"ERROR: Failed to decompress {filename}")
                        
                except Exception as e:
                    print(f"ERROR: Processing {filename} failed: {e}")
                    
        except Exception as e:
            print(f"ERROR: Checking incoming directory failed: {e}")

    def run(self):
        """Main processing loop"""
        try:
            print("SETUP: ATAK handler running, press Ctrl+C to exit")
            
            while True:
                # Check for CoT packets from ATAK
                for (addr, port), sock in self.sockets.items():
                    sock.settimeout(0.1)
                    try:
                        data, src = sock.recvfrom(65535)
                        packet_id = f"pkt_{int(time.time() * 1000)}"
                        print(f"RECEIVE: {packet_id} - {len(data)} bytes from {src[0]}:{src[1]} on {addr}:{port}")
                        self.process_packet(data, packet_id=packet_id, source_addr=addr, source_port=port)
                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"ERROR: Receiving packet failed: {e}")
                
                # Check for incoming packets
                self.process_incoming()
                
                # Small sleep to prevent CPU hogging
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\nEXIT: Shutting down...")
            for sock in self.sockets.values():
                sock.close()

def main():
    """Main entry point"""
    handler = ATAKHandler()
    handler.run()

if __name__ == "__main__":
    main()
