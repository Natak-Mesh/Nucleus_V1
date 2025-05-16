# Mesh Network System Configuration

This directory contains the system configuration files necessary for setting up and maintaining the mesh network infrastructure. These files configure various system services and components that work together to create a secure, reliable mesh network with support for TAK Protocol transmission.

## System Overview

The configuration in this directory establishes a network architecture that includes:

1. **Bridge Interface**: A network bridge (br0) that connects ethernet (eth0) and wireless (wlan0) interfaces
2. **Wireless Access Point**: Configuration for hosting a wireless network
3. **MACsec Encryption**: Layer 2 encryption for secure communication between mesh nodes
4. **Batman-adv Mesh Routing**: Advanced mesh routing protocol for resilient connectivity
5. **Systemd Services**: Services that start the mesh network and Reticulum stack

## Network Architecture

### Bridge Configuration

The system uses a bridge interface (br0) to connect multiple network interfaces:

- The bridge has a static IP address (192.168.200.1/24)
- It runs a DHCP server to provide IP addresses to connected clients
- IP masquerading (NAT) is enabled for internet connectivity
- Both the ethernet (eth0) and wireless (wlan0) interfaces are added to the bridge

This configuration allows devices connected to either the ethernet port or the wireless network to communicate with each other and access the mesh network.

### Wireless Access Point

The hostapd configuration sets up a wireless access point:

- The access point uses the wlan0 interface
- It broadcasts an SSID named after the node (e.g., takNode1)
- WPA2 security is enabled with a pre-shared key
- It operates on the 2.4GHz band (channel 1)

This allows wireless clients to connect to the mesh node and access the network.

### Network Interface Management

NetworkManager is configured to ignore specific interfaces:

- wlan0, wlan1, and eth0 are marked as unmanaged
- This prevents NetworkManager from interfering with the custom network configuration
- The interfaces are instead managed by systemd-networkd and the mesh scripts

### MACsec Encryption

MACsec (Media Access Control Security) provides layer 2 encryption between mesh nodes:

- Configured on the wlan1 interface with a macsec0 virtual interface
- Each node has a unique encryption key for transmitting data
- Each node is configured with the public keys of all other nodes in the mesh
- This ensures all traffic between mesh nodes is encrypted at the link layer
- The MTU is adjusted to accommodate the encryption overhead

### Batman-adv Mesh Routing

The Batman-adv (Better Approach To Mobile Ad-hoc Networking) protocol provides mesh routing:

- Creates a virtual bat0 interface for mesh routing
- The macsec0 interface is added to the bat0 mesh
- The bat0 interface is then added to the br0 bridge
- Various Batman-adv optimizations are configured:
  - OGM interval set to 1000ms for better adaptation to mobility
  - Hop penalty set to 40 to favor stronger direct links
  - Network coding enabled to improve throughput
  - Distributed ARP table enabled to reduce broadcast traffic

## System Services

### Mesh Network Startup Service

The mesh-startup.service handles the initialization of the mesh network:

- Runs after the network.target systemd target
- Executes three main components in sequence:
  1. MACsec configuration script (macsec.sh)
  2. Batman-adv mesh configuration script (batmesh.sh)
  3. Mesh monitor application (app.py)
- Uses sleep commands to ensure proper initialization sequence
- Configured as a oneshot service that remains active after execution

### Reticulum Stack Service

The reticulum-stack.service starts the Reticulum networking stack:

- Runs as the natak user
- Executes the start_reticulum_stack.sh script
- Automatically restarts on failure
- The script:
  - Cleans up old packet files
  - Sets the Python path
  - Starts the Reticulum test setup script

## Network Configuration Files

### Bridge Device Configuration

The br0.netdev file defines the bridge network device:
- Creates a virtual network interface of type "bridge"
- Named "br0" for consistent reference in other configuration files

### Bridge Network Configuration

The br0.network file configures the network settings for the bridge:
- Sets the static IP address and subnet
- Configures the DHCP server settings
- Defines the IP masquerading for NAT
- Configures DNS settings

### Interface Configurations

The eth0.network and wlan0.network files:
- Match the respective physical interfaces
- Add them to the br0 bridge
- This allows traffic to flow between the interfaces through the bridge

## Startup Process

When the system boots:

1. systemd-networkd starts and applies the network configurations
2. The mesh-startup.service runs:
   - macsec.sh configures the encrypted mesh links
   - batmesh.sh sets up the Batman-adv mesh routing
   - The mesh monitor starts to track node status
3. The reticulum-stack.service starts:
   - Cleans up any old packet files
   - Starts the Reticulum networking stack
   - Initializes the TAK transmission components

## Integration with Other Components

These configuration files work together with scripts in the home/natak/mesh/ directory:

- **macsec.sh**: Configures the MACsec encryption
- **batmesh.sh**: Sets up the Batman-adv mesh routing
- **mesh_config.env**: Contains environment variables for mesh configuration

The system also integrates with:

- The mesh monitor in home/natak/mesh_monitor/
- The Reticulum stack in reticulum_mesh/
- The TAK transmission components in reticulum_mesh/tak_transmission/

## Security Considerations

The configuration implements several security measures:

- WPA2 encryption for the wireless access point
- MACsec encryption for all mesh traffic
- Isolation of the mesh interfaces from NetworkManager
- Proper MTU settings to ensure encrypted traffic flows correctly

## Troubleshooting

Common issues and their solutions:

- If the bridge doesn't come up, check the systemd-networkd logs with `journalctl -u systemd-networkd`
- If wireless clients can't connect, check the hostapd logs with `journalctl -u hostapd`
- If mesh nodes can't see each other, verify the MACsec configuration and Batman-adv status with `batctl n`
- If services fail to start, check their status with `systemctl status mesh-startup.service` or `systemctl status reticulum-stack.service`
