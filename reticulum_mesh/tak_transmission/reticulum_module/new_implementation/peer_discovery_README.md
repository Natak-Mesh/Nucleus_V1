# Peer Discovery

A transport-agnostic module that manages peer announcements, identity tracking, and destination management for the Reticulum mesh network.

## Core Functionality

- **Identity Management**: Creates and maintains this node's Reticulum identity
- **Destination Ownership**: Creates and owns the IN destination for receiving packets
- **Announce Processing**: Broadcasts presence and processes peer announces
- **Peer Tracking**: Maintains mappings between hostnames, identities, and destination hashes
- **State Synchronization**: Provides JSON state file for inter-process communication

## Announce Mechanism

### Outgoing Announces
- Periodic announces every 60 seconds (configurable)
- Hostname included as application data
- Uses `RNS.Destination.announce()` with app_data parameter
- Responsive announces when new peers are detected

### Incoming Announces
- Filtered by APP_NAME and ASPECT (e.g., "atak.cot")
- Extracts hostname from app_data
- Updates peer mapping and last_seen timestamp
- Triggers responsive announce with random delay (0.5-1.5s)

## Peer Management

### In-Memory State
- `peer_map`: Maps hostnames to peer data (identity, destination_hash)
- `last_seen`: Tracks when each peer was last seen
- Local node excluded from tracking

### JSON State File
- Path: `peer_discovery.json`
- Updated whenever peers are added/removed
- Format:
  ```json
  {
    "timestamp": 1744488097,
    "peers": {
      "hostname": {
        "destination_hash": "ab12cd34...",
        "last_seen": 1744488097
      }
    }
  }
  ```

### Stale Peer Handling
- Peers not seen for 300 seconds (configurable) are removed
- Automatic cleanup on both in-memory state and JSON file
- Fresh state on every startup

## Critical Implementation Detail

The destination hash stored in peer_discovery.json MUST be the one received directly from Reticulum announces. Never derive it from the public key, as this will break routing. A destination hash in Reticulum includes aspects, destination type, and other characteristics beyond just the public key.

## Integration Points

### Packet Manager
- Provides the IN destination for receiving packets
- Supplies peer identities for outbound packet addressing
- Maintains peer state independent of packet operations

### Reticulum
- Registers announce handler with `RNS.Transport.register_announce_handler()`
- Creates identity with `RNS.Identity()`
- Creates destination with:
  ```python
  RNS.Destination(
      identity,
      RNS.Destination.IN,
      RNS.Destination.SINGLE,
      config.APP_NAME,
      config.ASPECT
  )
  ```

## Configuration Parameters

- `APP_NAME`: Application identifier ("atak")
- `ASPECT`: Application aspect ("cot")
- `ANNOUNCE_INTERVAL`: Time between announces (60 seconds)
- `PEER_TIMEOUT`: Time before peer considered stale (300 seconds)

## Transport Independence

- Completely independent of WiFi/OGM status
- No reliance on Batman-adv or other network layers
- Works across any transport Reticulum supports
- Peer discovery happens solely through Reticulum's announce mechanism
