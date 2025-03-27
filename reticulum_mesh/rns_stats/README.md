# RNS Monitor

## Inputs
- Optional command-line argument for config path
- Configuration constants (OUTPUT_PATH, UPDATE_INTERVAL, APP_NAME, ASPECT)

## Outputs
- JSON file (/home/natak/reticulum_mesh/rns_stats/rns_status.json) with Reticulum network status
- Logs status updates

## Internal Functionality
- Connects to existing Reticulum instance
- Registers announce handler for peer announcements
- Collects peer information (destination hash, last seen time, hostname, RSSI, SNR)
- Adds path information (hops, next hop, next hop interface)
- Updates JSON file at regular intervals (default: 10 seconds)
