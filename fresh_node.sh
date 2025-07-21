#!/bin/bash
# ==============================================================================
# FRESH NODE SETUP SCRIPT
# ==============================================================================

# ******************************************************************************
# If you are flashing an existing NatakMesh image onto your harware, run the below machine ID reset commands. Otherwise ignore if this is a fresh build
# Remove leftover kernel build artifacts from image
rm -rf /home/natak/linux

# Reset machine ID, SSH keys etc
sudo rm /etc/machine-id
sudo dbus-uuidgen --ensure=/etc/machine-id
sudo rm -f /etc/machine-id
sudo systemd-machine-id-setup
sudo rm /etc/ssh/ssh_host_*
sudo dpkg-reconfigure openssh-server
sudo systemctl restart systemd-networkd
# ******************************************************************************

# ------------------------------------------------------------------------------
# For fresh build install required packages
sudo apt update && sudo apt install -y hostapd batctl python3 python3-pip

# Install Reticulum
pip3 install --break-system-packages rns 
# you need to install and start rns/rnsd at least once, auto start script now will start it and the git tracked config file

# Install Flask system-wide for systemd services
sudo pip3 install --break-system-packages 


# Add ~/.local/bin to PATH for pip-installed scripts
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Enable NetworkManager
sudo systemctl enable NetworkManager
# system wpa_supplicant may need to be disabled to its not running in parallel with the one you use for wlan1
# dont forget to unmask and enable hostapd
# -------------------------------------------------------------------------------


# If this is a TAKserver node
# *****Download and install TAKserver arm64 .deb from tak.gov******

# media mtx install
# 1. Download latest MediaMTX release for ARM64
wget https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_linux_arm64.tar.gz

# 2. Extract it
tar -xvzf mediamtx_linux_arm64.tar.gz
