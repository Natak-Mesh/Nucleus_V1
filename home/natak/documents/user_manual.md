# Dual-Mode Mesh Network System User Manual

## Table of Contents
1. [System Overview](#system-overview)
2. [Hardware Requirements](#hardware-requirements)
3. [Installation and Setup](#installation-and-setup)
4. [Configuration](#configuration)
5. [Operation](#operation)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Features](#advanced-features)

## System Overview

The Dual-Mode Mesh Network System is a resilient communication platform that combines IP-based 802.11s mesh networking with long-range Reticulum/LoRa capabilities. This hybrid approach provides both high-bandwidth local connectivity and long-range communication when needed. The system is designed as a general-purpose platform that can support a wide range of applications and devices, not limited to any specific use case.

### Key Components

#### IP-Based 802.11s with Batman-adv

The system uses the Batman-adv (Better Approach To Mobile Ad-hoc Networking) protocol to create a layer 2 mesh network over 802.11s wireless connections. This general-purpose IP network provides:

- Self-healing mesh topology
- Automatic route discovery and optimization
- Seamless client roaming
- Layer 2 bridging capabilities
- Standard IP connectivity for any connected device

#### MACsec Security Layer

All mesh traffic is encrypted using MACsec (IEEE 802.1AE) to provide:

- Link-layer encryption
- Data integrity protection
- Replay protection
- Secure node authentication

#### Reticulum/LoRa Fallback

When WiFi mesh connectivity is degraded or unavailable, the system automatically switches to Reticulum over LoRa. The current implementation of this fallback mechanism is primarily designed to support ATAK communication when the WiFi mesh is unavailable. The Reticulum/LoRa component provides:

- Long-range communication (up to several kilometers)
- Low-bandwidth but reliable messaging
- Resilient peer discovery
- End-to-end encryption

**Note**: While the current reticulum_mesh module is specifically designed for ATAK packet transmission, the system includes a full Reticulum installation that can be used for other applications. See the "General Purpose Connectivity" section for more information on using Reticulum for other purposes.

#### ATAK Integration

The system integrates with Android Team Awareness Kit (ATAK) to provide:

- Tactical situational awareness
- Position reporting
- Message exchange
- Seamless transition between WiFi and LoRa modes

### Network Architecture

The system operates in two primary modes:

1. **WIFI Mode**: High-bandwidth mesh networking using 802.11s and Batman-adv
2. **LORA Mode**: Long-range, low-bandwidth communication using Reticulum over LoRa

The system automatically switches between these modes based on connectivity quality, ensuring continuous communication even in challenging environments. While the mode switching happens automatically regardless of application, the LORA mode's functionality is primarily designed for ATAK packet transmission. Other applications will continue to use the WiFi mesh when available, but will not automatically utilize the Reticulum/LoRa fallback.

## Hardware Requirements

### Required Components

- **Raspberry Pi 4** (4GB RAM recommended, minimum 2GB) - The system has been tested and built on the Pi 4 with 4GB RAM. A custom kernel is used that supports MACsec encryption.

- **Storage** - 32GB microSD card recommended. While the system may function with smaller capacity cards, 32GB provides ample space for the operating system, applications, and data storage.

- **Radio Components**:
  - **WiFi Adapter** - USB WiFi adapter supporting 802.11s mesh mode with appropriate antenna
  - **RNode-compatible LoRa Device** - LoRa transceiver with RNode firmware installed. Users must verify their LoRa device has compatible RNode firmware for proper integration with the Reticulum network stack.

- **Power Supply** - 5V power supply for the Raspberry Pi 4. Standard Raspberry Pi power supply (5V/3A) recommended for stable operation.

- **Optional: Weatherproof Enclosure** - For outdoor or harsh environment deployments

### Modular Radio Components

As this is an open-source project, the radio components are designed to be modular and can be swapped with compatible alternatives:

- **WiFi Adapter** - Any USB adapter supporting 802.11s mesh mode
  - The system connects via USB, allowing for easy replacement with compatible alternatives
  - Recommended: Adapters with in kernel drivers 

- **LoRa Transceiver/Reticulum Node** - USB-connected LoRa device
  - Can be replaced with other LoRa transceivers compatible with Reticulum
  - The USB connection allows for easy swapping of different radio options


## Configuration

### Mesh Network Configuration

**File Location**: `/home/natak/mesh/mesh_config.env`

**Key Variables**:
- `MESH_NAME`: Defines the mesh network name (must be identical across all nodes)
- `MESH_CHANNEL`: Specifies the WiFi channel for mesh communication
  - 2.4 GHz channels (1-11): Better range, more potential interference
  - 5 GHz channels: Higher bandwidth, shorter range
  - DFS channels (52-144): Require radar detection, may not be available in all locations

**Channel Setup Note**: When changing channels, uncomment the desired channel and ensure you comment out the previously used channel. All nodes in the mesh must use the same channel to communicate with each other.

**After Configuration Changes**: Restart the mesh service with `sudo systemctl restart mesh-startup`

### Node Configuration with MACsec Config Tool

**Tool Location**: `/home/natak/macsec_config_tool/Macsec_config_generator.py`

**Generated Files**:
- `hostname_mapping.json`: Maps MAC addresses to hostnames and IP addresses
- `macsec.sh`: Contains encryption keys and peer configurations

**Important**: These files are generated automatically by the configuration tool and should not be modified manually. Incorrect modifications can break the mesh network's security and functionality.

**Adding Nodes**: Run the MACsec configuration tool and follow the prompts. The tool provides detailed instructions during the node addition process. After configuration, restart the mesh service.

### Reticulum Configuration

**File Location**: `/home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/config.py`

**Key Variables**:
- `APP_NAME`: Application identifier (functions as the Reticulum mesh name)
- `ASPECT`: Communication aspect (functions as the Reticulum mesh password)
- `ANNOUNCE_INTERVAL`: Frequency of presence announcements (seconds)
- `PEER_TIMEOUT`: Time before considering a peer offline (seconds)
- `RETRY_MAX_ATTEMPTS`: Maximum packet retry attempts
- `RETRY_INITIAL_DELAY`: Base delay for first retry (seconds)
- `RETRY_BACKOFF_FACTOR`: Multiplier for delay increase
- `RETRY_MAX_DELAY`: Maximum allowed delay between retries (seconds)
- `RETRY_JITTER`: Randomness added to calculated delay

**After Configuration Changes**: Restart the Reticulum stack with `sudo systemctl restart reticulum-stack`

### WiFi Hotspot Configuration

**File Location**: `/etc/hostapd/hostapd.conf`

**Purpose**: Configures the WiFi access point that allows client devices to connect to the mesh node.
Note: access point name is set here

**After Configuration Changes**: Restart the hostapd service with `sudo systemctl restart hostapd`

### Network Interface Configuration

**File Location**: `/etc/systemd/network/`

**Key Files**:
- `br0.netdev`: Bridge device configuration
- `br0.network`: Bridge network configuration
- `eth0.network`: Ethernet interface configuration
- `wlan0.network`: WiFi interface configuration

**Purpose**: Configures the node's primary IP addressing and network bridge setup

**After Configuration Changes**: Restart the systemd-networkd service with `sudo systemctl restart systemd-networkd`

### Batman-adv Configuration

**File Location**: `/home/natak/mesh/batmesh.sh`

**Key Parameters**:
- `OGM Interval`: 1000ms for better adaptation to mobility
- `Hop Penalty`: 40 to favor stronger direct links in poor RF conditions
- `Network Coding`: Enabled to improve throughput in challenging environments
- `Distributed ARP Table`: Enabled to reduce broadcast traffic

**After Configuration Changes**: Restart the mesh service with `sudo systemctl restart mesh-startup`

### Mode Transition Configuration

**File Location**: `/home/natak/reticulum_mesh/ogm_monitor/enhanced_ogm_monitor.py`

**Key Parameters**:
- `FAILURE_THRESHOLD`: Time without OGMs to consider a failure (seconds)
- `FAILURE_COUNT`: Consecutive failures to switch to LORA mode
- `RECOVERY_COUNT`: Consecutive good readings to switch back to WIFI mode

**After Configuration Changes**: Restart the Reticulum stack with `sudo systemctl restart reticulum-stack`

### ATAK Rate Limiting

**File Location**: `/home/natak/reticulum_mesh/tak_transmission/atak_module/atak_handler.py`

**Key Parameter**:
- `POSITION_UPDATE_RATE_LIMIT`: Minimum time between position updates (default: 60 seconds)

**After Configuration Changes**: Restart the Reticulum stack with `sudo systemctl restart reticulum-stack`

## Operation

### Starting the System

The system starts automatically on boot. If you need to start it manually:

```bash
# Start the mesh network
sudo systemctl start mesh-startup

# Start the Reticulum stack
sudo systemctl start reticulum-stack
```

### Stopping the System

To stop the system:

```bash
# Stop the Reticulum stack
sudo systemctl stop reticulum-stack

# Stop the mesh network
sudo systemctl stop mesh-startup
```

### Checking System Status

To check the status of the mesh network:

```bash
# Check mesh service status
sudo systemctl status mesh-startup

# Check Batman-adv status
sudo batctl o

# Check node status
cat /home/natak/reticulum_mesh/ogm_monitor/node_status.json
```

To check the status of the Reticulum stack:

```bash
# Check Reticulum service status
sudo systemctl status reticulum-stack

# Check peer discovery status
cat /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.json
```

### Monitoring Node Modes

The system automatically switches between WIFI and LORA modes based on connectivity quality. Node modes and network status can be monitored through the mesh_monitor web interface.

To access the mesh monitor interface:

1. Connect to the mesh network
2. Open a web browser
3. Navigate to the mesh monitor web page at <node IP>:5000

The web interface provides a visual representation of:
- Current mode of each node (WIFI or LORA)
- Connection quality
- Network topology
- Packet statistics

**Important**: While the mode switching happens automatically for all nodes based on connectivity quality, the LORA mode primarily affects ATAK communication. When a node switches to LORA mode, ATAK packets will be routed through Reticulum/LoRa, but other network traffic will not automatically use this fallback path.

### ATAK Integration

The system integrates with ATAK through the following mechanisms:

1. In WIFI mode, ATAK communicates directly over the mesh network
2. In LORA mode, ATAK messages are compressed and sent via Reticulum

This dual-mode capability is a key feature of the system, allowing ATAK to maintain communication even when WiFi connectivity is degraded or unavailable. The Reticulum/LoRa component is specifically designed to handle ATAK packet transmission and does not provide general-purpose networking for other applications.

ATAK EUD (via the network setting menu) should be configured to use the following multicast addresses:

- Primary: 224.10.10.1:17012
- Secondary: 239.2.3.1:6969

When the system detects ATAK packets and nodes are in LORA mode, it automatically:
1. Compresses the ATAK packets using a specialized algorithm
2. Transmits them via Reticulum over LoRa
3. Decompresses them on the receiving end
4. Forwards them to the local ATAK instance

### General Purpose Connectivity

While the system includes specific integration with ATAK, it is designed as a general-purpose connectivity platform that can support a wide range of applications and devices.

#### IP Mesh Network for Any Device

The Batman-adv mesh network provides standard IP connectivity that can be used by any IP-capable device:

- **Standard IP Applications**: Any application that uses IP networking (web browsing, file sharing, VoIP, etc.) can operate over the mesh network
- **Device Connectivity**: Any device that can connect to a network (laptops, smartphones, IoT devices, etc.) can join the mesh through any node
- **Transparent Routing**: Batman-adv automatically handles routing between nodes, making the entire mesh appear as a single network segment
- **Bridged Connectivity**: The br0 bridge interface allows devices connected via Ethernet or WiFi client mode to communicate seamlessly with the mesh

To connect a device to the mesh network:
1. Connect to any mesh node via WiFi or Ethernet
2. The device will receive an IP address via DHCP
3. The device can now communicate with any other device on the mesh

#### Extended Reticulum Usage

While the current reticulum_mesh module is specifically designed for ATAK integration, the system includes a full Reticulum installation that can be used for other applications:

- **Reticulum Applications**: The system can run other Reticulum-based applications such as Sideband or Mesh Chat
- **TCP Interface**: Reticulum can be configured with a TCP interface to allow other devices to connect and use Reticulum services
- **Custom Applications**: Developers can create custom applications using the Reticulum API

Advanced users can configure Reticulum for additional use cases:
- Configure a TCP interface to allow other devices to connect to Reticulum
- Run additional Reticulum applications alongside the ATAK integration
- Develop custom applications using the Reticulum API
- Reconfigure the system to let Reticulum use the WiFi interface directly for a full Reticulum device

**Note**: Extended Reticulum usage may require additional configuration beyond the scope of this manual. Refer to the Reticulum documentation for more information.

## Troubleshooting

### Common Issues

#### Node Not Joining Mesh

If a node is not joining the mesh network:

1. Verify the mesh configuration:
   ```
   cat /home/natak/mesh/mesh_config.env
   ```
   Ensure MESH_NAME and MESH_CHANNEL match across all nodes.

2. Check the WiFi interface:
   ```
   iw dev wlan1 info
   ```
   Verify it's in mesh mode with the correct mesh ID.

3. Check Batman-adv status:
   ```
   sudo batctl o
   ```
   Look for other nodes in the output.

4. Restart the mesh service:
   ```
   sudo systemctl restart mesh-startup
   ```

#### MACsec Issues

If you're experiencing connectivity issues that might be related to MACsec:

1. Check MACsec interface status:
   ```
   ip link show macsec0
   ```
   Verify the interface is up.

2. Check MACsec statistics:
   ```
   ip -s macsec show
   ```
   Look for TX and RX packet counts.

3. Verify MACsec configuration:
   ```
   cat /home/natak/mesh/macsec.sh
   ```
   Ensure all nodes have the correct MAC addresses and keys.

#### Reticulum Not Working

If Reticulum communication is not working:

1. Check the Reticulum service status:
   ```
   sudo systemctl status reticulum-stack
   ```

2. Check peer discovery:
   ```
   cat /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.json
   ```
   Verify other nodes are listed.

3. Check for packet logs:
   ```
   cat /home/natak/reticulum_mesh/logs/packet_logs.log
   ```
   Look for any error messages.

4. Restart the Reticulum stack:
   ```
   sudo systemctl restart reticulum-stack
   ```

### Log Files

The system maintains several log files that can help diagnose issues:

- Mesh startup log:
  ```
  journalctl -u mesh-startup
  ```

- Reticulum stack log:
  ```
  journalctl -u reticulum-stack
  ```

- Packet logs:
  ```
  cat /home/natak/reticulum_mesh/logs/packet_logs.log
  ```

- OGM monitor log:
  ```
  journalctl | grep EnhancedOGMMonitor
  ```

## Advanced Features

### Mode Transition Thresholds

The system automatically switches between WIFI and LORA modes based on connectivity quality. The thresholds for this transition can be adjusted in:

```
/home/natak/reticulum_mesh/ogm_monitor/enhanced_ogm_monitor.py
```

Key parameters:

- **FAILURE_THRESHOLD**: Time without OGMs to consider a failure (seconds)
- **FAILURE_COUNT**: Consecutive failures to switch to LORA mode
- **RECOVERY_COUNT**: Consecutive good readings to switch back to WIFI mode

### Batman-adv Optimizations

The Batman-adv protocol is configured with several optimizations for mobile ad-hoc networks:

- **OGM Interval**: 1000ms for better adaptation to mobility
- **Hop Penalty**: 40 to favor stronger direct links in poor RF conditions
- **Network Coding**: Enabled to improve throughput in challenging environments
- **Distributed ARP Table**: Enabled to reduce broadcast traffic

These settings can be adjusted in:

```
/home/natak/mesh/batmesh.sh
```

### Packet Retry Configuration

The Reticulum packet manager includes a sophisticated retry mechanism with exponential backoff. The retry parameters can be adjusted in:

```
/home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/config.py
```

Key parameters:

- **RETRY_INITIAL_DELAY**: Base delay for first retry (seconds)
- **RETRY_BACKOFF_FACTOR**: Multiplier for delay increase
- **RETRY_MAX_DELAY**: Maximum allowed delay between retries (seconds)
- **RETRY_JITTER**: Randomness added to calculated delay
- **RETRY_MAX_ATTEMPTS**: Maximum number of retry attempts

### ATAK Rate Limiting

To prevent network congestion, ATAK position updates are rate-limited. This rate limit can be adjusted in:

```
/home/natak/reticulum_mesh/tak_transmission/atak_module/atak_handler.py
```

Look for the `POSITION_UPDATE_RATE_LIMIT` parameter (default: 60 seconds).
