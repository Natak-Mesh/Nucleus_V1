# Mesh-V1.7
802.11s/BATMAN-adv  Wi-Fi Mesh and Rnode/Reticulum with CoT Tx Script

## Network Connectivity Options

### Reticulum TCP Interface
For connecting phones or other devices to the mesh network:
- Enable the TCP Server Interface in the Reticulum config
- Default settings: listen_ip = 0.0.0.0, listen_port = 4242
- All gateway nodes should use consistent port settings
- Only needed on nodes that will serve as gateways for external devices

## Software Requirements
- Pi-OS Bookworm with Macsec enabled kernel
- Python and pip
- RNS Reticulum
- Batman-ADV
- zstd Zstandard for compression
- hostapd for wlan0 wifi ap
- git, create folder to sync online repo

## Hardware Requirements
- Pi 4 w/ 4 GB ram
- Alfa AWUS036ACHM wifi card
- RAK19007 kit
- 32 GB microSD
- assorted cables/bulkead fittings/connectors
