#!/bin/bash

# Set interfaces to not be managed by NetworkManager
nmcli device set eth0 managed no
nmcli device set wlan1 managed no
nmcli device set br0 managed no

#wpa_supplicant sets up mesh and disables HWMP routing
wpa_supplicant -B -i wlan1 -c /etc/wpa_supplicant/wpa_supplicant-wlan1.conf

# Load batman-adv and set routing algorithm
modprobe batman-adv
batctl ra BATMAN_V
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
