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
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/pending"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/processing"
mkdir -p "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/incoming"
mkdir -p "$CLEAN_REPO_DIR/etc/systemd/system"
mkdir -p "$CLEAN_REPO_DIR/etc/systemd/network"
mkdir -p "$CLEAN_REPO_DIR/home/natak/mesh"
mkdir -p "$CLEAN_REPO_DIR/home/natak/mesh_monitor/templates"
mkdir -p "$CLEAN_REPO_DIR/home/natak/macsec_config_tool"
mkdir -p "$CLEAN_REPO_DIR/home/natak/.reticulum"
mkdir -p "$CLEAN_REPO_DIR/var/log/reticulum"

echo "Copying files..."

# Copy Reticulum config
cp -v /home/natak/.reticulum/config "$CLEAN_REPO_DIR/home/natak/.reticulum/"

# Copy only the files you want to keep
# Mesh files
cp -v /home/natak/mesh/batmesh.sh "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/macsec.sh "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/mesh_config.env "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/hostname_mapping.json "$CLEAN_REPO_DIR/home/natak/mesh/"
cp -v /home/natak/mesh/README.md "$CLEAN_REPO_DIR/home/natak/mesh/"

# Copy systemd service files
cp -v /etc/systemd/system/mesh-startup.service "$CLEAN_REPO_DIR/etc/systemd/system/"
cp -v /etc/systemd/system/reticulum-stack.service "$CLEAN_REPO_DIR/etc/systemd/system/"
#cp -v /etc/systemd/system/reticulum-mesh-identity.service "$CLEAN_REPO_DIR/etc/systemd/system/"
#cp -v /etc/systemd/system/reticulum-mesh-network.service "$CLEAN_REPO_DIR/etc/systemd/system/"
#cp -v /etc/systemd/system/reticulum-mesh-ogm.service "$CLEAN_REPO_DIR/etc/systemd/system/"
#cp -v /etc/systemd/system/reticulum-mesh-controller.service "$CLEAN_REPO_DIR/etc/systemd/system/"
#cp -v /etc/systemd/system/reticulum-mesh-reticulum.service "$CLEAN_REPO_DIR/etc/systemd/system/"
#cp -v /etc/systemd/system/reticulum-mesh-atak.service "$CLEAN_REPO_DIR/etc/systemd/system/"
#cp -v /etc/systemd/system/reticulum-mesh-rns-monitor.service "$CLEAN_REPO_DIR/etc/systemd/system/"
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
cp -v /home/natak/mesh_monitor/templates/packet_logs.html "$CLEAN_REPO_DIR/home/natak/mesh_monitor/templates/"

# Copy macsec_config_tool files (excluding node subdirectories and mesh_nodes.json)
cp -v /home/natak/macsec_config_tool/Macsec_config_generator.py "$CLEAN_REPO_DIR/home/natak/macsec_config_tool/"
cp -v /home/natak/macsec_config_tool/example.md "$CLEAN_REPO_DIR/home/natak/macsec_config_tool/"
cp -v /home/natak/macsec_config_tool/README.md "$CLEAN_REPO_DIR/home/natak/macsec_config_tool/"

# Copy reticulum mesh components
echo "Copying reticulum mesh components..."

# Identity Handler (Check on this one, may be ok to drop)
cp -v /home/natak/reticulum_mesh/identity_handler/identity_mapper.py "$CLEAN_REPO_DIR/reticulum_mesh/identity_handler/"
cp -v /home/natak/reticulum_mesh/identity_handler/README.md "$CLEAN_REPO_DIR/reticulum_mesh/identity_handler/"

# Mesh Controller
#cp -v /home/natak/reticulum_mesh/mesh_controller/mesh_controller.py "$CLEAN_REPO_DIR/reticulum_mesh/mesh_controller/"
#cp -v /home/natak/reticulum_mesh/mesh_controller/README.md "$CLEAN_REPO_DIR/reticulum_mesh/mesh_controller/"

# OGM Monitor
#cp -v /home/natak/reticulum_mesh/ogm_monitor/ogm_monitor.py "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor/"
cp -v /home/natak/reticulum_mesh/ogm_monitor/enhanced_ogm_monitor.py "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor/"
cp -v /home/natak/reticulum_mesh/ogm_monitor/node_status.json "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor/"
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
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/atak_port_change.md "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/compression.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/cot_zstd_compressor.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/"
cp -v /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/cot_zstd_decompressor.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/"

# Reticulum Module
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/reticulum_handler.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/README.md "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/"

# New Implementation Reticulum Module
echo "Copying new implementation reticulum module components..."
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/__init__.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/config.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/logger.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
#cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/file_manager.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
#cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/link_manager.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/packet_manager.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
#cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/reticulum_handler.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
#cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/run_reticulum.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/README.md "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery_README.md "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/test_peer_discovery.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.json "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/packet_handler_README.md "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/test_setup.py "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/"
cp -v /home/natak/reticulum_mesh/start_reticulum_stack.sh "$CLEAN_REPO_DIR/reticulum_mesh/"

# Copy log files
cp -v /var/log/reticulum/packet_logs.log "$CLEAN_REPO_DIR/var/log/reticulum/" 2>/dev/null || touch "$CLEAN_REPO_DIR/var/log/reticulum/packet_logs.log"

# Create .gitkeep files for empty directories
touch "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/pending/.gitkeep"
touch "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/processing/.gitkeep"
touch "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/incoming/.gitkeep"
touch "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/shared/sent_buffer/.gitkeep"

echo "Clean sync complete!"
