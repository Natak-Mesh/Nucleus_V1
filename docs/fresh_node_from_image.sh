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
#           Mesh Networking Radio           #
#############################################

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

# Clean up vscode storage
rm -rf ~/.vscode
rm -rf ~/.config/Code

# Clear Reticulum identity and cached data
sudo rm -f ~/.reticulum/storage/transport_identity
sudo rm -f ~/.reticulum/storage/destination_table
sudo rm -f ~/.reticulum/storage/known_destinations
sudo rm -f ~/.reticulum/storage/packet_hashlist
sudo rm -rf ~/.reticulum/storage/ratchets/*
sudo rm -rf ~/.reticulum/storage/cache/*
sudo rm -rf ~/.reticulum/storage/identities/*
sudo rm -rf ~/.reticulum/storage/tunnels
sudo rm -rf ~/.reticulum/storage/resources/*

# Clear Nomadnet identity and user data
sudo rm -f ~/.nomadnetwork/storage/identity
sudo rm -f ~/.nomadnetwork/storage/directory
sudo rm -f ~/.nomadnetwork/storage/peersettings
sudo rm -f ~/.nomadnetwork/logfile
sudo rm -f ~/.nomadnetwork/pnannounced
sudo rm -rf ~/.nomadnetwork/storage/conversations/*
sudo rm -rf ~/.nomadnetwork/storage/cache/*
sudo rm -rf ~/.nomadnetwork/storage/lxmf/ratchets/*
sudo rm -rf ~/.nomadnetwork/storage/lxmf/messagestore/*
sudo rm -f ~/.nomadnetwork/storage/lxmf/local_deliveries
sudo rm -f ~/.nomadnetwork/storage/lxmf/node_stats
sudo rm -f ~/.nomadnetwork/storage/lxmf/outbound_stamp_costs
sudo rm -f ~/.nomadnetwork/storage/lxmf/peers
sudo rm -rf ~/.nomadnetwork/storage/files/*
sudo rm -rf ~/.nomadnetwork/storage/resources/*

echo "Fresh node setup complete - system and Reticulum/Nomadnet identities cleared"
