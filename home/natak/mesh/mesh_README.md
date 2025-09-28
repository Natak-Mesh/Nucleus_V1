       ..        .....        ...       
       ....     ......       ....      
       .......... ...       .....       
       ........    ..      ......       
       ......      ..     .......       
       .....       ...  .........       
       ....        .....     ....      
       ...         ....        ..   


       N A T A K   -   Nucleus V1         
                                         
          Mesh Networking Radio           



# Mesh Networking System

A comprehensive mesh networking solution built on batman-adv (Better Approach To Mobile Ad-hoc Networking) with real-time monitoring, encrypted communications, and integrated service orchestration.

## Overview

This mesh networking system provides a complete infrastructure for mobile ad-hoc networking using batman-adv as the core routing protocol. The system combines mesh network setup, encrypted communications, real-time node monitoring, and service integration to create a robust networking platform suitable for tactical, emergency, or distributed communication scenarios.

The system automatically configures wireless interfaces, establishes encrypted mesh connections, monitors network topology, and provides data integration points for external applications and monitoring systems.

## System Components

### Core Scripts

**batmesh.sh** - Primary mesh network configuration script
- Configures batman-adv mesh networking with BATMAN_V algorithm
- Sets up wireless interface (wlan1) in mesh mode with encryption
- Establishes bridge networking for service integration
- Manages NetworkManager interface states
- Configures optimal settings for mobile mesh networking

**startup_sequence.sh** - System orchestration and service startup
- Coordinates the complete system initialization process
- Manages service dependencies and startup timing
- Starts mesh networking, monitoring, and integrated services
- Provides process tracking and logging
- Handles background service management

### Monitoring System

**ogm_monitor/enhanced_ogm_monitor.py** - Real-time mesh network monitor
- Continuously monitors batman-adv originator messages (OGMs)
- Tracks node connectivity, throughput, and routing metrics
- Generates real-time status data for external consumption
- Provides network topology awareness
- Filters and processes batman-adv routing information

**ogm_monitor/node_status.json** - Live network status data
- Real-time JSON data file containing current mesh state
- Node connectivity information with timing data
- Throughput metrics and routing next-hop information
- Timestamp-based data for historical analysis
- Integration point for monitoring applications

## Network Architecture

### Batman-adv Configuration
The system uses batman-adv version 5 (BATMAN_V) routing algorithm which provides:
- Throughput-based routing decisions
- Better adaptation to mobile networking scenarios
- Enhanced routing metric calculations
- Improved handling of asymmetric links

### Wireless Configuration
- **Interface**: wlan1 configured in 802.11s mesh mode
- **Channel**: Default channel 11 (configurable via MESH_CHANNEL variable)
- **Mesh ID**: "natak_mesh" for network identification
- **Encryption**: WPA encryption via wpa_supplicant for secure communications
- **MTU**: Increased to 1560 bytes to accommodate batman-adv overhead

### Network Integration
- **Bridge Interface**: br0 for service integration
- **batman-adv Interface**: bat0 as the mesh routing layer
- **Network Management**: systemd-networkd for interface configuration
- **Service Integration**: Bridge configuration allows external services to utilize mesh connectivity

## Startup Process

### Initialization Sequence
1. **Network Interface Preparation**
   - Removes interfaces from NetworkManager control
   - Loads batman-adv kernel module
   - Configures wireless regulatory domain

2. **Mesh Interface Setup**
   - Sets wlan1 to mesh mode with 4-address support
   - Configures mesh parameters (ID, channel, encryption)
   - Disables stock HWMP routing to allow batman-adv control

3. **Batman-adv Configuration**
   - Creates bat0 batman-adv interface
   - Associates wlan1 with batman-adv routing
   - Sets routing algorithm to BATMAN_V
   - Configures OGM interval for mobility optimization

4. **Service Integration**
   - Establishes bridge networking (br0)
   - Integrates batman-adv with bridge interface
   - Restarts network services for configuration application

### Service Orchestration
The startup sequence coordinates multiple system services:
- **Reticulum Network Stack** (rnsd) for extended networking capabilities
- **OGM Monitor** for real-time network monitoring
- **Media Services** (mediamtx) for streaming capabilities
- **Background Process Management** with PID tracking

## Monitoring System

### Real-Time Network Monitoring
The enhanced OGM monitor provides continuous network awareness:
- **Node Discovery**: Automatic detection of mesh network participants
- **Connectivity Metrics**: Last-seen timestamps and connection quality
- **Throughput Analysis**: Real-time bandwidth measurements between nodes
- **Routing Information**: Next-hop routing decisions and path optimization

### Data Structure
Node status information includes:
- **MAC Address**: Unique node identifier
- **Last Seen**: Time since last communication (seconds)
- **Throughput**: Measured bandwidth capacity (Mbps)
- **Next Hop**: Routing path to destination node
- **Timestamp**: Data collection time for synchronization

### Integration Points
The monitoring system provides data integration through:
- **JSON File Output**: Real-time status file for external applications
- **Standardized Format**: Consistent data structure for parsing
- **Atomic Updates**: File locking prevents data corruption
- **Historical Tracking**: Timestamp-based data for trend analysis

## Configuration Options

### Network Settings
- **MESH_NAME**: Network identifier for mesh group membership
- **MESH_CHANNEL**: WiFi channel selection (default: 11)
- **OGM_INTERVAL**: Originator message frequency (default: 1000ms)
- **MTU_SIZE**: Maximum transmission unit (default: 1560 bytes)

### Encryption Configuration
- **WPA Supplicant**: Configured via `/etc/wpa_supplicant/wpa_supplicant-wlan1-encrypt.conf`
- **Pre-shared Key**: Network authentication for mesh access
- **Encryption Method**: WPA-based security for mesh communications

### Interface Management
- **Regulatory Domain**: WiFi regulatory compliance (default: US)
- **Bridge Configuration**: systemd-networkd managed networking
- **Service Integration**: NetworkManager exclusion for manual control

## Usage Instructions

### Manual Startup
```bash
# Start complete mesh system
sudo /home/natak/mesh/startup_sequence.sh

# Start only mesh networking
sudo /home/natak/mesh/batmesh.sh

# Start monitoring separately
cd /home/natak/mesh/ogm_monitor && python3 enhanced_ogm_monitor.py
```

### Status Monitoring
- **Node Status**: Check `/home/natak/mesh/ogm_monitor/node_status.json`
- **Batman Status**: Use `sudo batctl o` for detailed routing information
- **Interface Status**: Monitor with `ip addr` and `iw dev wlan1 info`

### Network Diagnostics
- **Mesh Connectivity**: `sudo batctl ping <destination_mac>`
- **Routing Table**: `sudo batctl o` for originator information
- **Interface Statistics**: `sudo batctl s` for batman-adv statistics

## Integration with External Systems

### Mesh Monitor Application
The system integrates with the mesh_monitor Flask application which:
- Reads node status from the OGM monitor JSON output
- Provides web-based visualization of network status
- Offers configuration management interfaces
- Enables remote monitoring and control capabilities

### Reticulum Integration
- **Network Stack**: rnsd provides extended networking protocols
- **Service Discovery**: Integration with mesh-based service announcement
- **Protocol Bridging**: Connects mesh networking with other communication systems

### Media Services
- **Streaming Integration**: mediamtx provides media streaming over mesh
- **Content Distribution**: Utilizes mesh topology for media delivery
- **Service Discovery**: Automatic service announcement across mesh nodes

## System Requirements

### Hardware Requirements
- WiFi interface capable of 802.11s mesh mode
- Sufficient processing power for batman-adv routing calculations
- Network bridge capabilities for service integration

### Software Dependencies
- batman-adv kernel module
- iw (wireless tools)
- wpa_supplicant for encryption
- systemd-networkd for network management
- Python 3 for monitoring services

### Permissions
- Root access for network interface configuration
- Sudo privileges for batman-adv management
- File system access for configuration and monitoring data

This mesh networking system provides a complete solution for establishing, monitoring, and managing mobile ad-hoc networks with enterprise-grade capabilities and integration options.
