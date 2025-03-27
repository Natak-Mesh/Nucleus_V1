# Identity Mapper

## Inputs
- No command-line arguments
- Reads hostname mapping file from "/home/natak/mesh/hostname_mapping.json"

## Outputs
- Identity mapping file at "/home/natak/reticulum_mesh/identity_handler/identity_map.json"
- Logs status updates

## Internal Functionality
- Loads hostname mapping information from JSON file
- Maps MAC addresses to hostnames and IP addresses
- Updates identity mapping file every 10 seconds
- Writes mapping atomically using temporary file and rename for consistency
