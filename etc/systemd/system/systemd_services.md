# Reticulum Mesh TAK Services

This document describes the systemd services used for TAK integration with the Reticulum mesh network.

## Service Start Order

The services must start in the following order to ensure proper operation:

1. `reticulum-mesh-network.service`
   - Sets up the network interfaces and mesh networking
   - Executes macsec.sh and batmesh.sh scripts
   - Must be running before any other services start

2. `reticulum-mesh-ogm.service`
   - Runs ogm_monitor.py
   - Monitors mesh network health through OGM (Originator Message) tracking
   - Depends on network service being active
   - Provides network health status for other services

3. `reticulum-mesh-identity.service`
   - Runs identity_mapper.py
   - Manages node identity mapping in the mesh network
   - Depends on network and OGM services
   - Must be running before RNS communication can begin

4. `reticulum-mesh-reticulum.service`
   - Runs reticulum_handler.py
   - Handles RNS (Reticulum Network Stack) communication for TAK data
   - Depends on network, OGM, and identity services
   - Includes a 10-second delay after dependencies start to ensure RNS is fully booted
   - Must be running before ATAK handler can start

5. `reticulum-mesh-atak.service`
   - Runs atak_handler.py
   - Manages ATAK client communication and data translation
   - Depends on reticulum handler service
   - Starts only after RNS communication is established

6. `reticulum-mesh-rns-monitor.service`
   - Runs rns_monitor.py
   - Monitors the Reticulum Network Stack and peer connections
   - Depends on reticulum handler service
   - Includes a 10-second delay after dependencies start
   - Collects and stores RNS status information for monitoring

7. `mesh-monitor.service`
   - Runs app.py in the mesh_monitor directory
   - Provides a web interface for monitoring the mesh network
   - Depends on RNS monitor service
   - Includes a 15-second delay after dependencies start
   - Visualizes mesh network status and performance

## Service Details

### reticulum-mesh-reticulum.service
- Runs the reticulum_handler.py script
- Translates TAK data into RNS messages
- Manages RNS connections and message routing
- Uses PYTHONPATH to access shared mesh modules
- Automatically restarts on failure with 7-second delay
- Requires dialout group access for serial communication

### reticulum-mesh-atak.service
- Runs the atak_handler.py script
- Interfaces with ATAK clients
- Translates between TAK and RNS message formats
- Uses PYTHONPATH to access shared mesh modules
- Automatically restarts on failure with 7-second delay
- Requires dialout group access for serial communication

### reticulum-mesh-rns-monitor.service
- Runs the rns_monitor.py script
- Monitors Reticulum network peers and connections
- Collects signal quality metrics (RSSI, SNR) when available
- Tracks path information (hops, next hop, interfaces)
- Writes status information to JSON file for other services
- Automatically restarts on failure with 10-second delay
- Requires dialout group access for serial communication

### mesh-monitor.service
- Runs the app.py script in the mesh_monitor directory
- Provides a web-based dashboard for monitoring mesh status
- Visualizes data from OGM monitor and RNS monitor
- Shows node connectivity, signal quality, and network topology
- Automatically restarts on failure with 10-second delay
