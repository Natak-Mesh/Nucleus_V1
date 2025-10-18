# Channel Analysis Tools

Scan and analyze 2.4 GHz Wi-Fi channel congestion for optimal mesh network placement.

## Web Interface (Recommended)

Access channel analysis through the mesh management web interface:

1. Navigate to **Management** page in web UI
2. Go to **Channel Analysis** section
3. Select scan duration (30/60/90 seconds)
4. Click **Start Channel Scan**
5. View real-time progress with countdown
6. Review recommendations and apply optimal channel with one click

**Features:**
- Automatic mesh service management (stops/restarts automatically)
- Real-time progress tracking
- Visual congestion indicators
- One-click channel application
- No CLI interaction required

## CLI Usage (Legacy)

For manual operation:

```bash
# Run scan (press Ctrl+C when done)
./channel_scan.sh

# Analyze results
./analyze_channels.py
```

## Output

The analyzer shows:
- **Channel scores**: Lower = better (network count + signal strength + interference)
- **Visual bars**: Congestion levels  
- **Recommendations**: Prioritizes non-overlapping channels (1, 6, 11)
- **Best choice**: Lowest congestion channel for mesh deployment

## Limitations

**Only detects standard 802.11 access points.** Does not detect:
- Mesh networks (batman-adv, 802.11s, etc.)
- Bluetooth devices
- RF jammers or interference sources
- Non-WiFi 2.4GHz devices (microwave ovens, etc.)

Results show Wi-Fi AP congestion but may not reflect total RF environment. Consider other interference sources when selecting channels.

Scan data is saved to `scan_output-01.csv` and overwritten on each scan.
