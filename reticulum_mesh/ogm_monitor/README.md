# OGM Monitor

## Inputs
- No command-line arguments
- Relies on output from `sudo batctl o` command
- Optional parameter for output filename (defaults to 'status.json')

## Outputs
- JSON file (status.json) with Batman mesh network status
- Console status updates showing node information

## Internal Functionality
- Runs `batctl o` command to get Batman mesh network originator information
- Parses command output for node data (MAC addresses, last seen time, throughput, nexthop)
- Updates JSON file every second (matching BATMAN OGM interval)
- Writes status atomically using temporary file and rename for consistency
