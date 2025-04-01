# ATAK Port Configuration Change

## Current Configuration

The ATAKHandler now implements a one-way flow system to prevent packet loops by separating output and input channels.

### Multicast Ports
The ATAKHandler listens on the following multicast addresses and ports:

| Purpose | Multicast Address | Port |
|---------|------------------|------|
| Chat Messages | 224.10.10.1 | 17012 |
| SA Multicast | 239.2.3.1 | 6970 |

## Problem Statement

The previous configuration caused potential looping behavior because:

1. Both ATAK devices and nodes were using the same ports for input and output
2. This made it impossible to distinguish between locally generated packets and packets received from other nodes
3. Could potentially create feedback loops in the network
4. Inefficient use of network resources

## Implemented Solution

We've created a new multicast channel configuration that separates local outgoing packets from incoming packets. Reticulum now reads from dedicated output ports and only writes to specific incoming ports in ATAK, preventing any potential looping behavior.

### Port Configuration

| Purpose | Direction | Multicast Address | Port |
|---------|-----------|------------------|------|
| Chat Messages | Listen (Output) | 224.10.10.1 | 17012 |
| Chat Messages | Forward to (Input) | 224.10.10.1 | 17013 |
| SA Multicast | Listen (Output) | 239.2.3.1 | 6970 |
| SA Multicast | Forward to (Input) | 239.2.3.1 | 6971 |

### ATAK EUD Configuration
ATAK devices must be configured with:

In "Manage Outputs" section:
- Chat Output: 224.10.10.1:17012:udp
- SA Multicast Output: 239.2.3.1:6970:udp

In "Manage Inputs" section:
- Chat Input: 224.10.10.1:17013:udp
- SA Multicast Input: 239.2.3.1:6971:udp

## Implementation Details

1. **ATAKHandler Changes**:
   - Listens only on output ports (17012, 6970)
   - Forwards decompressed packets to input ports (17013, 6971)
   - Removed unused 239.5.5.55 addresses

2. **Packet Flow**:
   - Local ATAK packets are sent to output ports
   - ATAKHandler receives these packets
   - After processing/compression, packets are forwarded to input ports
   - ATAK receives processed packets on input ports

## Benefits

1. **Clean Separation**: Clear distinction between outgoing and incoming packets
2. **Loop Prevention**: One-way flow prevents packet feedback loops
3. **Efficient Processing**: Each packet follows a clear path through the system
4. **Simple Configuration**: Clear separation of input/output ports in ATAK configuration
5. **Reduced Network Load**: Eliminates duplicate packet transmission

## Testing

1. Verify ATAK devices are configured with correct input/output ports
2. Confirm packets flow from output ports to input ports
3. Monitor for any looping behavior
4. Check packet reception on all configured nodes

## WiFi Packet Filtering

When nodes are operating over WiFi, we can prevent packet loops by filtering out non-local packets using the br0 neighbor table. This works because WiFi packets maintain their original source IP addresses.

### Implementation

In atak_handler.run(), before processing any packet:
```python
data, src = sock.recvfrom(65535)
# Get list of directly connected devices
local_ips = []
output = subprocess.check_output("ip neigh show dev br0", shell=True).decode().strip()
for line in output.split('\n'):
    if 'lladdr' in line:  # Only include entries with MAC addresses
        ip = line.split()[0]
        local_ips.append(ip)

# Only process packets from local devices
if src[0] in local_ips:
    self.process_packet(data)
```

This ensures that only packets from directly connected devices (visible in br0's neighbor table) are processed and forwarded through the LoRa network.

Note: This filtering only works for WiFi packets. LoRa-forwarded packets will need a different solution as they appear to come from the local node's IP address.
