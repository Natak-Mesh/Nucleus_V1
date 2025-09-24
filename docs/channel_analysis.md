# WiFi Channel Analysis Implementation

## Overview
Add channel analysis functionality to find the clearest WiFi channels for mesh operation. Temporarily disrupts mesh to scan both 2.4GHz and 5GHz bands.

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

# Scan both bands (2.4GHz + 5GHz)
airodump-ng wlan1mon --band abg

# Cleanup
airmon-ng stop wlan1mon
systemctl start mesh-startup.service
```

### Automated Scan (60 seconds)
```bash
timeout 60 airodump-ng wlan1mon --band abg --write /tmp/scan --output-format csv
```

### Band-Specific Options
- `--band bg` - 2.4GHz only
- `--band a` - 5GHz only  
- `--band abg` - Both bands

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
- `/api/channel-scan` - POST to start scan
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
