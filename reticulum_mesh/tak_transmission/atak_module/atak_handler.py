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
import subprocess
import logger
from collections import deque
from typing import Dict, Tuple
from utils.compression import compress_cot_packet, decompress_cot_packet

# LoraOutSocketManager from atak_relay_resilient.py
class LoraOutSocketManager:
    def __init__(self):
        """Initialize the socket manager with persistent sockets"""
        self.lora_out_sockets = {}  # (addr, port) -> socket
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
            return None

    def setup_persistent_sockets(self):
        """Set up persistent UDP sockets for LoRa output addresses"""
        with self.lock:
            # Close any existing sockets first
            self.cleanup_sockets()
            
            br0_ip = self.get_br0_ip()
            
            for addr, port in zip(LORA_OUT_ADDRS, LORA_OUT_PORTS):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
                    sock.setblocking(False)
                    
                    if br0_ip:
                        sock.bind((br0_ip, 0))
                    
                    self.lora_out_sockets[(addr, port)] = sock
                except Exception:
                    pass
    
    def send_packet(self, data: bytes, addr: str, port: int) -> bool:
        """Send a packet using the persistent socket"""
        with self.lock:
            sock = self.lora_out_sockets.get((addr, port))
            if not sock:
                # Socket missing - try to recreate
                self.setup_persistent_sockets()
                sock = self.lora_out_sockets.get((addr, port))
                if not sock:
                    return False

            try:
                sock.sendto(data, (addr, port))
                return True
            except BlockingIOError:
                # Would block - try again next cycle
                return False
            except Exception:
                # Socket error - mark for recreation
                self.cleanup_socket(addr, port)
                return False

    def cleanup_socket(self, addr: str, port: int):
        """Clean up a specific socket"""
        try:
            sock = self.lora_out_sockets.pop((addr, port), None)
            if sock:
                sock.close()
        except Exception:
            pass

    def cleanup_sockets(self):
        """Clean up all sockets"""
        for (addr, port) in list(self.lora_out_sockets.keys()):
            self.cleanup_socket(addr, port)

# ATAK output addresses and ports
ATAK_OUT_ADDRS = ["224.10.10.1", "239.2.3.1", "239.5.5.55"]
ATAK_OUT_PORTS = [17012, 6969, 7171]

# LoRa output addresses and ports
LORA_OUT_ADDRS = ["224.10.10.1", "239.2.3.1"]
LORA_OUT_PORTS = [17013, 6971]

class NetworkStateMonitor:
    """
    Monitors network state changes and refreshes sockets when needed.
    This helps maintain connectivity when interfaces change state.
    """
    
    def __init__(self, atak_handler):
        """Initialize the network state monitor"""
        self.atak_handler = atak_handler
        self.logger = atak_handler.logger
        self.should_quit = False
        
        # Track interface states
        self.wlan1_state = self.get_interface_state("wlan1")
        self.bat0_state = self.get_interface_state("bat0")
        
        # Track socket activity
        self.last_packet_received = time.time()
        
        # Track node status
        self.node_status = self.get_node_status()
        
        # Start monitoring threads
        self.start_monitoring()
    
    def start_monitoring(self):
        """Start all monitoring threads"""
        threading.Thread(target=self.monitor_interface_states, daemon=True).start()
        threading.Thread(target=self.monitor_socket_activity, daemon=True).start()
        threading.Thread(target=self.monitor_node_status, daemon=True).start()
        self.logger.info("Network state monitoring started")
    
    def get_interface_state(self, interface):
        """Get state of a network interface"""
        try:
            # Check if interface exists and get its state
            result = subprocess.run(
                ["ip", "link", "show", interface],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode != 0:
                return {"exists": False}
            
            # Parse link state (UP/DOWN)
            link_state = "DOWN"
            if "state UP" in result.stdout:
                link_state = "UP"
            
            # Check if RUNNING (carrier)
            running = "RUNNING" in result.stdout
            
            return {
                "exists": True,
                "state": link_state,
                "running": running
            }
        except Exception as e:
            self.logger.error(f"Error getting interface state for {interface}: {e}")
            return {"exists": False, "error": str(e)}
    
    def get_node_status(self):
        """Get status of all nodes from node_status.json"""
        try:
            with open("/home/natak/reticulum_mesh/ogm_monitor/node_status.json", 'r') as f:
                status = json.load(f)
                
            # Extract node status
            modes = {}
            for mac, node_info in status.get("nodes", {}).items():
                hostname = node_info.get("hostname")
                mode = node_info.get("mode")
                if hostname and mode:
                    modes[hostname] = mode
            
            return modes
        except Exception as e:
            self.logger.error(f"Error getting node status: {e}")
            return {}
    
    def monitor_interface_states(self):
        """Monitor interface states and trigger socket refresh on changes"""
        self.logger.info("Starting interface state monitoring")
        while not self.should_quit:
            try:
                # Get current states
                current_wlan1_state = self.get_interface_state("wlan1")
                current_bat0_state = self.get_interface_state("bat0")
                
                # Check for significant changes
                wlan1_changed = (
                    self.wlan1_state.get("exists") != current_wlan1_state.get("exists") or
                    self.wlan1_state.get("state") != current_wlan1_state.get("state") or
                    self.wlan1_state.get("running") != current_wlan1_state.get("running")
                )
                
                bat0_changed = (
                    self.bat0_state.get("exists") != current_bat0_state.get("exists") or
                    self.bat0_state.get("state") != current_bat0_state.get("state") or
                    self.bat0_state.get("running") != current_bat0_state.get("running")
                )
                
                # If wlan1 or bat0 changed state, refresh sockets
                if wlan1_changed:
                    self.logger.info(f"wlan1 state changed: {self.wlan1_state} -> {current_wlan1_state}")
                    self.refresh_sockets("wlan1 state change")
                
                if bat0_changed:
                    self.logger.info(f"bat0 state changed: {self.bat0_state} -> {current_bat0_state}")
                    self.refresh_sockets("bat0 state change")
                
                # Update stored states
                self.wlan1_state = current_wlan1_state
                self.bat0_state = current_bat0_state
                
                # Check every 2 seconds
                time.sleep(2)
            except Exception as e:
                self.logger.error(f"Error in interface state monitoring: {e}")
                time.sleep(5)  # Longer delay on error
    
    def monitor_socket_activity(self):
        """Monitor socket activity and refresh if no packets received"""
        self.logger.info("Starting socket activity monitoring")
        INACTIVITY_THRESHOLD = 30  # 30 seconds without packets is considered inactive
        
        while not self.should_quit:
            try:
                current_time = time.time()
                time_since_last_packet = current_time - self.last_packet_received
                
                if time_since_last_packet > INACTIVITY_THRESHOLD:
                    self.logger.warning(f"No packets received for {time_since_last_packet:.1f} seconds")
                    self.refresh_sockets("socket inactivity")
                    # Reset timer to avoid continuous refreshes
                    self.last_packet_received = current_time
                
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Error in socket activity monitoring: {e}")
                time.sleep(5)
    
    def monitor_node_status(self):
        """Monitor node status and refresh sockets on mode changes"""
        self.logger.info("Starting node status monitoring")
        while not self.should_quit:
            try:
                current_status = self.get_node_status()
                
                # Check for mode changes
                for hostname, mode in current_status.items():
                    if hostname in self.node_status and self.node_status[hostname] != mode:
                        self.logger.info(f"Node {hostname} mode changed: {self.node_status[hostname]} -> {mode}")
                        self.refresh_sockets(f"node {hostname} mode change")
                        break
                
                # Update stored status
                self.node_status = current_status
                
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Error in node status monitoring: {e}")
                time.sleep(5)
    
    def refresh_sockets(self, reason):
        """Refresh all sockets in the ATAK handler"""
        self.logger.info(f"Refreshing sockets due to: {reason}")
        
        try:
            # Clean up existing sockets
            for (addr, port) in list(self.atak_handler.atak_listening_sockets.keys()):
                self.atak_handler.cleanup_atak_socket(addr, port)
            
            # Clean up socket manager sockets
            self.atak_handler.socket_manager.cleanup_sockets()
            
            # Small delay to ensure clean shutdown
            time.sleep(1)
            
            # Set up new sockets
            self.atak_handler.setup_atak_listening_sockets()
            self.atak_handler.socket_manager.setup_persistent_sockets()
            
            self.logger.info("Socket refresh completed successfully")
        except Exception as e:
            self.logger.error(f"Error refreshing sockets: {e}")
    
    def packet_received(self):
        """Call this when a packet is received to update activity timestamp"""
        self.last_packet_received = time.time()
    
    def stop(self):
        """Stop the network state monitor"""
        self.should_quit = True

class ATAKHandler:
    def __init__(self, shared_dir: str = "/home/natak/reticulum_mesh/tak_transmission/shared"):
        """Initialize handler"""
        # Set up logger
        self.logger = logger.get_logger("ATAKHandler", "packet_logs.log")
        
        # ATAK listening socket handling
        self.atak_listening_sockets: Dict[Tuple[str, int], socket.socket] = {}
        self.lock = threading.Lock()
        
        # IP tracking
        self.local_ips = set()
        self.remote_ips = set()
        
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
        
        # Node status path
        self.node_status_path = "/home/natak/reticulum_mesh/ogm_monitor/node_status.json"
        
        # Set up ATAK listening sockets for receiving
        self.setup_atak_listening_sockets()
        
        # Set up socket manager for sending
        self.socket_manager = LoraOutSocketManager()
        
        # Set up network state monitor
        self.network_monitor = NetworkStateMonitor(self)
        
    def get_br0_ip(self):
        """Get the IP address of the br0 interface"""
        try:
            import subprocess
            output = subprocess.check_output("ip -4 addr show br0 | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'", shell=True).decode().strip()
            if output:
                return output
        except Exception:
            return None
    
    def cleanup_atak_socket(self, addr: str, port: int) -> None:
        """Clean up a specific ATAK listening socket"""
        try:
            sock = self.atak_listening_sockets.pop((addr, port), None)
            if sock:
                sock.close()
        except Exception:
            pass

    def setup_atak_listening_sockets(self) -> None:
        """Set up UDP sockets for listening to ATAK output"""
        # Get the IP address of the br0 interface
        br0_ip = self.get_br0_ip()
            
        # Clean up existing sockets first
        for (addr, port) in list(self.atak_listening_sockets.keys()):
            self.cleanup_atak_socket(addr, port)
            
        for addr, port in zip(ATAK_OUT_ADDRS, ATAK_OUT_PORTS):
            try:
                # Create socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
                sock.setblocking(False)
                sock.bind(('', port))
                
                # Add socket to multicast group
                if br0_ip:
                    # Use br0 interface explicitly
                    mreq = struct.pack("4s4s", socket.inet_aton(addr), socket.inet_aton(br0_ip))
                else:
                    # Fall back to INADDR_ANY (though this will likely fail on some nodes)
                    mreq = struct.pack("4sl", socket.inet_aton(addr), socket.INADDR_ANY)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                
                self.atak_listening_sockets[(addr, port)] = sock
            except Exception:
                pass

    def is_duplicate(self, data: bytes) -> bool:
        """Check if packet has been seen recently"""
        packet_hash = hashlib.md5(data).hexdigest()
        if packet_hash in self.recent_packets:
            return True
        self.recent_packets.append(packet_hash)
        return False
    
    def get_non_wifi_nodes(self):
        """Get list of nodes that are in LORA mode and have peer discovery entries"""
        try:
            # First get nodes in LORA mode
            with open(self.node_status_path, 'r') as f:
                status = json.load(f)
                lora_nodes = [
                    node["hostname"] 
                    for node in status.get("nodes", {}).values()
                    if node.get("mode") == "LORA"
                ]
            
            # Then filter to only those with peer discovery entries
            peer_discovery_path = "/home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.json"
            with open(peer_discovery_path, 'r') as f:
                peer_status = json.load(f)
                return [
                    node for node in lora_nodes
                    if node in peer_status.get("peers", {})
                ]
        except Exception:
            return []
            
    def cleanup_shared_directories(self):
        """Clean up all files in shared directories when no nodes are in LoRa mode"""
        try:
            # Clean pending directory
            for filename in os.listdir(self.pending_dir):
                path = os.path.join(self.pending_dir, filename)
                os.remove(path)
                
            # Clean incoming directory
            for filename in os.listdir(self.incoming_dir):
                path = os.path.join(self.incoming_dir, filename)
                os.remove(path)
                
            # Clean processing directory
            for filename in os.listdir(self.processing_dir):
                path = os.path.join(self.processing_dir, filename)
                os.remove(path)
                
        except Exception:
            pass
    
    def get_dhcp_leases(self) -> set:
        """Get IPs from DHCP leases"""
        try:
            output = subprocess.check_output("networkctl status br0", shell=True).decode()
            leases = set()
            found_leases = False
            for line in output.split('\n'):
                stripped = line.strip()
                if "Offered DHCP leases: " in stripped:
                    found_leases = True
                if "(to" in line:
                    ip = line.strip().split("(to")[0].replace("Offered DHCP leases:", "").strip()
                    if ip and ":" not in ip:
                        self.logger.info(f"Found lease IP: {ip}")
                        leases.add(ip)
            return leases
        except Exception:
            return set()

    def check_ip_location(self, ip: str) -> str:
        """Check if IP is local or remote"""
        if ip in self.local_ips:
            return "LOCAL"
        if ip in self.remote_ips:
            return "REMOTE"
            
        # Cache miss - check DHCP leases
        leases = self.get_dhcp_leases()
        if ip in leases:
            # Remove from remote cache if it was wrongly marked
            self.remote_ips.discard(ip)
            self.local_ips.add(ip)
            return "LOCAL"
            
        self.remote_ips.add(ip)
        return "REMOTE"

    def process_packet(self, data: bytes, src_port: int = None) -> None:
        """Process an ATAK packet for transmission"""
        try:
            compressed = compress_cot_packet(data)
            if not compressed:
                return
            
            # Check for duplicates before writing
            if self.is_duplicate(compressed):
                return
            
            # Check if any nodes are in non-WIFI mode
            non_wifi_nodes = self.get_non_wifi_nodes()
            if non_wifi_nodes:
                # Write to pending directory
                timestamp = str(int(time.time() * 1000))
                filename = f"packet_{timestamp}.zst"
                path = f"{self.pending_dir}/{filename}"
                
                with open(path, 'wb') as f:
                    f.write(compressed)
                if src_port:
                    self.logger.info(f"ATAK to LoRa: From port {src_port} -> {filename}")
            else:
                # Clean up directories if all nodes in WIFI mode
                self.cleanup_shared_directories()
                
        except Exception:
            pass

    def forward_to_lora_out(self, data: bytes) -> None:
        """Forward packet to LoRa output addresses"""
        ports = []
        for addr, port in zip(LORA_OUT_ADDRS, LORA_OUT_PORTS):
            if self.socket_manager.send_packet(data, addr, port):
                ports.append(str(port))
        if ports:
            self.logger.info(f"LoRa to ATAK: Writing to ports {','.join(ports)}")

    def process_incoming(self) -> None:
        """Process packets in the incoming directory"""
        try:
            for filename in os.listdir(self.incoming_dir):
                if not filename.endswith('.zst'):
                    continue
                    
                path = f"{self.incoming_dir}/{filename}"
                try:
                    # Read compressed data
                    with open(path, 'rb') as f:
                        compressed = f.read()
                    
                    # Check for duplicates
                    if self.is_duplicate(compressed):
                        os.remove(path)
                        continue
                    
                    # Decompress and forward
                    decompressed = decompress_cot_packet(compressed)
                    if decompressed:
                        self.forward_to_lora_out(decompressed)
                        os.remove(path)
                        
                except Exception:
                    pass
                    
        except Exception:
            pass

    def run(self):
        """Main processing loop"""
        try:
            while True:
                # Check for CoT packets from ATAK
                for (addr, port), sock in self.atak_listening_sockets.items():
                    sock.settimeout(0.1)
                    try:
                        data, src = sock.recvfrom(65535)
                        # Update network monitor when packet received
                        self.network_monitor.packet_received()
                        
                        ip_type = self.check_ip_location(src[0])
                        if port in [17012, 6969] and ip_type == "LOCAL":
                            self.logger.info(f"UDP RECEIVE: From port {port} ({len(data)} bytes)")
                            self.process_packet(data, port)
                    except socket.timeout:
                        continue
                    except Exception:
                        # Socket error - recreate socket
                        self.cleanup_atak_socket(addr, port)
                        self.setup_atak_listening_sockets()
                        break
                
                # Check for incoming packets
                self.process_incoming()
                
                # Small sleep to prevent CPU hogging
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            self.network_monitor.stop()
            for sock in self.atak_listening_sockets.values():
                sock.close()

def main():
    """Main entry point"""
    handler = ATAKHandler()
    handler.run()

if __name__ == "__main__":
    main()
