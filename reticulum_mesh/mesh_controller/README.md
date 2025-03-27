# Mesh Controller

## Inputs
- No command-line arguments
- Reads status file from "/home/natak/reticulum_mesh/ogm_monitor/status.json"
- Reads node modes file from "/home/natak/reticulum_mesh/mesh_controller/node_modes.json"

## Outputs
- Updates node modes file at "/home/natak/reticulum_mesh/mesh_controller/node_modes.json"
- Prints color-coded status updates to console (green for WIFI, yellow for LORA)

## Internal Functionality
- Monitors mesh node status based on OGM data
- Tracks "last seen" time to detect connectivity issues
- Implements state machine to switch between "WIFI" and "LORA" modes
- Uses failure and recovery counters to prevent rapid mode switching
- Updates node modes every second
