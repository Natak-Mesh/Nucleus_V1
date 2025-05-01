#!/usr/bin/env python3

import json
import os
import secrets
import re
from pathlib import Path
from typing import Dict, NamedTuple

class NodeConfig(NamedTuple):
    mac: str
    ip: str
    key: str
    hostname: str

class MeshConfigurator:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.json_path = self.base_dir / 'mesh_nodes.json'
        self.nodes: Dict[str, NodeConfig] = {}
        
    def load_config(self) -> bool:
        try:
            if self.json_path.exists():
                with open(self.json_path, 'r') as f:
                    data = json.load(f)
                    self.nodes = {mac: NodeConfig(**node_data) for mac, node_data in data.items()}
                return True
            return False
        except json.JSONDecodeError:
            print("Error: Corrupt JSON file, starting fresh")
            return False
            
    def save_config(self):
        temp_path = self.json_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w') as f:
                data = {mac: node._asdict() for mac, node in self.nodes.items()}
                json.dump(data, f, indent=2)
            temp_path.replace(self.json_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def generate_key(self) -> str:
        return secrets.token_hex(16)

    def add_node(self, mac: str, ip: str, hostname: str):
        if mac not in self.nodes:
            # Auto-append /24 if not present
            if '/' not in ip:
                ip = ip + "/24"
            self.nodes[mac] = NodeConfig(mac=mac, ip=ip, key=self.generate_key(), hostname=hostname)
            self.save_config()

    def remove_node(self, mac: str) -> bool:
        if mac in self.nodes:
            del self.nodes[mac]
            self.save_config()
            return True
        return False

    def generate_macsec_script(self, node_mac: str) -> str:
        node = self.nodes[node_mac]
        lines = [
            "#!/bin/bash\n",
            "ip link set wlan1 mtu 1564",
            "ip link set br0 mtu 1500\n",
            "ip link add link wlan1 macsec0 type macsec encrypt on",
            "ip link set macsec0 mtu 1532\n",
            "# My Node",
            f"ip macsec add macsec0 tx sa 0 pn 1 on key 00 {node.key}\n"
        ]
        
        # Add peer configurations
        port = 1
        for peer_mac, peer in self.nodes.items():
            if peer_mac != node_mac:
                mac_suffix = peer_mac[-5:].replace(':', '')
                lines.extend([
                    f"# Peer Node ({mac_suffix}-{peer.hostname})",
                    f"ip macsec add macsec0 rx port 1 address {peer_mac}",
                    f"ip macsec add macsec0 rx port 1 address {peer_mac} sa 0 pn 1 on key 01 {peer.key}\n"
                ])
        
        lines.append("ip link set macsec0 up")
        return '\n'.join(lines)

    def generate_mapping_file(self) -> str:
        # Generate a single shared key for all nodes (do this once)
        if not hasattr(self, '_shared_group_key'):
            self._shared_group_key = secrets.token_hex(32)  # 32 bytes = 64 hex chars
            
        mapping = {
            "reticulum_group_key": self._shared_group_key,  # Clearly labeled as Reticulum key
            "nodes": {}
        }
        
        for mac, node in self.nodes.items():
            mapping["nodes"][mac] = {
                "hostname": node.hostname,
                "ip": node.ip.replace("/24", "")  # Remove /24 for the mapping file
            }
        return json.dumps(mapping, indent=2)

    def generate_all_configs(self):
        if not self.nodes:
            return False
            
        for node_mac in self.nodes:
            # Create node directory using last 4 characters of MAC and hostname
            mac_suffix = node_mac[-5:].replace(':', '')
            node = self.nodes[node_mac]
            node_dir = self.base_dir / f"{mac_suffix}-{node.hostname}"
            node_dir.mkdir(exist_ok=True)
            
            # Generate and write macsec.sh
            with open(node_dir / 'macsec.sh', 'w') as f:
                f.write(self.generate_macsec_script(node_mac))
            
            # Generate and write hostname mapping file
            with open(node_dir / 'hostname_mapping.json', 'w') as f:
                f.write(self.generate_mapping_file())
            
            # Make macsec.sh executable
            os.chmod(node_dir / 'macsec.sh', 0o755)
        return True

def validate_mac(mac: str) -> bool:
    pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(pattern.match(mac))

def validate_ip(ip: str) -> bool:
    pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$')
    if not pattern.match(ip):
        return False
    
    # Validate each octet
    try:
        addr, mask = ip.split('/')
        if not 0 <= int(mask) <= 32:
            return False
        for octet in addr.split('.'):
            if not 0 <= int(octet) <= 255:
                return False
        return True
    except ValueError:
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    configurator = MeshConfigurator(script_dir)
    
    if configurator.load_config():
        print("Loaded existing configuration")
    
    while True:
        print("\nMesh Network Configurator")
        print("1. Add node")
        print("2. Remove node")
        print("3. Generate all node configs")
        print("4. List current nodes")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            mac = input("Enter MAC address (xx:xx:xx:xx:xx:xx): ").strip()
            if not mac:
                print("MAC address cannot be empty")
                continue
            if not validate_mac(mac):
                print("Invalid MAC address format")
                continue

            hostname = input("Enter Pi's hostname (run 'hostname' command to find it): ").strip()
            if not hostname:
                print("Hostname cannot be empty")
                continue

            ip = input("Enter br0 IP address (without /24, e.g. 192.168.1.1): ").strip()
            if not validate_ip(ip + "/24"):
                print("Invalid IP address format")
                continue

            configurator.add_node(mac.lower(), ip, hostname)
            print(f"Added node {mac} with hostname {hostname}")
                
        elif choice == '2':
            if not configurator.nodes:
                print("No nodes configured")
                continue
                
            print("\nCurrent nodes:")
            for i, mac in enumerate(configurator.nodes, 1):
                print(f"{i}. {mac}")
            
            node_num = input("Enter node number to remove: ").strip()
            try:
                mac = list(configurator.nodes.keys())[int(node_num) - 1]
                if configurator.remove_node(mac):
                    print(f"Removed node {mac}")
            except (ValueError, IndexError):
                print("Invalid selection")
                
        elif choice == '3':
            if not configurator.nodes:
                print("No nodes configured")
                continue
                
            if configurator.generate_all_configs():
                print("Generated configs for all nodes")
                
        elif choice == '4':
            if not configurator.nodes:
                print("No nodes configured")
                continue
                
            print("\nConfigured nodes:")
            for mac, node in configurator.nodes.items():
                print(f"MAC: {mac}")
                print(f"Hostname: {node.hostname}")
                print(f"IP: {node.ip}")
                print(f"KEY: {node.key}\n")
                
        elif choice == '5':
            break
            
        else:
            print("Invalid option")

if __name__ == "__main__":
    main()
