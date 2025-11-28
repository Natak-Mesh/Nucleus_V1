# Natak Mesh Web Interface

Simple web interface for monitoring mesh network connections.

## Features
- Real-time mesh node monitoring
- Card-based display showing:
  - Node IPv4 addresses
  - Link quality metrics
  - Connection status (connected/disconnected)
  - Connection duration tracking
- Auto-refresh every 5 seconds
- Dark theme matching Natak branding
- Keeps disconnected nodes visible for 60 seconds

## Requirements
- Python 3
- Flask (`pip3 install flask`)
- Babeld with monitoring interface enabled (port 33123)

## Running the Web Interface

### Development Mode (manual start)
```bash
cd /opt/nucleus/web
python3 app.py
```

Then access the interface at: http://localhost:5000

### Configuration
Edit `/opt/nucleus/web/app.py` to customize:
- `REFRESH_INTERVAL` - Auto-refresh interval in seconds (default: 5)
- `DISCONNECTED_DISPLAY_TIME` - How long to keep disconnected nodes visible in seconds (default: 60)
- `BABELD_PORT` - Babeld monitoring port (default: 33123)

## File Structure
```
/opt/nucleus/web/
├── app.py                 # Flask application
├── templates/
│   └── index.html        # Main dashboard page
├── static/
│   ├── css/
│   │   └── style.css    # Dark theme styles
│   └── images/
│       └── NatakMeshsecondary-overlay.png  # Logo
```

## How It Works

1. **Queries babeld** monitoring interface for neighbor data (IPv6 link-local addresses and metrics)
2. **Queries IPv6 neighbor cache** to map link-local addresses to MAC addresses
3. **Queries IPv4 neighbor cache** to map MAC addresses to IPv4 addresses
4. **Correlates** the data to display nodes with their IPv4 addresses and link quality

## Troubleshooting

**No nodes showing:**
- Verify babeld is running: `sudo systemctl status babeld`
- Check babeld monitoring is enabled: `echo "dump" | nc localhost 33123`
- Verify mesh connections exist: `ip neigh show dev wlan1`

**Web interface won't start:**
- Check Flask is installed: `python3 -c "import flask"`
- Verify port 5000 is available: `sudo netstat -tlnp | grep 5000`
