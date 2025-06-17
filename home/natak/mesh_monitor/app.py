from flask import Flask, render_template, Response, jsonify
import socket
import subprocess
import json
import time
import os

app = Flask(__name__)

# Configuration
NODE_TIMEOUT = 30  # Seconds - nodes not seen within this time will be greyed out

def get_local_mac():
    """Get local MAC from wlan1 interface"""
    try:
        result = subprocess.run(['cat', '/sys/class/net/wlan1/address'], 
                              capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except:
        return "unknown"

def read_node_status():
    try:
        with open('/home/natak/mesh/ogm_monitor/node_status.json', 'r') as f:
            data = json.load(f)
            return data.get('nodes', {})
    except Exception as e:
        print(f"Error reading node_status.json: {e}")
        return {}



@app.route('/')
def wifi_page():
    """Default WiFi page showing node status"""
    node_status = read_node_status()
    return render_template('wifi.html', 
                         hostname=socket.gethostname(),
                         local_mac=get_local_mac(),
                         node_status=node_status,
                         node_timeout=NODE_TIMEOUT)


def parse_log_line(line):
    try:
        # Extract timestamp and message
        parts = line.split(" - ", 1)
        if len(parts) != 2:
            return None
            
        timestamp = parts[0].split()[1]  # Get HH:MM:SS
        message = parts[1].strip()
        
        # Determine message type
        msg_type = "default"
        if "UDP RECEIVE:" in message:
            msg_type = "udp"
        elif "ATAK to LoRa:" in message:
            msg_type = "atak-to-lora"
        elif "LoRa to ATAK:" in message:
            msg_type = "lora-to-atak"
        elif "Received packet" in message:
            msg_type = "received"
        elif "delivered to" in message:
            msg_type = "delivered"
        elif "All nodes received" in message:
            msg_type = "complete"
        elif "Retrying packet" in message:
            msg_type = "retry"
            
        return {
            'time': timestamp,
            'message': message,
            'type': msg_type
        }
    except Exception:
        return None

def read_packet_logs():
    try:
        with open('/var/log/reticulum/packet_logs.log', 'r') as f:
            lines = f.readlines()
            logs = []
            for line in lines:
                parsed = parse_log_line(line)
                # Only add logs that aren't of the types we want to filter out
                if parsed and parsed['type'] not in ['udp', 'atak-to-lora', 'lora-to-atak']:
                    logs.append(parsed)
            return logs
    except Exception as e:
        print(f"Error reading packet_logs.log: {e}")
        return []

@app.route('/packet-logs')
def packet_logs():
    logs = read_packet_logs()
    return render_template('packet_logs.html', 
                         hostname=socket.gethostname(),
                         logs=logs)

@app.route('/api/wifi')
def api_wifi():
    """API endpoint for WiFi page data"""
    return jsonify({
        'hostname': socket.gethostname(),
        'local_mac': get_local_mac(),
        'node_status': read_node_status(),
        'node_timeout': NODE_TIMEOUT
    })


@app.route('/api/packet-logs')
def api_packet_logs():
    return jsonify({
        'hostname': socket.gethostname(),
        'logs': read_packet_logs()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
