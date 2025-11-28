#       ..        .....        ...       
#       ....     ......       ....      
#       .......... ...       .....       
#       ........    ..      ......       
#       ......      ..     .......       
#       .....       ...  .........       
#       ....        .....     ....      
#       ...         ....        ..   

#############################################
#        N A T A K   -   Nucleus OS v2.0    #
#                                           #
#         Web Interface Planning            #
#############################################

## File Structure

Following Linux Filesystem Hierarchy Standard (FHS) and Flask conventions:

```
/opt/nucleus/web/                      # Flask web application
├── app.py                             # Main Flask application file
├── static/                            # Static assets (CSS, JS, images)
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
│       └── NatakMeshsecondary-overlay.png  (already exists)
└── templates/                         # HTML Jinja2 templates
    ├── base.html                      # Base template with common elements
    ├── index.html                     # Dashboard/home page
    └── ...                            # Additional page templates

/etc/nucleus/                          # Configuration files (already exists)
└── mesh.conf                          # Mesh configuration

/opt/nucleus/bin/                      # Shell scripts (already exists)
├── config_generation.sh
├── mesh-start.sh
└── eth0-mode.sh
```

## Mesh Connection Monitoring

### Babeld Configuration
Enable monitoring interface in `/etc/babeld.conf`:
```
local-port 33123
```

### Data Sources for Mesh Connections

**1. Babeld Monitoring Interface**
```bash
echo "dump" | nc localhost 33123
```
Provides:
- Neighbor link-local IPv6 addresses (e.g., `fe80::11`)
- Link quality metrics: `cost`, `reach`, `rxcost`, `txcost`
- Router IDs
- Route information

**2. IPv6 Neighbor Cache**
```bash
ip -6 neigh show dev wlan1
```
Maps: IPv6 link-local → MAC address

**3. IPv4 Neighbor Cache**
```bash
ip neigh show dev wlan1
```
Maps: MAC address → IPv4 address

### Correlation Logic
1. Query babeld for neighbor `fe80::11` with link metrics
2. Query IPv6 neighbor cache: `fe80::11` → MAC `00:c0:ca:b7:af:be`
3. Query IPv4 neighbor cache: MAC `00:c0:ca:b7:af:be` → IP `10.20.1.11`
4. Result: Display `10.20.1.11` with babeld's link quality metrics

### Web Interface Implementation
- Connect to babeld's monitoring port (localhost:33123)
- Parse neighbor data from `dump` command
- Query system neighbor caches to resolve IPv4 addresses
- Display: Node IP, Link Quality/Cost, Connection Status
- Use `monitor` command for real-time updates
