# Reticulum Stack Startup Process

This document describes the startup process for the Reticulum stack and the files involved.

## Startup Process

The Reticulum stack starts through a systemd service that follows this sequence:

1. The systemd service (`reticulum-stack.service`) triggers at boot or when manually started
2. The service executes the startup script 
3. The startup script cleans old packet files and launches the main Python script
4. The main Python script starts components in this order:
   - OGM monitor for tracking node status
   - Peer discovery for identifying network peers
   - Packet manager for handling message transmission
   - ATAK handler for interfacing with the Team Awareness Kit

## Files Involved

1. **Systemd Service File**: `/etc/systemd/system/reticulum-stack.service`
   - Defines how and when the stack starts
   - Configures service to restart on failure
   - Sets the user context (natak)

2. **Startup Script**: `/home/natak/reticulum_mesh/start_reticulum_stack.sh`
   - Cleans up old packet files from shared directories
   - Sets up the Python environment
   - Launches the main orchestration script

3. **Main Orchestration Script**: `/home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/test_setup.py`
   - Starts all required components in sequence
   - Manages the lifecycle of subprocesses and threads
   - Handles graceful shutdown on interruption

4. **Configuration File**: `/home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/config.py`
   - Defines startup delay for LoRa radio (10 seconds)
   - Specifies file paths and directories for packet handling
   - Contains retry mechanisms and other operational parameters
