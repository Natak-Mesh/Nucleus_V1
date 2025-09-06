from flask import Flask, render_template, Response, jsonify, request
import socket
import subprocess
import json
import time
import os

app = Flask(__name__)

# WiFi Channel to Frequency Mapping
WIFI_CHANNELS = {
    # 2.4 GHz
    1: 2412, 2: 2417, 3: 2422, 4: 2427, 5: 2432, 6: 2437,
    7: 2442, 8: 2447, 9: 2452, 10: 2457, 11: 2462, 12: 2467, 13: 2472, 14: 2484,
    
    # 5 GHz (common channels)
    36: 5180, 40: 5200, 44: 5220, 48: 5240,
    52: 5260, 56: 5280, 60: 5300, 64: 5320,
    100: 5500, 104: 5520, 108: 5540, 112: 5560,
    116: 5580, 120: 5600, 124: 5620, 128: 5640,
    132: 5660, 136: 5680, 140: 5700, 144: 5720,
    149: 5745, 153: 5765, 157: 5785, 161: 5805, 165: 5825
}

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

def get_current_channel():
    """Read current channel from batmesh.sh"""
    try:
        with open('/home/natak/mesh/batmesh.sh', 'r') as f:
            for line in f:
                if line.startswith('MESH_CHANNEL='):
                    return int(line.split('=')[1].strip())
    except:
        return 11  # default

def update_batmesh_channel(new_channel):
    """Update channel in batmesh.sh using sed"""
    cmd = f'sed -i "s/^MESH_CHANNEL=.*/MESH_CHANNEL={new_channel}/" /home/natak/mesh/batmesh.sh'
    return subprocess.run(cmd, shell=True, capture_output=True)

def update_wpa_supplicant_frequency(new_frequency):
    """Update frequency in wpa_supplicant config using sed"""
    cmd = f'sed -i "s/frequency=.*/frequency={new_frequency}/" /etc/wpa_supplicant/wpa_supplicant-wlan1-encrypt.conf'
    return subprocess.run(cmd, shell=True, capture_output=True)

def reboot_system():
    """Reboot the system to apply changes"""
    return subprocess.run(['sudo', 'reboot'], capture_output=True)

def get_current_ip():
    """Read current IP from br0.network"""
    try:
        with open('/etc/systemd/network/br0.network', 'r') as f:
            for line in f:
                if line.startswith('Address='):
                    # Extract IP without subnet mask
                    return line.split('=')[1].strip().split('/')[0]
    except:
        return "10.20.1.2"  # default

def update_br0_ip(new_ip):
    """Update IP in br0.network using sed"""
    cmd = f'sed -i "s/^Address=.*/Address={new_ip}\/24/" /etc/systemd/network/br0.network'
    return subprocess.run(cmd, shell=True, capture_output=True)



@app.route('/')
def wifi_page():
    """Default WiFi page showing node status"""
    node_status = read_node_status()
    return render_template('wifi.html', 
                         hostname=socket.gethostname(),
                         local_mac=get_local_mac(),
                         node_status=node_status,
                         node_timeout=NODE_TIMEOUT)

@app.route('/management')
def management_page():
    """Management page for mesh configuration"""
    current_channel = get_current_channel()
    current_frequency = WIFI_CHANNELS.get(current_channel, 2462)
    current_ip = get_current_ip()
    return render_template('management.html', 
                         hostname=socket.gethostname(),
                         local_mac=get_local_mac(),
                         current_channel=current_channel,
                         current_frequency=current_frequency,
                         current_ip=current_ip,
                         available_channels=list(WIFI_CHANNELS.keys()))


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

@app.route('/api/mesh-config', methods=['GET'])
def get_mesh_config():
    """Get current mesh configuration"""
    current_channel = get_current_channel()
    current_frequency = WIFI_CHANNELS.get(current_channel, 2462)
    
    return jsonify({
        'current_channel': current_channel,
        'current_frequency': current_frequency,
        'available_channels': list(WIFI_CHANNELS.keys())
    })

@app.route('/api/node-ip', methods=['GET'])
def get_node_ip():
    """Get current node IP configuration"""
    current_ip = get_current_ip()
    
    return jsonify({
        'current_ip': current_ip
    })

@app.route('/api/reboot', methods=['POST'])
def reboot_node():
    """Reboot the node"""
    try:
        reboot_result = reboot_system()
        
        if reboot_result.returncode != 0:
            return jsonify({'error': 'Failed to reboot system'}), 500
            
        return jsonify({
            'success': True,
            'message': 'System is rebooting...'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/node-ip', methods=['POST'])
def set_node_ip():
    """Change node IP address"""
    try:
        data = request.get_json()
        new_ip = data.get('ip')
        
        # Basic IP validation
        ip_parts = new_ip.split('.')
        if len(ip_parts) != 4:
            return jsonify({'error': 'Invalid IP format'}), 400
            
        for part in ip_parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    return jsonify({'error': 'Invalid IP format'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid IP format'}), 400
        
        # Update IP in br0.network
        result = update_br0_ip(new_ip)
        
        if result.returncode != 0:
            return jsonify({'error': 'Failed to update IP address'}), 500
            
        return jsonify({
            'success': True,
            'ip': new_ip,
            'message': 'IP address updated successfully.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mesh-config', methods=['POST'])
def set_mesh_config():
    """Change mesh channel"""
    try:
        data = request.get_json()
        new_channel = int(data.get('channel'))
        
        # Validate channel
        if new_channel not in WIFI_CHANNELS:
            return jsonify({'error': 'Invalid channel'}), 400
            
        new_frequency = WIFI_CHANNELS[new_channel]
        
        # Update both config files
        batmesh_result = update_batmesh_channel(new_channel)
        wpa_result = update_wpa_supplicant_frequency(new_frequency)
        
        if batmesh_result.returncode != 0 or wpa_result.returncode != 0:
            return jsonify({'error': 'Failed to update configuration'}), 500
            
        return jsonify({
            'success': True,
            'channel': new_channel,
            'frequency': new_frequency,
            'message': 'Channel changed successfully. Node must be rebooted to apply changes.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
