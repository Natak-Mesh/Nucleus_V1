from flask import Flask, render_template, Response, jsonify, request
import socket
import subprocess
import json
import time
import os
import threading
import signal
import csv
from collections import defaultdict

app = Flask(__name__)

# WiFi Channel to Frequency Mapping
WIFI_CHANNELS = {
    # 2.4 GHz
    1: 2412, 2: 2417, 3: 2422, 4: 2427, 5: 2432, 6: 2437,
    7: 2442, 8: 2447, 9: 2452, 10: 2457, 11: 2462, 12: 2467, 13: 2472, 14: 2484
}

# Configuration
NODE_TIMEOUT = 30  # Seconds - nodes not seen within this time will be greyed out

# Channel scanning state
scan_state = {
    'status': 'idle',  # idle, running, complete, error
    'progress': 0,
    'duration': 60,
    'results': None,
    'error': None,
    'process': None,
    'start_time': None
}
scan_lock = threading.Lock()

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

def parse_scan_csv(csv_file):
    """Parse airodump-ng CSV output and extract channel data"""
    networks = []
    
    if not os.path.exists(csv_file):
        return networks
    
    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Split by the station data section - we only want AP data
        sections = content.split('\nStation MAC')
        ap_data = sections[0]
        
        lines = ap_data.strip().split('\n')
        if len(lines) < 2:
            return networks
            
        reader = csv.reader(lines)
        header = next(reader, None)
        
        if not header:
            return networks
        
        # Find column indices
        try:
            bssid_idx = header.index('BSSID')
            pwr_idx = header.index(' Power')
            channel_idx = header.index(' channel')
            essid_idx = header.index(' ESSID')
        except ValueError:
            return networks
        
        for row in reader:
            if len(row) > max(bssid_idx, pwr_idx, channel_idx, essid_idx):
                try:
                    bssid = row[bssid_idx].strip()
                    power = int(row[pwr_idx].strip())
                    channel = row[channel_idx].strip()
                    essid = row[essid_idx].strip()
                    
                    # Skip invalid entries
                    if channel == '-1' or channel == '' or power == -1:
                        continue
                    
                    channel = int(channel)
                    
                    # Only analyze 2.4GHz channels (1-14)
                    if 1 <= channel <= 14:
                        networks.append({
                            'bssid': bssid,
                            'channel': channel,
                            'power': power,
                            'essid': essid
                        })
                        
                except (ValueError, IndexError):
                    continue
                    
    except Exception:
        pass
    
    return networks

def analyze_channels(networks):
    """Calculate congestion scores for each channel"""
    channel_data = defaultdict(lambda: {'networks': [], 'score': 0})
    
    # Group networks by channel
    for network in networks:
        channel = network['channel']
        channel_data[channel]['networks'].append(network)
    
    # Calculate scores for channels 1-14
    for channel in range(1, 15):
        networks_on_channel = channel_data[channel]['networks']
        
        if not networks_on_channel:
            channel_data[channel]['score'] = 0
            continue
        
        # Base score: number of networks * 10
        network_count_score = len(networks_on_channel) * 10
        
        # Signal strength penalty
        power_scores = []
        for network in networks_on_channel:
            power = network['power']
            if power > -30:  # Very strong signal
                power_scores.append(20)
            elif power > -50:  # Strong signal
                power_scores.append(15)
            elif power > -70:  # Medium signal
                power_scores.append(10)
            else:  # Weak signal
                power_scores.append(5)
        
        avg_power_score = sum(power_scores) / len(power_scores) if power_scores else 0
        
        # Adjacent channel interference
        adjacent_penalty = 0
        for adj_channel in range(max(1, channel-2), min(15, channel+3)):
            if adj_channel != channel:
                adj_networks = len(channel_data[adj_channel]['networks'])
                if adj_networks > 0:
                    distance = abs(adj_channel - channel)
                    if distance == 1:
                        adjacent_penalty += adj_networks * 5
                    elif distance == 2:
                        adjacent_penalty += adj_networks * 3
        
        total_score = network_count_score + avg_power_score + adjacent_penalty
        channel_data[channel]['score'] = total_score
    
    return channel_data

def run_channel_scan(duration):
    """Run channel scan in background thread"""
    global scan_state
    
    try:
        # Change to channel analysis directory
        scan_dir = '/home/natak/mesh/channel_analysis'
        csv_file = os.path.join(scan_dir, 'scan_output-01.csv')
        
        # Remove old scan files
        subprocess.run(['rm', '-f', os.path.join(scan_dir, 'scan_output*.csv')], 
                      capture_output=True)
        
        # Stop mesh services
        subprocess.run(['sudo', 'systemctl', 'stop', 'mesh-startup.service'], 
                      capture_output=True)
        subprocess.run(['sudo', 'pkill', 'wpa_supplicant'], 
                      capture_output=True)
        time.sleep(2)
        
        # Enable monitor mode
        monitor_result = subprocess.run(['sudo', 'airmon-ng', 'start', 'wlan1'], 
                                      capture_output=True)
        if monitor_result.returncode != 0:
            raise Exception("Failed to enable monitor mode")
        
        # Start airodump scan
        with scan_lock:
            scan_state['status'] = 'running'
            scan_state['start_time'] = time.time()
        
        process = subprocess.Popen([
            'sudo', 'airodump-ng', 'wlan1mon', '--band', 'bg', 
            '-w', os.path.join(scan_dir, 'scan_output'), 
            '--output-format', 'csv'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        with scan_lock:
            scan_state['process'] = process
        
        # Wait for specified duration
        time.sleep(duration)
        
        # Stop scan gracefully
        try:
            process.send_signal(signal.SIGINT)
            process.wait(timeout=5)
        except:
            process.kill()
        
        # Parse results
        time.sleep(1)  # Allow file to be written
        networks = parse_scan_csv(csv_file)
        channel_data = analyze_channels(networks)
        
        # Format results
        results = []
        for channel in range(1, 15):
            data = channel_data[channel]
            network_count = len(data['networks'])
            score = data['score']
            
            # Determine status
            if score == 0:
                status = 'EMPTY'
            elif score < 20:
                status = 'EXCELLENT'
            elif score < 40:
                status = 'GOOD'
            elif score < 60:
                status = 'MODERATE'
            else:
                status = 'CONGESTED'
            
            results.append({
                'channel': channel,
                'network_count': network_count,
                'score': score,
                'status': status,
                'networks': data['networks'][:3]  # Show top 3 networks
            })
        
        # Sort by score (lower is better)
        results.sort(key=lambda x: x['score'])
        
        with scan_lock:
            scan_state['status'] = 'complete'
            scan_state['results'] = results
            scan_state['process'] = None
        
    except Exception as e:
        with scan_lock:
            scan_state['status'] = 'error'
            scan_state['error'] = str(e)
            scan_state['process'] = None
    
    finally:
        # Cleanup - always restore mesh services
        try:
            subprocess.run(['sudo', 'airmon-ng', 'stop', 'wlan1mon'], 
                          capture_output=True)
            subprocess.run(['sudo', 'systemctl', 'start', 'mesh-startup.service'], 
                          capture_output=True)
        except:
            pass



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



@app.route('/api/wifi')
def api_wifi():
    """API endpoint for WiFi page data"""
    return jsonify({
        'hostname': socket.gethostname(),
        'local_mac': get_local_mac(),
        'node_status': read_node_status(),
        'node_timeout': NODE_TIMEOUT
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

@app.route('/api/channel-scan/start', methods=['POST'])
def start_channel_scan():
    """Start channel scan"""
    global scan_state
    
    with scan_lock:
        if scan_state['status'] == 'running':
            return jsonify({'error': 'Scan already in progress'}), 400
    
    try:
        data = request.get_json()
        duration = int(data.get('duration', 60))
        
        # Validate duration
        if duration < 10 or duration > 300:  # 10 seconds to 5 minutes
            return jsonify({'error': 'Duration must be between 10 and 300 seconds'}), 400
        
        # Reset state
        with scan_lock:
            scan_state['status'] = 'starting'
            scan_state['duration'] = duration
            scan_state['results'] = None
            scan_state['error'] = None
            scan_state['progress'] = 0
        
        # Start scan in background thread
        thread = threading.Thread(target=run_channel_scan, args=(duration,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Channel scan started for {duration} seconds',
            'duration': duration
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/channel-scan/status', methods=['GET'])
def get_channel_scan_status():
    """Get channel scan status"""
    with scan_lock:
        status = scan_state['status']
        duration = scan_state['duration']
        start_time = scan_state['start_time']
        error = scan_state['error']
        
        # Calculate progress if running
        progress = 0
        remaining = 0
        if status == 'running' and start_time:
            elapsed = time.time() - start_time
            progress = min(int((elapsed / duration) * 100), 100)
            remaining = max(0, int(duration - elapsed))
    
    return jsonify({
        'status': status,
        'progress': progress,
        'remaining': remaining,
        'duration': duration,
        'error': error
    })

@app.route('/api/channel-scan/results', methods=['GET'])
def get_channel_scan_results():
    """Get channel scan results"""
    with scan_lock:
        if scan_state['status'] != 'complete':
            return jsonify({'error': 'Scan not complete'}), 400
        
        results = scan_state['results']
        
        if not results:
            return jsonify({'error': 'No scan results available'}), 400
        
        # Find best channels (non-overlapping: 1, 6, 11)
        non_overlapping = [1, 6, 11]
        best_channels = []
        
        for result in results:
            if result['channel'] in non_overlapping:
                best_channels.append({
                    'channel': result['channel'],
                    'score': result['score'],
                    'status': result['status'],
                    'network_count': result['network_count'],
                    'recommended': True
                })
        
        # Sort best channels by score
        best_channels.sort(key=lambda x: x['score'])
        
        return jsonify({
            'all_channels': results,
            'best_channels': best_channels[:3],  # Top 3 recommendations
            'total_networks': sum(r['network_count'] for r in results)
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
