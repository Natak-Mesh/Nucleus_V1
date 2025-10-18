# WiFi Channel Analysis Implementation

## Overview
Add channel analysis functionality to find the clearest WiFi channels for mesh operation. Temporarily disrupts mesh to scan 2.4GHz band (hardware limited to 2.4GHz only).

## Required Package
```bash
apt install aircrack-ng
```

## Commands

### Basic Process
```bash
# Stop mesh
systemctl stop mesh-startup.service
pkill wpa_supplicant

# Start monitor mode
airmon-ng start wlan1

# Scan 2.4GHz band
airodump-ng wlan1mon --band bg

# Cleanup
airmon-ng stop wlan1mon
systemctl start mesh-startup.service
```

### Automated Scan (60 seconds)
```bash
timeout 60 airodump-ng wlan1mon --band bg --write /tmp/scan --output-format csv
```

## Manual 2.4 GHz Channel Scan

### Interactive Terminal Scan
```bash
# Set custom scan time (in seconds)
SCAN_TIME=60

# Stop mesh services
sudo systemctl stop mesh-startup.service
sudo pkill wpa_supplicant

# Enable monitor mode
sudo airmon-ng start wlan1

# Run scan with custom duration (displays results in real-time)
timeout $SCAN_TIME airodump-ng wlan1mon --band bg

# Cleanup and restore mesh
sudo airmon-ng stop wlan1mon
sudo systemctl start mesh-startup.service
```

### One-liner with Custom Scan Time
```bash
# Replace 120 with desired scan time in seconds
sudo systemctl stop mesh-startup.service && sudo pkill wpa_supplicant && sudo airmon-ng start wlan1 && timeout 120 airodump-ng wlan1mon --band bg && sudo airmon-ng stop wlan1mon && sudo systemctl start mesh-startup.service
```

### Save Scan Results to File
```bash
# Set scan duration and output file
SCAN_TIME=60
OUTPUT_FILE="/tmp/channel_scan_$(date +%Y%m%d_%H%M%S)"

sudo systemctl stop mesh-startup.service
sudo pkill wpa_supplicant
sudo airmon-ng start wlan1
timeout $SCAN_TIME airodump-ng wlan1mon --band bg --write $OUTPUT_FILE --output-format csv
sudo airmon-ng stop wlan1mon
sudo systemctl start mesh-startup.service

# View results
cat ${OUTPUT_FILE}-01.csv
```

## Reading Results

### Key Columns
- **CH** - Channel number
- **#Data** - Total packets (lower = less traffic)
- **#/s** - Packets per second (lower = less active)
- **PWR** - Signal strength (more negative = weaker/distant)

### Best Channel Criteria
1. Fewer networks per channel
2. Lower data packet counts
3. Lower real-time activity (#/s)
4. Weaker signal strengths (distant interference)

## Web Integration Method

### Backend API Endpoint
- `/api/channel-scan` - POST to start scan (2.4GHz only)
- Returns JSON with channel data sorted by interference level
- Handles mesh service stop/start automatically

### Frontend
- "Scan Channels" button with progress indicator
- Results table showing channels ranked by interference
- "Apply Best Channel" button to auto-switch

### Process Flow
1. User clicks "Scan Channels"
2. Backend stops mesh services
3. Runs airodump-ng for specified duration
4. Parses CSV output to rank channels
5. Restores mesh services
6. Returns sorted channel list to frontend

## Integration Points
- Add route to existing Flask app
- Add page link to navigation
- Reuse existing channel-changing functionality
- Parse airodump CSV output for channel scoring
