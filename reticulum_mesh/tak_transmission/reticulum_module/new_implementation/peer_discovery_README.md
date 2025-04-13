# PeerDiscovery Module

## Overview

The PeerDiscovery module is responsible for announcing our presence on the Reticulum network, tracking peers, and maintaining mappings between various identity representations. It operates independently of specific transport mediums (such as WiFi or LoRa).

## Core Functionality

### 1. Announce Management
- Broadcasts our presence on the network
- Processes announces from other peers
- Uses responsive announces to quickly form mesh connections
- A thread runs in the background to periodically send announces

### 2. Identity Tracking
- Maintains bidirectional mappings between different identity representations:
  - Hostname ↔ Identity
  - Identity Hash ↔ Hostname
  - Destination Hash ↔ Hostname
- Tracks peer last-seen timestamps
- Provides lookup methods for the rest of the system

### 3. JSON Export (Optional)
- Periodically exports peer state to a JSON file
- Provides interoperability with other programs without direct IPC
- Format is clean and human-readable

## Independence from WiFi/OGM

The PeerDiscovery module is completely independent of WiFi status and does not rely on OGM monitoring. All peer discovery happens through Reticulum's announce mechanism. This makes it fully transport-agnostic.

## Responsive Announce Mechanism

To enable quick mesh formation, the module implements a responsive announce system:
1. When a new peer announce is received, it's immediately identified as new
2. A responsive announce is scheduled with a small random delay (0.5-2.0 seconds)
3. This ensures rapid bidirectional discovery without causing announce storms

## Key Data Structures

- `peer_map`: Maps hostnames to RNS.Identity objects
- `last_seen`: Tracks when each peer was last seen
- `identity_hash_to_hostname`, `hostname_to_identity_hash`: Bidirectional mapping
- `dest_hash_to_hostname`, `hostname_to_dest_hash`: Bidirectional mapping
- `known_peers`: Set of seen destination hashes

## JSON Export Format

If enabled, the module exports peer data in this format:
```json
{
  "last_updated": 1744501206,
  "peers": {
    "hostname1": {
      "identity_hash": "abcdef1234567890...",
      "destination_hash": "0987654321fedcba...",
      "last_seen": 1744501200
    },
    "hostname2": {
      "identity_hash": "1234567890abcdef...",
      "destination_hash": "fedcba0987654321...",
      "last_seen": 1744501205
    }
  }
}
```

## Key Methods

### PeerDiscovery Class
- `__init__(identity, destination)`: Initialize discovery module
- `announce_presence()`: Send announce on the network
- `add_peer(hostname, identity, destination_hash)`: Add a new peer
- `update_peer(hostname, identity, reset_last_seen)`: Update an existing peer
- `get_peer_identity(hostname)`: Get a peer's identity
- `get_hostname_from_hash(hash_str)`: Look up hostname from hash
- `get_peer_by_any_hash(hash_str)`: Find a peer by any hash type
- `clean_stale_peers()`: Remove peers not seen recently
- `export_to_json()`: Export peer information to JSON

### AnnounceHandler Class
- `__init__(aspect_filter, parent)`: Initialize announce handler
- `received_announce(destination_hash, announced_identity, app_data)`: Process incoming announces

## Configuration

In `config.py`:
- `ANNOUNCE_INTERVAL`: Time between periodic announces (seconds)
- `PEER_TIMEOUT`: Time after which peers are considered stale (seconds)
- `PEER_STATUS_PATH`: Path to JSON export file (if enabled)
