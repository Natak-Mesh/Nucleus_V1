#!/bin/bash

# Nucleus Node SSH Configuration Optimizer
# Run this ON THE NODE to fix SSH connection and performance issues
# 
# This script applies the critical fix (UseDNS no) and includes optional
# optimizations that can be uncommented if needed.

set -e

SSHD_CONFIG="/etc/ssh/sshd_config"
BACKUP_DIR="/etc/ssh/backups"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run as root or with sudo"
    echo "Usage: sudo $0"
    exit 1
fi

echo "=========================================="
echo "Nucleus Node SSH Configuration Optimizer"
echo "=========================================="
echo "Time: $(date)"
echo ""

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    echo "✓ Created backup directory: $BACKUP_DIR"
fi

# Backup current sshd_config
BACKUP_FILE="$BACKUP_DIR/sshd_config.backup.$(date +%Y%m%d_%H%M%S)"
cp "$SSHD_CONFIG" "$BACKUP_FILE"
echo "✓ Backed up current config to: $BACKUP_FILE"
echo ""

echo "=== Applying SSH Configuration Changes ==="
echo ""

# Function to add or update a configuration option
update_ssh_config() {
    local option="$1"
    local value="$2"
    local commented="${3:-no}"
    
    if [ "$commented" = "yes" ]; then
        # Add as commented line if not already present
        if ! grep -q "^#*${option}" "$SSHD_CONFIG"; then
            echo "# ${option} ${value}" >> "$SSHD_CONFIG"
            echo "  Added (commented): ${option} ${value}"
        else
            echo "  Already present: ${option}"
        fi
    else
        # Remove existing lines (commented or not)
        sed -i "/^#*${option}/d" "$SSHD_CONFIG"
        # Add the new configuration
        echo "${option} ${value}" >> "$SSHD_CONFIG"
        echo "✓ Applied: ${option} ${value}"
    fi
}

echo "--- ACTIVE FIXES (Applied) ---"
echo ""

# CRITICAL FIX: Disable UseDNS (prevents connection delays and lag)
update_ssh_config "UseDNS" "no" "no"
echo "  → Prevents DNS reverse lookup delays on connections and keystrokes"
echo ""

echo "--- OPTIONAL OPTIMIZATIONS (Commented) ---"
echo "Uncomment these in $SSHD_CONFIG if needed:"
echo ""

# Disable GSSAPI authentication (can cause delays)
# Uncomment if you experience slow authentication
# update_ssh_config "GSSAPIAuthentication" "no" "yes"
echo "# GSSAPIAuthentication no"
echo "#   → Prevents Kerberos/GSSAPI authentication delays"
echo "#   → Uncomment if auth takes a long time even with UseDNS=no"
echo ""

# Increase max startup connections (prevents connection exhaustion)
# Uncomment if you get "ssh_exchange_identification" errors
# update_ssh_config "MaxStartups" "10:30:60" "yes"
echo "# MaxStartups 10:30:60"
echo "#   → Allows more simultaneous connection attempts"
echo "#   → Uncomment if you see 'connection refused' on rapid reconnects"
echo ""

# Increase max sessions per connection
# Uncomment if you need multiple shells/tunnels per connection
# update_ssh_config "MaxSessions" "10" "yes"
echo "# MaxSessions 10"
echo "#   → Allows more concurrent sessions per connection"
echo "#   → Uncomment if you use SSH multiplexing or multiple terminals"
echo ""

# Keep connections alive (prevents timeouts)
# Uncomment if your SSH sessions disconnect due to inactivity
# update_ssh_config "ClientAliveInterval" "60" "yes"
# update_ssh_config "ClientAliveCountMax" "3" "yes"
echo "# ClientAliveInterval 60"
echo "# ClientAliveCountMax 3"
echo "#   → Sends keepalive packets every 60 seconds"
echo "#   → Disconnects after 3 missed responses (3 minutes idle)"
echo "#   → Uncomment to prevent idle session timeouts"
echo ""

# Set login grace time (how long to wait for authentication)
# Uncomment if you want to reduce the auth timeout
# update_ssh_config "LoginGraceTime" "30" "yes"
echo "# LoginGraceTime 30"
echo "#   → Reduces time allowed for login from 120s to 30s"
echo "#   → Uncomment to free up connection slots faster"
echo ""

echo "=== Validating SSH Configuration ==="
if sshd -t 2>&1; then
    echo "✓ SSH configuration is valid"
else
    echo "✗ ERROR: SSH configuration is invalid!"
    echo "  Restoring backup..."
    cp "$BACKUP_FILE" "$SSHD_CONFIG"
    echo "  Backup restored. Please check the configuration manually."
    exit 1
fi
echo ""

echo "=== Restarting SSH Service ==="
if systemctl restart sshd 2>/dev/null || systemctl restart ssh 2>/dev/null; then
    echo "✓ SSH service restarted successfully"
else
    echo "✗ Failed to restart SSH service"
    echo "  The configuration is valid but service restart failed"
    echo "  Try manually: sudo systemctl restart sshd"
    exit 1
fi
echo ""

echo "=========================================="
echo "SSH Configuration Update Complete!"
echo "=========================================="
echo ""
echo "Applied fixes:"
echo "  ✓ UseDNS disabled (fixes connection delays and input lag)"
echo ""
echo "Optional optimizations available in $SSHD_CONFIG:"
echo "  → GSSAPIAuthentication no"
echo "  → MaxStartups 10:30:60"
echo "  → MaxSessions 10"
echo "  → ClientAliveInterval 60"
echo "  → ClientAliveCountMax 3"
echo "  → LoginGraceTime 30"
echo ""
echo "To enable optional optimizations:"
echo "  1. Edit: sudo nano $SSHD_CONFIG"
echo "  2. Uncomment desired lines"
echo "  3. Test: sudo sshd -t"
echo "  4. Restart: sudo systemctl restart sshd"
echo ""
echo "Backup location: $BACKUP_FILE"
echo ""
echo "You can now disconnect and reconnect - SSH should be fast!"
echo ""
