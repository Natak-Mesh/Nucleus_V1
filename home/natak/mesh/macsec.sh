#!/bin/bash

ip link set wlan1 mtu 1564
ip link set bat0 mtu 1500
ip link set br0 mtu 1500


ip link add link wlan1 macsec0 type macsec encrypt on
ip link set macsec0 mtu 1532

# My Node
ip macsec add macsec0 tx sa 0 pn 1 on key 00 ed8bb8c025a343daad904509119183e8

# Peer Node (92cb-takNode3)
ip macsec add macsec0 rx port 1 address 00:c0:ca:b6:92:cb
ip macsec add macsec0 rx port 1 address 00:c0:ca:b6:92:cb sa 0 pn 1 on key 01 d715fa2dd31a0404083442286dd93627

# Peer Node (9523-takNode2)
ip macsec add macsec0 rx port 1 address 00:c0:ca:b6:95:23
ip macsec add macsec0 rx port 1 address 00:c0:ca:b6:95:23 sa 0 pn 1 on key 01 2a64b0b22e6c8097ba9ac1df650b4c55

ip link set macsec0 up
