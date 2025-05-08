# MACsec Configuration Tool

This tool helps configure MACsec encryption for mesh network nodes. It generates configuration files and maintains a mapping between MAC addresses, hostnames, and IP addresses.

## Usage

Run the tool:
```bash
python3 Macsec_config_generator.py
```

## Menu Options

1. **Add node** - Add a new node to the mesh network
2. **Remove node** - Remove an existing node
3. **Generate all node configs** - Generate configuration files for all nodes
4. **List current nodes** - Display information about configured nodes
5. **Exit** - Exit the program

## Required Information

When adding a new node, you'll need:

1. **MAC Address**
   - Format: `xx:xx:xx:xx:xx:xx`
   - How to get: Run `ip addr show wlan1` and look for "link/ether" line

2. **Hostname**
   - This is your Raspberry Pi's hostname
   - How to get: Run `hostname`
   - Example output: `meshpi1`

3. **br0 IP Address**
   - This is the IP address of your bridge interface
   - How to get: Run `ip addr show br0` and look for "inet" line
   - Enter WITHOUT the /24 suffix
   - Example: If you see `192.168.1.1/24`, enter just `192.168.1.1`

## Output Files

For each node, the tool creates a directory structure:
```
{last4ofMAC}/
└── {hostname}/
    ├── macsec.sh
    └── hostname_mapping.json
```

For example:
```
4455/
└── meshpi1/
    ├── macsec.sh
    └── hostname_mapping.json
```

Each directory contains:

1. **macsec.sh**
   - MACsec configuration script
   - Automatically made executable
   - Contains encryption keys and peer configurations

2. **hostname_mapping.json**
   - Maps MAC addresses to hostnames and IPs
   - Used by the mesh monitor application
   - Example:
     ```json
     {
       "00:11:22:33:44:55": {
         "hostname": "meshpi1",
         "ip": "192.168.1.1"
       }
     }
     ```

## Example Usage

1. Get required information:
   ```bash
   # Get MAC address
   ip addr show wlan1
   
   # Get hostname
   hostname
   
   # Get br0 IP
   ip addr show br0
   ```

2. Add a node:
   - Select option 1
   - Enter MAC address (e.g., `00:11:22:33:44:55`)
   - Enter hostname (e.g., `meshpi1`)
   - Enter br0 IP without /24 (e.g., `192.168.1.1`)

3. Generate configs:
   - Select option 3
   - Files will be created in directories named like `4455-meshpi1`

## Notes

- Always use the br0 IP address without the /24 suffix
- The hostname should match exactly what the `hostname` command returns

