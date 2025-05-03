#!/bin/bash
# Cleanup script to remove files that are in clean_sync.sh but not in clean_sync_2.sh

# Base directory
BASE_DIR="/home/natak/git_mesh"
cd $BASE_DIR || { echo "Error: Cannot change to $BASE_DIR"; exit 1; }

echo "Starting cleanup of files not in clean_sync_2.sh..."

# Remove individual files
FILES_TO_REMOVE=(
  "etc/systemd/system/mesh-monitor.service"
  "etc/systemd/system/systemd_services.md"
  "reticulum_mesh/identity_handler/identity_mapper.py"
  "reticulum_mesh/identity_handler/README.md"
  "reticulum_mesh/rns_stats/rns_monitor.py"
  "reticulum_mesh/rns_stats/README.md"
  "reticulum_mesh/tak_transmission/systemd_services.md"
  "reticulum_mesh/tak_transmission/atak_module/atak_port_change.md"
  "reticulum_mesh/tak_transmission/reticulum_module/reticulum_handler.py"
  "reticulum_mesh/tak_transmission/reticulum_module/README.md"
  "reticulum_mesh/tak_transmission/reticulum_module/new_implementation/timing_fix_packet_manager.md"
  "reticulum_mesh/tak_transmission/reticulum_module/new_implementation/test_peer_discovery.py"
  "reticulum_mesh/tak_transmission/reticulum_module/new_implementation/packet_handler_README.md"
  "var/log/reticulum/packet_logs.log"
)

# Remove files and untrack from git
for file in "${FILES_TO_REMOVE[@]}"; do
  if [ -f "$file" ]; then
    echo "Removing $file"
    git rm -f "$file" || echo "Warning: Failed to git rm $file"
  else
    echo "File $file does not exist, skipping"
  fi
done

# Directories to check and remove if empty
DIRS_TO_CHECK=(
  "reticulum_mesh/mesh_controller"
  "reticulum_mesh/identity_handler"
  "reticulum_mesh/rns_stats"
  "var/log/reticulum"
)

# Check and remove empty directories
for dir in "${DIRS_TO_CHECK[@]}"; do
  if [ -d "$dir" ]; then
    if [ -z "$(ls -A "$dir")" ]; then
      echo "Removing empty directory $dir"
      git rm -rf "$dir" || rmdir "$dir" || echo "Warning: Failed to remove directory $dir"
    else
      echo "Directory $dir is not empty, skipping"
    fi
  else
    echo "Directory $dir does not exist, skipping"
  fi
done

echo "Cleanup complete!"
