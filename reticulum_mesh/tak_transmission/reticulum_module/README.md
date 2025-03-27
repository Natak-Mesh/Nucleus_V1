# Reticulum Handler

## Inputs
- No command-line arguments
- Reads node modes from "/home/natak/reticulum_mesh/mesh_controller/node_modes.json"
- Reads identity mapping from "/home/natak/reticulum_mesh/identity_handler/identity_map.json"
- Reads compressed packets from "/home/natak/reticulum_mesh/tak_transmission/shared/pending" directory
- Receives Reticulum announces and packets from other nodes

## Outputs
- Writes received packets to "/home/natak/reticulum_mesh/tak_transmission/shared/incoming" directory
- Sends Reticulum announces and packets to other nodes
- Logs status updates

## Internal Functionality
- Initializes Reticulum with a 10-second startup delay for LoRa radio
- Implements peer discovery through Reticulum announce/response mechanism:
  - Creates a destination with app name "atak" and aspect "cot"
  - Announces presence with hostname encoded as app_data
  - Re-announces every 60 seconds to maintain peer visibility
  - Registers an announce handler with aspect filter "atak.cot"
  - When announces are received, extracts hostname from app_data
  - Builds an in-memory map of hostnames to destinations
  - Updates "last seen" timestamp for each peer on announce receipt
  - Removes peers after 5 minutes of inactivity to prevent stale entries
- Monitors node_modes.json for nodes in non-WIFI mode
- Only activates message processing loops when non-WIFI nodes are detected
- Processes files from the pending directory and transmits them over Reticulum
- Writes received messages to the incoming directory with timestamp-based filenames
