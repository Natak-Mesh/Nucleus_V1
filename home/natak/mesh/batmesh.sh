#!/bin/bash

# Add debug output
#set -x

# Load configuration
#set -a; source /home/natak/mesh/mesh_config.env; set +a

# Set interfaces to not be managed by NetworkManager
nmcli device set eth0 managed no
nmcli device set wlan1 managed no
nmcli device set br0 managed no

# Stop systemd-timesyncd to prevent network interference during SAE
echo "batmesh: Stopping systemd-timesyncd" >> /var/log/batmesh.log
systemctl stop systemd-timesyncd

# Set consistent time for SAE authentication
echo "batmesh: Setting consistent time" >> /var/log/batmesh.log
date -s "2025-07-16 12:00:00"

wpa_supplicant -B -i wlan1 -c /etc/wpa_supplicant/wpa_supplicant-wlan1.conf

# Load batman-adv and set routing algorithm
modprobe batman-adv
batctl ra BATMAN_V
sudo ip link add bat0 type batadv
sudo ip link set dev wlan1 master bat0
sudo ip link set dev bat0 up
sudo ip link set dev br0 up
sudo ip link set dev bat0 master br0

# Configure mesh interface
#ifconfig wlan1 down
#iw reg set "US"
#iw dev wlan1 set type managed
#iw dev wlan1 set 4addr on
#iw dev wlan1 set type mesh
#iw dev wlan1 set meshid $MESH_NAME
#iw dev wlan1 set channel $MESH_CHANNEL

# Bring up the mesh interface
#ifconfig wlan1 up

# Disable HWMP routing while keeping mesh formation
#iw dev wlan1 set mesh_param mesh_fwding 0

# Bridge setup
#ip link set dev br0 up
#ip link add bat0 type batadv
#ip link set dev bat0 mtu 1500
#ip link set dev eth0 mtu 1500

# Configure batman-adv
nmcli device set bat0 managed no
#ip link set dev wlan1 master bat0
#ip link set dev macsec0 master bat0
#ip link set dev wlan1 master bat0
#ip link set dev bat0 up

#ip link set dev bat0 master br0
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
