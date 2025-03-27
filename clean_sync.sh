#!/bin/bash
# Base directory for clean GitHub repo
CLEAN_REPO_DIR="/home/natak/git_mesh"

# Create necessary directories first
echo "Creating directories..."
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/identity_handler"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/mesh_controller"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/rns_stats"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/pending"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/processing"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/incoming"
mkdir -p "$CLEAN_REPO_DIR/etc/systemd/system"
mkdir -p "$CLEAN_REPO_DIR/etc/systemd/network"
mkdir -p "$CLEAN_REPO_DIR/home/natak/mesh"
mkdir -p "$CLEAN_REPO_DIR/home/natak/mesh_monitor/templates"

echo "Copying files..."

# Copy only the files you want to keep
# Mesh files
cp -v /home/natak/mesh/batmesh.sh "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/macsec.sh "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/mesh_config.env "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/hostname_mapping.json "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/README.md "$CLEAN_REPO_DIR/home/natak/mesh/"

# Copy systemd service files
cp -v /etc/systemd/system/mesh-startup.service "$CLEAN_REPO_DIR/etc/systemd/system/"
cp -v /etc/systemd/system/reticulum-mesh-identity.service "$CLEAN_REPO_DIR/etc/systemd/system/"
cp -v /etc/systemd/system/reticulum-mesh-network.service "$CLEAN_REPO_DIR/etc/systemd/system/"
cp -v /etc/systemd/system/reticulum-mesh-ogm.service "$CLEAN_REPO_DIR/etc/systemd/system/"
cp -v /etc/systemd/system/reticulum-mesh-controller.service "$CLEAN_REPO_DIR/etc/systemd/system/"
cp -v /etc/systemd/system/reticulum-mesh-reticulum.service "$CLEAN_REPO_DIR/etc/systemd/system/"
cp -v /etc/systemd/system/reticulum-mesh-atak.service "$CLEAN_REPO_DIR/etc/systemd/system/"
cp -v /etc/systemd/system/reticulum-mesh-rns-monitor.service "$CLEAN_REPO_DIR/etc/systemd/system/"
cp -v /etc/systemd/system/mesh-monitor.service "$CLEAN_REPO_DIR/etc/systemd/system/"
cp -v /home/natak/reticulum_mesh/tak_transmission/systemd_services.md "$CLEAN_REPO_DIR/etc/systemd/system/"

# Copy systemd network configuration
cp -v /etc/systemd/network/br0.netdev "$CLEAN_REPO_DIR/etc/systemd/network/"
cp -v /etc/systemd/network/br0.network "$CLEAN_REPO_DIR/etc/systemd/network/"
cp -v /etc/systemd/network/eth0.network "$CLEAN_REPO_DIR/etc/systemd/network/"
cp -v /etc/systemd/network/wlan0.network "$CLEAN_REPO_DIR/etc/systemd/network/"

# Copy mesh monitor application
cp -v /home/natak/mesh_monitor/app.py "$CLEAN_REPO_DIR/home/natak/mesh_monitor/"
cp -v /home/natak/mesh_monitor/templates/index.html "$CLEAN_REPO_DIR/home/natak/mesh_monitor/templates/"
cp -v /home/natak/mesh_monitor/README.md "$CLEAN_REPO_DIR/home/natak/mesh_monitor/"

# Copy reticulum mesh components
echo "Copying reticulum mesh components..."

# Identity Handler
cp -v /home/natak/reticulum_mesh/identity_handler/identity_mapper.py "$CLEAN_REPO_DIR/reticulum_mesh/identity_handler/"
cp -v /home/natak/reticulum_mesh/identity_handler/README.md "$CLEAN_REPO_DIR/reticulum_mesh/identity_handler/"

# Mesh Controller
cp -v /home/natak/reticulum_mesh/mesh_controller/mesh_controller.py "$CLEAN_REPO_DIR/reticulum_mesh/mesh_controller/"
cp -v /home/natak/reticulum_mesh/mesh_controller/README.md "$CLEAN_REPO_DIR/reticulum_mesh/mesh_controller/"

# OGM Monitor
cp -v /home/natak/reticulum_mesh/ogm_monitor/ogm_monitor.py "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor/"
cp -v /home/natak/reticulum_mesh/ogm_monitor/README.md "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor/"

# RNS Stats
cp -v /home/natak/reticulum_mesh/rns_stats/rns_monitor.py "$CLEAN_REPO_DIR/reticulum_mesh/rns_stats/"
cp -v /home/natak/reticulum_mesh/rns_stats/README.md "$CLEAN_REPO_DIR/reticulum_mesh/rns_stats/"

# TAK Transmission
echo "Copying TAK transmission components..."

# Main files
cp -v /home/natak/reticulum_mesh/tak_transmission/systemd_services.md "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/"

# ATAK Module
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/atak_handler.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/README.md "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/compression.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/cot_zstd_compressor.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/cot_zstd_decompressor.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/"

# Reticulum Module
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/reticulum_handler.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/README.md "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/"

# Create .gitkeep files for empty directories
touch "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/pending/.gitkeep"
touch "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/processing/.gitkeep"
touch "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/incoming/.gitkeep"

echo "Clean sync complete!"
