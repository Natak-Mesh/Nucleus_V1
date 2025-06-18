#!/bin/bash

# Mesh Startup Sequence Script
# Runs atak_module, macsec.sh, and batmesh.sh in proper order

# Enable error reporting
set -e

echo "Starting mesh startup sequence..."

# Start atak_module in background
#echo "Starting ATAK module..."
#cd /home/natak/meshtastic && python3 atak_module.py &
#ATAK_PID=$!

# Give atak_module time to initialize
sleep 2

# Run macsec setup (with sudo)
#echo "Running MACSec setup..."
#sudo /home/natak/mesh/macsec.sh

#wpa_supplicant -B -i wlan1 -c /etc/wpa_supplicant/wpa_supplicant-wlan1.conf

# Brief pause between network setup steps
sleep 5

# Run batman mesh setup (with sudo)
echo "Running Batman mesh setup..."
sudo /home/natak/mesh/batmesh.sh

# Brief pause after network setup
sleep 2

# Start rnsd (Reticulum Network Stack Daemon) in background
echo "Starting rnsd (Reticulum Network Stack Daemon)..."
nohup rnsd > /var/log/rnsd.log 2>&1 &
RNSD_PID=$!

# Give rnsd time to initialize
sleep 2

# Start enhanced OGM monitor in background
echo "Starting enhanced OGM monitor..."
cd /home/natak/mesh/ogm_monitor && python3 enhanced_ogm_monitor.py &
OGM_PID=$!

echo "Mesh startup sequence completed successfully"
echo "ATAK module running with PID: $ATAK_PID"
echo "rnsd running with PID: $RNSD_PID"
echo "Enhanced OGM monitor running with PID: $OGM_PID"