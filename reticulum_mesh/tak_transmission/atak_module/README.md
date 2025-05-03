# ATAK Handler

## Overview
ATAK Handler is a specialized component that manages the transmission of TAK Protocol packets between ATAK instances and the mesh network. It handles packet compression, deduplication, and routing to ensure efficient and reliable communication across different network conditions. The handler dynamically adapts its behavior based on network environment, optimizing packet transmission according to whether nodes are operating in LORA or WiFi mode.

## Packet Flow Architecture

### Shared Directory Structure
The handler uses a structured directory system in `/home/natak/reticulum_mesh/tak_transmission/shared/` to manage packet flow:

- **pending/**: Compressed packets waiting to be transmitted to other nodes
  - Packets are written here after being received from local ATAK instances
  - Only used when nodes are in LORA mode with valid peer discovery entries
  
- **incoming/**: Compressed packets received from other nodes
  - Monitored continuously for new packets
  - Files are processed and then removed after successful decompression
  
- **processing/**: Temporary storage during packet processing operations
  - Used as an intermediate step in the workflow

When all nodes are in WiFi mode, the handler automatically cleans up these directories to prevent accumulation of unneeded files.

### Packet Processing Workflow
1. ATAK packets are received on multicast addresses (224.10.10.1, 239.2.3.1, 239.5.5.55)
2. Packets are compressed using Zstandard compression
3. Compressed packets are written to the `pending/` directory with timestamp-based filenames (if nodes are in LORA mode)
4. Other components pick up these packets for transmission over the mesh network
5. Incoming compressed packets from the mesh are placed in the `incoming/` directory
6. The handler decompresses these packets and forwards them to ATAK multicast addresses

## Compression Technology

### Zstandard (zstd) Implementation
- Uses the high-performance Zstandard compression algorithm
- Implements compression level 22 (maximum) for optimal size reduction
- Achieves significant compression ratios for TAK Protocol XML data

### Dictionary-Based Compression
- Utilizes a pre-trained dictionary (`cot_dict_131072.zstd`) specialized for CoT packets
- Dictionary improves compression efficiency for the repetitive XML structure of TAK packets
- Significantly reduces packet size compared to standard compression

### Size Management
- Limits compressed packet size to 350 bytes by default
- Skips packets that exceed the maximum size after compression
- Provides comprehensive statistics on compression performance

### Error Handling
- Gracefully handles compression and decompression failures
- Maintains system stability even when processing malformed packets
- Logs compression errors for troubleshooting

## Network Configuration

### Multicast Listening
- Listens on the following ATAK multicast addresses and ports:
  - 224.10.10.1:17012
  - 239.2.3.1:6969
  - 239.5.5.55:7171
- Binds to the br0 network interface when available
- Uses persistent socket connections managed by specialized socket managers

### Packet Output
- Forwards decompressed packets to LoRa output addresses and ports:
  - 224.10.10.1:17013
  - 239.2.3.1:6971
- Uses separate output ports to prevent packet loops

### Packet Loop Prevention
The system implements multiple strategies to prevent packet loops:

1. **Port Separation**: Uses different ports for input (17012, 6969, 7171) and output (17013, 6971)
2. **Multicast Loop Prevention**: Sets IP_MULTICAST_LOOP to 0 to prevent packets from looping back
3. **MD5 Hash Deduplication**: 
   - Maintains a queue of the 1000 most recent packet hashes
   - Calculates MD5 hash of each packet (both incoming and outgoing)
   - Skips processing if the hash is already in the queue
   - Automatically removes oldest hashes when the queue is full

### UDP Traffic Filtering
- **Local/Remote IP Detection**:
  - Tracks local and remote IP addresses
  - Uses DHCP leases to identify local network devices
  - Caches IP classification to improve performance
  - Actively queries network interfaces for DHCP lease information
  
- **Selective Processing**:
  - Only processes packets from local IPs on ports 17012 and 6969
  - Logs source IP and classification for monitoring
  - Prevents unnecessary packet processing from external sources

## Adaptive Behavior

### Node Mode Detection
- Checks for nodes operating in LORA mode vs WiFi mode
- Reads node status from `/home/natak/reticulum_mesh/ogm_monitor/node_status.json`
- Only processes packets for transmission when LORA mode nodes are present

### Peer Discovery Integration
- Integrates with peer discovery system to identify valid transmission targets
- Only writes packets to pending directory when LORA nodes have peer discovery entries
- Filters nodes based on entries in `/home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.json`

### Dynamic Resource Management
- Automatically cleans up shared directories when all nodes are in WiFi mode
- Prevents accumulation of unprocessed packets when not needed
- Optimizes system resources based on current network topology

## Socket Management

### Persistent Socket Architecture
- Implements `LoraOutSocketManager` for maintaining persistent UDP sockets
- Reduces socket creation/destruction overhead during high-traffic periods
- Automatically recreates sockets if they become unavailable
- Uses non-blocking socket operations to prevent thread blocking

### Interface Binding
- Automatically detects and binds to br0 network interface when available
- Handles multicast group membership properly across interface changes
- Provides graceful fallback when interface is unavailable

## Configurable Variables

### Packet Processing
- `MAX_RECENT_PACKETS`: Size of the deduplication queue (default: 1000)
  - Increasing this value improves deduplication at the cost of memory usage
  - Decreasing reduces memory usage but may allow duplicate packets

### Network Configuration
- `ATAK_OUT_ADDRS`: Multicast addresses for ATAK communication
  - Default: ["224.10.10.1", "239.2.3.1", "239.5.5.55"]
  
- `ATAK_OUT_PORTS`: Ports for ATAK communication
  - Default: [17012, 6969, 7171]
  
- `LORA_OUT_ADDRS`: Multicast addresses for LoRa output
  - Default: ["224.10.10.1", "239.2.3.1"]
  
- `LORA_OUT_PORTS`: Ports for LoRa output
  - Default: [17013, 6971]
