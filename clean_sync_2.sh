#!/bin/bash
# Base directory for clean GitHub repo
CLEAN_REPO_DIR="/home/natak/git_mesh"

# Copy reticulum mesh components
echo "Copying reticulum mesh components..."

# Add documentation
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/documentation"
cp -v /home/natak/reticulum_mesh/documentation/Reticulum*.pdf "$CLEAN_REPO_DIR/reticulum_mesh/documentation/"

# Add logs directory
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/logs"
cp -v /home/natak/reticulum_mesh/logs/packet_logs.log "$CLEAN_REPO_DIR/reticulum_mesh/logs/"

# OGM Monitor
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor"
cp -v /home/natak/reticulum_mesh/ogm_monitor/enhanced_ogm_monitor.py "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor/"
cp -v /home/natak/reticulum_mesh/ogm_monitor/node_status.json "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor/"
cp -v /home/natak/reticulum_mesh/ogm_monitor/README.md "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor/"

# Main reticulum_mesh files
cp -v /home/natak/reticulum_mesh/start_reticulum_stack.sh "$CLEAN_REPO_DIR/reticulum_mesh/"
cp -v /home/natak/reticulum_mesh/startup_process.md "$CLEAN_REPO_DIR/reticulum_mesh/"

# TAK Transmission
echo "Copying TAK transmission components..."

# ATAK Module
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/atak_handler.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/__init__.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/README.md "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/compression.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/cot_dict_131072.zstd "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/cot_zstd_compressor.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/cot_zstd_decompressor.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/__init__.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/"

# Reticulum Module
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/__init__.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/"

# New Implementation Reticulum Module
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/__init__.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/config.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/logger.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/packet_manager.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.json "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery_README.md "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/README.md "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/test_setup.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"

# Create .gitkeep files for empty directories in shared folders
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/pending"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/processing"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/incoming"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/sent_buffer"
touch "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/pending/.gitkeep"
touch "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/processing/.gitkeep"
touch "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/incoming/.gitkeep"
touch "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/sent_buffer/.gitkeep"

# Copy systemd service files
mkdir -p "$CLEAN_REPO_DIR/etc/systemd/system"
cp -v /etc/systemd/system/mesh-startup.service "$CLEAN_REPO_DIR/etc/systemd/system/"
cp -v /etc/systemd/system/reticulum-stack.service "$CLEAN_REPO_DIR/etc/systemd/system/"

# Copy systemd network configuration
mkdir -p "$CLEAN_REPO_DIR/etc/systemd/network"
cp -v /etc/systemd/network/br0.netdev "$CLEAN_REPO_DIR/etc/systemd/network/"
cp -v /etc/systemd/network/br0.network "$CLEAN_REPO_DIR/etc/systemd/network/"
cp -v /etc/systemd/network/eth0.network "$CLEAN_REPO_DIR/etc/systemd/network/"
cp -v /etc/systemd/network/wlan0.network "$CLEAN_REPO_DIR/etc/systemd/network/"

# Copy mesh files
mkdir -p "$CLEAN_REPO_DIR/home/natak/mesh"
cp -v /home/natak/mesh/batmesh.sh "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/hostname_mapping.json "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/hotspot-setup.sh "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/macsec.sh "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/mesh_config.env "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/README.md "$CLEAN_REPO_DIR/home/natak/mesh/"

# Copy mesh monitor application
mkdir -p "$CLEAN_REPO_DIR/home/natak/mesh_monitor/templates"
cp -v /home/natak/mesh_monitor/app.py "$CLEAN_REPO_DIR/home/natak/mesh_monitor/"
cp -v /home/natak/mesh_monitor/templates/index.html "$CLEAN_REPO_DIR/home/natak/mesh_monitor/templates/"
cp -v /home/natak/mesh_monitor/README.md "$CLEAN_REPO_DIR/home/natak/mesh_monitor/"
cp -v /home/natak/mesh_monitor/templates/packet_logs.html "$CLEAN_REPO_DIR/home/natak/mesh_monitor/templates/"

# Copy macsec_config_tool files (excluding node subdirectories and mesh_nodes.json)
mkdir -p "$CLEAN_REPO_DIR/home/natak/macsec_config_tool"
cp -v /home/natak/macsec_config_tool/Macsec_config_generator.py "$CLEAN_REPO_DIR/home/natak/macsec_config_tool/"
cp -v /home/natak/macsec_config_tool/example.md "$CLEAN_REPO_DIR/home/natak/macsec_config_tool/"
cp -v /home/natak/macsec_config_tool/README.md "$CLEAN_REPO_DIR/home/natak/macsec_config_tool/"

# Copy Reticulum config
mkdir -p "$CLEAN_REPO_DIR/home/natak/.reticulum"
cp -v /home/natak/.reticulum/config "$CLEAN_REPO_DIR/home/natak/.reticulum/"

# Copy NetworkManager and hostapd configuration files
mkdir -p "$CLEAN_REPO_DIR/etc/NetworkManager/conf.d"
mkdir -p "$CLEAN_REPO_DIR/etc/hostapd"
cp -v /etc/NetworkManager/conf.d/unmanaged.conf "$CLEAN_REPO_DIR/etc/NetworkManager/conf.d/"
cp -v /etc/hostapd/hostapd.conf "$CLEAN_REPO_DIR/etc/hostapd/"
