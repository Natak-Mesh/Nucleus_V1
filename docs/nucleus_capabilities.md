# Nucleus V1 Capabilities

## Platform Overview

The Nucleus V1 is a Raspberry Pi-based Mobile Ad-hoc Network (MANET) radio system designed for tactical and emergency communications. The platform integrates multiple wireless interfaces and communication protocols to provide mesh networking, device connectivity, and long-range communications.

## Hardware Architecture

**Primary Interfaces:**
- **wlan0**: Onboard WiFi adapter - Access Point mode for End User Device (EUD) connectivity
- **wlan1**: External WiFi adapter - 802.11s mesh interface with BATMAN-ADV routing
- **eth0**: Ethernet interface - Bridged to mesh network for wired device integration
- **RAK4631**: LoRa radio module - Standalone Meshtastic node with RNode firmware capability

**Network Topology:**
- **br0**: Bridge interface connecting wlan0, eth0, and bat0 (BATMAN-ADV interface)
- **bat0**: BATMAN-ADV mesh routing layer operating over wlan1
- All interfaces integrated through bridge networking for seamless connectivity

## Mesh Networking

**Routing Protocol:** BATMAN-ADV version 5 (BATMAN_V algorithm)
- Throughput-based routing decisions
- Mobile network optimization
- Encrypted mesh communications via WPA supplicant
- Automatic node discovery and topology management
- Real-time network monitoring with OGM (Originator Message) tracking

**Wireless Configuration:**
- 802.11s mesh mode operation
- Configurable channel selection (2.4GHz and 5GHz bands)
- Mesh ID: "natak_mesh"
- MTU: 1560 bytes to accommodate BATMAN-ADV overhead
- WPA encryption for secure mesh communications

## Communication Protocols

**Reticulum Network Stack:**
- Transport instances active on wlan1 (mesh) and eth0 (ethernet)
- Distributed networking protocol for resilient communications
- Cryptographic packet routing and authentication
- Optional LoRa transport integration via RNode-capable RAK4631

**Nomadnet:**
- Distributed messaging and content sharing platform
- Operates over Reticulum transport layer
- Offline-capable communications

**Meshtastic Integration:**
- RAK4631 operates as standalone Meshtastic node
- Direct EUD interface capability
- Alternative RNode firmware support for Reticulum integration

## Device Connectivity

**EUD Access Methods:**
- WiFi connection via wlan0 Access Point
- Ethernet connection via eth0 interface
- Direct Meshtastic radio interface via RAK4631
- All methods provide access to mesh network resources

**Supported Protocols:**
- Standard IP networking over mesh
- Reticulum packet transport
- Nomadnet messaging services
- Meshtastic LoRa communications

## Management and Monitoring

**Web Interface (Port 5000):**
- Real-time node status monitoring
- Network topology visualization
- WiFi channel configuration management
- IP address configuration
- System reboot and control functions
- Mobile-responsive design

**Monitoring Capabilities:**
- Live mesh node discovery and status tracking
- Throughput measurement and routing metrics
- Connection quality assessment
- Historical data logging via JSON output
- BATMAN-ADV originator message monitoring

## Installed Software

**Core Networking:**
- hostapd (Access Point management)
- batctl (BATMAN-ADV control utilities)
- wpa_supplicant (WiFi encryption)
- systemd-networkd (Interface management)
- NetworkManager (System integration)

**Communication Platforms:**
- Reticulum Network Stack (distributed networking)
- Nomadnet (messaging platform)
- Meshtastic CLI tools (LoRa radio management)

**System Services:**
- Flask web application (management interface)
- Enhanced OGM monitor (network status tracking)
- MediaMTX (media streaming server)
- TAKserver 5.3 (installed, not configured)

**Utilities:**
- iperf3 (network performance testing)
- aircrack-ng (wireless analysis tools)
- ufw (firewall management)

## Media and Streaming

**MediaMTX Integration:**
- RTSP/WebRTC streaming server
- Automatic startup and mesh integration
- Content distribution over mesh topology
- Support for multiple media formats and protocols

## Security Features

**Encryption:**
- WPA-encrypted mesh communications
- Reticulum cryptographic packet authentication
- Meshtastic radio encryption (when enabled)
- UFW firewall protection

**Access Control:**
- Pre-shared key authentication for mesh access
- Network segregation through bridge configuration
- Service-specific access controls

## Technical Specifications

**Operating System:** Linux-based (Raspberry Pi OS)
**Architecture:** ARM64
**Network Interfaces:** 4 active (wlan0, wlan1, eth0, RAK4631)
**Routing:** BATMAN-ADV with 802.11s mesh
**Management:** Web-based interface on port 5000
**Transport Protocols:** IP, Reticulum, Meshtastic LoRa
**Power Requirements:** Standard Raspberry Pi specifications

## Operational Modes

**Standard Configuration:**
- BATMAN-ADV mesh networking over wlan1
- EUD access via wlan0 AP and eth0
- Standalone Meshtastic radio operation
- Reticulum transport over WiFi and ethernet

**Alternative LoRa Integration:**
- RNode firmware flash to RAK4631 enables Reticulum LoRa transport
- Integrated LoRa communications through Reticulum stack
- Extended range capabilities via LoRa modulation

The Nucleus V1 provides a comprehensive MANET solution combining mesh networking, device connectivity, and multiple communication protocols in a single platform suitable for tactical, emergency response, and distributed communication applications.
