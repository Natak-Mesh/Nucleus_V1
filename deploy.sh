#!/bin/bash

# Base directory for clean GitHub repo
CLEAN_REPO_DIR="/home/natak/git_mesh"

echo "Creating directories..."
# Create system directories (requires sudo)
sudo mkdir -p /etc/systemd/system
sudo mkdir -p /etc/systemd/network
sudo mkdir -p /var/log/reticulum

# Create user directories
mkdir -p /home/natak/mesh
mkdir -p /home/natak/mesh_monitor/templates
mkdir -p /home/natak/macsec_config_tool
mkdir -p /home/natak/.reticulum
mkdir -p /home/natak/reticulum_mesh/identity_handler
mkdir -p /home/natak/reticulum_mesh/mesh_controller
mkdir -p /home/natak/reticulum_mesh/ogm_monitor
mkdir -p /home/natak/reticulum_mesh/rns_stats
mkdir -p /home/natak/reticulum_mesh/tak_transmission/atak_module/utils
mkdir -p /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation
mkdir -p /home/natak/reticulum_mesh/tak_transmission/shared/pending
mkdir -p /home/natak/reticulum_mesh/tak_transmission/shared/processing
mkdir -p /home/natak/reticulum_mesh/tak_transmission/shared/incoming

echo "Copying files..."

# Copy Reticulum config
cp -v "$CLEAN_REPO_DIR/home/natak/.reticulum/config" /home/natak/.reticulum/

# Copy mesh files
cp -v "$CLEAN_REPO_DIR/home/natak/mesh/batmesh.sh" /home/natak/mesh/
cp -v "$CLEAN_REPO_DIR/home/natak/mesh/macsec.sh" /home/natak/mesh/
cp -v "$CLEAN_REPO_DIR/home/natak/mesh/mesh_config.env" /home/natak/mesh/
cp -v "$CLEAN_REPO_DIR/home/natak/mesh/hostname_mapping.json" /home/natak/mesh/
cp -v "$CLEAN_REPO_DIR/home/natak/mesh/README.md" /home/natak/mesh/

# Copy systemd service files (requires sudo)
sudo cp -v "$CLEAN_REPO_DIR/etc/systemd/system/mesh-startup.service" /etc/systemd/system/
sudo cp -v "$CLEAN_REPO_DIR/etc/systemd/system/reticulum-stack.service" /etc/systemd/system/
sudo cp -v "$CLEAN_REPO_DIR/etc/systemd/system/mesh-monitor.service" /etc/systemd/system/
sudo cp -v "$CLEAN_REPO_DIR/etc/systemd/system/systemd_services.md" /etc/systemd/system/

# Copy systemd network configuration (requires sudo)
sudo cp -v "$CLEAN_REPO_DIR/etc/systemd/network/br0.netdev" /etc/systemd/network/
sudo cp -v "$CLEAN_REPO_DIR/etc/systemd/network/br0.network" /etc/systemd/network/
sudo cp -v "$CLEAN_REPO_DIR/etc/systemd/network/eth0.network" /etc/systemd/network/
sudo cp -v "$CLEAN_REPO_DIR/etc/systemd/network/wlan0.network" /etc/systemd/network/

# Copy mesh monitor application
cp -v "$CLEAN_REPO_DIR/home/natak/mesh_monitor/app.py" /home/natak/mesh_monitor/
cp -v "$CLEAN_REPO_DIR/home/natak/mesh_monitor/templates/index.html" /home/natak/mesh_monitor/templates/
cp -v "$CLEAN_REPO_DIR/home/natak/mesh_monitor/README.md" /home/natak/mesh_monitor/
cp -v "$CLEAN_REPO_DIR/home/natak/mesh_monitor/templates/packet_logs.html" /home/natak/mesh_monitor/templates/

# Copy macsec_config_tool files
cp -v "$CLEAN_REPO_DIR/home/natak/macsec_config_tool/Macsec_config_generator.py" /home/natak/macsec_config_tool/
cp -v "$CLEAN_REPO_DIR/home/natak/macsec_config_tool/example.md" /home/natak/macsec_config_tool/
cp -v "$CLEAN_REPO_DIR/home/natak/macsec_config_tool/README.md" /home/natak/macsec_config_tool/

# Copy reticulum mesh components
echo "Copying reticulum mesh components..."

# Identity Handler
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/identity_handler/identity_mapper.py" /home/natak/reticulum_mesh/identity_handler/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/identity_handler/README.md" /home/natak/reticulum_mesh/identity_handler/

# OGM Monitor
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor/enhanced_ogm_monitor.py" /home/natak/reticulum_mesh/ogm_monitor/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor/node_status.json" /home/natak/reticulum_mesh/ogm_monitor/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/ogm_monitor/README.md" /home/natak/reticulum_mesh/ogm_monitor/

# RNS Stats
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/rns_stats/rns_monitor.py" /home/natak/reticulum_mesh/rns_stats/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/rns_stats/README.md" /home/natak/reticulum_mesh/rns_stats/

# TAK Transmission
echo "Copying TAK transmission components..."

# Main files
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/systemd_services.md" /home/natak/reticulum_mesh/tak_transmission/

# ATAK Module
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/atak_handler.py" /home/natak/reticulum_mesh/tak_transmission/atak_module/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/README.md" /home/natak/reticulum_mesh/tak_transmission/atak_module/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/atak_port_change.md" /home/natak/reticulum_mesh/tak_transmission/atak_module/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/compression.py" /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/cot_zstd_compressor.py" /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/atak_module/utils/cot_zstd_decompressor.py" /home/natak/reticulum_mesh/tak_transmission/atak_module/utils/

# Reticulum Module
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/reticulum_handler.py" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/README.md" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/

# New Implementation Reticulum Module
echo "Copying new implementation reticulum module components..."
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/__init__.py" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/config.py" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/logger.py" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.py" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/packet_manager.py" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/README.md" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery_README.md" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/test_peer_discovery.py" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.json" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/packet_handler_README.md" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/
cp -v "$CLEAN_REPO_DIR/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/test_setup.py" /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/

cp -v "$CLEAN_REPO_DIR/reticulum_mesh/start_reticulum_stack.sh" /home/natak/reticulum_mesh/

# Copy log files
sudo cp -v "$CLEAN_REPO_DIR/var/log/reticulum/packet_logs.log" /var/log/reticulum/ 2>/dev/null || sudo touch /var/log/reticulum/packet_logs.log

# Set proper permissions for log directory
sudo chown -R natak:natak /var/log/reticulum
sudo chmod 755 /var/log/reticulum
sudo chmod 644 /var/log/reticulum/packet_logs.log

echo "Deployment complete!"
