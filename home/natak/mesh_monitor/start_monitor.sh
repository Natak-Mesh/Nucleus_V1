#!/bin/bash

# Mesh Monitor Startup Script
# Starts the Flask web interface independently of mesh networking

# Enable error reporting
set -e

echo "Starting mesh monitor web interface..."

# Set environment variables
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/home/natak
export USER=natak
export PYTHONPATH=/home/natak/meshtastic

# COPYING WORKING TIMING FROM MESH-STARTUP SEQUENCE:
# mesh-startup waits 5s + 5s + macsec + 5s + batmesh setup before systemd-networkd restart
# Adding equivalent waits to match working pattern

echo "Waiting for system initialization (copying mesh-startup timing)..."
sleep 5

echo "Additional wait before network restart..."
sleep 5

# Restart systemd-networkd to ensure hostapd can hand out DHCP addresses
echo "Restarting systemd-networkd for hostapd DHCP..."
sudo systemctl restart systemd-networkd

# Wait for systemd-networkd to settle
sleep 5

# Change to mesh_monitor directory
cd /home/natak/mesh_monitor

# Start Flask app in foreground
echo "Starting Flask app on port 5000..."
python3 app.py
