# 802.11s + Babel + smcroute Migration Guide (Concise)

This document summarizes the required steps to migrate from an 802.11s + BATMAN-adv L2 mesh to a clean L3 routed mesh using Babel and smcroute, with systemd-networkd handling all interface configuration.

Why Switch
- BATMAN-adv = constant L2 flooding (OGMs, ARP, DHCP, mDNS, SSDP).
- Babel = unicast neighbor updates → far lower load.
- No giant L2 broadcast domain.
- mesh0 becomes a clean routed interface.
- wlan0/eth0 clients can access the mesh without static routes.
- AP clients and OTG phone connections work automatically.

Final Network Architecture

Interfaces
- mesh0 → 802.11s mesh, static IP, Babel routing
- br-lan → LAN bridge (wlan0 + optionally eth0)
- wlan0 → AP
- eth0 → automatic WAN/LAN (DHCP or fallback static)

Subnets
- mesh0: 10.0.0.x/24 (static per node)
- br-lan: 192.168.50.1/24
- LAN clients: served via networkd DHCP server
- WAN (eth0 plugged into home router): DHCP from router

Required Packages
sudo apt install babeld smcroute hostapd nftables tcpdump networkd-dispatcher

Service Configuration
Disable auto-start for services managed by mesh-start.sh:
sudo systemctl disable hostapd
sudo systemctl mask wpa_supplicant@.service

These services will be started manually by the mesh setup script after configs are generated.

systemd-networkd Configuration

1. mesh0 – Static Mesh IP
/etc/systemd/network/10-mesh0.network:
[Match]
Name=mesh0
[Network]
Address=10.0.0.2/24

2. br-lan Bridge

NetDev:
/etc/systemd/network/20-brlan.netdev:
[NetDev]
Name=br-lan
Kind=bridge

Bridge IP + DHCP Server:
/etc/systemd/network/21-brlan.network:
[Match]
Name=br-lan
[Network]
Address=192.168.50.1/24
DHCPServer=yes

3. wlan0 → Bridge into br-lan
/etc/systemd/network/30-wlan0.network:
[Match]
Name=wlan0
[Network]
Bridge=br-lan

4. eth0 – Dual Mode Operation (Option A: Script-Based)

**Default State:** eth0 starts in br-lan (LAN mode, DHCP server)

/etc/systemd/network/40-eth0-lan.network:
[Match]
Name=eth0
[Network]
Bridge=br-lan

**Switching Logic via networkd-dispatcher:**

/etc/networkd-dispatcher/routable.d/50-eth0-wan-switch:
```bash
#!/bin/bash
if [ "$IFACE" = "eth0" ] && [ "$AdministrativeState" = "routable" ]; then
    # DHCP succeeded - switch to WAN mode
    ip link set eth0 nomaster  # Remove from bridge
    nft add rule ip nat postrouting oifname "eth0" masquerade
fi
```

/etc/networkd-dispatcher/off.d/50-eth0-lan-fallback:
```bash
#!/bin/bash
if [ "$IFACE" = "eth0" ]; then
    # Connection lost - return to LAN mode
    nft delete rule ip nat postrouting oifname "eth0" masquerade 2>/dev/null
    ip link set eth0 master br-lan
fi
```

**Requires:** `apt install networkd-dispatcher`

**Behavior:**
- Boot: eth0 in br-lan, serves DHCP to clients
- Cable plugged + DHCP → eth0 becomes WAN with NAT
- Cable unplugged → eth0 returns to br-lan

**Note:** This adds complexity. For simpler deployments, dedicate eth0 to either WAN or LAN role only.

Babeld Setup

/etc/babeld.conf:
interface mesh0
interface br-lan
redistribute ip
redistribute local

Enable Babel:
sudo systemctl enable --now babeld

smcroute Setup (example ATAK CoT group 239.2.3.1)

/etc/smcroute.conf:
mgroup from mesh0 group 239.2.3.1
mgroup from br-lan group 239.2.3.1
mroute from mesh0 group 239.2.3.1 to mesh0 br-lan
mroute from br-lan group 239.2.3.1 to mesh0

Enable smcroute:
sudo systemctl enable --now smcroute

NAT for Internet (eth0 as WAN)
/etc/nftables.conf example:
table ip nat {
    chain postrouting {
        type nat hook postrouting priority 100;
        oifname "eth0" masquerade
    }
}

tcpdump Verification

Multicast forwarding test:
tcpdump -n -i mesh0 host 239.2.3.1

Babel traffic test:
tcpdump -n -i mesh0 port 6696

Summary
- mesh0 = static IP, routed by Babel
- br-lan = AP + LAN clients (DHCP via systemd-networkd)
- eth0 = WAN if DHCP works, LAN if fallback static
- smcroute forwards only needed multicast
- No bridging of mesh0
- No static routes needed for users

Filesystem Structure

```
/etc/nucleus/                  # Config files
  ├── mesh.conf               # Mesh settings
  └── web.conf                # Flask settings

/opt/nucleus/                  # Application root
  ├── bin/                     # Executable scripts
  │   └── mesh-setup          # Mesh establishment
  └── web/                     # Flask app (no venv)
      ├── app.py
      ├── static/
      └── templates/

/etc/systemd/system/           # Service files
  ├── mesh-setup.service
  └── nucleus-web.service

/etc/networkd-dispatcher/      # eth0 switching scripts
  ├── routable.d/
  │   └── 50-eth0-wan-switch
  └── off.d/
      └── 50-eth0-lan-fallback
```

**Notes:**
- No venv required (packages installed with --break-system-packages)
- Flask service uses: `ExecStart=/usr/bin/python3 /opt/nucleus/web/app.py`
- All Nucleus components under /opt/nucleus/ for easy management
