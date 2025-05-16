# Mesh Monitor Directory

This directory contains a Flask-based web application that provides real-time monitoring of the mesh network status. It visualizes both BATMAN-adv mesh connections and Reticulum peer information through an interactive web interface.

## File Overview

### app.py
A Python Flask application that serves as the backend for the mesh monitoring system. This script:
- Creates a web server that hosts the monitoring interface
- Reads data from multiple sources:
  - Node status information from `/home/natak/reticulum_mesh/ogm_monitor/node_status.json`
  - Peer discovery data from `/home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.json`
  - Packet logs from `/var/log/reticulum/packet_logs.log`
- Provides several routes:
  - `/`: The main monitoring dashboard
  - `/packet-logs`: A dedicated view for packet transmission logs
  - `/api/node-status`: JSON API endpoint for node and peer data
  - `/api/packet-logs`: JSON API endpoint for packet log data
- Parses and processes log entries to extract meaningful information
- Serves the web interface templates with real-time data

### templates/index.html
The main web interface template that displays the mesh network status. This file:
- Provides a responsive layout that works on both desktop and mobile devices
- Displays BATMAN mesh nodes in a grid layout with detailed status information:
  - Hostname and IP address
  - MAC address
  - Current mode (WIFI or LORA)
  - Last seen time
  - Throughput metrics
  - Next hop information
  - Failure and success counts
- Shows Reticulum peers with their connection details:
  - Peer hostname
  - Destination hash
  - Last seen time
- Implements automatic refresh using JavaScript fetch API
- Uses a dark-themed interface for better visibility in field conditions

### templates/packet_logs.html
A template for displaying packet transmission logs. This file:
- Shows a chronological list of packet-related events
- Filters out non-essential log entries to focus on important events
- Color-codes different types of log entries:
  - UDP packets
  - ATAK to LoRa transmissions
  - LoRa to ATAK transmissions
  - Received packets
  - Delivered packets
  - Completed transmissions
  - Retry attempts
- Provides a connection status indicator
- Includes timestamp information for each log entry
- Automatically scrolls to show the most recent logs

### packet_logs.html
A standalone HTML file that provides an enhanced view of packet delivery logs. This file:
- Offers a more sophisticated interface for monitoring packet transmissions
- Includes features not present in the template version:
  - Pause/resume functionality for log updates
  - Manual scroll controls
  - More detailed packet status visualization
  - Enhanced filtering of log entries
  - Improved formatting of packet information
  - Connection status indicator
- Uses EventSource for real-time updates
- Implements advanced log parsing to extract packet IDs, destinations, and timing information
- Provides visual differentiation between various packet states (sent, confirmed, failed, retry)
- Includes link establishment and data transmission monitoring

## Data Sources

The mesh monitor integrates with several data sources:

1. **Node Status JSON**
   - Path: `/home/natak/reticulum_mesh/ogm_monitor/node_status.json`
   - Contains information about mesh nodes collected by the OGM monitor
   - Includes node hostnames, IP addresses, MAC addresses, and connection metrics

2. **Peer Discovery JSON**
   - Path: `/home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.json`
   - Stores information about Reticulum peers
   - Includes peer hostnames, destination hashes, and last seen timestamps

3. **Packet Logs**
   - Path: `/var/log/reticulum/packet_logs.log`
   - Contains detailed logs of packet transmissions
   - Records events such as packet sending, delivery confirmations, and retries

## Usage

The mesh monitor is typically accessed through a web browser by navigating to the IP address of the mesh node running the application, on port 5000:

```
http://<node-ip>:5000/
```

Note: The node IP address is set by the `/etc/systemd/network/br0.network` configuration file.

The application provides two main views:
- The main dashboard showing node and peer status
- The packet logs view for monitoring message transmissions

The web interface automatically refreshes to show the current state of the mesh network, making it valuable for both setup/configuration and ongoing monitoring of network health.
