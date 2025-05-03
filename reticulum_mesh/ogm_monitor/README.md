# Enhanced OGM Monitor

## Overview

The Enhanced OGM Monitor is a consolidated monitoring solution that tracks mesh node status and controls mode switching between WiFi and LoRa interfaces. It replaces the separate OGM Monitor and Mesh Controller components with a single, integrated solution.

## Key Features

- **Hostname-Based Node Tracking**: Uses the hostname mapping as the authoritative source of nodes
- **Complete Visibility**: Always maintains entries for all remote nodes, even when disconnected
- **Automatic Mode Switching**: Switches nodes between WiFi and LoRa based on connection quality
- **Centralized Status File**: Provides a single source of truth for node status
- **Human-Readable Output**: Includes hostnames alongside MAC addresses
- **Local Node Exclusion**: Excludes the local node (takNode1) from monitoring

## Architecture

The Enhanced OGM Monitor:
1. Loads the hostname mapping to get the list of authorized nodes
2. Filters out the local node to avoid self-monitoring
3. Checks Batman-adv status to determine connectivity of remote nodes
4. Updates mode information based on connection quality
5. Writes consolidated status to a single file

## File Paths

- **Hostname Map**: `/home/natak/mesh/hostname_mapping.json`
- **Status Output**: `/home/natak/reticulum_mesh/ogm_monitor/node_status.json`

## Configuration Parameters

- `FAILURE_THRESHOLD`: Seconds without OGMs to consider a failure (default: 3.0)
- `FAILURE_COUNT`: Consecutive failures to switch to LoRa (default: 3)
- `RECOVERY_COUNT`: Consecutive good readings to switch back to WiFi (default: 10)

## Status File Format

```json
{
  "timestamp": 1744488097,
  "nodes": {
    "00:c0:ca:b6:92:cb": {
      "hostname": "takNode3",
      "ip": "192.168.200.3",
      "last_seen": 5.4,
      "mode": "LORA",
      "failure_count": 10,
      "good_count": 0,
      "throughput": 10.2,
      "nexthop": "00:c0:ca:b6:95:23"
    },
    "00:c0:ca:b6:95:23": {
      "hostname": "takNode2",
      "ip": "192.168.200.2",
      "last_seen": 0.2,
      "mode": "WIFI",
      "failure_count": 0,
      "good_count": 15
    }
    // Note: takNode1 (00:c0:ca:b6:92:c0) is excluded as it's the local node
  }
}
```

## Transition from Previous Implementation

This implementation consolidates functionality from:
- `ogm_monitor.py`: Monitoring Batman-adv OGM status
- `mesh_controller.py`: Mode switching logic

The enhanced monitor uses the same core logic for mode switching but improves on the previous implementation by:
1. Always tracking all remote nodes from the hostname mapping
2. Excluding the local node to avoid self-monitoring
3. Including hostname information
4. Providing more detailed status information
5. Consolidating configuration into a single component

## Usage

Run the enhanced monitor:

```bash
python3 enhanced_ogm_monitor.py
```

The script will continuously monitor node status and update the status file.
