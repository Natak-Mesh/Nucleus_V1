having a tough time with wpa_3 the longer the nodes sit aroun. potentially due to time drift since we dont have any internet connection. allegedly we can get them to converge on a single time via chrony. 
it doesnt need to be "correct" but all nodes need to agree

# Chrony Configuration for MANET Mesh Time Sync

This document describes how to configure **Chrony** on Raspberry Pi 4 nodes in a MANET mesh network to synchronize clocks for WPA3-SAE. The goal is to ensure all nodes maintain a common time (not necessarily correct), avoiding authentication issues due to clock drift.

---

## 1. Configuration File

Create or edit the Chrony configuration file on **all nodes**:

**`/etc/chrony/chrony.conf`**

bindaddress 0.0.0.0
broadcast 224.0.1.1 port 323
allow 10.0.0.0/24
local stratum 10
makestep 1.0 3
rtcsync

### Explanation:

- `bindaddress 0.0.0.0`: Listen on all interfaces.
- `broadcast 224.0.1.1 port 323`: Periodically send time packets to the multicast address.
- `allow 10.0.0.0/24`: Accept requests from mesh subnet.
- `local stratum 10`: Allow this node’s clock to be used for sync if no better source is found.
- `makestep 1.0 3`: Force stepping of the clock if offset >1s during first 3 updates.
- `rtcsync`: If a hardware RTC exists, keep it in sync.

---

## 2. Install Chrony

On Raspberry Pi OS (Debian-based):

sudo apt update
sudo apt install chrony

---

## 3. Start Chrony

Enable and start the Chrony service so it runs on boot:

sudo systemctl enable chronyd
sudo systemctl start chronyd

---

## 4. Manual Time Step After Mesh Formation (Optional)

If you need to manually step the clock immediately after the mesh forms:

chronyc -a makestep

This forces the system clock to align with the peer time without waiting.

---

## 5. Behavior in MANET

- All nodes will broadcast their clocks over the mesh.
- Nodes dynamically pick peers based on reachability and stability.
- As long as nodes are mesh-connected, their clocks converge within seconds.

---

## 6. Notes

- **Multicast support:** Ensure your mesh passes multicast traffic (802.11s does by default; BATMAN-adv may need multicast_mode enabled).
- **No internet required:** This works entirely within the MANET.
- **No master needed:** Any node can join or leave; the mesh will resynchronize dynamically.
---
