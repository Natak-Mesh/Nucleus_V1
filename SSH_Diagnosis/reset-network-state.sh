#!/bin/bash

# Nucleus Network State Reset Script
# Run this to fix SSH connectivity issues without rebooting

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
echo "Nucleus Network State Reset"
echo "=========================================="
echo "Target: $NODE_USER@$NODE_IP"
echo "Network Interface: $NETWORK_IFACE"
echo "Time: $(date)"
echo ""

# 1. Clear ARP cache for the specific IP
echo "=== 1. Clearing ARP cache entry for $NODE_IP ==="
if sudo arp -d "$NODE_IP" 2>/dev/null; then
    echo "✓ ARP entry deleted"
else
    echo "  (No ARP entry to delete or permission denied)"
fi
echo ""

# 2. Remove stale SSH control sockets
echo "=== 2. Removing stale SSH control sockets ==="
CONTROL_SOCKETS=$(find ~/.ssh -name "control-*" 2>/dev/null | grep "$NODE_IP")
if [ -n "$CONTROL_SOCKETS" ]; then
    echo "$CONTROL_SOCKETS" | while read socket; do
        rm -f "$socket"
        echo "✓ Removed: $socket"
    done
else
    echo "  No control sockets found for this IP"
fi
echo ""

# 3. Kill any hanging SSH processes to this IP
echo "=== 3. Checking for hanging SSH processes ==="
SSH_PROCS=$(ps aux | grep "ssh.*$NODE_IP" | grep -v grep | awk '{print $2}')
if [ -n "$SSH_PROCS" ]; then
    echo "  Found SSH processes:"
    ps aux | grep "ssh.*$NODE_IP" | grep -v grep
    echo ""
    echo "  Terminating them..."
    echo "$SSH_PROCS" | while read pid; do
        kill -9 "$pid" 2>/dev/null && echo "✓ Killed PID: $pid"
    done
else
    echo "  No hanging SSH processes found"
fi
echo ""

# 4. Clear known_hosts entries for this IP
echo "=== 4. Clearing known_hosts entries for $NODE_IP ==="
KNOWN_HOSTS_FILES=("$HOME/.ssh/known_hosts" "/root/.ssh/known_hosts")
REMOVED_COUNT=0
for known_hosts_file in "${KNOWN_HOSTS_FILES[@]}"; do
    if [ -f "$known_hosts_file" ]; then
        if grep -q "$NODE_IP" "$known_hosts_file" 2>/dev/null; then
            ssh-keygen -R "$NODE_IP" -f "$known_hosts_file" > /dev/null 2>&1
            echo "✓ Removed entries from: $known_hosts_file"
            REMOVED_COUNT=$((REMOVED_COUNT + 1))
        fi
    fi
done
if [ "$REMOVED_COUNT" -eq 0 ]; then
    echo "  No known_hosts entries found for this IP"
fi
echo ""

# 5. Clear VSCode SSH connection cache files
echo "=== 5. Clearing VSCode SSH connection cache ==="
# VSCode stores connection info in various places
VSCODE_STORAGE="$HOME/.vscode-server"
if [ -d "$VSCODE_STORAGE" ]; then
    # Don't delete the whole directory, just connection-related files
    # Look for any lock or socket files
    find "$VSCODE_STORAGE" -name "*.sock" -o -name "*.lock" 2>/dev/null | while read file; do
        rm -f "$file"
        echo "✓ Removed: $file"
    done
    echo "  VSCode cache cleaned"
else
    echo "  No VSCode cache to clean"
fi
echo ""

# 6. Restart network interface (optional but can help)
if [ -n "$NETWORK_IFACE" ]; then
    echo "=== 6. Refreshing network interface ($NETWORK_IFACE) ==="
    echo "  This will briefly interrupt your connection..."
    echo -n "  Bringing $NETWORK_IFACE down... "
    if sudo ip link set "$NETWORK_IFACE" down 2>/dev/null; then
        echo "OK"
        sleep 1
        echo -n "  Bringing $NETWORK_IFACE up... "
        if sudo ip link set "$NETWORK_IFACE" up 2>/dev/null; then
            echo "OK"
            sleep 2
            echo "  ✓ Interface restarted"
        else
            echo "FAILED"
            echo "  ⚠ Could not bring interface up"
        fi
    else
        echo "SKIPPED (not needed or no permission)"
    fi
    echo ""
fi

# 7. Force a new ARP request
echo "=== 7. Triggering new ARP resolution ==="
echo -n "  Pinging $NODE_IP to refresh ARP... "
if ping -c 1 -W 2 "$NODE_IP" > /dev/null 2>&1; then
    echo "✓ Success"
    NEW_ARP=$(arp -n | grep "$NODE_IP")
    if [ -n "$NEW_ARP" ]; then
        echo "  New ARP entry:"
        echo "  $NEW_ARP"
    fi
else
    echo "✗ No response"
    echo "  Node may still be booting or powered off"
fi
echo ""

# 8. Test SSH connectivity
echo "=== 8. Testing SSH connectivity ==="
echo -n "  Checking if SSH port 22 is open... "
if command -v nc > /dev/null 2>&1; then
    if nc -z -w 5 "$NODE_IP" 22 2>/dev/null; then
        echo "✓ Port is open"
        echo ""
        echo "  Attempting SSH connection..."
        if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE_USER@$NODE_IP" exit 2>/dev/null; then
            echo "  ✓ SSH connection successful!"
        else
            echo "  ✗ SSH connection failed (but port is open)"
            echo "  You may need to wait longer or check SSH service on node"
        fi
    else
        echo "✗ Port is closed"
        echo "  SSH service may not be running yet"
    fi
else
    echo "SKIPPED (nc not installed)"
fi
echo ""

echo "=========================================="
echo "Network state reset complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Wait 10-15 seconds for network to stabilize"
echo "  2. Try connecting: ssh $NODE_USER@$NODE_IP"
echo "  3. If it still fails, run: ./diagnose-ssh-issue.sh $NODE_IP $NODE_USER"
echo ""
echo "If this still doesn't work, the issue may be on the node itself:"
echo "  - SSH service may not have started"
echo "  - Node may need more time to boot (try waiting 60 seconds)"
echo "  - Check node's console if accessible"
echo ""
