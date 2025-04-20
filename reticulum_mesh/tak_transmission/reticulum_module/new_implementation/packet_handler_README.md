# Packet Handler Documentation

## Overview
The Packet Handler is responsible for managing packet transmission between nodes in the mesh network, specifically focusing on LORA mode nodes. It operates two main loops:

1. **Outgoing Loop**: Monitors pending packets and manages their transmission to LORA nodes
2. **Incoming Loop**: Receives and processes incoming packets from the mesh network

## Critical Implementation Notes

### Pure Transport Layer
- **NO PACKET MODIFICATION**: This is a critical requirement. The packet handler ONLY moves files between directories and sends them via Reticulum. It NEVER modifies packet contents.
- **Sequential Processing**: Due to LORA radio constraints, all operations are sequential. There is no concurrent processing.
- **Directory Operations**: Only performs move operations between directories:
  * `/pending` → `/sent_buffer` (after sending)
  * `/incoming` ← received packets

### Reticulum Integration
- Uses peer_discovery's 'IN' destination for receiving packets
- Creates RNS.Packet instances for sending with delivery proofs
- Leverages Reticulum's built-in proof system:
  ```python
  # Example packet sending with proof tracking
  packet = RNS.Packet(destination, data)
  receipt = packet.send()
  receipt.set_delivery_callback(on_delivery)
  receipt.set_timeout_callback(on_timeout)
  ```

### Core Components

1. **Packet Monitoring**
   - Monitors `/pending` directory for new files
   - Processes one packet at a time (sequential)
   - Moves processed packets to `/sent_buffer`
   - Moves received packets to `/incoming`

2. **Node Status**
   - Reads node_status.json to identify LORA nodes
   - Only sends packets to nodes in LORA mode
   - No peer tracking (handled by peer_discovery)

3. **Delivery Handling**
   - Uses Reticulum's built-in proof system with callbacks
   - Tracks delivery status per file and per node
   - Maintains state of which nodes have confirmed receipt
   - Automatic retry system for failed deliveries
   - Removes from tracking when all nodes confirm

### Configuration
```python
# Required config.py settings
PACKET_TIMEOUT = 300      # Time in seconds to wait for delivery proof
RETRY_MAX_ATTEMPTS = 5    # Max retry attempts per node
RETRY_INITIAL_DELAY = 10  # Base delay for first retry
RETRY_BACKOFF_FACTOR = 2  # Multiplier for delay increase
RETRY_MAX_DELAY = 120     # Maximum delay between retries
```

### Error Handling
- Failed packet deliveries logged but do not stop processing
- No packet modification on errors
- Failed deliveries tracked per node for retry
- Exponential backoff for retries
- Max retry attempts enforced per node

## Implementation Notes

### Outgoing Flow
1. Monitor `/pending` directory for new files
2. When file found, read node_status.json for LORA nodes
3. For each LORA node:
   - Create RNS.Packet with delivery proof
   - Send packet and track receipt
   - Move to sent_buffer after sending
   - Initialize delivery tracking for each node
   - Track delivery status per node
   - Retry failed nodes with exponential backoff
   - Remove tracking when all nodes confirm

### Incoming Flow
1. Listen on peer_discovery's IN destination
2. When packet received:
   - Move directly to incoming directory
   - No modification of packet contents
   - No acknowledgment handling (done by Reticulum)

### Error Handling
1. Failed Sends:
   - Log error
   - Mark node as failed in delivery tracking
   - Keep packet in sent_buffer
   - Retry based on backoff schedule
   - Continue with next packet

2. Failed Receives:
   - Log error
   - Continue with next packet
   - No retry needed (handled by Reticulum)

### Key Differences from Old Implementation
1. No peer tracking (handled by peer_discovery)
2. No threading/concurrency
3. Simplified error handling
4. Uses Reticulum's built-in proof system
5. Strict no-modification policy for packets
6. Sequential processing only

## Integration Points

1. **File System**
   - `/pending`: Watch for new files
   - `/sent_buffer`: Store sent files
   - `/incoming`: Store received files
   - `node_status.json`: Read LORA node list

2. **Reticulum**
   - Uses peer_discovery's IN destination
   - Uses RNS.Packet for sending
   - Uses built-in proof system

3. **Logging**
   - File movements
   - Delivery status
   - Errors
   - No performance metrics needed
