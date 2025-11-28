#!/usr/bin/env python3
"""
Natak Mesh - Web Interface
Simple Flask app for monitoring mesh network connections
"""

from flask import Flask, render_template, jsonify
import socket
import subprocess
import re
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuration
BABELD_HOST = 'localhost'
BABELD_PORT = 33123
REFRESH_INTERVAL = 5  # seconds
DISCONNECTED_DISPLAY_TIME = 60  # seconds

# Store node history
node_history = {}


def query_babeld():
    """Query babeld monitoring interface"""
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        sock.connect(('::1', BABELD_PORT))
        
        # Read banner (ends with first "ok\n")
        banner = b''
        while b'ok\n' not in banner:
            banner += sock.recv(1024)
        
        # Send dump command
        sock.sendall(b'dump\n')
        
        # Read dump output (ends with second "ok\n")
        data = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            # Look for the final "ok\n" at end of dump
            if data.endswith(b'ok\n'):
                break
        
        sock.close()
        return data.decode('utf-8')
    except Exception as e:
        print(f"Error querying babeld: {e}")
        return ""


def get_ipv6_neighbors():
    """Get IPv6 neighbor cache (link-local to MAC mapping)"""
    try:
        result = subprocess.run(['ip', '-6', 'neigh', 'show', 'dev', 'wlan1'],
                              capture_output=True, text=True)
        neighbors = {}
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            match = re.match(r'(\S+)\s+lladdr\s+(\S+)', line)
            if match:
                ipv6, mac = match.groups()
                neighbors[ipv6] = mac
        return neighbors
    except Exception as e:
        print(f"Error getting IPv6 neighbors: {e}")
        return {}


def get_ipv4_neighbors():
    """Get IPv4 neighbor cache on wlan1 interface"""
    try:
        result = subprocess.run(['ip', 'neigh', 'show', 'dev', 'wlan1'],
                              capture_output=True, text=True)
        neighbors = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            # Parse: 10.20.1.11 dev wlan1 lladdr 00:c0:ca:b7:af:be STALE
            match = re.match(r'(\S+)\s+', line)
            if match:
                ipv4 = match.group(1)
                neighbors.append(ipv4)
        return neighbors
    except Exception as e:
        print(f"Error getting IPv4 neighbors: {e}")
        return []


def parse_babeld_dump(dump_data):
    """Parse babeld dump output for neighbor information"""
    neighbors = []
    for line in dump_data.split('\n'):
        if line.startswith('add neighbour'):
            # Parse: add neighbour <id> address <ipv6> if <interface> reach <reach> ... cost <cost>
            parts = line.split()
            neighbor = {}
            for i, part in enumerate(parts):
                if part == 'address' and i + 1 < len(parts):
                    neighbor['ipv6'] = parts[i + 1]
                elif part == 'cost' and i + 1 < len(parts):
                    neighbor['cost'] = parts[i + 1]
                elif part == 'reach' and i + 1 < len(parts):
                    neighbor['reach'] = parts[i + 1]
            if 'ipv6' in neighbor and 'cost' in neighbor:
                neighbors.append(neighbor)
    return neighbors


def get_mesh_nodes():
    """Get current mesh node status"""
    # Query babeld
    dump_data = query_babeld()
    print(f"DEBUG: Babeld dump data length: {len(dump_data)} bytes")
    print(f"DEBUG: Babeld dump preview: {dump_data[:200] if dump_data else 'EMPTY'}")
    
    babel_neighbors = parse_babeld_dump(dump_data)
    print(f"DEBUG: Found {len(babel_neighbors)} babel neighbors: {babel_neighbors}")
    
    # Get neighbor caches
    ipv6_neighbors = get_ipv6_neighbors()
    print(f"DEBUG: IPv6 neighbors: {ipv6_neighbors}")
    
    ipv4_neighbors = get_ipv4_neighbors()
    print(f"DEBUG: IPv4 neighbors: {ipv4_neighbors}")
    
    # Correlate data - match by interface (wlan1)
    # Since babeld shows neighbors on wlan1 and we have IPv4 neighbors on wlan1,
    # we pair them up (typically 1:1 mapping)
    current_time = datetime.now()
    active_nodes = set()
    nodes = []
    
    # Match babel neighbors to IPv4 addresses on wlan1
    if babel_neighbors and ipv4_neighbors:
        # Pair up babel neighbors with IPv4 addresses
        for i, neighbor in enumerate(babel_neighbors):
            if i < len(ipv4_neighbors):
                ipv4 = ipv4_neighbors[i]
                active_nodes.add(ipv4)
                
                # Track connection time
                if ipv4 not in node_history:
                    node_history[ipv4] = {
                        'first_seen': current_time,
                        'last_seen': current_time,
                        'status': 'connected'
                    }
                else:
                    node_history[ipv4]['last_seen'] = current_time
                    node_history[ipv4]['status'] = 'connected'
                
                # Calculate duration
                duration = current_time - node_history[ipv4]['first_seen']
                duration_str = format_duration(duration)
                
                # Classify cost quality
                cost_val = int(neighbor['cost'])
                if cost_val < 400:
                    cost_quality = 'good'
                elif cost_val < 700:
                    cost_quality = 'fair'
                else:
                    cost_quality = 'poor'
                
                nodes.append({
                    'ipv4': ipv4,
                    'cost': neighbor['cost'],
                    'cost_quality': cost_quality,
                    'status': 'connected',
                    'duration': duration_str,
                    'duration_label': 'Connected for'
                })
    
    # Check for recently disconnected nodes
    for ipv4, info in list(node_history.items()):
        if ipv4 not in active_nodes:
            time_since_disconnect = current_time - info['last_seen']
            if time_since_disconnect.total_seconds() <= DISCONNECTED_DISPLAY_TIME:
                duration_str = format_duration(time_since_disconnect)
                nodes.append({
                    'ipv4': ipv4,
                    'cost': 'N/A',
                    'status': 'disconnected',
                    'duration': duration_str,
                    'duration_label': 'Disconnected'
                })
            else:
                # Remove from history if too old
                del node_history[ipv4]
    
    return nodes


def format_duration(delta):
    """Format timedelta into human-readable string"""
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds}s"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html', 
                         refresh_interval=REFRESH_INTERVAL)


@app.route('/api/nodes')
def api_nodes():
    """API endpoint for mesh node data"""
    nodes = get_mesh_nodes()
    return jsonify({
        'nodes': nodes,
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
