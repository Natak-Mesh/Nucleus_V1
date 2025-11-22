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

# Copy opt files
sudo mkdir -p /opt/nucleus/bin
sudo cp "$SOURCE_DIR/opt/nucleus/bin/mesh-start.sh" /opt/nucleus/bin/
sudo chmod +x /opt/nucleus/bin/mesh-start.sh

# Copy web directory if exists
if [ -d "$SOURCE_DIR/opt/nucleus/web" ]; then
    sudo cp -r "$SOURCE_DIR/opt/nucleus/web" /opt/nucleus/
fi

echo "Deployment complete."
