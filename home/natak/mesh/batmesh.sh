#!/bin/bash

# Add debug output
#set -x

# Clean up any existing batman interface
sudo ip link del bat0 2>/dev/null || true


# Set interfaces to not be managed by NetworkManager
nmcli device set eth0 managed no
nmcli device set wlan1 managed no
nmcli device set br0 managed no

#sudo ip link set dev wlan1 mtu 1532

#wpa_supplicant sets up mesh and disables HWMP routing
sudo wpa_supplicant -B -i wlan1 -c /etc/wpa_supplicant/wpa_supplicant-wlan1.conf

sleep 5
#iw wlan1 mesh_param mesh_auto_open_plinks 1


# Load batman-adv and set routing algorithm
sudo modprobe batman-adv
sudo batctl ra BATMAN_V
sudo ip link add bat0 type batadv
sudo ip link set dev wlan1 master bat0
sudo ip link set dev bat0 up
sudo ip link set dev br0 up
sudo ip link set dev bat0 master br0

# Configure batman-adv
nmcli device set bat0 managed no

# Batman-adv optimizations for MANET deployment
# Set OGM interval to 1000ms for better adaptation to mobility
batctl it 1000

# Set hop penalty to favor stronger direct links in poor RF conditions
batctl hp 40

# Enable network coding to improve throughput in challenging environments
batctl nc 1

# Enable distributed ARP table to reduce broadcast traffic
batctl dat 1

# Restart networking
systemctl restart systemd-networkd
