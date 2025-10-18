#!/usr/bin/env python3

#       ..        .....        ...       
#       ....     ......       ....      
#       .......... ...       .....       
#       ........    ..      ......       
#       ......      ..     .......       
#       .....       ...  .........       
#       ....        .....     ....      
#       ...         ....        ..   

#############################################
#        N A T A K   -   Nucleus V1         #
#                                           #
#        2.4 GHz Channel Analyzer           #
#############################################

import csv
import os
import sys
from collections import defaultdict

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color

def print_header():
    print()
    print(f"{BLUE}╔════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║       2.4 GHz Channel Analyzer         ║{NC}")
    print(f"{BLUE}╚════════════════════════════════════════╝{NC}")
    print()

def parse_csv_data(csv_file):
    """Parse airodump-ng CSV output and extract channel data"""
    networks = []
    
    if not os.path.exists(csv_file):
        print(f"{RED}[ERROR]{NC} Scan data file not found: {csv_file}")
        print(f"{YELLOW}[INFO]{NC} Run channel_scan.sh first to generate data.")
        sys.exit(1)
    
    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Split by the station data section (starts with "Station MAC")
        # We only want the AP data (first section)
        sections = content.split('\nStation MAC')
        ap_data = sections[0]
        
        # Parse AP data
        lines = ap_data.strip().split('\n')
        if len(lines) < 2:
            print(f"{YELLOW}[WARNING]{NC} No network data found in CSV file.")
            return networks
            
        reader = csv.reader(lines)
        header = next(reader, None)
        
        if not header:
            print(f"{YELLOW}[WARNING]{NC} Invalid CSV format.")
            return networks
        
        # Find column indices
        try:
            bssid_idx = header.index('BSSID')
            pwr_idx = header.index(' Power')
            channel_idx = header.index(' channel')
            essid_idx = header.index(' ESSID')
        except ValueError as e:
            print(f"{RED}[ERROR]{NC} CSV format error: {e}")
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
                    
    except Exception as e:
        print(f"{RED}[ERROR]{NC} Error reading CSV file: {e}")
        sys.exit(1)
    
    return networks

def calculate_channel_scores(networks):
    """Calculate congestion scores for each channel"""
    channel_data = defaultdict(lambda: {'networks': [], 'score': 0})
    
    # Group networks by channel
    for network in networks:
        channel = network['channel']
        channel_data[channel]['networks'].append(network)
    
    # Calculate scores
    for channel in range(1, 15):  # 2.4GHz channels 1-14
        networks_on_channel = channel_data[channel]['networks']
        
        if not networks_on_channel:
            channel_data[channel]['score'] = 0
            continue
        
        # Base score: number of networks * 10
        network_count_score = len(networks_on_channel) * 10
        
        # Signal strength penalty (stronger signals = worse)
        # Convert power to positive value and scale
        power_scores = []
        for network in networks_on_channel:
            # airodump shows negative dBm values, closer to 0 = stronger
            power = network['power']
            if power < -30:  # Very strong signal
                power_scores.append(20)
            elif power < -50:  # Strong signal
                power_scores.append(15)
            elif power < -70:  # Medium signal
                power_scores.append(10)
            else:  # Weak signal
                power_scores.append(5)
        
        avg_power_score = sum(power_scores) / len(power_scores) if power_scores else 0
        
        # Adjacent channel interference
        # 2.4GHz channels overlap significantly
        adjacent_penalty = 0
        for adj_channel in range(max(1, channel-2), min(15, channel+3)):
            if adj_channel != channel:
                adj_networks = len(channel_data[adj_channel]['networks'])
                if adj_networks > 0:
                    # Closer channels have more interference
                    distance = abs(adj_channel - channel)
                    if distance == 1:
                        adjacent_penalty += adj_networks * 5
                    elif distance == 2:
                        adjacent_penalty += adj_networks * 3
        
        total_score = network_count_score + avg_power_score + adjacent_penalty
        channel_data[channel]['score'] = total_score
    
    return channel_data

def display_analysis(channel_data):
    """Display channel analysis results"""
    print(f"{CYAN}═══════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}                    CHANNEL ANALYSIS{NC}")
    print(f"{CYAN}═══════════════════════════════════════════════════════════{NC}")
    
    # Sort channels by score (lower is better)
    sorted_channels = sorted(
        [(ch, data) for ch, data in channel_data.items() if 1 <= ch <= 14],
        key=lambda x: x[1]['score']
    )
    
    print(f"\n{BLUE}Channel Congestion Summary:{NC}")
    print(f"{'Channel':<8} {'Networks':<10} {'Score':<8} {'Status':<12} {'Bar':<20}")
    print("─" * 65)
    
    max_score = max(data['score'] for _, data in sorted_channels) if sorted_channels else 1
    
    for channel, data in sorted_channels:
        network_count = len(data['networks'])
        score = data['score']
        
        # Create visual bar
        if max_score > 0:
            bar_length = int((score / max_score) * 15)
        else:
            bar_length = 0
        bar = "█" * bar_length + "░" * (15 - bar_length)
        
        # Determine status and color
        if score == 0:
            status = "EMPTY"
            color = GREEN
        elif score < 20:
            status = "EXCELLENT"
            color = GREEN
        elif score < 40:
            status = "GOOD"
            color = CYAN
        elif score < 60:
            status = "MODERATE"
            color = YELLOW
        else:
            status = "CONGESTED"
            color = RED
        
        print(f"{channel:<8} {network_count:<10} {score:<8.0f} {color}{status:<12}{NC} {bar}")
    
    # Recommendations
    print(f"\n{GREEN}━━━ RECOMMENDATIONS ━━━{NC}")
    
    # Best channels (non-overlapping: 1, 6, 11)
    non_overlapping = [1, 6, 11]
    best_non_overlapping = sorted(
        [(ch, channel_data[ch]['score']) for ch in non_overlapping],
        key=lambda x: x[1]
    )
    
    print(f"\n{BLUE}Non-overlapping channels (1, 6, 11) - RECOMMENDED:{NC}")
    for i, (channel, score) in enumerate(best_non_overlapping, 1):
        networks = len(channel_data[channel]['networks'])
        if score == 0:
            status = f"{GREEN}EMPTY - BEST CHOICE{NC}"
        elif score < 30:
            status = f"{GREEN}LOW CONGESTION{NC}"
        elif score < 60:
            status = f"{YELLOW}MODERATE CONGESTION{NC}"
        else:
            status = f"{RED}HIGH CONGESTION{NC}"
        
        print(f"  {i}. Channel {channel}: {networks} networks, score {score:.0f} - {status}")
    
    # Overall best channel
    if sorted_channels:
        best_channel, best_data = sorted_channels[0]
        print(f"\n{GREEN}🏆 BEST OVERALL: Channel {best_channel}{NC}")
        print(f"   {len(best_data['networks'])} networks, congestion score: {best_data['score']:.0f}")
        
        if best_data['networks']:
            print(f"\n{BLUE}Networks on Channel {best_channel}:{NC}")
            for network in best_data['networks'][:5]:  # Show up to 5 networks
                essid = network['essid'] if network['essid'] else "<hidden>"
                print(f"   • {network['bssid']} ({network['power']} dBm) - {essid}")
            if len(best_data['networks']) > 5:
                print(f"   ... and {len(best_data['networks']) - 5} more")

def main():
    print_header()
    
    # Look for CSV file
    csv_file = 'scan_output-01.csv'
    
    print(f"{BLUE}[INFO]{NC} Analyzing scan data from {csv_file}...")
    
    # Parse CSV data
    networks = parse_csv_data(csv_file)
    
    if not networks:
        print(f"{YELLOW}[WARNING]{NC} No valid network data found.")
        print(f"{BLUE}[INFO]{NC} Make sure you ran channel_scan.sh and let it collect data.")
        sys.exit(0)
    
    print(f"{GREEN}[SUCCESS]{NC} Found {len(networks)} networks across 2.4GHz channels.")
    
    # Calculate channel scores
    channel_data = calculate_channel_scores(networks)
    
    # Display analysis
    display_analysis(channel_data)
    
    print(f"\n{CYAN}═══════════════════════════════════════════════════════════{NC}")
    print(f"{BLUE}[INFO]{NC} Analysis complete. Choose channels with lowest congestion.")
    print(f"{BLUE}[TIP]{NC} Stick to channels 1, 6, or 11 for best mesh performance.")
    print()

if __name__ == "__main__":
    main()
