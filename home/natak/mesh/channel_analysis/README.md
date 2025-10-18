# Channel Analysis Tools

Scan and analyze 2.4 GHz Wi-Fi channel congestion for optimal mesh network placement.

## Usage

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

Scan data is saved to `scan_output-01.csv` and overwritten on each scan.
