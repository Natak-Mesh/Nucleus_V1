#!/bin/bash
# ==============================================================================
# FRESH NODE SETUP SCRIPT
# ==============================================================================
# TODO LIST - Manual Configuration Required After Running This Script:
# 
# 1. Configure /etc/hostapd/hostapd.conf , dont forget you have to unmask and enable
# 2. Configure NetworkManager unmanaged.conf ***added to script****
# 3. Edit /etc/systemd/network/br0.network with correct IP addres and DHCP lease range
# 4. Move over MACsec config tool files ***added to script****
# 5. Move over mesh contents, including ogm_monitor subdirectory
# 6. Move over Mesh_monitor contents, including templates subdirectory
# 7. Move over meshtastic directory contents, including test programs and doc sub directories
# 8. Set mesh variables in ~/mesh/mesh_config.env
# 9. move hostname mapping.json and macsec.sh from the macsec config tool folder into ~/mesh
# 10. still need to sort out web page startup, had to comment that out of mesh-startup.system
# ==============================================================================

# Remove leftover kernel build artifacts from image
rm -rf /home/natak/linux

sudo rm /etc/machine-id
sudo dbus-uuidgen --ensure=/etc/machine-id
sudo rm -f /etc/machine-id
sudo systemd-machine-id-setup
sudo rm /etc/ssh/ssh_host_*
sudo dpkg-reconfigure openssh-server
sudo systemctl restart systemd-networkd

# Install required packages
sudo apt update && sudo apt install -y hostapd batctl python3 python3-pip

# Install Python packages
pip3 install --break-system-packages meshtastic takproto PyQRCode pyserial PyYAML pypng Pypubsub protobuf rns

# Install Flask system-wide for systemd services
sudo pip3 install --break-system-packages Flask
# you need to install and start rns/rnsd at least once, auto start script now will start it and the git tracked config file
#has the info for a tcp server to allow external devices to use rns over wifi


# Add ~/.local/bin to PATH for pip-installed scripts
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Enable NetworkManager
sudo systemctl enable NetworkManager
