#!/bin/bash

ip link set wlan1 mtu 1564
ip link set br0 mtu 1500

ip link add link wlan1 macsec0 type macsec encrypt on
ip link set macsec0 mtu 1532

# My Node
ip macsec add macsec0 tx sa 0 pn 1 on key 00 79de38f94f0f3ef94314b715df40835f

# Peer Node (9523-takNode2)
ip macsec add macsec0 rx port 1 address 00:c0:ca:b6:95:23
ip macsec add macsec0 rx port 1 address 00:c0:ca:b6:95:23 sa 0 pn 1 on key 01 1d0a496cc163580587b949612850ac04

# Peer Node (92cb-takNode3)
ip macsec add macsec0 rx port 1 address 00:c0:ca:b6:92:cb
ip macsec add macsec0 rx port 1 address 00:c0:ca:b6:92:cb sa 0 pn 1 on key 01 ef474c13a0b4e5f7e9ddc99484ff4543

# Peer Node (92ca-takNode4)
ip macsec add macsec0 rx port 1 address 00:c0:ca:b6:92:ca
ip macsec add macsec0 rx port 1 address 00:c0:ca:b6:92:ca sa 0 pn 1 on key 01 c482c5d736c46c93f89c9e04fde7ac45

ip link set macsec0 up