from flask import Flask, render_template, jsonify, Response
import socket
import json
import os
import time
import logging
from functools import partial

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configuration
UPDATE_INTERVAL = 1  # Update interval in seconds

# File paths
NODE_MODES_PATH = '/home/natak/reticulum_mesh/mesh_controller/node_modes.json'
IDENTITY_MAP_PATH = '/home/natak/reticulum_mesh/identity_handler/identity_map.json'
STATUS_PATH = '/home/natak/reticulum_mesh/ogm_monitor/status.json'
RNS_STATUS_PATH = '/home/natak/reticulum_mesh/rns_stats/rns_status.json'

# Cache for file data to avoid reading files on every request
file_cache = {
    'node_modes': {'data': None, 'timestamp': 0},
    'identity_map': {'data': None, 'timestamp': 0},
    'status': {'data': None, 'timestamp': 0},
    'rns_status': {'data': None, 'timestamp': 0}
}

# Cache expiration time in seconds
CACHE_EXPIRATION = UPDATE_INTERVAL

def read_json_file(file_path, cache_key):
    """Read a JSON file with caching and error handling"""
    try:
        # Check if cache is valid
        current_time = time.time()
        if (file_cache[cache_key]['data'] is not None and 
            current_time - file_cache[cache_key]['timestamp'] < CACHE_EXPIRATION):
            return file_cache[cache_key]['data']
        
        # Read file and update cache
        with open(file_path, 'r') as f:
            data = json.load(f)
            file_cache[cache_key] = {
                'data': data,
                'timestamp': current_time
            }
            return data
    except FileNotFoundError:
        app.logger.error(f"File not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        app.logger.error(f"Invalid JSON in file: {file_path}")
        return {}
    except Exception as e:
        app.logger.error(f"Error reading file {file_path}: {e}")
        return {}

def get_node_modes():
    """Get node operation modes from node_modes.json"""
    return read_json_file(NODE_MODES_PATH, 'node_modes')

def get_identity_map():
    """Get identity mapping from identity_map.json"""
    identity_data = read_json_file(IDENTITY_MAP_PATH, 'identity_map')
    # Extract the nodes dictionary or return empty dict if not found
    return identity_data.get('nodes', {})

def get_wifi_status():
    """Get WiFi status from status.json"""
    status_data = read_json_file(STATUS_PATH, 'status')
    return status_data.get('nodes', {})

def get_reticulum_status():
    """Get Reticulum status from rns_status.json"""
    rns_data = read_json_file(RNS_STATUS_PATH, 'rns_status')
    return rns_data.get('peers', {})

def get_local_info():
    """Get local node information from identity_map.json"""
    local_hostname = socket.gethostname()
    identity_map = get_identity_map()
    
    # Find the entry for the local hostname
    for mac, node_info in identity_map.items():
        if node_info.get('hostname') == local_hostname:
            return {
                'wlan_mac': mac,
                'bat_mac': mac,  # Using the same MAC for both since we don't have separate batman MAC
                'ip': node_info.get('ip', 'Unknown')
            }
    
    # Fallback if not found
    return {
        'wlan_mac': 'Unknown',
        'bat_mac': 'Unknown',
        'ip': 'Unknown'
    }

def process_wifi_nodes():
    """Process WiFi nodes data from status.json and map to hostnames"""
    nodes = []
    wifi_status = get_wifi_status()
    identity_map = get_identity_map()
    node_modes = get_node_modes()
    
    for mac, status in wifi_status.items():
        # Get hostname and IP from identity map
        node_info = identity_map.get(mac, {})
        hostname = node_info.get('hostname', 'Unknown')
        ip = node_info.get('ip', 'Unknown')
        
        # Get node mode
        mode_info = node_modes.get(mac, {})
        mode = mode_info.get('mode', 'Unknown')
        
        # Create node entry
        node = {
            'mac': mac,
            'hostname': hostname,
            'ip': ip,
            'mode': mode,
            'throughput': status.get('throughput', 0),
            'last_seen': status.get('last_seen', 0),
            'nexthop': status.get('nexthop', 'Unknown')
        }
        
        nodes.append(node)
    
    return nodes

def process_reticulum_peers():
    """Process Reticulum peers data from rns_status.json"""
    reticulum_peers = {}
    rns_status = get_reticulum_status()
    local_hostname = socket.gethostname()
    
    for hash_id, peer_data in rns_status.items():
        # Skip the local node
        hostname = peer_data.get('hostname', 'Unknown')
        if hostname == local_hostname:
            continue
            
        # Convert timestamp to relative time
        last_seen = 0
        if 'last_seen' in peer_data:
            current_time = time.time()
            last_seen = int(current_time - peer_data['last_seen'])
        
        # Create peer entry with hostname as the main identifier
        reticulum_peers[hash_id] = {
            'name': hostname,
            'last_seen': last_seen,
            'rssi': peer_data.get('rssi', 0),
            'snr': peer_data.get('snr', 0),
            'hops': peer_data.get('hops', 0)
        }
    
    return reticulum_peers

@app.route('/')
def home():
    return render_template('index.html', hostname=socket.gethostname())


@app.route('/get_mesh_data')
def get_mesh_data():
    # Get local node info
    local_info = get_local_info()
    success = True
    error = None
    
    try:
        # Process WiFi nodes
        nodes = process_wifi_nodes()
        
        # Process Reticulum peers
        reticulum_peers = process_reticulum_peers()
    except Exception as e:
        app.logger.error(f"Unexpected error processing mesh data: {e}")
        success = False
        error = "An unexpected error occurred"
        nodes = []
        reticulum_peers = {}
    
    return jsonify({
        'success': success,
        'error': error,
        'local_info': local_info,
        'nodes': nodes,
        'reticulum_peers': reticulum_peers
    })

def generate_events():
    """Generate SSE events with mesh data"""
    while True:
        try:
            # Get current mesh data
            data = {
                'success': True,
                'error': None,
                'local_info': get_local_info(),
                'nodes': process_wifi_nodes(),
                'reticulum_peers': process_reticulum_peers()
            }
            
            # Send the event
            yield f"data: {json.dumps(data)}\n\n"
            
            # Wait for next update
            time.sleep(UPDATE_INTERVAL)
            
        except Exception as e:
            app.logger.error(f"Error generating event: {e}")
            yield f"data: {json.dumps({'success': False, 'error': str(e)})}\n\n"
            time.sleep(UPDATE_INTERVAL)

@app.route('/events')
def events():
    """SSE endpoint for real-time updates"""
    return Response(
        generate_events(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
