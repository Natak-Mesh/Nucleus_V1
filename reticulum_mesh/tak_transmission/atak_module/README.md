# ATAK Handler

## Inputs
- No command-line arguments
- Listens for TAK Protocol packets on ATAK multicast addresses and ports
- Reads node modes from "/home/natak/reticulum_mesh/mesh_controller/node_modes.json"
- Reads compressed packets from "/home/natak/reticulum_mesh/tak_transmission/shared/incoming" directory

## Outputs
- Writes compressed packets to "/home/natak/reticulum_mesh/tak_transmission/shared/pending" directory
- Forwards decompressed packets to ATAK multicast addresses
- Logs status updates

## Internal Functionality
- Listens for TAK Protocol packets on multicast addresses
- Compresses packets using zstd compression:
  - Uses Zstandard (zstd) algorithm for high compression ratio
  - Supports optional dictionary-based compression for better efficiency
  - Limits compressed packet size to 350 bytes by default
  - Handles compression failures gracefully
- Implements packet deduplication using MD5 hashing:
  - Maintains a queue of the 1000 most recent packet hashes
  - Calculates MD5 hash of each packet (both incoming and outgoing)
  - Skips processing if the hash is already in the queue
  - Adds new hashes to the queue, automatically removing oldest when full
- Conditionally stores packets based on node modes (only when nodes are in non-WIFI mode)
- Decompresses packets received from shared/incoming directory and forwards them back to ATAK
- Manages shared directories for packet exchange with other components
