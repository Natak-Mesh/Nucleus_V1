# Nucleus V1 Deployment Scenarios

## Core Platform

WiFi mesh (BATMAN-ADV) + bridged ethernet/AP + LoRa radio (Meshtastic/RNode) + optional internet (Starlink/Tailscale)

## Use Cases

### 1. ATAK Mesh Network
- WiFi mesh for UDP auto-discovery between ATAK EUDs
- Meshtastic (BLE) provides parallel comms + interoperability with Meshtastic-only ATAK users

### 2. ATAK + TAKserver
- All above features plus TCP connections (requires certs)
- Video streaming over WiFi mesh
- Advanced TAKserver capabilities
- Data packages supported

### 3. Reticulum Network
- Transport runs on WiFi mesh and ethernet by default
- Apps: Sideband, MeshChat, Nomadnet
- Nomadnet accessible via SSH, can host Reticulum "web" servers
- Optional: Flash RNode firmware to add LoRa transport
- Seamlessly bridges data between internet and wireless connections

### 4. General Mesh Applications
- LAN messaging apps over WiFi mesh
- File sharing and standard network services
- Works over Tailscale tunnels and Starlink bridge

### 5. Standalone Meshtastic Node
- Full Meshtastic functionality with official app
- BLE pairing for direct device connection
- Standard Meshtastic mesh operations

### 6. Network Monitoring
- Web interface on port 5000
- aircrack-ng: Currently AP monitoring, expandable for additional wireless analysis
