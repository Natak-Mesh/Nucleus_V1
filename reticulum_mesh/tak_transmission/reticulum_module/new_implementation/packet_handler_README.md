# Packet Handler Documentation

## Overview
The Packet Handler is responsible for managing packet transmission between nodes in the mesh network, specifically focusing on LORA mode nodes. It operates two main loops:

1. **Outgoing Loop**: Monitors pending packets and manages their transmission to LORA nodes
2. **Incoming Loop**: Receives and processes incoming packets from the mesh network

## Directory Structure
```
/home/natak/reticulum_mesh/tak_transmission/shared/
├── pending/         # New packets awaiting transmission
├── sent_buffer/     # Successfully transmitted packets
└── incoming/        # Received packets from other nodes
```

## Outgoing Loop

### Functionality
- Monitors `/pending` directory for new packets
- Reads `node_status.json` to identify LORA mode nodes
- Transmits packets to each LORA node with delivery proof requirement
- Moves processed packets to `/sent_buffer`
- Tracks packet delivery status and proofs

### Packet Tracking
```python
{
    "packet_name": {
        "timestamp": sent_time,
        "nodes": {
            "node1": {"status": "pending", "attempts": 1},
            "node2": {"status": "delivered", "proof_time": time}
        }
    }
}
```

### Delivery States
- **Pending**: Initial state after sending to node
- **Delivered**: Proof of delivery received
- **Failed**: No proof received within timeout period

### Timeout Handling
- Uses `RETRY_*` configurations from `config.py`
- Initial delay: 10 seconds
- Backoff factor: 2 (doubles each retry)
- Maximum delay: 120 seconds
- Maximum attempts: 5
- Rate limit: 1 retry per second

### Failure Handling
When a packet fails to deliver (no proof received within timeout):
1. Packet remains in tracking dictionary with "failed" status
2. Failed delivery is logged for monitoring
3. Packet remains in sent_buffer for manual inspection
4. System continues monitoring for late proofs

## Incoming Loop

### Functionality
- Listens for incoming packets over Reticulum
- Moves received packets directly to `/incoming` directory
- Maintains packet integrity (no modifications)
- Operates independently of outgoing loop

### Critical Requirements
- **No Packet Modification**: Incoming packets must be stored exactly as received
- **Immediate Processing**: Packets should be moved to incoming directory without delay
- **Error Handling**: Any receive errors should be logged but not impact continuous operation

## Implementation Notes

### Key Classes
1. **DirectoryMonitor**
   - Watches `/pending` directory for new files
   - Triggers packet processing workflow

2. **PacketTracker**
   - Manages delivery status dictionary
   - Handles proof updates
   - Monitors timeouts

3. **ProofHandler**
   - Processes delivery proofs
   - Updates tracking status
   - Triggers cleanup of successful deliveries

### Configuration Requirements
```python
# Add to config.py:
PACKET_TIMEOUT = 300  # 5 minutes to receive proof
TRACKING_FILE = "packet_tracking.json"  # For persistence
```

### Monitoring & Logging
- All packet movements logged with timestamps
- Delivery statistics tracked (success/failure rates)
- Node-specific performance metrics
- Proof receipt timing data

## Future Considerations

### Potential Enhancements
1. Automated cleanup of old successful deliveries
2. Performance optimization for high packet volumes
3. Advanced retry strategies based on node performance
4. Real-time monitoring dashboard

### Integration Points
- Node status monitoring
- Network performance metrics
- System health monitoring
