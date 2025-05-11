#!/usr/bin/env python3

"""
##############################################################################
#                                                                            #
#                          !!! IMPORTANT NOTE !!!                            #
#                                                                            #
#  Destination Handling:                                                     #
#  - PeerDiscovery creates and owns the IN destination                      #
#  - PacketManager must access it through peer_discovery.destination        #
#  - NEVER create new destinations or get through RNS.Reticulum.get_instance #
#  - This ensures we use the same destination PeerDiscovery announced       #
#                                                                            #
##############################################################################
"""

import os
import json
import time
import RNS
import config
import logger

class PacketManager:
    def __init__(self, peer_discovery=None):
        self.peer_discovery = peer_discovery
        self.logger = logger.get_logger("PacketManager", "packet_logs.log")
        
        # Directory paths
        self.pending_dir = config.PENDING_DIR
        self.sent_buffer = config.SENT_BUFFER_DIR
        self.incoming_dir = config.INCOMING_DIR
        
        # Monitoring state
        self.should_quit = False

        # Delivery tracking
        self.delivery_status = {}  # filename -> {nodes: {hostname: {sent: bool, sent_time: time, delivered: bool}}, retry_count: int}
        self.last_send_time = 0  # timestamp of last send to respect radio cycle time
        self.last_identity_check = {}  # node -> timestamp of last identity check
        
        # Logging rate control
        self.identity_check_counter = 0  # Counter for identity check logging
        self.previous_lora_node_count = None  # Track previous count of LORA nodes
        
        # Ensure directories exist
        os.makedirs(self.pending_dir, exist_ok=True)
        os.makedirs(self.sent_buffer, exist_ok=True)
        os.makedirs(self.incoming_dir, exist_ok=True)

        # Set up packet callback on peer_discovery's destination
        if self.peer_discovery and self.peer_discovery.destination:
            self.peer_discovery.destination.set_packet_callback(self.handle_incoming_packet)
            self.peer_discovery.destination.set_proof_strategy(RNS.Destination.PROVE_ALL)

    def run(self):
        """Main loop - process outgoing and handle incoming"""
        self.logger.info("PacketManager running")
        while not self.should_quit:
            try:
                # Check if we're allowed to transmit
                current_time = time.time()
                can_transmit = current_time - self.last_send_time >= config.SEND_SPACING_DELAY
                
                if can_transmit:
                    # Process new outgoing packets
                    self.process_outgoing(transmit_allowed=True)
                    # Retry logic commented out
                    # if self.process_outgoing(transmit_allowed=True):
                    #     # If we sent something, don't try retries this cycle
                    #     pass
                    # else:
                    #     # If no new outgoing packets, try retries
                    #     self.process_retries(transmit_allowed=True)
                else:
                    # Still run the processes but don't allow transmission
                    self.process_outgoing(transmit_allowed=False)
                    # Retry logic commented out
                    # self.process_retries(transmit_allowed=False)
                
                # Process any pending delivery receipts directly in the main loop
                # Extract just what we need from the original retry logic to process receipts
                try:
                    # Process each file in delivery status to keep RNS active
                    for filename, status in list(self.delivery_status.items()):
                        # Clean up if max retries reached
                        if status["retry_count"] >= config.RETRY_MAX_ATTEMPTS:
                            self.logger.warning(f"Max retries reached for {filename}")
                            # Clean up the failed packet
                            sent_path = os.path.join(self.sent_buffer, filename)
                            try:
                                os.remove(sent_path)
                                del self.delivery_status[filename]
                                self.logger.info(f"Removed failed packet {filename} from sent buffer after max retries")
                            except Exception as e:
                                self.logger.error(f"Error removing failed packet {filename} from sent buffer: {e}")
                        else:
                            # Process delivery status to prompt receipt callbacks
                            # This loop checks each node entry in a way that encourages
                            # Reticulum to process its event queue for delivery receipts
                            for node, node_status in status["nodes"].items():
                                # Check nodes that haven't been delivered but were sent
                                if not node_status["delivered"] and node_status["sent"]:
                                    # Rate limit peer identity checks to once every 5 seconds per node
                                    current_time = time.time()
                                    if node not in self.last_identity_check or current_time - self.last_identity_check.get(node, 0) >= 5:
                                        if self.peer_discovery:
                                            try:
                                                # Only log every 30th identity check
                                                self.identity_check_counter += 1
                                                if self.identity_check_counter % 30 == 0:
                                                    self.logger.info(f"Checking identity for node {node} to prompt receipt processing")
                                                self.peer_discovery.get_peer_identity(node)
                                                self.last_identity_check[node] = current_time
                                            except Exception as e:
                                                import traceback
                                                self.logger.error(f"Error getting peer identity for {node}: {e}")
                                                self.logger.error(f"Traceback: {traceback.format_exc()}")
                except Exception as e:
                    self.logger.error(f"Error processing delivery receipts: {e}")
                    
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")

    def process_retries(self, transmit_allowed=True):
        """Check sent_buffer for failed deliveries and retry if needed - COMMENTED OUT"""
        # RETRY LOGIC COMMENTED OUT
        return False
        
        # try:
        #     # If transmission not allowed, just return
        #     if not transmit_allowed:
        #         return False

        #     current_time = time.time()
        #     lora_nodes = self.get_lora_nodes()
        #     sent_something = False

        #     # Process each file in delivery status
        #     for filename, status in list(self.delivery_status.items()):
        #         # Clean up if max retries reached
        #         if status["retry_count"] >= config.RETRY_MAX_ATTEMPTS:
        #             self.logger.warning(f"Max retries reached for {filename}")
        #             # Clean up the failed packet
        #             sent_path = os.path.join(self.sent_buffer, filename)
        #             try:
        #                 os.remove(sent_path)
        #                 del self.delivery_status[filename]
        #                 self.logger.info(f"Removed failed packet {filename} from sent buffer after max retries")
        #             except Exception as e:
        #                 self.logger.error(f"Error removing failed packet {filename} from sent buffer: {e}")
        #             continue

        #         # Calculate backoff delay
        #         delay = min(
        #             config.RETRY_INITIAL_DELAY * (config.RETRY_BACKOFF_FACTOR ** status["retry_count"]),
        #             config.RETRY_MAX_DELAY
        #         )

        #         # Check if enough time has passed since last retry
        #         if current_time - status["last_retry"] < delay:
        #             continue

        #         # Get nodes that need retry (not delivered, in LORA mode, and have identity)
        #         retry_nodes = [
        #             node for node in lora_nodes
        #             if (node in status["nodes"] and  # Node is in our tracking
        #                 not status["nodes"][node] and  # Node hasn't received packet
        #                 self.peer_discovery.get_peer_identity(node))  # Node has valid identity
        #         ]

        #         if retry_nodes:
        #             # Read file data
        #             file_path = os.path.join(self.sent_buffer, filename)
        #             try:
        #                 with open(file_path, 'rb') as f:
        #                     data = f.read()
        #             except Exception as e:
        #                 self.logger.error(f"Error reading {filename} for retry: {e}")
        #                 continue

        #             # Only retry to the first node in this cycle
        #             node = retry_nodes[0]
        #             try:
        #                 if self.peer_discovery:  # Only try if peer_discovery exists
        #                     self.logger.info(f"Retrying {filename} to {node} (retry #{status['retry_count'] + 1})")
        #                     self.send_to_node(node, data, filename)
        #                     # Mark this transmission in our tracking
        #                     self.delivery_status[filename]["nodes"][node] = True
        #                     sent_something = True
                            
        #                     # Only try one packet per cycle
        #                     break
        #             except Exception as e:
        #                 self.logger.error(f"Error retrying {filename} to {node}: {e}")

        #             # Update retry tracking
        #             status["retry_count"] += 1
        #             status["last_retry"] = current_time

        #     return sent_something

        # except Exception as e:
        #     self.logger.error(f"Error processing retries: {e}")
        #     return False

    def process_outgoing(self, transmit_allowed=True):
        """Process files in pending directory, sends to all nodes sequentially"""
        try:
            # If transmission not allowed, just check and return
            if not transmit_allowed:
                return False
                
            # Get LORA nodes from node_status.json
            lora_nodes = self.get_lora_nodes()
            if not lora_nodes:
                return False
                
            # First process existing files in pending
            pending_files = [f for f in os.listdir(self.pending_dir) if f.endswith('.zst')]
            if not pending_files:
                return False
                
            # Filter to get valid nodes with identities
            valid_nodes = []
            for node in lora_nodes:
                try:
                    if self.peer_discovery.get_peer_identity(node):
                        valid_nodes.append(node)
                except Exception as e:
                    # Log error but continue with other nodes
                    self.logger.warning(f"Error checking identity for node {node}: {e}")

            if not valid_nodes:
                self.logger.warning("No valid nodes found with identities - will try again later")
                return False
                
            # Process oldest file first
            pending_files.sort()
            filename = pending_files[0]
            pending_path = os.path.join(self.pending_dir, filename)
            sent_path = os.path.join(self.sent_buffer, filename)
            
            # Check if we have this file in our tracking already
            if filename not in self.delivery_status:
                # Read file data
                with open(pending_path, 'rb') as f:
                    data = f.read()
                    
                # Initialize tracking with per-node structure
                self.delivery_status[filename] = {
                    "nodes": {
                        node: {
                            "sent": False,        # Have we sent to this node?
                            "sent_time": 0,       # When did we send to this node?
                            "delivered": False    # Have we received delivery confirmation?
                        } for node in valid_nodes
                    },
                    "retry_count": 0              # Keep retry_count for backward compatibility
                }
                
                # Find first node that needs sending
                for node in valid_nodes:
                    if not self.delivery_status[filename]["nodes"][node]["sent"]:
                        # Send to this node
                        try:
                            if self.peer_discovery and self.send_to_node(node, data, filename):
                                # Mark as sent and record time
                                current_time = time.time()
                                self.delivery_status[filename]["nodes"][node]["sent"] = True
                                self.delivery_status[filename]["nodes"][node]["sent_time"] = current_time
                                return True  # We sent something
                        except Exception as e:
                            self.logger.error(f"Error sending to {node}: {e}")
                            
                # We shouldn't get here unless something failed with all nodes
                return False
            else:
                # We're working with a file already in progress
                # Read file data
                with open(pending_path, 'rb') as f:
                    data = f.read()
                
                # Make sure all valid nodes are in our tracking structure
                # This handles newly discovered nodes since initial send
                for node in valid_nodes:
                    if node not in self.delivery_status[filename]["nodes"]:
                        self.logger.info(f"Adding newly discovered node {node} to tracking for {filename}")
                        self.delivery_status[filename]["nodes"][node] = {
                            "sent": False, 
                            "sent_time": 0,
                            "delivered": False
                        }
                
                # Find first node that needs sending
                for node in valid_nodes:
                    # Skip nodes we've already sent to
                    if node in self.delivery_status[filename]["nodes"] and not self.delivery_status[filename]["nodes"][node]["sent"]:
                        # Send to this node
                        try:
                            if self.peer_discovery and self.send_to_node(node, data, filename):
                                # Mark as sent and record time
                                current_time = time.time()
                                self.delivery_status[filename]["nodes"][node]["sent"] = True
                                self.delivery_status[filename]["nodes"][node]["sent_time"] = current_time
                                
                                # Check if we've sent to all nodes
                                all_sent = all(self.delivery_status[filename]["nodes"][node]["sent"] 
                                               for node in self.delivery_status[filename]["nodes"])
                                
                                # Only move to sent_buffer after sending to all nodes
                                if all_sent:
                                    os.rename(pending_path, sent_path)
                                    self.logger.info(f"Sent {filename} to all nodes, moved to sent buffer")
                                
                                return True  # We sent something
                        except Exception as e:
                            self.logger.error(f"Error sending to {node}: {e}")
                
                # If we get here, we've either sent to all nodes or all attempts failed
                # Check if we've sent to all nodes
                all_sent = all(self.delivery_status[filename]["nodes"][node]["sent"] 
                               for node in self.delivery_status[filename]["nodes"])
                
                # Only move to sent_buffer after sending to all nodes
                if all_sent and os.path.exists(pending_path):
                    os.rename(pending_path, sent_path)
                    self.logger.info(f"Sent {filename} to all nodes, moved to sent buffer")
                
                return False  # We didn't send anything new this cycle

        except Exception as e:
            self.logger.error(f"Error processing outgoing: {e}")
            return False

    def get_lora_nodes(self):
        """Get list of nodes that are in LORA mode and have peer discovery entries"""
        lora_nodes = []
        try:
            # First try to read node status
            with open(config.NODE_STATUS_PATH, 'r') as f:
                content = f.read()
                if not content.strip():
                    self.logger.error(f"Node status file is empty: {config.NODE_STATUS_PATH}")
                    return []
                status = json.loads(content)
                
                # More robust parsing of nodes with better error handling
                for node_data in status.get("nodes", {}).values():
                    try:
                        hostname = node_data.get("hostname")
                        mode = node_data.get("mode")
                        if hostname and mode == "LORA":
                            lora_nodes.append(hostname)
                    except Exception as e:
                        # Skip problematic nodes but continue processing others
                        self.logger.warning(f"Error processing node data {node_data}: {e}")
                        continue
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in node status file: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error reading node status file: {e}")
            return []

        try:
            # Then try to read peer discovery
            peer_discovery_path = os.path.join(os.path.dirname(config.NODE_STATUS_PATH), 
                "..", "tak_transmission/reticulum_module/new_implementation/peer_discovery.json")
            
            # Check if the file exists before trying to open it
            if not os.path.exists(peer_discovery_path):
                self.logger.error(f"Peer discovery file does not exist: {peer_discovery_path}")
                return []
                
            with open(peer_discovery_path, 'r') as f:
                content = f.read()
                if not content.strip():
                    self.logger.error(f"Peer discovery file is empty: {peer_discovery_path}")
                    return []
                    
                peer_status = json.loads(content)
                
                # Return only nodes that are both in LORA mode and have peer discovery entries
                filtered_nodes = []
                for node in lora_nodes:
                    try:
                        if node in peer_status.get("peers", {}):
                            filtered_nodes.append(node)
                    except Exception as e:
                        self.logger.warning(f"Error checking peer status for node {node}: {e}")
                        continue
                
                # Only log when the node count changes
                node_count = len(filtered_nodes)
                if self.previous_lora_node_count is None or self.previous_lora_node_count != node_count:
                    self.logger.info(f"Found {node_count} LORA nodes with peer identities")
                    self.previous_lora_node_count = node_count
                return filtered_nodes
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in peer discovery file: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error reading peer discovery file: {e}")
            return []

    def send_to_node(self, hostname, data, filename):
        """Send data to a specific node"""
        # Check if enough time has passed since last radio send
        current_time = time.time()
        if current_time - self.last_send_time < config.SEND_SPACING_DELAY:
            return False  # Too soon for radio

        # Get peer identity from peer_discovery with error handling
        try:
            peer_identity = self.peer_discovery.get_peer_identity(hostname)
            if not peer_identity:
                self.logger.error(f"No identity found for {hostname}")
                return False
        except Exception as e:
            self.logger.error(f"Error getting peer identity for {hostname}: {e}")
            return False

        # Create outbound destination with error handling
        try:
            destination = RNS.Destination(
                peer_identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                config.APP_NAME,
                config.ASPECT
            )
        except Exception as e:
            self.logger.error(f"Error creating destination for {hostname}: {e}")
            return False

        # Add log message before sending
        self.logger.info(f"Sending packet {filename} to node {hostname}")

        # Create and send packet with proof tracking
        try:
            packet = RNS.Packet(destination, data)
            receipt = packet.send()
        except Exception as e:
            self.logger.error(f"Error creating or sending packet to {hostname}: {e}")
            return False

        if receipt:
            # Set timeout and callbacks
            receipt.set_timeout(config.PACKET_TIMEOUT)

            def on_delivery(r):
                if r.get_status() == RNS.PacketReceipt.DELIVERED:
                    rtt = r.get_rtt()
                    if rtt >= 1:
                        rtt = round(rtt, 3)
                        rtt_str = f"{rtt} seconds"
                    else:
                        rtt = round(rtt * 1000, 3)
                        rtt_str = f"{rtt} milliseconds"
                        
                    self.logger.info(f"Packet {filename} delivered to {hostname} (RTT: {rtt_str})")
                    if filename in self.delivery_status:
                        # Update the delivery status
                        self.delivery_status[filename]["nodes"][hostname]["delivered"] = True
                        # Check if all nodes received
                        all_delivered = all(node_status["delivered"] for node_status in 
                                           self.delivery_status[filename]["nodes"].values())
                        if all_delivered:
                            # Use only the configured sent buffer path
                            sent_path = os.path.join(self.sent_buffer, filename)
                            try:
                                os.remove(sent_path)
                                self.logger.info(f"All nodes received {filename} - removed from sent buffer")
                            except Exception as e:
                                self.logger.error(f"Error removing {filename} from sent buffer: {e}")
                            
                            # Always clear from tracking even if file wasn't found
                            del self.delivery_status[filename]

            def on_timeout(r):
                self.logger.warning(f"Packet {filename} to {hostname} timed out")
                if filename in self.delivery_status:
                    # Remove the file from sent buffer
                    sent_path = os.path.join(self.sent_buffer, filename)
                    try:
                        os.remove(sent_path)
                        del self.delivery_status[filename]
                        self.logger.info(f"Removed timed out packet {filename} from sent buffer")
                    except Exception as e:
                        self.logger.error(f"Error removing timed out packet {filename} from sent buffer: {e}")

            receipt.set_delivery_callback(on_delivery)
            receipt.set_timeout_callback(on_timeout)
            
            # Update last send time
            self.last_send_time = current_time
            return True

        self.logger.error(f"Failed to send packet to {hostname}")
        return False

    def handle_incoming_packet(self, data, packet):
        """Handle incoming packets by moving to incoming directory"""
        try:
            # Generate unique filename with timestamp
            timestamp = int(time.time())
            filename = f"incoming_{timestamp}.zst"
            file_path = os.path.join(self.incoming_dir, filename)
            
            # Write data to file
            with open(file_path, 'wb') as f:
                f.write(data)
                
            self.logger.info(f"Received packet, saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error handling incoming packet: {e}")

    def stop(self):
        """Stop the packet manager"""
        self.should_quit = True

if __name__ == "__main__":
    manager = PacketManager()
    manager.run()
