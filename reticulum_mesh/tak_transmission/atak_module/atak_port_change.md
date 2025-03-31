# ATAK Port Configuration Change

## Current Configuration

### Current Multicast Ports
The ATAKHandler currently listens on the following multicast addresses and ports:

| Purpose | Multicast Address | Port |
|---------|------------------|------|
| CoT Messages | 224.10.10.1 | 17012 |
| SA Multicast | 239.2.3.1 | 6969 |
| Additional Channel | 239.5.5.55 | 7171 |

### Current ATAK Configuration
All ATAK devices are currently configured to both send and receive on these same ports:
- CoT Output/Input: 224.10.10.1:17012:udp
- SA Multicast Output/Input: 239.2.3.1:6969:udp
- Additional Channel Output/Input: 239.5.5.55:7171:udp

## Problem Statement

The current configuration causes excessive traffic to takNode2 because:

1. Each position update is being forwarded twice to takNode2 (once by takNode1 and once by takNode3)
2. We cannot distinguish between locally generated packets and packets received from other nodes
3. This creates a "triangle problem" where takNode2 receives duplicate information
4. The slow LoRa link (1.3 kbps) cannot handle this volume of traffic, causing extreme lag

## Proposed Solution

### New Port Configuration
We will separate the output and input ports to distinguish between locally generated packets and packets from other nodes:

| Purpose | Direction | Multicast Address | Port |
|---------|-----------|------------------|------|
| CoT Messages | Output (Send) | 224.10.10.1 | 17012 |
| CoT Messages | Input (Receive) | 224.10.10.1 | 17013 |
| SA Multicast | Output (Send) | 239.2.3.1 | 6969 |
| SA Multicast | Input (Receive) | 239.2.3.1 | 6970 |
| Additional Channel | Output (Send) | 239.5.5.55 | 7171 |
| Additional Channel | Input (Receive) | 239.5.5.55 | 7172 |

### New ATAK Configuration
All ATAK devices will be configured with:
- CoT Output: 224.10.10.1:17012:udp
- CoT Input: 224.10.10.1:17013:udp
- SA Multicast Output: 239.2.3.1:6969:udp
- SA Multicast Input: 239.2.3.1:6970:udp
- Additional Channel Output: 239.5.5.55:7171:udp
- Additional Channel Input: 239.5.5.55:7172:udp

## Implementation Steps

1. **Update ATAK Configuration**:
   - Configure all ATAK devices to use the new port configuration
   - Ensure that output ports are different from input ports

2. **Modify ATAKHandler**:
   - Update the code to listen on all ports (both output and input)
   - Add logic to only forward packets received on output ports (locally generated)
   - Skip forwarding packets received on input ports (from other nodes)

3. **Code Changes Required**:
   ```python
   # Update multicast addresses and ports
   MULTICAST_ADDRS = ["224.10.10.1", "224.10.10.1", "239.2.3.1", "239.2.3.1", "239.5.5.55", "239.5.5.55"]
   MULTICAST_PORTS = [17012, 17013, 6969, 6970, 7171, 7172]
   
   # Define which ports are for output (locally generated packets)
   OUTPUT_PORTS = [17012, 6969, 7171]
   
   # In process_packet method
   def process_packet(self, data, src, addr, port):
       # Only forward packets from output ports (locally generated)
       if port in OUTPUT_PORTS:
           # Compress and write to pending directory
           print(f"FORWARDING: Local packet from output port {port}")
       else:
           # Skip forwarding
           print(f"SKIPPING: Remote packet from input port {port}")
   ```

## Benefits

1. **Reduced Traffic**: Each position update will be forwarded only once to takNode2
2. **Automatic Operation**: No manual configuration needed for each node
3. **Resilient to Changes**: Works regardless of IP address changes
4. **No Packet Parsing**: Doesn't require parsing ATAK packet content
5. **Improved Performance**: Significantly reduces lag on takNode2's LoRa connection

## Testing Plan

1. Configure one ATAK device with the new port settings
2. Modify ATAKHandler to implement the port-based forwarding logic
3. Monitor logs to verify that only locally generated packets are being forwarded
4. Deploy to all nodes once verified
