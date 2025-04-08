from flask import Flask, render_template, jsonify, Response
import socket
import json
import os
import time
import logging
import subprocess
import re
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
PACKET_LOG_PATH = '/home/natak/reticulum_mesh/logs/packet_logs.log'

# Link status tracking
active_links = {}  # hostname -> link status
link_events = []   # recent link events (establish/close)

# Cache for file data to avoid reading files on every request
file_cache = {
    'node_modes': {'data': None, 'timestamp': 0},
    'identity_map': {'data': None, 'timestamp': 0},
    'status': {'data': None, 'timestamp': 0},
    'rns_status': {'data': None, 'timestamp': 0},
    'packet_logs': {'data': None, 'timestamp': 0}
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

@app.route('/wifi/toggle', methods=['POST'])
def toggle_wifi():
    try:
        # Check current state
        result = subprocess.run(['ip', 'link', 'show', 'wlan1'], capture_output=True, text=True)
        is_up = 'state UP' in result.stdout
        
        if is_up:
            # Turn WiFi off
            cmd = ['ip', 'link', 'set', 'wlan1', 'down']
            subprocess.run(cmd, check=True)
            new_state = 'down'
        else:
            # Turn WiFi on
            cmd = ['ip', 'link', 'set', 'wlan1', 'up']
            subprocess.run(cmd, check=True)
            new_state = 'up'
        
        # Verify the change
        verify = subprocess.run(['ip', 'link', 'show', 'wlan1'], capture_output=True, text=True)
        actual_state = 'up' if 'state UP' in verify.stdout else 'down'
        
        return jsonify({
            'success': True,
            'state': actual_state,
            'changed': actual_state == new_state
        })
    except Exception as e:
        app.logger.error(f"Error toggling WiFi: {e}")
        return jsonify({'success': False, 'error': str(e)})

def get_local_info():
    """Get local node information from identity_map.json and rns_status.json"""
    local_hostname = socket.gethostname()
    identity_map = get_identity_map()
    # Find MAC and IP from identity map
    local_info = {
        'wlan_mac': 'Unknown',
        'bat_mac': 'Unknown',
        'ip': 'Unknown',
        'hostname': local_hostname,
        'hash': 'Unknown'
    }
    
    # Get MAC and IP
    for mac, node_info in identity_map.items():
        if node_info.get('hostname') == local_hostname:
            local_info.update({
                'wlan_mac': mac,
                'bat_mac': mac,  # Using the same MAC for both since we don't have separate batman MAC
                'ip': node_info.get('ip', 'Unknown')
            })
            break
    
    # Get hash from RNS status (get raw data, not just peers)
    rns_data = read_json_file(RNS_STATUS_PATH, 'rns_status')
    for hash_id, peer_data in rns_data.get('peers', {}).items():
        if peer_data.get('hostname', 'Unknown') == local_hostname:
            # Remove angle brackets from hash
            local_info['hash'] = hash_id.replace('<', '').replace('>', '')
            break
    
    return local_info

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

@app.route('/packet-logs')
def packet_logs():
    return render_template('packet_logs.html', hostname=socket.gethostname())

def read_packet_logs():
    """Read the most recent packet log entries (last 100 lines)"""
    try:
        if not os.path.exists(PACKET_LOG_PATH):
            return []
            
        # Use deque to efficiently get last N lines without loading entire file
        from collections import deque
        
        # Read last 100 lines
        lines = deque(maxlen=100)
        with open(PACKET_LOG_PATH, 'r') as f:
            for line in f:
                lines.append(line)
                
        # Process logs to extract link information
        logs = [line.strip() for line in lines]
        process_link_events(logs)
        
        return logs
    except Exception as e:
        app.logger.error(f"Error reading packet logs: {e}")
        return []

def process_link_events(logs):
    """Process packet logs to extract link events and status"""
    global active_links, link_events
    
    # Keep only the most recent 20 link events
    if len(link_events) > 20:
        link_events = link_events[-20:]
    
    for log in logs:
        # Skip log entries without timestamp
        if not ' - ' in log:
            continue
            
        # Extract timestamp and message
        parts = log.split(' - ', 1)
        if len(parts) < 2:
            continue
            
        timestamp, message = parts
        
        # Process link established events
        if 'LINK_ESTABLISHED' in message:
            # Extract hostname
            if 'from' in message:
                # Incoming link
                hostname_match = re.search(r'from (\w+)', message)
                direction = 'incoming'
            elif 'to' in message:
                # Outgoing link
                hostname_match = re.search(r'to (\w+)', message)
                direction = 'outgoing'
            else:
                hostname_match = None
                direction = 'unknown'
                
            if hostname_match:
                hostname = hostname_match.group(1)
                if hostname != 'unknown':
                    # Update active links
                    active_links[hostname] = {
                        'status': 'active',
                        'established_at': timestamp,
                        'last_activity': timestamp,
                        'direction': direction
                    }
                    
                    # Add to link events
                    link_events.append({
                        'type': 'established',
                        'hostname': hostname,
                        'timestamp': timestamp,
                        'direction': direction
                    })
        
        # Process link closed events
        elif 'LINK_CLOSED' in message:
            # Extract hostname
            hostname_match = re.search(r'with (\w+)', message)
            
            # Extract age and inactive time if available
            age_match = re.search(r'Age: ([^,]+)', message)
            inactive_match = re.search(r'Inactive: ([^)]+)', message)
            
            if hostname_match:
                hostname = hostname_match.group(1)
                if hostname != 'unknown':
                    # Remove from active links
                    if hostname in active_links:
                        active_links.pop(hostname, None)
                    
                    # Add to link events
                    event = {
                        'type': 'closed',
                        'hostname': hostname,
                        'timestamp': timestamp
                    }
                    
                    if age_match:
                        event['age'] = age_match.group(1)
                    
                    if inactive_match:
                        event['inactive'] = inactive_match.group(1)
                        
                    link_events.append(event)
        
        # Process link data events to update last activity
        elif 'LINK_DATA_RECEIVED' in message or 'SENT:' in message:
            # Extract hostname
            if 'LINK_DATA_RECEIVED' in message:
                hostname_match = re.search(r'Source=(\w+)', message)
            else:  # SENT
                hostname_match = re.search(r'to (\w+)', message)
                
            if hostname_match:
                hostname = hostname_match.group(1)
                if hostname != 'unknown' and hostname in active_links:
                    # Update last activity
                    active_links[hostname]['last_activity'] = timestamp

def generate_packet_log_events():
    """Generate SSE events with packet log data"""
    last_size = 0
    while True:
        try:
            current_size = os.path.getsize(PACKET_LOG_PATH) if os.path.exists(PACKET_LOG_PATH) else 0
            if current_size != last_size:
                logs = read_packet_logs()
                last_size = current_size
                yield f"data: {json.dumps({'success': True, 'logs': logs})}\n\n"
            time.sleep(1)
        except Exception as e:
            app.logger.error(f"Error generating packet log events: {e}")
            yield f"data: {json.dumps({'success': False, 'error': str(e)})}\n\n"
            time.sleep(1)

@app.route('/packet-log-events')
def packet_log_events():
    """SSE endpoint for real-time packet log updates"""
    return Response(
        generate_packet_log_events(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )


def get_active_links():
    """Get information about active Reticulum links"""
    # Make sure we have the latest link information
    read_packet_logs()
    
    # Convert active_links to a list for the API
    links = []
    for hostname, link_info in active_links.items():
        links.append({
            'hostname': hostname,
            'status': link_info.get('status', 'unknown'),
            'established_at': link_info.get('established_at', 'unknown'),
            'last_activity': link_info.get('last_activity', 'unknown'),
            'direction': link_info.get('direction', 'unknown')
        })
    
    return links

def get_link_events():
    """Get recent link events (establish/close)"""
    # Make sure we have the latest link information
    read_packet_logs()
    
    return link_events

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
        
        # Get active links and link events
        active_links_data = get_active_links()
        link_events_data = get_link_events()
    except Exception as e:
        app.logger.error(f"Unexpected error processing mesh data: {e}")
        success = False
        error = "An unexpected error occurred"
        nodes = []
        reticulum_peers = {}
        active_links_data = []
        link_events_data = []
    
    return jsonify({
        'success': success,
        'error': error,
        'local_info': local_info,
        'nodes': nodes,
        'reticulum_peers': reticulum_peers,
        'active_links': active_links_data,
        'link_events': link_events_data
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
                'reticulum_peers': process_reticulum_peers(),
                'active_links': get_active_links(),
                'link_events': get_link_events()
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
