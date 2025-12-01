#!/bin/bash

# Nucleus SSH Connectivity Diagnostic Script
# Run this when you cannot connect to the node via SSH

set +e  # Don't exit on errors

NODE_IP="${1}"
NODE_USER="${2:-natak}"  # Default user is 'natak'

if [ -z "$NODE_IP" ]; then
    echo "Usage: $0 <node_ip> [username]"
    echo "Example: $0 192.168.1.100 natak"
    exit 1
fi

# Auto-detect network interface for this connection
detect_interface() {
    # Get the interface used to reach the target IP
    IFACE=$(ip route get "$NODE_IP" 2>/dev/null | grep -oP 'dev \K\S+' | head -n1)
    if [ -z "$IFACE" ]; then
        # Fallback: find first active non-loopback interface
        IFACE=$(ip link show | grep -E '^[0-9]+: (eth|enp|ens|wlan|wlp)' | head -n1 | cut -d: -f2 | tr -d ' ')
    fi
    echo "$IFACE"
}

NETWORK_IFACE=$(detect_interface)

echo "=========================================="
echo "Nucleus SSH Connectivity Diagnostics"
echo "=========================================="
echo "Target: $NODE_USER@$NODE_IP"
echo "Network Interface: $NETWORK_IFACE"
echo "Time: $(date)"
echo ""

# 1. Check ping connectivity
echo "=== 1. Testing Network Connectivity (ping) ==="
if ping -c 3 -W 2 "$NODE_IP" > /dev/null 2>&1; then
    echo "✓ Node responds to ping"
    PING_OK=1
else
    echo "✗ Node does NOT respond to ping"
    echo "  This means the node is powered off, network is down, or IP is wrong"
    PING_OK=0
fi
echo ""

# 2. Check ARP table
echo "=== 2. Checking ARP Table ==="
ARP_ENTRY=$(arp -n | grep "$NODE_IP")
if [ -n "$ARP_ENTRY" ]; then
    echo "✓ ARP entry found:"
    echo "  $ARP_ENTRY"
    MAC_ADDR=$(echo "$ARP_ENTRY" | awk '{print $3}')
    
    # Check if it's incomplete
    if echo "$ARP_ENTRY" | grep -q "incomplete"; then
        echo "  ⚠ WARNING: ARP entry is incomplete (stale/invalid)"
        ARP_STALE=1
    else
        ARP_STALE=0
    fi
else
    echo "✗ No ARP entry found for $NODE_IP"
    echo "  This could mean the node hasn't communicated recently"
    ARP_STALE=1
fi
echo ""

# 3. Check if SSH port is open
echo "=== 3. Checking SSH Port (22) ==="
if command -v nc > /dev/null 2>&1; then
    if nc -z -w 2 "$NODE_IP" 22 2>/dev/null; then
        echo "✓ SSH port 22 is OPEN"
        SSH_PORT_OK=1
    else
        echo "✗ SSH port 22 is CLOSED or not responding"
        echo "  SSH service may not be running on the node"
        SSH_PORT_OK=0
    fi
else
    echo "⚠ 'nc' command not found, skipping port check"
    echo "  Install with: sudo apt install netcat-openbsd"
    SSH_PORT_OK=-1
fi
echo ""

# 4. Check network interface status
if [ -n "$NETWORK_IFACE" ]; then
    echo "=== 4. Checking Network Interface ($NETWORK_IFACE) ==="
    IFACE_INFO=$(ip addr show "$NETWORK_IFACE" 2>/dev/null)
    if [ -n "$IFACE_INFO" ]; then
        if echo "$IFACE_INFO" | grep -q "state UP"; then
            echo "✓ $NETWORK_IFACE is UP"
            # Show IP address
            IFACE_IP=$(echo "$IFACE_INFO" | grep "inet " | awk '{print $2}')
            if [ -n "$IFACE_IP" ]; then
                echo "  IP: $IFACE_IP"
            fi
        else
            echo "✗ $NETWORK_IFACE is DOWN"
            echo "$IFACE_INFO" | grep "state"
        fi
    else
        echo "✗ $NETWORK_IFACE interface not found"
    fi
else
    echo "=== 4. Checking Network Interface ==="
    echo "⚠ Could not detect network interface"
fi
echo ""

# 5. Check known_hosts for conflicting entries
echo "=== 5. Checking SSH known_hosts ==="
KNOWN_HOSTS_FILES=("$HOME/.ssh/known_hosts" "/root/.ssh/known_hosts")
FOUND_ENTRIES=0
for known_hosts_file in "${KNOWN_HOSTS_FILES[@]}"; do
    if [ -f "$known_hosts_file" ]; then
        if grep -q "$NODE_IP" "$known_hosts_file" 2>/dev/null; then
            echo "  ⚠ Found entries in: $known_hosts_file"
            echo "    This could cause 'Host key verification failed' errors"
            FOUND_ENTRIES=$((FOUND_ENTRIES + 1))
        fi
    fi
done
if [ "$FOUND_ENTRIES" -eq 0 ]; then
    echo "  No known_hosts entries found for this IP (this is OK)"
fi
echo ""

# 6. Check VSCode SSH connection cache
echo "=== 6. Checking VSCode SSH Cache ==="
VSCODE_SSH_DIR="$HOME/.vscode-server"
if [ -d "$VSCODE_SSH_DIR" ]; then
    echo "✓ VSCode server directory exists: $VSCODE_SSH_DIR"
    
    # Check for control sockets
    CONTROL_SOCKETS=$(find ~/.ssh -name "control-*" 2>/dev/null | grep "$NODE_IP")
    if [ -n "$CONTROL_SOCKETS" ]; then
        echo "  ⚠ Found SSH control sockets for $NODE_IP:"
        echo "$CONTROL_SOCKETS" | sed 's/^/    /'
        echo "  These might be stale"
    else
        echo "  No control sockets found for this IP"
    fi
else
    echo "  VSCode server directory not found"
fi
echo ""

# 7. Check DHCP lease information
echo "=== 7. Checking DHCP Lease State ==="
if command -v dhcpcd > /dev/null 2>&1; then
    LEASE_FILE="/var/lib/dhcpcd/dhcpcd-eth0.lease"
    if [ -f "$LEASE_FILE" ]; then
        echo "  DHCP lease file found"
    fi
elif command -v dhclient > /dev/null 2>&1; then
    LEASE_FILE="/var/lib/dhcp/dhclient.eth0.leases"
    if [ -f "$LEASE_FILE" ]; then
        echo "  DHCP lease file found"
    fi
fi
echo ""

# 8. Try verbose SSH connection
echo "=== 8. Attempting SSH Connection (verbose) ==="
echo "Running: ssh -v -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $NODE_USER@$NODE_IP exit"
echo ""
ssh -v -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE_USER@$NODE_IP" exit 2>&1 | tail -25
echo ""

# Summary and Recommendations
echo "=========================================="
echo "SUMMARY & RECOMMENDATIONS"
echo "=========================================="

if [ "$PING_OK" -eq 0 ]; then
    echo "⚠ PRIMARY ISSUE: Node is not reachable on network"
    echo "  → Check if node is powered on"
    echo "  → Check ethernet cable connection"
    echo "  → Verify node IP address is correct"
elif [ "$SSH_PORT_OK" -eq 0 ]; then
    echo "⚠ PRIMARY ISSUE: SSH service not responding"
    echo "  → Node is reachable but SSH may not be running"
    echo "  → The node may still be booting (wait 30-60 seconds)"
    echo "  → SSH service may have failed to start"
    echo ""
    echo "  POSSIBLE NODE-SIDE ISSUES:"
    echo "  → Check /etc/ssh/sshd_config - set 'UseDNS no'"
    echo "  → Check if SSH host keys are being regenerated on boot"
    echo "  → Check systemd: sudo systemctl status sshd"
elif [ "$ARP_STALE" -eq 1 ]; then
    echo "⚠ POTENTIAL ISSUE: Stale ARP cache"
    echo "  → Try the reset-network-state.sh script"
    echo "  → This often fixes reconnection issues"
else
    echo "ℹ Network appears OK but SSH still failing"
    echo "  → Try the reset-network-state.sh script"
    echo "  → Check SSH verbose output above for specific errors"
    echo ""
    if grep -q "banner exchange" <(ssh -v -o ConnectTimeout=5 "$NODE_USER@$NODE_IP" exit 2>&1); then
        echo "  BANNER EXCHANGE TIMEOUT DETECTED:"
        echo "  → This usually indicates an issue on the NODE itself"
        echo "  → Most common cause: UseDNS enabled in /etc/ssh/sshd_config"
        echo "  → Fix: On the node, edit /etc/ssh/sshd_config and add/change:"
        echo "      UseDNS no"
        echo "  → Then restart SSH: sudo systemctl restart sshd"
    fi
fi

echo ""
echo "Next steps:"
echo "  1. Run: ./reset-network-state.sh $NODE_IP"
echo "  2. Wait 10 seconds"
echo "  3. Try connecting again: ssh $NODE_USER@$NODE_IP"
echo ""
