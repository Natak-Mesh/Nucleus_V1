# WiFi Channel Change Implementation Plan

## Overview
Add functionality to the Natak Mesh web application to allow users to change the mesh WiFi channel through the web interface. This requires updating both the batmesh.sh script and wpa_supplicant configuration, then restarting the mesh services.

## Current System Analysis

### Files Involved
- **batmesh.sh**: `/home/natak/mesh/batmesh.sh` - Contains `MESH_CHANNEL=11` variable
- **wpa_supplicant config**: `/etc/wpa_supplicant/wpa_supplicant-wlan1-encrypt.conf` - Contains `frequency=2462` (channel 11)
- **Flask app**: `/home/natak/mesh_monitor/app.py` - Web application backend
- **WiFi template**: `/home/natak/mesh_monitor/templates/wifi.html` - Current WiFi monitoring page

### Current Channel Configuration
- Channel 11 (2462 MHz) is currently configured
- batmesh.sh uses: `iw dev wlan1 set channel $MESH_CHANNEL`
- wpa_supplicant uses: `frequency=2462`

## Implementation Plan

### 1. Backend Changes (Flask App)

#### Add Channel-to-Frequency Mapping
```python
# Add to app.py
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
```

#### Add Helper Functions
```python
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
    return subprocess.run(['sudo'] + cmd.split(), capture_output=True)

def restart_mesh_services():
    """Restart mesh services to apply changes"""
    return subprocess.run(['sudo', 'systemctl', 'restart', 'mesh-startup.service'], capture_output=True)
```

#### Add API Endpoints
```python
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
            
        # Restart mesh services
        restart_result = restart_mesh_services()
        
        if restart_result.returncode != 0:
            return jsonify({'error': 'Failed to restart mesh services'}), 500
            
        return jsonify({
            'success': True,
            'channel': new_channel,
            'frequency': new_frequency,
            'message': 'Channel changed successfully. Mesh is restarting.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 2. Frontend Changes (HTML Template)

#### Add Channel Configuration Section to wifi.html
```html
<!-- Add after existing sections -->
<div class="section">
    <h2>Mesh Configuration</h2>
    <div class="config-controls">
        <div class="current-config">
            <strong>Current Channel:</strong> <span id="current-channel">11</span> 
            (<span id="current-frequency">2462</span> MHz)
        </div>
        
        <div class="channel-selector">
            <label for="channel-select">Change Channel:</label>
            <select id="channel-select">
                <!-- Populated by JavaScript -->
            </select>
            <button id="apply-channel" onclick="changeChannel()">Apply Channel</button>
        </div>
        
        <div id="config-status" class="status-message"></div>
    </div>
</div>
```

#### Add CSS Styles
```css
.config-controls {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.current-config {
    font-size: 16px;
    padding: 8px;
    background-color: var(--background-color);
    border-radius: 4px;
}

.channel-selector {
    display: flex;
    align-items: center;
    gap: 12px;
}

#channel-select {
    background-color: var(--background-color);
    color: var(--text-color);
    border: 1px solid #444;
    padding: 8px;
    border-radius: 4px;
}

#apply-channel {
    background-color: #4caf50;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
}

#apply-channel:hover {
    background-color: #45a049;
}

#apply-channel:disabled {
    background-color: #666;
    cursor: not-allowed;
}

.status-message {
    padding: 8px;
    border-radius: 4px;
    display: none;
}

.status-success {
    background-color: #4caf50;
    color: white;
}

.status-error {
    background-color: #f44336;
    color: white;
}
```

#### Add JavaScript Functions
```javascript
// Channel-to-frequency mapping (same as backend)
const WIFI_CHANNELS = {
    1: 2412, 2: 2417, 3: 2422, 4: 2427, 5: 2432, 6: 2437,
    7: 2442, 8: 2447, 9: 2452, 10: 2457, 11: 2462, 12: 2467, 13: 2472, 14: 2484,
    36: 5180, 40: 5200, 44: 5220, 48: 5240,
    52: 5260, 56: 5280, 60: 5300, 64: 5320,
    100: 5500, 104: 5520, 108: 5540, 112: 5560,
    116: 5580, 120: 5600, 124: 5620, 128: 5640,
    132: 5660, 136: 5680, 140: 5700, 144: 5720,
    149: 5745, 153: 5765, 157: 5785, 161: 5805, 165: 5825
};

function loadMeshConfig() {
    fetch('/api/mesh-config')
        .then(response => response.json())
        .then(data => {
            // Update current channel display
            document.getElementById('current-channel').textContent = data.current_channel;
            document.getElementById('current-frequency').textContent = data.current_frequency;
            
            // Populate channel selector
            const select = document.getElementById('channel-select');
            select.innerHTML = '';
            
            // Group channels by band
            const channels_24 = data.available_channels.filter(ch => ch <= 14);
            const channels_5 = data.available_channels.filter(ch => ch > 14);
            
            // Add 2.4GHz channels
            if (channels_24.length > 0) {
                const group24 = document.createElement('optgroup');
                group24.label = '2.4 GHz';
                channels_24.forEach(channel => {
                    const option = document.createElement('option');
                    option.value = channel;
                    option.textContent = `Channel ${channel} (${WIFI_CHANNELS[channel]} MHz)`;
                    if (channel === data.current_channel) option.selected = true;
                    group24.appendChild(option);
                });
                select.appendChild(group24);
            }
            
            // Add 5GHz channels
            if (channels_5.length > 0) {
                const group5 = document.createElement('optgroup');
                group5.label = '5 GHz';
                channels_5.forEach(channel => {
                    const option = document.createElement('option');
                    option.value = channel;
                    option.textContent = `Channel ${channel} (${WIFI_CHANNELS[channel]} MHz)`;
                    if (channel === data.current_channel) option.selected = true;
                    group5.appendChild(option);
                });
                select.appendChild(group5);
            }
        })
        .catch(error => {
            console.error('Failed to load mesh config:', error);
            showStatus('Failed to load current configuration', 'error');
        });
}

function changeChannel() {
    const selectedChannel = parseInt(document.getElementById('channel-select').value);
    const currentChannel = parseInt(document.getElementById('current-channel').textContent);
    
    if (selectedChannel === currentChannel) {
        showStatus('Channel is already set to ' + selectedChannel, 'error');
        return;
    }
    
    if (!confirm(`Change mesh channel to ${selectedChannel}? This will restart the mesh and temporarily disconnect all nodes.`)) {
        return;
    }
    
    // Disable button during operation
    const button = document.getElementById('apply-channel');
    button.disabled = true;
    button.textContent = 'Applying...';
    
    showStatus('Changing channel and restarting mesh...', 'info');
    
    fetch('/api/mesh-config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            channel: selectedChannel
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showStatus(data.message, 'success');
            // Reload config after a delay to show new channel
            setTimeout(loadMeshConfig, 3000);
        } else {
            showStatus(data.error || 'Failed to change channel', 'error');
        }
    })
    .catch(error => {
        console.error('Channel change failed:', error);
        showStatus('Failed to change channel', 'error');
    })
    .finally(() => {
        // Re-enable button
        button.disabled = false;
        button.textContent = 'Apply Channel';
    });
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('config-status');
    statusDiv.textContent = message;
    statusDiv.className = `status-message status-${type}`;
    statusDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds for non-error messages
    if (type !== 'error') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

// Load mesh config when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadMeshConfig();
    // Also load it as part of the existing update cycle
    // Modify existing updateData function to also call loadMeshConfig periodically
});
```

### 3. Security Considerations

#### Sudo Requirements
The web application needs sudo privileges to:
- Modify `/etc/wpa_supplicant/wpa_supplicant-wlan1-encrypt.conf`
- Restart `mesh-startup.service`

#### Sudoers Configuration
Add to `/etc/sudoers.d/mesh-monitor`:
```
www-data ALL=(ALL) NOPASSWD: /bin/sed -i s/frequency=.*/frequency=*/ /etc/wpa_supplicant/wpa_supplicant-wlan1-encrypt.conf
www-data ALL=(ALL) NOPASSWD: /bin/systemctl restart mesh-startup.service
```

### 4. Error Handling

#### Validation
- Validate channel numbers against WIFI_CHANNELS dict
- Check file permissions before attempting modifications
- Verify sed commands completed successfully
- Monitor service restart status

#### User Feedback
- Show current channel and frequency
- Confirm channel changes with user
- Display progress during mesh restart
- Show error messages for failed operations
- Auto-refresh configuration after successful changes

### 5. Testing Plan

#### Manual Testing
1. Load web page and verify current channel display
2. Select different channel and apply
3. Verify both config files are updated correctly
4. Confirm mesh services restart
5. Check that mesh reconnects on new channel
6. Test with both 2.4GHz and 5GHz channels
7. Test error conditions (invalid channels, permission errors)

#### Verification Commands
```bash
# Check current channel in batmesh.sh
grep "MESH_CHANNEL=" /home/natak/mesh/batmesh.sh

# Check current frequency in wpa_supplicant
grep "frequency=" /etc/wpa_supplicant/wpa_supplicant-wlan1-encrypt.conf

# Check mesh service status
systemctl status mesh-startup.service

# Monitor mesh interface
iw dev wlan1 info
```

### 6. Implementation Steps

1. **Update Flask app** - Add channel mapping, helper functions, and API endpoints
2. **Update HTML template** - Add configuration section with channel selector
3. **Add CSS styling** - Style the new configuration controls
4. **Add JavaScript** - Implement channel changing functionality
5. **Configure sudo permissions** - Allow web app to modify configs and restart services
6. **Test functionality** - Verify channel changes work correctly
7. **Document usage** - Update user documentation

### 7. Files to Modify

#### `/home/natak/mesh_monitor/app.py`
- Add WIFI_CHANNELS dictionary
- Add helper functions for config management
- Add /api/mesh-config GET and POST endpoints
- Import request module for POST data

#### `/home/natak/mesh_monitor/templates/wifi.html`
- Add mesh configuration section
- Add CSS styles for new controls
- Add JavaScript functions for channel management
- Integrate with existing update cycle

#### `/etc/sudoers.d/mesh-monitor` (new file)
- Add sudo permissions for config file modifications
- Add sudo permissions for service restart

### 8. Command Reference

#### Sed Commands Used
```bash
# Update batmesh.sh channel
sed -i "s/^MESH_CHANNEL=.*/MESH_CHANNEL=$new_channel/" /home/natak/mesh/batmesh.sh

# Update wpa_supplicant frequency  
sed -i "s/frequency=.*/frequency=$new_frequency/" /etc/wpa_supplicant/wpa_supplicant-wlan1-encrypt.conf
```

#### Service Management
```bash
# Restart mesh services
sudo systemctl restart mesh-startup.service

# Check service status
systemctl status mesh-startup.service
```

This implementation provides a complete web-based interface for changing WiFi mesh channels while maintaining system security and providing proper user feedback.
