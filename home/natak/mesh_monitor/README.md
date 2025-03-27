# Mesh Monitor

A Flask web application that provides real-time monitoring of mesh network status, including both batman-adv mesh connections and Reticulum peers.

## Overview

The mesh monitor consists of a Flask backend (`app.py`) that collects data from multiple sources and serves it through a web interface. It provides:

- Real-time monitoring of mesh network nodes with hostname resolution
- Local node information (MAC addresses and IP)
- Hostname and IP mapping for mesh nodes
- Throughput metrics from BATMAN_V routing algorithm
- Reticulum peer status
- Auto-refresh and pull-to-refresh capabilities
- Mobile-friendly responsive design

## How app.py Works

### Main Components

1. **Flask Application Setup**
   - Creates a Flask web server
   - Serves a dynamic web interface using the `templates/index.html` template
   - Provides API endpoints for data retrieval

2. **Data Collection Functions**

   a. `load_hostname_mapping()`
   - Loads the hostname mapping file from `/home/natak/mesh/hostname_mapping.json`
   - Maps MAC addresses to hostnames and IP addresses
   - Used to provide human-readable node identification
   - Returns a dictionary of MAC address mappings

   b. `get_local_info()`
   - Retrieves information about the local node
   - Uses `batctl o` to get batman-adv interface information
   - Uses `ip addr show br0` to get IP address information
   - Returns MAC addresses (WLAN and batman-adv) and IP address

   b. `get_reticulum_peers()`
   - Connects to ATAK relay Unix domain socket
   - Tries two possible socket paths:
     1. `/var/run/atak_relay.sock`
     2. `/tmp/atak_relay.sock`
   - Retrieves peer information from the ATAK relay service
   - Returns a dictionary of connected Reticulum peers

   c. `parse_batman_originators()`
   - Parses the output of `batctl o` command
   - Processes batman-adv mesh node information
   - Extracts details like:
     - MAC addresses
     - Last seen times
     - Route metrics
     - Next hop information
     - Interface details

### Routes

1. **Main Route (`/`)**
   ```python
   @app.route('/')
   def home():
      return render_template('index.html', hostname=socket.gethostname())
   ```
   - Serves the main web interface
   - Passes local hostname to the template

2. **API Endpoints**

   a. `/get_mesh_data`
   ```python
   @app.route('/get_mesh_data')
   def get_mesh_data():
       # Collects and returns mesh network data
   ```
   - Returns JSON containing:
     - Local node information
     - Connected mesh nodes
     - Reticulum peers
     - Success/error status

   b. `/force_announce` (POST)
   ```python
   @app.route('/force_announce', methods=['POST'])
   def handle_force_announce():
       # Triggers announce to update peer timestamps
   ```
   - Sends force announce command to ATAK relay
   - Triggers peer responses to update "last seen" times
   - Returns success/error status

### Data Sources

1. **batman-adv**
   - Uses `batctl o` command to get mesh originator information
   - Provides details about connected mesh nodes
   - Shows throughput metrics from BATMAN_V routing algorithm
   - Displays link quality through Mbps measurements

2. **Hostname Mapping**
   - JSON file located at `/home/natak/mesh/hostname_mapping.json`
   - Maps MAC addresses to hostnames and IP addresses
   - Format:
     ```json
     {
       "00:11:22:33:44:55": {
         "hostname": "nodeName",
         "ip": "192.168.x.x"
       }
     }
     ```
   - Enables human-readable node identification

3. **Local Network**
   - Uses `ip addr show br0` to get bridge interface information
   - Provides local IP address information

4. **Reticulum Network**
   - Connects to ATAK relay socket
   - Gets information about connected Reticulum peers
   - Provides peer hostnames and hashes

### Data Flow

1. Frontend makes periodic requests to `/get_mesh_data`
2. Backend collects data from multiple sources:
   - Loads hostname mapping from JSON file
   - Executes system commands for batman-adv info
   - Reads network interface details
   - Connects to ATAK relay socket
3. Data is processed and enriched:
   - MAC addresses are mapped to hostnames and IPs
   - Throughput metrics are extracted from batman-adv output
   - Node information is consolidated
4. JSON response is sent back to frontend
5. Frontend updates the UI with new information:
   - Displays hostnames and IPs for each node
   - Shows throughput in Mbps
   - Updates connection status

## Integration Points

### batman-adv Integration
- Directly interfaces with batman-adv through the `batctl` command
- Parses command output to extract node and routing information
- Filters and processes data to show relevant mesh network status

### ATAK Relay Integration
- Connects to Unix domain socket created by ATAK relay service
- Receives peer information from the Reticulum network
- Integrates Reticulum peer data with mesh network information
- Provides force announce mechanism to:
  - Trigger peer announces on demand
  - Update "last seen" timestamps
  - Verify peer connectivity

### Frontend Integration
- Serves a responsive web interface
- Updates data in real-time
- Provides interactive features like:
  - Expandable node details
  - Click-to-copy MAC and IP addresses
  - Pull-to-refresh functionality
  - Connection status indicator
  - Force announce to update peer status

For more details about the force announce mechanism and recent updates, see [force_announce_update.md](force_announce_update.md).
