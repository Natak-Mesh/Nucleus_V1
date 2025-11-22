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
#        N A T A K   -   Nucleus OS v2.0    #
#                                           #
#           Mesh Networking Radio           #
#############################################


# Source configuration
source /etc/nucleus/mesh.conf

# Calculate frequency from channel (2.4GHz)
MESH_FREQ=$((2407 + ($MESH_CHANNEL * 5)))

# Set interfaces to not be managed by NetworkManager
nmcli device set eth0 managed no
nmcli device set wlan1 managed no
nmcli device set br0 managed no

# Configure mesh interface
ifconfig wlan1 down
iw reg set "US"
iw dev wlan1 set type managed
iw dev wlan1 set 4addr on
iw dev wlan1 set type mesh
iw dev wlan1 set meshid $MESH_NAME
iw dev wlan1 set channel $MESH_CHANNEL HT20
ifconfig wlan1 up

# Generate hostapd config
cat > /etc/hostapd/hostapd.conf <<EOF
interface=wlan0
ssid=$AP_NAME
hw_mode=g
channel=$AP_CHANNEL
auth_algs=1
wmm_enabled=1
wpa=2
wpa_passphrase=$AP_PASSWORD
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

# Generate wpa_supplicant config
cat > /etc/wpa_supplicant/wpa_supplicant-wlan1-encrypt.conf <<EOF
ctrl_interface=/var/run/wpa_supplicant
update_config=1
ap_scan=0
country=US

network={
    ssid="$MESH_NAME"
    mode=5
    frequency=$MESH_FREQ
    key_mgmt=SAE
    psk="$MESH_PASSWORD"
    mesh_fwding=0
    ieee80211w=2
}
EOF

# Establish encryption with generated wpa_supplicant config
wpa_supplicant -B -i wlan1 -c /etc/wpa_supplicant/wpa_supplicant-wlan1-encrypt.conf

# Wait for encryption to be established
sleep 15

systemctl restart systemd-networkd

# Start hostapd with generated config
systemctl start hostapd
