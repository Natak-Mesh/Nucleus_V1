This version uses reticulum/rnode as the lora connection. uses zstd to just directly compress packets as i had a very hard time parsing out required info in takproto and making a new packet. the meshtastic branch probably solved that problem, but with reticulum, message retries, ack's etc all have to be done manually and it got very complex. plus this does not ahve a good multicast option, so reticulum had to send to each node sequentially and packet sizes were still large due to compressing the entire CoT packet. mesh flooded very quickly. works ok on bench but field tests were poor when on lora


# Mesh-V1
802.11s/BATMAN-adv  Wi-Fi Mesh and Rnode/Reticulum with CoT Tx Script

### System Requirements
- Pi-OS Bookworm with MACsec enabled kernel
- NetworkManager
- systemd-networkd
- iw (wireless configuration tool)
- batman-adv kernel module
- batctl (Batman-adv control utility)
- hostapd (for WiFi AP functionality, needs to be unmasked)
- git

### Python Requirements
- Python 3.11
- pip
- RNS (Reticulum Network Stack)
- zstd (Zstandard compression library)
- takproto (TAK protocol handling)

## Hardware Requirements
- Pi 4 w/ 4 GB ram
- 802.11s Compatible wifi card
- Rnode compatible LoRa Radio
- 32 GB microSD
- assorted cables/bulkead fittings/connectors
