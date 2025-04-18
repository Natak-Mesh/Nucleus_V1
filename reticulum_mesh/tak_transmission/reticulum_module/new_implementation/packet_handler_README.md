# Packet Manager

A transport-layer component that handles reliable packet transmission between mesh nodes, focusing on nodes in LORA mode.

## Core Functionality

- **Pure Transport Layer**: Moves packets between directories and transmits via Reticulum without modifying content
- **Sequential Processing**: Handles one packet at a time due to LORA radio constraints
- **Delivery Confirmation**: Uses Reticulum's built-in proof system to track packet delivery
- **Automatic Retries**: Implements exponential backoff for failed transmissions

## Data Flow

### Outgoing Packets
1. Monitors `pending/` directory for new compressed packet files
2. Reads `node_status.json` to identify nodes in LORA mode
3. Sends packet to each LORA node with delivery tracking
4. Moves processed packet to `sent_buffer/` directory
5. Tracks delivery status per node with callbacks
6. Removes packet from `sent_buffer/` when all nodes confirm receipt

### Incoming Packets
1. Receives packets via Peer Discovery's IN destination
2. Writes received packets directly to `incoming/` directory
3. No content modification or additional processing

## Retry Mechanism

- **Exponential Backoff**: Delay increases with each retry attempt
- **Per-Node Tracking**: Each node's delivery status tracked independently
- **Configurable Parameters**:
  - Initial delay: 25 seconds
  - Backoff factor: 2x (doubles each retry)
  - Maximum delay: 120 seconds
  - Maximum attempts: 5

## Integration Points

### Peer Discovery
- Uses Peer Discovery's IN destination for receiving packets
- Retrieves peer identities for packet addressing
- No direct peer tracking (handled by Peer Discovery)

### Node Status
- Reads `node_status.json` to identify nodes in LORA mode
- Only sends packets to nodes marked as "LORA" mode
- Combines with peer discovery data to determine valid targets

### Reticulum
- Creates outbound destinations for each target node
- Uses `RNS.Packet` with delivery confirmation
- Sets callbacks for delivery and timeout events:
  ```python
  packet = RNS.Packet(destination, data)
  receipt = packet.send()
  receipt.set_delivery_callback(on_delivery)
  receipt.set_timeout_callback(on_timeout)
  ```

## Configuration Parameters

- `PACKET_TIMEOUT`: Time to wait for delivery proof (300 seconds)
- `RETRY_MAX_ATTEMPTS`: Maximum retry attempts (5)
- `RETRY_INITIAL_DELAY`: Base delay for first retry (25 seconds)
- `RETRY_BACKOFF_FACTOR`: Multiplier for delay increase (2)
- `RETRY_MAX_DELAY`: Maximum delay between retries (120 seconds)
- `SEND_SPACING_DELAY`: Minimum time between sends (2 seconds)

## Error Handling

- Failed deliveries logged but don't stop processing
- Packets remain in `sent_buffer/` until delivery confirmed or max retries reached
- Automatic cleanup of failed packets after max retries
- Rate-limited logging prevents log flooding
