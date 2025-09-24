# ------------------------------------------------------------------------------
# For fresh build install required apt packages
sudo apt update && sudo apt install -y hostapd batctl python3 python3-pip aircrack-ng iperf3 ufw

# Install Reticulum
pip3 install --break-system-packages rns # you need to install and start rns/rnsd at least once to generate config
# Install Nomadnet
pip3 install nomadnet --break-system-packages # update config after starting nomadnet once

# Install Flask system-wide for systemd services
sudo pip3 install --break-system-packages flask

# Meshtastic CLI tools
 pip3 install --upgrade pytap2 --break-system-packages
 pip3 install --upgrade "meshtastic[cli]" --break-system-packages

# Add ~/.local/bin to PATH for pip-installed scripts
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Enable NetworkManager
sudo systemctl enable NetworkManager
# system wpa_supplicant may need to be disabled to its not running in parallel with the one you use for wlan1
# dont forget to unmask and enable hostapd

# TAKserver
# *****Download and install TAKserver arm64 .deb from tak.gov******
# Install using dpkg -i command

# media mtx 
# Download latest MediaMTX release for ARM64
wget https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_linux_arm64.tar.gz
# Extract it
tar -xvzf mediamtx_linux_arm64.tar.gz


