#!/bin/bash
# ==============================================================================
# FRESH NODE SETUP SCRIPT
# ==============================================================================
# TODO LIST - Manual Configuration Required After Running This Script:
# 
# 1. Configure /etc/hostapd/hostapd.conf , dont forget you have to unmask and enable
# 2. Configure NetworkManager unmanaged.conf ***added to script****
# 3. Enable systemd-networkd
# 4. Edit /etc/systemd/network/br0.network with correct IP addres and DHCP lease range
# 5. 
# 6. 
# 7.
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
pip3 install --break-system-packages rns

# Install Flask system-wide for systemd services
sudo pip3 install --break-system-packages Flask
# you need to install and start rns/rnsd at least once, auto start script now will start it and the git tracked config file
#has the info for a tcp server to allow external devices to use rns over wifi


# Add ~/.local/bin to PATH for pip-installed scripts
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Enable NetworkManager
sudo systemctl enable NetworkManager
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable systemd-networkd
