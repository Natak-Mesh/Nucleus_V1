# Reticulum Mesh System

## System Overview

The Reticulum Mesh System is a comprehensive solution that provides a WiFi mesh network with Reticulum fallback specifically for ATAK (Android Team Awareness Kit) communications. The system automatically manages network transport selection based on link quality, switching between WiFi and LoRa radios to ensure reliable communications even in challenging environments.

The underlying IP network created by the mesh is available for any program to use, not just ATAK. Additionally, the Reticulum implementation can be easily reconfigured to support other applications beyond ATAK as needed, making this a flexible platform for various mesh networking needs.

## System Components

The system consists of several interconnected components, each responsible for a specific aspect of the mesh network:

### 1. Network Setup (macsec.sh and batmesh.sh)
- **Purpose**: Establish the underlying mesh network infrastructure
- **Functions**:
  - Configure network interfaces
  - Set up MACsec encryption for secure communications
  - Initialize BATMAN-adv mesh protocol
  - Create bridge interfaces for network integration

### 2. OGM Monitor (ogm_monitor.py)
- **Purpose**: Monitor BATMAN-adv mesh network health
- **Functions**:
  - Track Originator Messages (OGMs) from mesh nodes
  - Record last seen times, throughput, and next hop information
  - Write status to `/reticulum_mesh/ogm_monitor/status.json`
- **Output Used By**:
  - Mesh Controller (for mode switching decisions)
  - Mesh Monitor web interface (for visualization)

### 3. Mesh Controller (mesh_controller.py)
- **Purpose**: Manage transport mode selection based on network quality
- **Functions**:
  - Read OGM data from status.json
  - Apply deadband logic to prevent rapid mode switching
  - Track failure and recovery counts for each node
  - Write mode decisions to `/reticulum_mesh/mesh_controller/node_modes.json`
- **Output Used By**:
  - ATAK Handler (to determine when to write packets to pending)
  - Reticulum Handler (to determine when to activate message loops)
  - Mesh Monitor web interface (for visualization)

### 4. Identity Mapper (identity_mapper.py)
- **Purpose**: Maintain mapping between network identifiers
- **Functions**:
  - Read hostname mapping from `/home/natak/mesh/hostname_mapping.json`
  - Create unified mapping of MAC addresses, hostnames, and IP addresses
  - Write mapping to `/reticulum_mesh/identity_handler/identity_map.json`
- **Output Used By**:
  - Reticulum Handler (to map MAC addresses to hostnames)
  - Mesh Monitor web interface (for human-readable node names)

### 5. RNS Monitor (rns_monitor.py)
- **Purpose**: Monitor Reticulum Network Stack connections
- **Functions**:
  - Connect to existing Reticulum instance
  - Track peer announces, signal quality, and path information
  - Write status to `/reticulum_mesh/rns_stats/rns_status.json`
- **Output Used By**:
  - Mesh Monitor web interface (for visualization)

### 6. ATAK Handler (atak_handler.py)
- **Purpose**: Interface with ATAK clients and manage TAK Protocol packets
- **Functions**:
  - Listen for TAK Protocol packets on multicast addresses
  - Compress packets using zstd compression
  - Implement packet deduplication using MD5 hashing
  - Write compressed packets to shared/pending directory when nodes are in non-WIFI mode
  - Decompress and forward received packets back to ATAK
- **Inputs**:
  - TAK Protocol packets from ATAK clients
  - Node modes from `/reticulum_mesh/mesh_controller/node_modes.json`
  - Compressed packets from `/reticulum_mesh/tak_transmission/shared/incoming`
- **Outputs**:
  - Compressed packets to `/reticulum_mesh/tak_transmission/shared/pending`
  - Decompressed packets forwarded to ATAK multicast addresses

### 7. Reticulum Handler (reticulum_handler.py)
- **Purpose**: Manage Reticulum communications for mesh data exchange
- **Functions**:
  - Initialize Reticulum with hostname-based peer discovery
  - Maintain in-memory map of peer hostnames to destinations
  - Monitor node_modes.json for nodes in non-WIFI mode
  - Process files from pending directory and transmit over Reticulum
  - Write received messages to incoming directory
- **Inputs**:
  - Node modes from `/reticulum_mesh/mesh_controller/node_modes.json`
  - Identity mapping from `/reticulum_mesh/identity_handler/identity_map.json`
  - Compressed packets from `/reticulum_mesh/tak_transmission/shared/pending`
- **Outputs**:
  - Received packets to `/reticulum_mesh/tak_transmission/shared/incoming`

### 8. Mesh Monitor Web Interface (app.py)
- **Purpose**: Provide visual monitoring of the entire mesh system
- **Functions**:
  - Display node status, connectivity, and signal quality
  - Visualize network topology and path information
  - Show transport mode for each node
  - Present historical performance data

## Data Flow and File Passing Scheme

### TAK Protocol Packet Flow

1. **ATAK Client → ATAK Handler**:
   - ATAK clients send TAK Protocol packets to multicast addresses
   - ATAK Handler receives these packets

2. **ATAK Handler Processing**:
   - Compresses packets using zstd compression
   - Calculates MD5 hash for deduplication
   - Checks node_modes.json to see if any nodes are in non-WIFI mode
   - If non-WIFI nodes exist, writes compressed packet to shared/pending directory
   - If all nodes are in WIFI mode, skips writing (packets stay on WiFi only)

3. **Reticulum Handler Processing**:
   - Monitors shared/pending directory for new .zst files
   - When a file is found, moves it to shared/processing
   - Identifies target nodes by checking node_modes.json for non-WIFI nodes
   - Maps MAC addresses to hostnames using identity_map.json
   - Sends file data to each target node using Reticulum
   - Removes file from processing directory after sending

4. **Receiving Node Processing**:
   - Reticulum Handler on receiving node gets packet data
   - Writes data to shared/incoming directory with timestamp-based filename
   - ATAK Handler monitors shared/incoming directory
   - When a file is found, checks for duplicates
   - Decompresses data and forwards to ATAK multicast addresses
   - Removes file from incoming directory

### Status Information Flow

1. **OGM Monitor → Mesh Controller**:
   - OGM Monitor writes BATMAN-adv mesh status to status.json
   - Mesh Controller reads this file to make mode decisions
   - Mesh Controller writes node modes to node_modes.json

2. **Node Modes → Handlers**:
   - Both ATAK Handler and Reticulum Handler read node_modes.json
   - ATAK Handler uses it to decide when to write packets to pending
   - Reticulum Handler uses it to activate/deactivate message loops

3. **Identity Mapping**:
   - Identity Mapper reads hostname_mapping.json
   - Creates unified mapping in identity_map.json
   - Reticulum Handler uses this to map MAC addresses to hostnames

4. **Monitoring Data Flow**:
   - OGM Monitor writes mesh status to status.json
   - RNS Monitor writes Reticulum status to rns_status.json
   - Mesh Monitor web interface reads these files for visualization

## System Resilience Features

1. **Automatic Transport Selection**:
   - System monitors link quality through OGM tracking
   - Switches to LoRa radio when WiFi connectivity degrades
   - Implements deadband logic to prevent rapid mode switching
   - Returns to WiFi when connectivity is restored

2. **File-Based Communication**:
   - Components communicate through files in shared directories
   - Atomic file operations ensure consistency
   - Each component can operate independently
   - System can recover from component failures

3. **Peer Discovery and Management**:
   - Reticulum announces with hostname information
   - In-memory peer mapping for efficient message routing
   - Peer timeout to remove stale entries
   - Regular re-announces to maintain peer visibility

4. **Packet Optimization**:
   - zstd compression reduces packet size
   - MD5-based deduplication prevents redundant transmissions
   - Conditional processing based on node modes
   - Cleanup of shared directories when not needed

## Service Dependencies and Startup Sequence

The system components are managed by systemd services that start in a specific order:

1. reticulum-mesh-network.service (network setup)
2. reticulum-mesh-ogm.service (OGM monitoring)
3. reticulum-mesh-identity.service (identity mapping)
4. reticulum-mesh-reticulum.service (Reticulum handling)
5. reticulum-mesh-atak.service (ATAK handling)
6. reticulum-mesh-rns-monitor.service (RNS monitoring)
7. mesh-monitor.service (web interface)

Each service depends on the successful startup of its predecessors, with appropriate delays to ensure proper initialization.
