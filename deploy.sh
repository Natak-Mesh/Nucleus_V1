#!/bin/bash

# Deploy Nucleus OS files to system locations

set -e

SOURCE_DIR="$(pwd)"

echo "Deploying from $SOURCE_DIR..."

# Copy etc files
sudo cp -r "$SOURCE_DIR/etc/hostapd" /etc/
sudo cp -r "$SOURCE_DIR/etc/wpa_supplicant" /etc/
sudo mkdir -p /etc/nucleus
sudo cp "$SOURCE_DIR/etc/nucleus/mesh.conf" /etc/nucleus/
sudo cp -r "$SOURCE_DIR/etc/systemd/network" /etc/systemd/

# Copy networkd-dispatcher scripts
sudo mkdir -p /etc/networkd-dispatcher/off.d
sudo mkdir -p /etc/networkd-dispatcher/routable.d
sudo cp "$SOURCE_DIR/etc/networkd-dispatcher/off.d/50-eth0-lan-fallback" /etc/networkd-dispatcher/off.d/
sudo cp "$SOURCE_DIR/etc/networkd-dispatcher/routable.d/50-eth0-wan-switch" /etc/networkd-dispatcher/routable.d/
sudo chmod +x /etc/networkd-dispatcher/off.d/50-eth0-lan-fallback
sudo chmod +x /etc/networkd-dispatcher/routable.d/50-eth0-wan-switch

# Copy opt files
sudo mkdir -p /opt/nucleus/bin
sudo cp "$SOURCE_DIR/opt/nucleus/bin/mesh-start.sh" /opt/nucleus/bin/
sudo chmod +x /opt/nucleus/bin/mesh-start.sh

# Copy web directory if exists
if [ -d "$SOURCE_DIR/opt/nucleus/web" ]; then
    sudo cp -r "$SOURCE_DIR/opt/nucleus/web" /opt/nucleus/
fi

echo "Deployment complete."
