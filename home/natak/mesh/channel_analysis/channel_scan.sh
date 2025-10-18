#!/bin/bash

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
#           2.4 GHz Channel Scanner         #
#############################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Run as regular user."
   exit 1
fi

# Check if aircrack-ng is installed
if ! command -v airodump-ng &> /dev/null; then
    print_error "aircrack-ng not installed. Install with: sudo apt install aircrack-ng"
    exit 1
fi

# Check if wlan1 exists
if ! ip link show wlan1 &> /dev/null; then
    print_error "Interface wlan1 not found!"
    exit 1
fi

echo
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        2.4 GHz Channel Scanner         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo

# Get scan duration from user
while true; do
    read -p "Enter scan duration in seconds (default: 60): " SCAN_TIME
    SCAN_TIME=${SCAN_TIME:-60}
    
    if [[ "$SCAN_TIME" =~ ^[0-9]+$ ]] && [ "$SCAN_TIME" -gt 0 ]; then
        break
    else
        print_error "Please enter a valid positive number."
    fi
done

print_status "Starting 2.4 GHz channel scan for ${SCAN_TIME} seconds..."
print_warning "This will temporarily disrupt mesh networking!"
echo

# Confirmation
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Scan cancelled."
    exit 0
fi

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    sudo airmon-ng stop wlan1mon &>/dev/null
    sudo systemctl start mesh-startup.service &>/dev/null
    print_success "Cleanup complete."
}

# Set trap to cleanup on script exit
trap cleanup EXIT

echo "═══════════════════════════════════════════════════════════"
print_status "Step 1/4: Removing old scan data..."
rm -f scan_output*.csv &>/dev/null
print_success "Old scan data cleared."

print_status "Step 2/4: Stopping mesh services..."
sudo systemctl stop mesh-startup.service
sudo pkill wpa_supplicant &>/dev/null
sleep 2
print_success "Mesh services stopped."

print_status "Step 3/4: Enabling monitor mode on wlan1..."
if sudo airmon-ng start wlan1 &>/dev/null; then
    print_success "Monitor mode enabled (wlan1mon)."
else
    print_error "Failed to enable monitor mode!"
    exit 1
fi

print_status "Step 4/4: Scanning 2.4 GHz channels..."
echo "Results will display in real-time and save to CSV. Press Ctrl+C to stop scan."
echo
echo "═══════════════════════════════════════════════════════════"
sudo airodump-ng wlan1mon --band bg -w scan_output --output-format csv
echo "═══════════════════════════════════════════════════════════"

print_status "Step 5/5: Cleaning up and restarting mesh..."
sudo airmon-ng stop wlan1mon &>/dev/null
sudo systemctl start mesh-startup.service
sleep 3
print_success "Mesh services restarted."

echo
print_success "Channel scan complete! Mesh networking restored."
print_status "Choose channels with fewer networks and weaker signals for best performance."
