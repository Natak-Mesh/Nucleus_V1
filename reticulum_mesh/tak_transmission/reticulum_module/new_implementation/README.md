# Reticulum Mesh System - Direct Packet Implementation

A streamlined implementation of Reticulum-based mesh networking that provides reliable packet delivery through direct packet transmission, with advanced retry mechanisms and integration with node mode detection.

## Key Design Principles

1. **Direct Packet Transmission**
   - No persistent links required
   - Each packet is independently transmitted
   - Built-in delivery confirmation
   - Automatic retries for failed packets

2. **Critical Destination Pattern**
   - PeerDiscovery owns the IN destination
   - All components access it through PeerDiscovery
   - No duplicate destinations created
   - Clean separation of responsibilities

## Architecture

This implementation follows a modular design with clear separation of responsibilities:

```
├── PeerDiscovery - Announce handling and peer tracking
└── PacketManager - Direct packet transmission and retry mechanism
```

### Components

1. **PeerDiscovery**: Manages peer announcements and tracking:
   - Creates and owns the IN destination
   - Announces our presence on the network
   - Processes announces from peers
   - Maintains peer identity mapping
   - Provides destination access to other components
   - Outputs peer information to peer_discovery.json

2. **PacketManager**: Handles packet operations:
   - Direct packet transmission to peers
   - Delivery confirmation tracking
   - Automatic retry with exponential backoff
   - Processing incoming packets
   - Managing buffer files for retries
   - Integrates with OGM system to identify LORA nodes

## Configuration

All configuration settings are centralized in the `config.py` file. Important settings include:

- Reticulum app name and aspect
- File paths for data directories:
  - `PENDING_DIR`: Directory for outgoing packets
  - `SENT_BUFFER_DIR`: Directory for packets waiting for delivery confirmation
  - `INCOMING_DIR`: Directory for received packets
  - `NODE_STATUS_PATH`: Path to the node status file from OGM
- Retry mechanism parameters:
  - `RETRY_INITIAL_DELAY`: Initial delay before first retry
  - `RETRY_BACKOFF_FACTOR`: Factor for exponential backoff
  - `RETRY_MAX_DELAY`: Maximum delay between retries
  - `RETRY_MAX_ATTEMPTS`: Maximum number of retry attempts
- Radio timing parameters:
  - `SEND_SPACING_DELAY`: Minimum delay between packet transmissions to respect radio constraints
  - `PACKET_TIMEOUT`: Maximum time to wait for delivery confirmation
- Logging settings

## How It Works

1. The system monitors `node_status.json` to identify peers that are in LORA mode.
2. When compressed files appear in the pending directory, they are processed and sent directly to peers:
   - Files are read from the pending directory
   - Only nodes in LORA mode with valid peer discovery entries receive packets
   - Packets are sent with delivery confirmation enabled
   - Files are moved to the sent_buffer directory until confirmed or max retries reached
3. Each packet transmission includes:
   - Per-node delivery tracking
   - Radio timing constraints (respecting `SEND_SPACING_DELAY`)
   - Automatic proof request for delivery confirmation
   - Buffer management for potential retries
4. Incoming packets are saved to files in the incoming directory with timestamped filenames.
5. For undelivered packets, the retry mechanism:
   - Uses exponential backoff with configurable parameters
   - Tracks delivery status per node
   - Removes files from buffer once all nodes confirm delivery
   - Cleans up failed packets after max retry attempts

## Running the System Components

To use the Reticulum mesh system, you need to run each component individually since they operate as separate modules:

### Running PacketManager

```bash
cd reticulum_mesh/tak_transmission/reticulum_module/new_implementation
python packet_manager.py
```

### Running PeerDiscovery
```bash
cd reticulum_mesh/tak_transmission/reticulum_module/new_implementation
python peer_discovery.py
```

## Interaction Between Components

### PacketManager and PeerDiscovery Integration

The PacketManager relies on PeerDiscovery in several critical ways:

1. **Destination Ownership**: 
   - PeerDiscovery creates and owns the IN destination
   - PacketManager accesses it through `peer_discovery.destination`
   - This ensures consistent destination handling between components

2. **Incoming Packet Callback**:
   - PacketManager sets up a packet callback on PeerDiscovery's destination
   - This allows it to receive and process incoming packets
   - All packets use `PROVE_ALL` strategy for delivery confirmation

3. **Peer Identity Resolution**:
   - Uses `peer_discovery.get_peer_identity(hostname)` to resolve peer identities
   - Creates outbound destinations to each peer for sending packets
   - Ensures correct routing through Reticulum's mesh

### Integration with OGM System

The PacketManager integrates with the OGM monitoring system:

1. **Node Mode Detection**:
   - Reads `node_status.json` from the OGM monitor
   - Identifies nodes operating in LORA mode
   - Only sends packets to nodes in LORA mode (saves bandwidth)

2. **Peer Filtering**:
   - Cross-references LORA mode nodes with peer_discovery.json
   - Only sends to nodes that have both:
     - LORA mode status in node_status.json
     - Valid peer entries in peer_discovery.json
   - This ensures packets are only sent to reachable nodes

### Logger Integration

The PacketManager uses the unified logger module:

1. **Dedicated Logger**:
   - Creates a dedicated logger instance with `logger.get_logger("PacketManager", "packet_logs.log")`
   - All operations are logged with appropriate severity levels
   - Log rotation and formatting handled by logger module

2. **Comprehensive Logging**:
   - Delivery confirmations with RTT measurements
   - Retry attempts and timing
   - Errors and exceptions
   - Radio timing constraints

## Radio Timing Considerations

The PacketManager implements specific optimizations for radio operation:

1. **Send Spacing**:
   - Enforces minimum delay between transmissions (`SEND_SPACING_DELAY`)
   - Prevents radio congestion and timing issues
   - Logs wait times when spacing is enforced

2. **RTT Reporting**:
   - Measures and reports round-trip time for successful deliveries
   - Formats RTT in appropriate units (milliseconds or seconds)
   - Uses this data for monitoring network performance

## Logging

All components produce detailed logs to aid in troubleshooting and monitoring. The logging format and verbosity can be adjusted in the config.py file.

## Current Implementation

### OGM Monitor
The OGM (Originator Message) monitor:
- Tracks the status of all mesh nodes using Batman-adv originator data
- Determines node modes (WIFI/LORA) based on connection quality metrics
- Outputs detailed status to `node_status.json` for use by other components
- Provides real-time console output showing node status and mode

### PeerDiscovery Module
The PeerDiscovery module features:
- Completely transport-agnostic peer discovery and tracking
- Responsive announce system for faster mesh formation
  - When a new peer is discovered, sends an immediate response announce
  - Uses random delays (0.5-1.5s) to prevent announce storms
- JSON export for inter-process visibility via peer_discovery.json
  - Provides status information to other programs without IPC
  - Updates whenever peers are added or removed

The PeerDiscovery module is fully independent of WiFi/OGM status, making it resilient and simple. It relies solely on Reticulum's native announce mechanism to build and maintain peer awareness.

### PacketManager Module
The PacketManager module implements:
- Direct packet transmission to peers
- Built-in delivery confirmation with RTT reporting
- Automatic retry mechanism with exponential backoff
- Integration with OGM monitoring for LORA node detection
- Directory-based workflow for packet processing

## Retry Mechanism Details

The PacketManager implements a sophisticated retry mechanism:

1. **Delivery Tracking**:
   - Tracks delivery status per file and per node
   - Structure: `delivery_status[filename] = {"nodes": {node1: delivered, node2: delivered}, "first_sent": timestamp, "last_retry": timestamp, "retry_count": count}`
   - Uses this to determine which nodes need retries

2. **Exponential Backoff**:
   - Initial delay: `RETRY_INITIAL_DELAY`
   - Backoff formula: `delay = min(RETRY_INITIAL_DELAY * (RETRY_BACKOFF_FACTOR ** retry_count), RETRY_MAX_DELAY)`
   - Maximum attempts: `RETRY_MAX_ATTEMPTS`
   - Prevents network congestion during retry scenarios

3. **Targeted Retries**:
   - Only retries to nodes that haven't confirmed delivery
   - Only retries to nodes still in LORA mode with valid identities
   - Avoids unnecessary transmissions

4. **Cleanup Logic**:
   - Removes files from buffer when all nodes confirm delivery
   - Removes files after max retry attempts
   - Logs all status changes for troubleshooting

## Directory Structure

The PacketManager manages three key directories:

1. **Pending Directory** (`PENDING_DIR`):
   - Contains compressed files waiting to be sent
   - Files are processed in chronological order (oldest first)
   - Files are moved to sent_buffer after initial sending

2. **Sent Buffer Directory** (`SENT_BUFFER_DIR`):
   - Contains files waiting for delivery confirmation
   - Files remain here until all nodes confirm delivery or max retries reached
   - Used as source for retry operations

3. **Incoming Directory** (`INCOMING_DIR`):
   - Destination for received packets
   - Files are saved with timestamp-based filenames
   - Processed by other system components

All directory paths are configurable in config.py for flexibility.
