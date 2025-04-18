# Reticulum TAK Transmission System

A streamlined implementation for transmitting TAK Protocol packets over Reticulum mesh networks, providing reliable packet delivery between nodes in different network modes.

## System Startup Flow

1. **Systemd Service**: `reticulum-stack.service`
   - Executes `/home/natak/reticulum_mesh/start_reticulum_stack.sh`
   - Runs as user `natak`
   - Restarts on failure

2. **Startup Script**: `start_reticulum_stack.sh`
   - Cleans old packet files from shared directories
   - Sets Python environment
   - Executes `test_setup.py`

3. **Main Coordinator**: `test_setup.py`
   - Initializes and orchestrates all components
   - Manages component lifecycle

## Core Components

### 1. Enhanced OGM Monitor
- **Path**: `/home/natak/reticulum_mesh/ogm_monitor/enhanced_ogm_monitor.py`
- **Function**: Tracks mesh node connectivity status
- **Output**: Writes node status to `node_status.json`
- **Decision Logic**: 
  - Switches nodes to LORA mode after 3 consecutive failures
  - Returns to WIFI mode after 10 consecutive good readings

### 2. Peer Discovery
- **Function**: Manages peer announcements and tracking
- **Key Operations**:
  - Creates and owns the Reticulum IN destination
  - Announces presence on the network
  - Processes announces from other nodes
  - Maintains peer identity mapping
  - Writes peer status to `peer_discovery.json`

### 3. Packet Manager
- **Function**: Handles packet transmission between nodes
- **Key Operations**:
  - Monitors pending directory for outgoing packets
  - Sends packets to nodes in LORA mode
  - Tracks delivery confirmation
  - Implements retry mechanism with exponential backoff
  - Processes incoming packets

### 4. ATAK Handler
- **Path**: `/home/natak/reticulum_mesh/tak_transmission/atak_module/atak_handler.py`
- **Function**: Interfaces between ATAK and the mesh network
- **Key Operations**:
  - Listens for ATAK multicast packets
  - Compresses packets using Zstandard
  - Writes compressed packets to pending directory
  - Processes incoming packets from Reticulum
  - Forwards to ATAK on different ports

## Module Interactions

```
test_setup.py
    │
    ├── Starts enhanced_ogm_monitor.py (subprocess)
    │
    ├── Initializes peer_discovery.py
    │   │
    │   └── Creates Reticulum destination
    │
    ├── Initializes packet_manager.py
    │   │
    │   ├── Uses peer_discovery for destination access
    │   └── Reads node_status.json to identify LORA nodes
    │
    └── Starts atak_handler.py (subprocess)
        │
        └── Monitors shared directories
```

## Data Flow

1. **ATAK → Mesh Network**:
   - ATAK sends multicast packets (224.10.10.1:17012, etc.)
   - ATAK Handler compresses packets with Zstandard
   - Compressed packets written to `pending/` directory
   - Packet Manager detects files in `pending/`
   - Packet Manager sends to nodes in LORA mode
   - Delivery confirmation tracked with automatic retries

2. **Mesh Network → ATAK**:
   - Incoming packets received by Peer Discovery destination
   - Packet Manager writes to `incoming/` directory
   - ATAK Handler monitors `incoming/` directory
   - ATAK Handler decompresses packets
   - Decompressed packets forwarded to ATAK multicast addresses

## Shared Directories

- **pending/**: Compressed packets waiting for transmission
- **incoming/**: Compressed packets received from other nodes
- **processing/**: Temporary storage during operations
- **sent_buffer/**: Storage for packets awaiting delivery confirmation

## Configuration

All settings centralized in `config.py`:
- Reticulum app name and aspect: `atak.cot`
- Announce interval: 60 seconds
- Peer timeout: 300 seconds
- Retry parameters: Initial delay 25s, backoff factor 2x
- Maximum retry attempts: 5
- Log settings and directory paths

## Logging

- Centralized logging system in `logger.py`
- Rate-limited error logging
- Rotating log files with configurable size
- Log files stored in `/var/log/reticulum/`
