# Reticulum Mesh System - New Implementation

A streamlined implementation of Reticulum-based mesh networking that provides reliable packet delivery through direct packet transmission, with advanced retry mechanisms and integration with node mode detection.

## System Overview

This implementation follows a modular design with clear separation of responsibilities, focusing on reliability and efficiency in mesh network communications. The system is designed to work across different network conditions, automatically adapting to nodes operating in WiFi or LoRa modes.

### Key Design Principles

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

3. **Adaptive Behavior**
   - Automatically detects node operating modes (WiFi/LoRa)
   - Optimizes transmission based on network conditions
   - Only sends packets to nodes in LoRa mode with valid peer discovery entries
   - Prevents unnecessary transmissions to save bandwidth

## File Structure

The new_implementation directory contains the following key files:

- **packet_manager.py**: Core component for packet transmission, delivery tracking, and retry handling
- **peer_discovery.py**: Manages peer announcements, tracking, and destination handling
- **config.py**: Centralizes all configuration settings for the system
- **logger.py**: Provides consistent logging across all components
- **test_setup.py**: Script to run all required components in sequence for testing
- **peer_discovery_README.md**: Detailed documentation for the peer discovery system
- **peer_discovery.json**: JSON state file containing peer information
- **__init__.py**: Package initialization file

## Component Details

### PacketManager (packet_manager.py)

The PacketManager is the core component responsible for reliable packet transmission across the mesh network. It implements a sophisticated system for sending packets, tracking delivery status, and automatically retrying failed transmissions.

#### Key Features

1. **Direct Packet Transmission**
   - Sends packets directly to peers without requiring persistent links
   - Uses Reticulum's built-in packet delivery confirmation
   - Measures and reports Round-Trip Time (RTT) for successful deliveries
   - Enforces minimum delay between transmissions to respect radio constraints

2. **Per-Node Delivery Tracking**
   - Tracks delivery status individually for each node
   - Structure: `delivery_status[filename] = {"nodes": {node1: {sent, sent_time, delivered, retry_count}, node2: {...}}, ...}`
   - Allows targeted retries only to nodes that haven't confirmed delivery
   - Optimizes bandwidth by avoiding unnecessary retransmissions

3. **Advanced Retry Mechanism**
   - Implements exponential backoff with configurable parameters
   - Backoff formula: `delay = min(RETRY_INITIAL_DELAY * (RETRY_BACKOFF_FACTOR ** retry_count), RETRY_MAX_DELAY)`
   - Adds random jitter to prevent retry storms: `actual_delay = base_delay * (1.0 + random.uniform(-RETRY_JITTER, RETRY_JITTER))`
   - Limits maximum retry attempts per node
   - Automatically cleans up files after successful delivery or max retries

4. **Directory-Based Workflow**
   - **Pending Directory**: Contains compressed files waiting to be sent
   - **Sent Buffer Directory**: Holds files waiting for delivery confirmation
   - **Incoming Directory**: Destination for received packets
   - Files move through directories based on their processing state
   - Automatically cleans up files when no longer needed

5. **Integration with Node Status**
   - Reads node_status.json to identify nodes in LoRa mode
   - Cross-references with peer_discovery.json to find valid transmission targets
   - Only sends packets to nodes that are both in LoRa mode and have peer discovery entries
   - Dynamically adapts to changing network conditions

6. **Radio Timing Considerations**
   - Enforces minimum delay between transmissions (SEND_SPACING_DELAY)
   - Prevents radio congestion and timing issues
   - Logs wait times when spacing is enforced
   - Optimizes transmission timing for better radio performance

7. **Comprehensive Error Handling**
   - Gracefully handles missing files, invalid JSON, and network errors
   - Implements rate-limited logging to prevent log flooding
   - Maintains system stability even during error conditions
   - Provides detailed logs for troubleshooting

#### Implementation Details

The PacketManager's main loop (`run()` method) continuously:
1. Checks if transmission is allowed based on radio timing constraints
2. Processes new outgoing packets from the pending directory
3. Handles retries for packets that haven't been delivered
4. Processes delivery receipts and updates tracking information
5. Cleans up completed or failed transmissions

For each packet, it:
1. Reads the file from the pending directory
2. Identifies valid LoRa nodes with peer discovery entries
3. Sends the packet to each node sequentially
4. Moves the file to the sent buffer after initial sending
5. Tracks delivery status for each node
6. Implements retries with exponential backoff for undelivered packets
7. Cleans up the file once all nodes confirm delivery or max retries are reached

### PeerDiscovery (peer_discovery.py)

The PeerDiscovery module manages peer announcements and tracking. It creates and owns the IN destination that other nodes use to communicate with this node, and provides a synchronized JSON state file for other modules to access peer information.

#### Key Features

1. **Identity and Destination Management**
   - Creates this node's identity and "IN" destination
   - Announces our presence on the network
   - Sets automatic proof strategy for delivery confirmation

2. **Peer Tracking**
   - Processes announces from other peers
   - Maintains peer identity mapping
   - Updates peer_discovery.json with current peer information
   - Removes stale peers that haven't been seen recently

3. **Responsive Announce System**
   - When a new peer is discovered, sends an immediate response announce
   - Uses random delays (0.5-1.5s) to prevent announce storms
   - Enables quick mesh formation

4. **Transport-Agnostic Design**
   - Completely independent of WiFi/OGM status
   - Relies solely on Reticulum's native announce mechanism
   - Works across different network transports

For more detailed information about the PeerDiscovery module, see the dedicated [peer_discovery_README.md](peer_discovery_README.md) file.

### Logger (logger.py)

The Logger module provides consistent logging across all components of the system. It implements several advanced features:

1. **Rate-Limited Logging**
   - Implements rate limiting for error messages
   - Prevents log flooding during error conditions
   - Configurable rate limit via ERROR_LOG_RATE_LIMIT

2. **Rotating Log Files**
   - Maintains a fixed number of log lines (PACKET_LOG_MAX_LINES)
   - Automatically removes oldest entries when the limit is reached
   - Ensures logs don't consume excessive disk space

3. **Consistent Formatting**
   - Provides uniform log format across all components
   - Configurable format via LOG_FORMAT
   - Includes timestamps, component names, and log levels

4. **Multiple Output Destinations**
   - Logs to both console and file
   - Allows different formatting for each destination
   - Centralizes log file location in config.LOG_DIR

### Config (config.py)

The Config module centralizes all configuration settings for the system. Key settings include:

1. **Reticulum Configuration**
   - APP_NAME and ASPECT for filtering announces
   - ANNOUNCE_INTERVAL for periodic announces
   - PEER_TIMEOUT for stale peer removal
   - STARTUP_DELAY for LoRa radio initialization

2. **File Paths**
   - BASE_DIR for the root directory
   - NODE_STATUS_PATH for OGM node status
   - Log and data directory paths

3. **Retry Mechanism Configuration**
   - RETRY_INITIAL_DELAY: Initial delay before first retry
   - RETRY_BACKOFF_FACTOR: Factor for exponential backoff
   - RETRY_MAX_DELAY: Maximum delay between retries
   - RETRY_JITTER: Random variation in retry timing
   - RETRY_MAX_ATTEMPTS: Maximum number of retry attempts

4. **Radio Timing Parameters**
   - SEND_SPACING_DELAY: Minimum delay between packet transmissions
   - PACKET_TIMEOUT: Maximum time to wait for delivery confirmation

5. **Logging Configuration**
   - LOG_LEVEL: Verbosity of logging
   - LOG_FORMAT: Format string for log entries
   - PACKET_LOG_MAX_LINES: Maximum number of lines in log files
   - ERROR_LOG_RATE_LIMIT: Rate limiting for repeated error messages

### Test Setup (test_setup.py)

The Test Setup script provides a convenient way to run all required components in sequence:

1. Starts the enhanced_ogm_monitor.py for node status tracking
2. Initializes the PeerDiscovery module
3. Starts the PacketManager with the PeerDiscovery instance
4. Waits for LoRa radio initialization
5. Starts the ATAK handler for ATAK integration

This script is useful for testing the complete system and ensuring all components work together correctly.

## System Workflow

### Packet Transmission Process

1. The system monitors node_status.json to identify peers that are in LoRa mode
2. When compressed files appear in the pending directory, they are processed and sent:
   - Files are read from the pending directory
   - Only nodes in LoRa mode with valid peer discovery entries receive packets
   - Packets are sent with delivery confirmation enabled
   - Files are moved to the sent_buffer directory until confirmed or max retries reached
3. Each packet transmission includes:
   - Per-node delivery tracking
   - Radio timing constraints (respecting SEND_SPACING_DELAY)
   - Automatic proof request for delivery confirmation
   - Buffer management for potential retries
4. For undelivered packets, the retry mechanism:
   - Uses exponential backoff with configurable parameters
   - Tracks delivery status per node
   - Only retries to nodes that haven't confirmed delivery
   - Removes files from buffer once all nodes confirm delivery or max retries reached

### Incoming Packet Handling

1. Incoming packets are received through the PeerDiscovery's IN destination
2. The PacketManager's packet callback processes these packets
3. Packets are saved to files in the incoming directory with timestamped filenames
4. Other system components monitor the incoming directory for new files

## Integration Points

### Integration with OGM System

The PacketManager integrates with the OGM monitoring system:

1. **Node Mode Detection**
   - Reads node_status.json from the OGM monitor
   - Identifies nodes operating in LoRa mode
   - Only sends packets to nodes in LoRa mode (saves bandwidth)

2. **Peer Filtering**
   - Cross-references LoRa mode nodes with peer_discovery.json
   - Only sends to nodes that have both:
     - LoRa mode status in node_status.json
     - Valid peer entries in peer_discovery.json
   - This ensures packets are only sent to reachable nodes

### Integration with ATAK Handler

The system integrates with the ATAK handler through the shared directory structure:

1. **Outgoing Packets**
   - ATAK handler compresses packets and places them in the pending directory
   - PacketManager picks up these packets and transmits them to LoRa nodes

2. **Incoming Packets**
   - PacketManager saves received packets to the incoming directory
   - ATAK handler monitors this directory and processes new files

## Running the System

To use the Reticulum mesh system, you can either run each component individually or use the test_setup.py script to start all components in sequence:

### Running Individual Components

```bash
# Start PeerDiscovery
cd reticulum_mesh/tak_transmission/reticulum_module/new_implementation
python peer_discovery.py

# Start PacketManager
cd reticulum_mesh/tak_transmission/reticulum_module/new_implementation
python packet_manager.py
```

### Running All Components with Test Setup

```bash
cd reticulum_mesh/tak_transmission/reticulum_module/new_implementation
python test_setup.py
```

## Troubleshooting

The system provides comprehensive logging to aid in troubleshooting:

1. **Log Files**
   - Main logs are stored in the directory specified by config.LOG_DIR
   - Each component has its own log file (e.g., packet_logs.log for PacketManager)

2. **Common Issues**
   - If packets aren't being sent, check node_status.json and peer_discovery.json
   - If retries aren't working, verify the retry configuration in config.py
   - If radio timing issues occur, adjust SEND_SPACING_DELAY in config.py

3. **Monitoring**
   - Monitor the log files for delivery confirmations and retry attempts
   - Check the contents of the pending, sent_buffer, and incoming directories
   - Verify that node_status.json is being updated correctly by the OGM monitor

4. **Real-time Log Monitoring**
   
   Use the following tail commands to watch the logs in real-time:
   
   ```bash
   # Monitor PacketManager logs
   tail -f /var/log/reticulum/packet_logs.log
   
   # Monitor PeerDiscovery logs
   tail -f /var/log/reticulum/peer_discovery.log
   
   # Monitor all Reticulum logs simultaneously
   tail -f /var/log/reticulum/*.log
   
   # Monitor with highlighted errors (requires ccze)
   tail -f /var/log/reticulum/packet_logs.log | ccze -A
   
   # Monitor with grep for specific events
   tail -f /var/log/reticulum/packet_logs.log | grep "delivered"
   tail -f /var/log/reticulum/packet_logs.log | grep "retry"
   ```
   
   These commands provide real-time visibility into the system's operation, which is particularly useful for debugging transmission issues or monitoring packet delivery.
