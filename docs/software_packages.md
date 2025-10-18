
       ..        .....        ...       
       ....     ......       ....      
       .......... ...       .....       
       ........    ..      ......       
       ......      ..     .......       
       .....       ...  .........       
       ....        .....     ....      
       ...         ....        ..   

 
        N A T A K   -   Nucleus V1         
                                          
          Mesh Networking Radio           



# Software Packages

## Initial Setup

### Update and Install Core Packages

```bash
sudo apt update && sudo apt install -y hostapd batctl python3 python3-pip aircrack-ng iperf3 ufw
```

## Python Packages

### Reticulum

```bash
# Install Reticulum (must start rns/rnsd at least once to generate config)
pip3 install --break-system-packages rns
```

### Nomadnet

```bash
# Install Nomadnet (update config after starting nomadnet once)
pip3 install nomadnet --break-system-packages
```

### Flask

```bash
# Install Flask system-wide for systemd services
sudo pip3 install --break-system-packages flask
```

### Meshtastic CLI Tools

```bash
pip3 install --upgrade pytap2 --break-system-packages
pip3 install --upgrade "meshtastic[cli]" --break-system-packages
```

## Environment Configuration

### Add ~/.local/bin to PATH

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

## System Services

### Enable NetworkManager

```bash
sudo systemctl enable NetworkManager
```

**Note:** System wpa_supplicant may need to be disabled so it's not running in parallel with the one used for wlan1. Don't forget to unmask and enable hostapd.

## Additional Software

### Tailscale
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```
### TAKserver

Download and install TAKserver arm64 .deb from [tak.gov](https://tak.gov)

```bash
# Install using dpkg
sudo dpkg -i takserver-*.deb
```

### MediaMTX

```bash
# Download latest MediaMTX release for ARM64
wget https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_linux_arm64.tar.gz

# Extract it
tar -xvzf mediamtx_linux_arm64.tar.gz
