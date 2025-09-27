# Mesh Monitor

A Flask web application that provides management and monitoring capabilities for mesh network nodes. The application serves as a centralized interface for node status monitoring, network configuration management, and system control.

## Overview

Mesh Monitor is a web-based management system that combines real-time node monitoring with configuration management capabilities. It provides a dual-interface design with separate pages for monitoring and administrative functions, accessible through any web browser on the mesh network.

The system integrates with existing mesh infrastructure by reading node status data, managing WiFi configuration files, and providing system-level control functions through a responsive web interface.

## Core Functionality

### Node Status Monitoring
- Real-time display of mesh node connectivity and status
- Node timeout detection and visual indication of inactive nodes
- Local node information including MAC address and hostname
- Integration with external node status data sources

### WiFi Configuration Management  
- Dynamic WiFi channel selection across 2.4GHz and 5GHz bands
- Real-time frequency mapping and validation
- Automated configuration file updates for mesh networking
- Support for channels 1-14 (2.4GHz) and common 5GHz channels (36-165)

### Network Configuration
- IP address management with validation
- Network interface configuration through systemd
- Subnet configuration and addressing scheme management

### System Control
- Web-based system reboot functionality
- Configuration change application and validation
- Status reporting and error handling

## Architecture

### Backend Components
The Flask backend provides a RESTful API architecture with the following key components:

- **Data Collection**: Interfaces with external JSON data sources for node status information
- **Configuration Management**: Handles reading and updating system configuration files
- **System Integration**: Manages interaction with network configuration and system services
- **API Layer**: Provides JSON endpoints for frontend communication

### Frontend Interfaces

**WiFi Status Page** (`/`)
- Primary monitoring interface showing current node status
- Real-time updates of mesh network connectivity
- Mobile-responsive design with touch-friendly controls
- Visual indicators for node health and timeout status

**Management Console** (`/management`)
- Administrative interface for configuration changes
- WiFi channel selection with frequency display
- IP address configuration with validation
- System control functions including reboot capability

## Data Sources and Integration

### External Dependencies
- **Node Status Data**: Reads from `/home/natak/mesh/ogm_monitor/node_status.json`
- **Mesh Configuration**: Manages `/home/natak/mesh/batmesh.sh` for WiFi settings  
- **Network Configuration**: Updates `/etc/systemd/network/br0.network` for IP settings
- **WiFi Configuration**: Modifies `/etc/wpa_supplicant/wpa_supplicant-wlan1-encrypt.conf`

### Configuration File Integration
The application uses automated file manipulation to update system configurations:
- WiFi channel changes update both mesh and supplicant configurations
- IP address changes modify systemd network configuration
- All changes require system reboot to take effect

## API Endpoints

### Monitoring Endpoints
- `GET /api/wifi` - Returns current node status and configuration data
- `GET /api/mesh-config` - Retrieves current WiFi channel and frequency settings
- `GET /api/node-ip` - Returns current IP configuration

### Management Endpoints  
- `POST /api/mesh-config` - Updates WiFi channel configuration
- `POST /api/node-ip` - Changes node IP address with validation
- `POST /api/reboot` - Initiates system reboot

All API endpoints return JSON responses with success/error status and relevant data.

## Technical Requirements

### System Dependencies
- Python 3 with Flask framework
- System access to network configuration files
- Sudo privileges for system reboot functionality
- Access to mesh networking utilities and configuration files

### Network Requirements
- Functioning mesh network infrastructure
- Node status monitoring system generating JSON data
- Proper network interface configuration (wlan1, br0)
- systemd-networkd for network management

## Installation and Usage

### Basic Setup
1. Ensure all system dependencies and file paths are properly configured
2. Install Python Flask and required modules
3. Configure file permissions for configuration file access
4. Start the Flask application on the desired network interface

### Access
- **Default Port**: 5000
- **WiFi Status**: `http://[node-ip]:5000/`
- **Management**: `http://[node-ip]:5000/management`
- **API Base**: `http://[node-ip]:5000/api/`

### Configuration Changes
Most configuration changes require a system reboot to take effect. The web interface provides appropriate warnings and reboot functionality when needed.

## File Structure

The application consists of:
- **app.py** - Main Flask application and API logic
- **templates/** - Jinja2 templates for web interfaces
  - **wifi.html** - Node monitoring interface
  - **management.html** - Administrative console
- **static/** - Static assets including logos and styling
- **start_monitor.sh** - Application startup script

## Integration Notes

The system integrates with existing mesh infrastructure by:
- Reading node status from external monitoring systems
- Managing standard Linux network configuration files  
- Using systemd for network interface management
- Interfacing with wpa_supplicant for WiFi configuration
- Providing web-based access to system-level functions

This design allows the application to serve as a centralized management point for mesh nodes while maintaining compatibility with existing network infrastructure and monitoring systems.
