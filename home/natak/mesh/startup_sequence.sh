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

# Mesh Startup Sequence Script


# Enable error reporting
set -e

# Brief pause between network setup steps
sleep 7

# Run batmesh. This creates mesh network, applies wpa3 encryption
sudo /home/natak/mesh/batmesh.sh

# Brief pause after network setup
sleep 2

# Start rnsd (Reticulum Network Stack Daemon) in background
nohup runuser -l natak -c 'rnsd' > /var/log/rnsd.log 2>&1 &
RNSD_PID=$!

# Give rnsd time to initialize
sleep 2

# Start enhanced OGM monitor in background
cd /home/natak/mesh/ogm_monitor && python3 enhanced_ogm_monitor.py &
OGM_PID=$!

sleep 5

# Start media mtx. required for TAKserver video
#su - natak -c "/home/natak/mediamtx &"

#sleep 2

# Reset RAK board to ensure BLE available for V1.1 hardware, requires reset pin on RAK board to be connected to GPIO 17
gpioset gpiochip0 17=0; sleep 0.1; gpioset gpiochip0 17=1


