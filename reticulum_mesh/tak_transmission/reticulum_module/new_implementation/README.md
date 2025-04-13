# Reticulum Handler - Modular Implementation

A modular implementation of the Reticulum mesh networking handler that provides reliable packet delivery, link management, and peer discovery.

## Architecture

This implementation follows a modular design with clear separation of responsibilities:

```
ReticulumHandler
    ├── FileManager - File operations and directory management
    ├── PeerDiscovery - Announce handling and peer tracking
    ├── LinkManager - Link establishment and monitoring
    └── PacketManager - Packet handling and retry mechanism
```

### Components

1. **ReticulumHandler**: Main coordinator that integrates all components.

2. **FileManager**: Handles all file operations:
   - Directory creation and management
   - Saving incoming data to files
   - Processing files in the pending directory
   - Managing buffer files for retries

3. **PeerDiscovery**: Manages peer announcements and tracking:
   - Announcing our presence on the network
   - Processing announces from peers
   - Tracking peer identities and states
   - Maintaining hostname to identity mappings

4. **LinkManager**: Handles link establishment and maintenance:
   - Establishing links to peers
   - Monitoring link health
   - Re-establishing failed links
   - Processing incoming/outgoing packets

5. **PacketManager**: Handles packet operations:
   - Sending packets with delivery tracking
   - Managing packet retry mechanism with exponential backoff
   - Processing incoming packets
   - Managing buffer references for retried packets

## Configuration

All configuration settings are centralized in the `config.py` file. Important settings include:

- Reticulum app name and aspect
- File paths for data directories
- Retry mechanism parameters (delays, backoff, etc.)
- Logging settings
- Thread intervals

## How It Works

1. The system monitors `node_modes.json` to identify peers that are in non-WiFi mode.
2. It establishes links to these peers and maintains them.
3. When files appear in the pending directory, they are processed and sent to all non-WiFi peers.
4. Packets are tracked, and if delivery proof isn't received, they are automatically retried.
5. Incoming packets are saved to files in the incoming directory.

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

The identity mapping section in PeerDiscovery has a placeholder that needs to be revisited. This handles the association between Reticulum identities, hostnames, and destination hashes.

### Retry Mechanism

The retry mechanism uses exponential backoff with jitter to prevent retry storms. It also tracks packet delivery state and buffers sent packets for potential retries.

### Link Management

The link manager tracks link health and automatically re-establishes links when they fail. It also collects statistics on link quality and performance.

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

### LinkManager Module
The LinkManager module has been implemented with:
- Robust encrypted link establishment and maintenance
- Physical layer statistics tracking (RSSI, SNR)
- Automatic link re-establishment for failed connections
- Link health monitoring with configurable intervals
- Status tracking and reporting for all active links
- JSON export for external monitoring and integration
- Detailed metrics and statistics for performance analysis

The LinkManager integrates with the node status monitoring to focus on establishing and maintaining links to non-WiFi nodes. It efficiently manages all aspects of link lifecycle, from creation to monitoring to graceful shutdown.

### Next Steps
The next components to implement are:
1. PacketManager - For handling reliable packet delivery with retries
2. FileManager - For handling file operations
3. ReticulumHandler - The main coordinator integrating all components
