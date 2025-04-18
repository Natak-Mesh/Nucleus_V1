# Enhanced OGM Monitor

A consolidated monitoring solution that tracks mesh node status and controls mode switching between WiFi and LoRa interfaces.

## Files and Data Sources

- **Input Files:**
  - `/home/natak/mesh/hostname_mapping.json`: Maps MAC addresses to hostnames and IPs
  - Batman-adv status via `batctl o` command: Provides real-time OGM data
  - Existing status file (if available): Preserves state between runs

- **Output File:**
  - `/home/natak/reticulum_mesh/ogm_monitor/node_status.json`: Single source of truth for node status

## Decision Logic

1. **Node Identification:**
   - Loads hostname mapping to identify all authorized nodes
   - Filters out local node to avoid self-monitoring
   - Always maintains entries for all remote nodes, even when disconnected

2. **Connection Quality Assessment:**
   - Failure detected when OGMs not received for > 3 seconds
   - Tracks consecutive failures and recoveries for each node

3. **Mode Switching Logic:**
   - WiFi → LoRa: After 3 consecutive failures
   - LoRa → WiFi: After 10 consecutive good readings
   - Preserves mode state between runs

## Configuration Parameters

- `FAILURE_THRESHOLD = 3.0`: Seconds without OGMs to consider a failure
- `FAILURE_COUNT = 3`: Consecutive failures to switch to LoRa
- `RECOVERY_COUNT = 10`: Consecutive good readings to switch back to WiFi

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
    }
  }
}
```

## Usage

```bash
python3 enhanced_ogm_monitor.py
```
