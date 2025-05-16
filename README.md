# Mesh-V1
802.11s/BATMAN-adv  Wi-Fi Mesh and Rnode/Reticulum with CoT Tx Script

## Network Connectivity Options

### Reticulum TCP Interface
For connecting phones or other devices to the mesh network:
- Enable the TCP Server Interface in the Reticulum config
- Default settings: listen_ip = 0.0.0.0, listen_port = 4242
- All gateway nodes should use consistent port settings
- Only needed on nodes that will serve as gateways for external devices

## Software Requirements

### System Requirements
- Pi-OS Bookworm with MACsec enabled kernel
- NetworkManager
- systemd-networkd
- iw (wireless configuration tool)
- batman-adv kernel module
- batctl (Batman-adv control utility)
- hostapd (for WiFi AP functionality, needs to be unmasked)
- git

### Python Requirements
- Python 3.11
- pip
- RNS (Reticulum Network Stack)
- zstd (Zstandard compression library)
- takproto (TAK protocol handling)

## Hardware Requirements
- Pi 4 w/ 4 GB ram
- Alfa AWUS036ACHM wifi card
- RAK19007 kit
- 32 GB microSD
- assorted cables/bulkead fittings/connectors
