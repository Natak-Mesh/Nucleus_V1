#!/bin/bash
# Script to start virtual AP on wlan0 and add it to br0
# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi
# Create virtual interface for AP if it doesn't exist
if ! ip link show wlan0_ap > /dev/null 2>&1; then
    iw phy phy0 interface add wlan0_ap type __ap
    echo "Created wlan0_ap interface"
else
    echo "wlan0_ap interface already exists"
fi
# Set NetworkManager to not manage wlan0_ap
nmcli device set wlan0_ap managed no
# Bring up the virtual interface
ip link set wlan0_ap up
#ip link set wlan0_ap mtu 1468
ip link set wlan0_ap mtu 1500
sleep 5
# Add wlan0_ap to br0
ip link set dev wlan0_ap master br0
# Start hostapd service
systemctl start hostapd.service
# Restart systemd-networkd to apply network changes
systemctl restart systemd-networkd
echo "Virtual AP should now be running on wlan0_ap and added to br0"
