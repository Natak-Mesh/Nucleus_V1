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

The Dual-Mode Mesh Network System is a resilient communication platform that combines IP-based 802.11s mesh networking with long-range Reticulum/LoRa capabilities. This hybrid approach provides both high-bandwidth local connectivity and long-range communication when needed.

### Key Components

#### IP-Based 802.11s with Batman-adv

The system uses the Batman-adv (Better Approach To Mobile Ad-hoc Networking) protocol to create a layer 2 mesh network over 802.11s wireless connections. This provides:

- Self-healing mesh topology
- Automatic route discovery and optimization
- Seamless client roaming
- Layer 2 bridging capabilities

#### MACsec Security Layer

All mesh traffic is encrypted using MACsec (IEEE 802.1AE) to provide:

- Link-layer encryption
- Data integrity protection
- Replay protection
- Secure node authentication

#### Reticulum/LoRa Fallback

When WiFi mesh connectivity is degraded or unavailable, the system automatically switches to Reticulum over LoRa. This fallback mechanism is primarily designed to support ATAK communication when the WiFi mesh is unavailable. The Reticulum/LoRa component provides:

- Long-range communication (up to several kilometers)
- Low-bandwidth but reliable ATAK message transmission
- Resilient peer discovery
- End-to-end encryption

**Note**: The Reticulum/LoRa component is specifically designed for ATAK packet transmission. Without ATAK, the Reticulum component will maintain connectivity between nodes but does not provide general-purpose networking capabilities.

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

- **Raspberry Pi 4** (with at least 2GB RAM) - Required specifically for the custom kernel that supports MACsec encryption
- **Storage** (minimum 16GB microSD card)
- **Power Supply** (battery or fixed)
- **Weatherproof Enclosure** (for outdoor deployments)

### Modular Radio Components

As this is an open-source project, the radio components are designed to be modular and can be swapped with compatible alternatives:

- **WiFi Adapter** - Any USB adapter supporting 802.11s mesh mode
  - The system connects via USB, allowing for easy replacement with compatible alternatives
  - Recommended: Adapters with external antenna connectors for better range

- **LoRa Transceiver/Reticulum Node** - USB-connected LoRa device
  - Can be replaced with other LoRa transceivers compatible with Reticulum
  - The USB connection allows for easy swapping of different radio options


## Configuration

### Mesh Network Configuration

The primary configuration file for the mesh network is located at:

```
/home/natak/mesh/mesh_config.env
```

This file contains the following key settings:

- **MESH_NAME**: The name of the mesh network (all devices must use the same name)
- **MESH_CHANNEL**: The WiFi channel to use for mesh communication

Example configuration:

```
MESH_NAME=natak_mesh
MESH_CHANNEL=11  # 2462 MHz (2.0 dBm)
```

#### Changing Mesh Name

To change the mesh network name:

1. Edit the mesh_config.env file:
   ```
   nano /home/natak/mesh/mesh_config.env
   ```

2. Modify the MESH_NAME parameter:
   ```
   MESH_NAME=your_new_mesh_name
   ```

3. Save the file and exit (Ctrl+X, Y, Enter)

4. Restart the mesh service:
   ```
   sudo systemctl restart mesh-startup
   ```

#### Changing Mesh Channel

The system supports various WiFi channels in both 2.4 GHz and 5 GHz bands. To change the channel:

1. Edit the mesh_config.env file:
   ```
   nano /home/natak/mesh/mesh_config.env
   ```

2. Comment out the current MESH_CHANNEL line by adding a # at the beginning
3. Uncomment the desired channel by removing the # at the beginning
4. Save the file and exit (Ctrl+X, Y, Enter)
5. Restart the mesh service:
   ```
   sudo systemctl restart mesh-startup
   ```

**Note**: When selecting a channel, consider:
- 2.4 GHz channels (1-11) offer better range but may have more interference
- 5 GHz channels offer higher bandwidth but shorter range
- DFS channels (52-144) require radar detection and may not be available in all locations

### Node Configuration with MACsec Config Tool

The system uses a dedicated MACsec configuration tool to generate the necessary configuration files for node management and secure communication. The tool automatically generates:

- **hostname_mapping.json**: Maps MAC addresses to hostnames and IP addresses
- **macsec.sh**: Contains encryption keys and peer configurations

**Important**: These files are generated automatically and should not be modified manually. Incorrect modifications can break the mesh network's security and functionality.

#### Adding a New Node

To add a new node to the network, use the MACsec configuration tool:

```
cd /home/natak/macsec_config_tool
python3 Macsec_config_generator.py
```

The tool will guide you through the process of adding a new node, generating the appropriate keys, and updating the configuration files. After the configuration is generated, restart the mesh service:

```
sudo systemctl restart mesh-startup
```

### Reticulum Configuration

The Reticulum stack is configured in:

```
/home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/config.py
```

Key settings include:

- **APP_NAME**: Application identifier
- **ASPECT**: Communication aspect
- **ANNOUNCE_INTERVAL**: How often to announce presence (seconds)
- **PEER_TIMEOUT**: Time before considering a peer offline (seconds)
- **RETRY_MAX_ATTEMPTS**: Maximum packet retry attempts

Most users will not need to modify these settings, but they can be adjusted for specific deployment scenarios.

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
3. Navigate to the mesh monitor web page (URL will be provided during system setup)

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

ATAK should be configured to use the following multicast addresses:

- Primary: 224.10.10.1:17012
- Secondary: 239.2.3.1:6969

When the system detects ATAK packets and nodes are in LORA mode, it automatically:
1. Compresses the ATAK packets using a specialized algorithm
2. Transmits them via Reticulum over LoRa
3. Decompresses them on the receiving end
4. Forwards them to the local ATAK instance

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
