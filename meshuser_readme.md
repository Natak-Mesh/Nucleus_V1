# Mesh User Setup and Proprietary Data Protection

This document outlines the process for setting up a restricted user account (`meshuser`) for purchasers of mesh nodes, while protecting proprietary code and allowing limited access to configuration files.

## Overview

The `meshuser` account is designed to:
- Allow users to configure mesh network settings
- Protect proprietary code in the reticulum_mesh directory
- Prevent access to critical system components
- Enable users to run the macsec_config_tool and edit necessary configuration files

## Setup Process

### 1. Create the Setup Script

Create a file called `setup_meshuser.sh` in `/home/natak/scripts/` with the following content:

```bash
#!/bin/bash
# setup_meshuser.sh - Script to set up meshuser account on new nodes

# Create meshuser account
useradd -m meshuser -s /bin/bash
echo "meshuser:MeshInitialPassword" | chpasswd
echo "Please change the default password immediately after first login"

# Block access to proprietary components
chmod 750 /home/natak/reticulum_mesh
chmod 750 /home/natak/mesh/batmesh.sh
chmod 750 /home/natak/mesh_monitor

# Allow access to required files
chmod 666 /home/natak/mesh/macsec.sh
chmod 666 /home/natak/mesh/hostname_mapping.json
chmod 666 /home/natak/mesh/mesh_config.env
chmod 755 /home/natak/macsec_config_tool

# Configure sudo access for file operations
echo 'meshuser ALL=(ALL) NOPASSWD: /bin/cp /home/natak/macsec_config_tool/*/*/macsec.sh /home/natak/mesh/' > /etc/sudoers.d/meshuser
echo 'meshuser ALL=(ALL) NOPASSWD: /bin/cp /home/natak/macsec_config_tool/*/*/hostname_mapping.json /home/natak/mesh/' >> /etc/sudoers.d/meshuser
echo 'meshuser ALL=(ALL) NOPASSWD: /bin/rm /home/natak/mesh/macsec.sh' >> /etc/sudoers.d/meshuser
echo 'meshuser ALL=(ALL) NOPASSWD: /bin/rm /home/natak/mesh/hostname_mapping.json' >> /etc/sudoers.d/meshuser
chmod 440 /etc/sudoers.d/meshuser

echo "meshuser setup complete"
```

### 2. Make the Script Executable

```bash
chmod +x /home/natak/scripts/setup_meshuser.sh
```

### 3. Run the Setup Script

```bash
sudo /home/natak/scripts/setup_meshuser.sh
```

### 4. Update the Sync Script

Add the following lines to the `clean_sync.sh` script to include the setup script in the repository:

```bash
# Create directory for the script
mkdir -p "$CLEAN_REPO_DIR/home/natak/scripts"

# Copy the setup script
cp -v /home/natak/scripts/setup_meshuser.sh "$CLEAN_REPO_DIR/home/natak/scripts/"
```

## File Permissions Explanation

The setup script configures the following permissions:

| File/Directory | Permission | Effect |
|----------------|------------|--------|
| `/home/natak/reticulum_mesh` | 750 | Blocks meshuser from accessing proprietary code |
| `/home/natak/mesh/batmesh.sh` | 750 | Blocks meshuser from accessing proprietary code |
| `/home/natak/mesh_monitor` | 750 | Blocks meshuser from accessing proprietary code |
| `/home/natak/mesh/macsec.sh` | 666 | Allows meshuser to read and write this file |
| `/home/natak/mesh/hostname_mapping.json` | 666 | Allows meshuser to read and write this file |
| `/home/natak/mesh/mesh_config.env` | 666 | Allows meshuser to read and write this file |
| `/home/natak/macsec_config_tool` | 755 | Allows meshuser to access and use the tool |

## Sudo Access Configuration

The setup script configures sudo access to allow meshuser to perform specific file operations without a password:

1. Copy macsec.sh from the macsec_config_tool directory to the mesh directory
2. Copy hostname_mapping.json from the macsec_config_tool directory to the mesh directory
3. Delete macsec.sh from the mesh directory
4. Delete hostname_mapping.json from the mesh directory

## User Documentation

Create a file called `meshuser_guide.md` in the meshuser's home directory with the following content:

```markdown
# Mesh Configuration Guide for Users

As a mesh node user, you have limited access to protect the proprietary components of the system. Here's what you can do:

## Allowed Actions

1. Use the macsec_config_tool to generate configuration files
   - Run: `python3 /home/natak/macsec_config_tool/Macsec_config_generator.py`

2. Manage configuration files in the mesh directory
   - Copy macsec.sh: `sudo cp /home/natak/macsec_config_tool/XXXX-YYYY/macsec.sh /home/natak/mesh/`
   - Copy hostname_mapping.json: `sudo cp /home/natak/macsec_config_tool/XXXX-YYYY/hostname_mapping.json /home/natak/mesh/`
   - Delete existing macsec.sh: `sudo rm /home/natak/mesh/macsec.sh`
   - Delete existing hostname_mapping.json: `sudo rm /home/natak/mesh/hostname_mapping.json`
   - Edit macsec.sh: `nano /home/natak/mesh/macsec.sh`
   - Edit hostname_mapping.json: `nano /home/natak/mesh/hostname_mapping.json`

3. Edit mesh configuration parameters
   - Edit mesh_config.env: `nano /home/natak/mesh/mesh_config.env`

## Restricted Components

You do not have access to:
- The reticulum_mesh directory
- The batmesh.sh script
- The mesh_monitor directory

For any issues requiring access to restricted components, please contact the system administrator.
```

## Implementation Checklist

- [ ] Create the `/home/natak/scripts` directory
- [ ] Create the `setup_meshuser.sh` script
- [ ] Make the script executable
- [ ] Run the script to set up the meshuser account
- [ ] Update the sync script to include the setup script
- [ ] Create the user documentation in the meshuser's home directory
- [ ] Test the setup to ensure meshuser can perform the allowed actions but not access restricted files

## Additional Considerations

1. **Password Management**: The initial password is set to "MeshInitialPassword". Ensure users change this password after first login.

2. **Service Impact**: This setup does not affect the operation of mesh services, which will continue to run as root.

3. **File Ownership**: This setup maintains the current ownership of files and directories (root or natak), only modifying permissions to restrict access.

4. **Mesh Monitor**: The mesh_monitor application will continue to function normally as it runs as root and can access all files regardless of permissions.

5. **Future Updates**: If new proprietary components are added to the system, remember to update the setup script to protect them as well.
