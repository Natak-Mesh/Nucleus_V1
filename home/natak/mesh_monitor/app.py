from flask import Flask, render_template, Response
import socket
import subprocess
import json
import time

app = Flask(__name__)

def read_node_status():
    try:
        with open('/home/natak/reticulum_mesh/ogm_monitor/node_status.json', 'r') as f:
            data = json.load(f)
            return data.get('nodes', {})
    except Exception as e:
        print(f"Error reading node_status.json: {e}")
        return {}

def read_peer_discovery():
    try:
        with open('/home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation/peer_discovery.json', 'r') as f:
            data = json.load(f)
            current_time = int(time.time())
            peers = data.get('peers', {})
            # Add current_time to each peer for calculating "seconds ago"
            for peer in peers.values():
                peer['current_time'] = current_time
            return peers
    except Exception as e:
        print(f"Error reading peer_discovery.json: {e}")
        return {}

@app.route('/')
def home():
    node_status = read_node_status()
    peer_discovery = read_peer_discovery()
    return render_template('index.html', 
                         hostname=socket.gethostname(),
                         node_status=node_status,
                         peer_discovery=peer_discovery)

@app.route('/packet-logs')
def packet_logs():
    return render_template('packet_logs.html', hostname=socket.gethostname())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
