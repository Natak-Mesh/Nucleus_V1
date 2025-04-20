# ATAK Handler Socket Resilience Implementation

## Problem Analysis

The ATAK handler breaks when wlan1 WiFi is turned off during testing of the WiFi/LoRa changeover logic. This document outlines the root cause and provides a comprehensive solution.

### Root Cause Analysis

When wlan1 is turned off:

1. The batman-adv mesh network detects the change and nodes switch to LORA mode (as expected)
2. The ATAK handler's sockets remain bound to the br0 IP address
3. Even though br0's IP address doesn't change, its multicast routing capabilities are affected
4. The ATAK handler doesn't detect this specific type of failure or properly recover

The key issue is that the ATAK handler is trying to connect to ATAK ports from an Android device over wlan0 via br0, but the network path or multicast routing may be disrupted when wlan1 is turned off.

## Solution: Network State Monitor

We'll implement a `NetworkStateMonitor` class that will:

1. Monitor interface states (wlan1, bat0)
2. Monitor socket activity
3. Monitor node mode changes
4. Trigger socket refresh when any of these change

### Implementation Details

#### 1. NetworkStateMonitor Class

```python
class NetworkStateMonitor:
    """
    Monitors network state changes and refreshes sockets when needed.
    This helps maintain connectivity when interfaces change state.
    """
    
    def __init__(self, atak_handler):
        """Initialize the network state monitor"""
        self.atak_handler = atak_handler
        self.logger = atak_handler.logger
        self.should_quit = False
        
        # Track interface states
        self.wlan1_state = self.get_interface_state("wlan1")
        self.bat0_state = self.get_interface_state("bat0")
        
        # Track socket activity
        self.last_packet_received = time.time()
        
        # Track node modes
        self.node_modes = self.get_node_modes()
        
        # Start monitoring threads
        self.start_monitoring()
    
    def start_monitoring(self):
        """Start all monitoring threads"""
        threading.Thread(target=self.monitor_interface_states, daemon=True).start()
        threading.Thread(target=self.monitor_socket_activity, daemon=True).start()
        threading.Thread(target=self.monitor_node_modes, daemon=True).start()
        self.logger.info("Network state monitoring started")
    
    def get_interface_state(self, interface):
        """Get state of a network interface"""
        try:
            # Check if interface exists and get its state
            result = subprocess.run(
                ["ip", "link", "show", interface],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode != 0:
                return {"exists": False}
            
            # Parse link state (UP/DOWN)
            link_state = "DOWN"
            if "state UP" in result.stdout:
                link_state = "UP"
            
            # Check if RUNNING (carrier)
            running = "RUNNING" in result.stdout
            
            return {
                "exists": True,
                "state": link_state,
                "running": running
            }
        except Exception as e:
            self.logger.error(f"Error getting interface state for {interface}: {e}")
            return {"exists": False, "error": str(e)}
    
    def get_node_modes(self):
        """Get modes of all nodes from node_status.json"""
        try:
            with open("/home/natak/reticulum_mesh/ogm_monitor/node_status.json", 'r') as f:
                status = json.load(f)
                
            # Extract node modes
            modes = {}
            for mac, node_info in status.get("nodes", {}).items():
                hostname = node_info.get("hostname")
                mode = node_info.get("mode")
                if hostname and mode:
                    modes[hostname] = mode
            
            return modes
        except Exception as e:
            self.logger.error(f"Error getting node modes: {e}")
            return {}
    
    def monitor_interface_states(self):
        """Monitor interface states and trigger socket refresh on changes"""
        self.logger.info("Starting interface state monitoring")
        while not self.should_quit:
            try:
                # Get current states
                current_wlan1_state = self.get_interface_state("wlan1")
                current_bat0_state = self.get_interface_state("bat0")
                
                # Check for significant changes
                wlan1_changed = (
                    self.wlan1_state.get("exists") != current_wlan1_state.get("exists") or
                    self.wlan1_state.get("state") != current_wlan1_state.get("state") or
                    self.wlan1_state.get("running") != current_wlan1_state.get("running")
                )
                
                bat0_changed = (
                    self.bat0_state.get("exists") != current_bat0_state.get("exists") or
                    self.bat0_state.get("state") != current_bat0_state.get("state") or
                    self.bat0_state.get("running") != current_bat0_state.get("running")
                )
                
                # If wlan1 or bat0 changed state, refresh sockets
                if wlan1_changed:
                    self.logger.info(f"wlan1 state changed: {self.wlan1_state} -> {current_wlan1_state}")
                    self.refresh_sockets("wlan1 state change")
                
                if bat0_changed:
                    self.logger.info(f"bat0 state changed: {self.bat0_state} -> {current_bat0_state}")
                    self.refresh_sockets("bat0 state change")
                
                # Update stored states
                self.wlan1_state = current_wlan1_state
                self.bat0_state = current_bat0_state
                
                # Check every 2 seconds
                time.sleep(2)
            except Exception as e:
                self.logger.error(f"Error in interface state monitoring: {e}")
                time.sleep(5)  # Longer delay on error
    
    def monitor_socket_activity(self):
        """Monitor socket activity and refresh if no packets received"""
        self.logger.info("Starting socket activity monitoring")
        INACTIVITY_THRESHOLD = 30  # 30 seconds without packets is considered inactive
        
        while not self.should_quit:
            try:
                current_time = time.time()
                time_since_last_packet = current_time - self.last_packet_received
                
                if time_since_last_packet > INACTIVITY_THRESHOLD:
                    self.logger.warning(f"No packets received for {time_since_last_packet:.1f} seconds")
                    self.refresh_sockets("socket inactivity")
                    # Reset timer to avoid continuous refreshes
                    self.last_packet_received = current_time
                
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Error in socket activity monitoring: {e}")
                time.sleep(5)
    
    def monitor_node_modes(self):
        """Monitor node modes and refresh sockets on mode changes"""
        self.logger.info("Starting node mode monitoring")
        while not self.should_quit:
            try:
                current_modes = self.get_node_modes()
                
                # Check for mode changes
                for hostname, mode in current_modes.items():
                    if hostname in self.node_modes and self.node_modes[hostname] != mode:
                        self.logger.info(f"Node {hostname} mode changed: {self.node_modes[hostname]} -> {mode}")
                        self.refresh_sockets(f"node {hostname} mode change")
                        break
                
                # Update stored modes
                self.node_modes = current_modes
                
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Error in node mode monitoring: {e}")
                time.sleep(5)
    
    def refresh_sockets(self, reason):
        """Refresh all sockets in the ATAK handler"""
        self.logger.info(f"Refreshing sockets due to: {reason}")
        
        try:
            # Clean up existing sockets
            for (addr, port) in list(self.atak_handler.atak_listening_sockets.keys()):
                self.atak_handler.cleanup_atak_socket(addr, port)
            
            # Clean up socket manager sockets
            self.atak_handler.socket_manager.cleanup_sockets()
            
            # Small delay to ensure clean shutdown
            time.sleep(1)
            
            # Set up new sockets
            self.atak_handler.setup_atak_listening_sockets()
            self.atak_handler.socket_manager.setup_persistent_sockets()
            
            self.logger.info("Socket refresh completed successfully")
        except Exception as e:
            self.logger.error(f"Error refreshing sockets: {e}")
    
    def packet_received(self):
        """Call this when a packet is received to update activity timestamp"""
        self.last_packet_received = time.time()
    
    def stop(self):
        """Stop the network state monitor"""
        self.should_quit = True
```

#### 2. Integration with ATAKHandler

```python
class ATAKHandler:
    def __init__(self, shared_dir: str = "/home/natak/reticulum_mesh/tak_transmission/shared"):
        """Initialize handler"""
        # Existing initialization code...
        
        # Set up ATAK listening sockets for receiving
        self.setup_atak_listening_sockets()
        
        # Set up socket manager for sending
        self.socket_manager = LoraOutSocketManager()
        
        # Set up network state monitor
        self.network_monitor = NetworkStateMonitor(self)
    
    def run(self):
        """Main processing loop"""
        try:
            while True:
                # Check for CoT packets from ATAK
                for (addr, port), sock in self.atak_listening_sockets.items():
                    sock.settimeout(0.1)
                    try:
                        data, src = sock.recvfrom(65535)
                        # Update network monitor when packet received
                        self.network_monitor.packet_received()
                        
                        ip_type = self.check_ip_location(src[0])
                        if port in [17012, 6969] and ip_type == "LOCAL":
                            self.logger.info(f"UDP RECEIVE: From port {port} ({len(data)} bytes)")
                            self.process_packet(data, port)
                    except socket.timeout:
                        continue
                    except Exception:
                        # Socket error - recreate socket
                        self.cleanup_atak_socket(addr, port)
                        self.setup_atak_listening_sockets()
                        break
                
                # Check for incoming packets
                self.process_incoming()
                
                # Small sleep to prevent CPU hogging
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            self.network_monitor.stop()
            for sock in self.atak_listening_sockets.values():
                sock.close()
```

## Implementation Reasoning

### 1. Why Monitor Multiple Aspects?

We monitor three different aspects of the network:

- **Interface States**: Detects immediate changes like wlan1 being turned off
- **Socket Activity**: Catches silent failures where packets stop flowing
- **Node Modes**: Ensures we refresh when nodes change between WIFI and LORA modes

This multi-layered approach ensures we catch all possible failure scenarios.

### 2. Why Use Separate Threads?

Each monitoring task runs in its own thread to:

- Avoid blocking the main ATAK handler loop
- Allow different monitoring intervals for each aspect
- Isolate failures (if one monitor fails, others continue)

### 3. Socket Refresh Strategy

When refreshing sockets, we:

1. Close all existing sockets first
2. Wait a short period to ensure clean shutdown
3. Create new sockets with fresh multicast group memberships
4. Log the reason for the refresh for troubleshooting

This complete refresh is more reliable than trying to repair individual sockets.

### 4. Handling Edge Cases

- **Continuous Failures**: We reset the inactivity timer after each refresh to prevent continuous refreshes
- **Error Handling**: Each monitoring function has its own error handling to ensure robustness
- **Graceful Shutdown**: The monitor can be stopped cleanly when the ATAK handler exits

## Testing Recommendations

To test this implementation:

1. **Normal Operation**: Verify that the monitor doesn't interfere with normal operation
2. **wlan1 Shutdown**: Turn off wlan1 and verify that sockets are refreshed
3. **Mode Changes**: Force nodes to switch between WIFI and LORA modes
4. **Packet Flow**: Verify that packets continue to flow after network changes

## Conclusion

This implementation provides a robust solution to the ATAK handler socket issues when network interfaces change state. By monitoring multiple aspects of the network and proactively refreshing sockets, we ensure continuous operation even during WiFi/LoRa changeovers or when interfaces are explicitly turned off.

The solution is:
- Non-intrusive to existing code
- Lightweight in terms of system resources
- Comprehensive in handling different failure scenarios
- Well-logged for troubleshooting
