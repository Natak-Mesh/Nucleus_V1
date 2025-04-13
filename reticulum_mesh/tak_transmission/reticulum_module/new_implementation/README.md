# Reticulum Handler - Direct Packet Implementation

A streamlined implementation of the Reticulum mesh networking handler that provides reliable packet delivery through direct packet transmission.

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
ReticulumHandler
    ├── FileManager - File operations and directory management
    ├── PeerDiscovery - Announce handling and peer tracking
    └── PacketManager - Direct packet transmission and retry mechanism
```

### Components

1. **ReticulumHandler**: Main coordinator that integrates all components.

2. **FileManager**: Handles all file operations:
   - Directory creation and management
   - Saving incoming data to files
   - Processing files in the pending directory
   - Managing buffer files for retries

3. **PeerDiscovery**: Manages peer announcements and tracking:
   - Creates and owns the IN destination
   - Announces our presence on the network
   - Processes announces from peers
   - Maintains peer identity mapping
   - Provides destination access to other components

4. **PacketManager**: Handles packet operations:
   - Direct packet transmission to peers
   - Delivery confirmation tracking
   - Automatic retry with exponential backoff
   - Processing incoming packets
   - Managing buffer references for retries

## Configuration

All configuration settings are centralized in the `config.py` file. Important settings include:

- Reticulum app name and aspect
- File paths for data directories
- Retry mechanism parameters (delays, backoff, etc.)
- Logging settings
- Thread intervals

## How It Works

1. The system monitors `node_modes.json` to identify peers that are in non-WiFi mode.
2. When files appear in the pending directory, they are processed and sent directly to peers.
3. Each packet transmission includes:
   - Automatic delivery confirmation
   - Retry mechanism for failed deliveries
   - Buffer management for potential retries
4. Incoming packets are saved to files in the incoming directory.

## Running the Handler

To run the Reticulum handler:

```bash
cd reticulum_mesh/tak_transmission/reticulum_module
python -m new_implementation.run_reticulum
```

Or directly:

```bash
./new_implementation/run_reticulum.py
```

## Implementation Notes

### Identity Mapping

PeerDiscovery maintains the mapping between:
- Hostnames
- Reticulum identities
- Destination hashes

This mapping is critical for packet addressing and delivery confirmation.

### Retry Mechanism

The retry mechanism includes:
- Exponential backoff with jitter to prevent retry storms
- Configurable retry attempts and delays
- Buffer management for retry data
- Automatic cleanup of delivered packets

### Packet Delivery

Direct packet transmission provides:
- Immediate delivery confirmation
- Automatic retry for failed packets
- Buffer management for retry data
- Clean separation from transport details

## Logging

All components produce detailed logs to aid in troubleshooting and monitoring. The logging format and verbosity can be adjusted in the config.py file.

## Implementation Progress

### Enhanced OGM Monitor
We've implemented an enhanced OGM (Originator Message) monitor that:
- Tracks the status of all mesh nodes using Batman-adv originator data
- Determines node modes (WIFI/LORA) based on connection quality metrics
- Outputs detailed status to `node_status.json` for use by other components
- Provides real-time console output showing node status and mode

### PeerDiscovery Module
The PeerDiscovery module has been enhanced with:
- Completely transport-agnostic peer discovery and tracking
- Bidirectional mapping between all identity representations
- Responsive announce system for faster mesh formation
  - When a new peer is discovered, sends an immediate response announce
  - Uses random delays (0.5-2.0s) to prevent announce storms
- Optional JSON export for inter-process visibility
  - Provides status information to other programs without IPC
  - Updates every 30 seconds with current peer information

The PeerDiscovery module is now fully independent of WiFi/OGM status, making it more resilient and simpler. It relies solely on Reticulum's native announce mechanism to build and maintain peer awareness.

### PacketManager Module
The PacketManager module implements:
- Direct packet transmission to peers
- Built-in delivery confirmation
- Automatic retry mechanism with exponential backoff
- Buffer management for retries
- Efficient packet processing and tracking

The PacketManager focuses on reliable packet delivery without the overhead of persistent links. It uses PeerDiscovery's IN destination for receiving packets and creates outbound destinations as needed for transmission.

### Next Steps
The next components to implement are:
1. FileManager - For handling file operations
2. ReticulumHandler - The main coordinator integrating all components
