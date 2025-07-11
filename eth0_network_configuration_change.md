# Natak Mesh Network Configuration Change: eth0 Routing Implementation

## Problem Statement

When multiple Natak mesh nodes are connected via ethernet to the same switch, the SAE (Simultaneous Authentication of Equals) mesh authentication fails. The mesh connection establishes (visible in `iw wlan1 station dump`) but plinks show as "blocked" - encryption doesn't establish on the mesh connection.

## Root Cause

The current configuration bridges eth0 and wlan1 (via bat0) through br0, creating Layer 2 loops when multiple nodes are ethernet-connected. This confuses the SAE mesh authentication protocol because it sees multiple Layer 2 paths to the same mesh peers.

## Current Network Configuration

### Current eth0.network
```ini
[Match]
Name=eth0  

[Network]
Bridge=br0
```

### Current br0.network
```ini
[Match]
Name=br0

[Network]
Address=192.168.200.1/24
IPMasquerade=ipv4
DHCPServer=yes

[DHCPServer]
PoolOffset=15
PoolSize=5
EmitDNS=no
DNS=192.168.200.1
```

### Current Network Topology (Problematic)
```
Your Home Network (192.168.1.x)
    ↓ (ethernet switch)
[eth0] ←→ [br0: 192.168.200.1] ←→ [bat0] ←→ [wlan1 mesh]
```

## Proposed Solution: Routed Configuration

### New eth0.network Configuration
```ini
[Match]
Name=eth0

[Network]
DHCP=yes
Address=192.168.100.50/24
Gateway=192.168.100.1
DNS=8.8.8.8
IPForward=yes

[Route]
Destination=192.168.200.0/24
Gateway=192.168.200.1

[DHCP]
RequestTimeout=10s
AttemptTimeout=20s
MaxAttempts=2
ClientIdentifier=mac
```

### New Network Topology (Solution)
```
Your Home Network (192.168.1.x)
    ↓ 
[eth0: 192.168.1.x] ←→ ROUTING ←→ [br0: 192.168.200.1] ←→ [bat0] ←→ [wlan1 mesh]
```

## Configuration Details

### DHCP with Static Fallback
- **Primary**: DHCP attempts to get IP from connected network
- **Fallback**: Static IP (192.168.100.50/24) if DHCP fails
- **Timeout**: Maximum 40 seconds before fallback (10s × 2 attempts)

### Routing Configuration
- **IPForward=yes**: Enables packet forwarding between interfaces
- **Route to mesh**: 192.168.200.0/24 via br0 (192.168.200.1)
- **Default route**: Via eth0's gateway (from DHCP or static)

### Internet Access
- **br0.network** already has `IPMasquerade=ipv4`
- Mesh network (192.168.200.x) gets NAT'd through eth0
- Any node with eth0 internet connection shares with entire mesh

## Benefits

### 1. Fixes SAE Authentication Issue
- Eliminates Layer 2 bridging conflicts
- Mesh authentication only sees direct wireless paths
- Multiple ethernet-connected nodes no longer interfere

### 2. Maintains Connectivity
- Home network can reach mesh nodes via routing
- Mesh nodes can reach home network and internet
- Inter-mesh communication unchanged (batman-adv)

### 3. Field Deployment Flexibility
- **DHCP networks**: Automatic configuration
- **Static networks**: Fallback IP configuration
- **No DHCP**: Uses static fallback after timeout
- **Internet sharing**: Any connected node shares internet with mesh

## Implementation Steps

### 1. Backup Current Configuration
```bash
sudo cp /etc/systemd/network/eth0.network /etc/systemd/network/eth0.network.backup
```

### 2. Update eth0.network
Replace the contents of `/etc/systemd/network/eth0.network` with the new configuration above.

### 3. Update batmesh.sh (Already Done)
The IP forwarding command has been added to batmesh.sh:
```bash
sudo sysctl -w net.ipv4.ip_forward=1
```
This enables routing between eth0 and br0 interfaces automatically when the mesh starts.

### 4. Restart Networking
```bash
sudo systemctl restart systemd-networkd
```

### 5. Verify Configuration
```bash
# Check eth0 IP
ip addr show eth0

# Check routing table
ip route

# Test mesh connectivity
ping 192.168.200.1

# Test internet (if available)
ping 8.8.8.8
```

## Traffic Flow Examples

### Home Network to Mesh Node
```
PC (192.168.1.100) → Node's eth0 (192.168.1.50) → routing → br0 (192.168.200.1) → mesh node (192.168.200.15)
```

### Mesh Node to Internet
```
Mesh node (192.168.200.15) → br0 (192.168.200.1) → NAT/masquerade → eth0 (192.168.1.50) → home router → internet
```

### Field Deployment Internet Sharing
```
Mesh node A (192.168.200.15) → br0 → NAT → eth0 (DHCP from field network) → field gateway → internet
```

## Fallback Scenarios

### No DHCP Server
- eth0 uses static IP: 192.168.100.50/24
- Gateway: 192.168.100.1
- Limited connectivity to 192.168.100.x range
- Mesh network still fully functional

### No Ethernet Connection
- eth0 remains unconfigured
- Mesh network operates independently
- Node accessible via mesh at 192.168.200.x

### Multiple Network Profiles (Advanced)
For different deployment scenarios, create multiple eth0.network files:
- `eth0.network.home` (current configuration)
- `eth0.network.field` (different static ranges)
- `eth0.network.dhcp-only` (DHCP without fallback)

## Troubleshooting

### Check DHCP Status
```bash
networkctl status eth0
```

### Check Routing
```bash
ip route show
```

### Test Mesh Authentication
```bash
iw wlan1 station dump
# Look for "plink: ESTAB" instead of "plink: BLOCKED"
```

### Verify Internet Sharing
```bash
# From mesh node
curl -I http://google.com
```

## Rollback Procedure

If issues occur, restore original bridged configuration:
```bash
sudo cp /etc/systemd/network/eth0.network.backup /etc/systemd/network/eth0.network
sudo systemctl restart systemd-networkd
```

## Notes

- This change maintains all existing mesh functionality
- br0.network and batman-adv configuration remain unchanged
- The solution is compatible with existing batmesh.sh script
- No changes needed to wpa_supplicant mesh configuration
