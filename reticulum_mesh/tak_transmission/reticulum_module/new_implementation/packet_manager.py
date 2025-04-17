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
        self.delivery_status = {}  # filename -> {nodes: {hostname: delivered}, first_sent: time, last_retry: time, retry_count: int}
        self.last_send_time = 0  # timestamp of last send to respect radio cycle time
        
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
                self.process_outgoing()
                self.process_retries()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")

    def process_retries(self):
        """Check sent_buffer for failed deliveries and retry if needed"""
        try:
            current_time = time.time()
            lora_nodes = self.get_lora_nodes()

            # Process each file in delivery status
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
                    continue

                # Calculate backoff delay
                delay = min(
                    config.RETRY_INITIAL_DELAY * (config.RETRY_BACKOFF_FACTOR ** status["retry_count"]),
                    config.RETRY_MAX_DELAY
                )

                # Check if enough time has passed since last retry
                if current_time - status["last_retry"] < delay:
                    continue

                # Get nodes that need retry (not delivered, in LORA mode, and have identity)
                retry_nodes = [
                    node for node in lora_nodes
                    if (node in status["nodes"] and  # Node is in our tracking
                        not status["nodes"][node] and  # Node hasn't received packet
                        self.peer_discovery.get_peer_identity(node))  # Node has valid identity
                ]

                if retry_nodes:
                    # Read file data
                    file_path = os.path.join(self.sent_buffer, filename)
                    try:
                        with open(file_path, 'rb') as f:
                            data = f.read()
                    except Exception as e:
                        self.logger.error(f"Error reading {filename} for retry: {e}")
                        continue

                    # Retry sending to each failed node
                    for node in retry_nodes:
                        try:
                            if self.peer_discovery:  # Only try if peer_discovery exists
                                self.logger.info(f"Retrying {filename} to {node} (retry #{status['retry_count'] + 1})")
                                self.send_to_node(node, data, filename)
                        except Exception as e:
                            self.logger.error(f"Error retrying {filename} to {node}: {e}")
                            continue  # Continue to next node even if this one fails

                    # Update retry tracking
                    status["retry_count"] += 1
                    status["last_retry"] = current_time

        except Exception as e:
            self.logger.error(f"Error processing retries: {e}")

    def process_outgoing(self):
        """Process files in pending directory"""
        try:
            # Get list of files in pending
            pending_files = [f for f in os.listdir(self.pending_dir) if f.endswith('.zst')]
            if not pending_files:
                return

            # Get LORA nodes from node_status.json
            lora_nodes = self.get_lora_nodes()
            if not lora_nodes:
                return

            # Process oldest file first
            pending_files.sort()
            filename = pending_files[0]
            pending_path = os.path.join(self.pending_dir, filename)
            sent_path = os.path.join(self.sent_buffer, filename)

            # Read file data
            with open(pending_path, 'rb') as f:
                data = f.read()

            # Initialize delivery tracking - only for nodes we have identities for
            filename = os.path.basename(pending_path)
            valid_nodes = [node for node in lora_nodes if self.peer_discovery.get_peer_identity(node)]
            self.delivery_status[filename] = {
                "nodes": {node: False for node in valid_nodes},
                "first_sent": time.time(),
                "last_retry": time.time(),
                "retry_count": 0
            }

            # Send to each valid node
            for node in valid_nodes:
                try:
                    if self.peer_discovery:  # Only try if peer_discovery exists
                        self.send_to_node(node, data, filename)
                except Exception as e:
                    self.logger.error(f"Error sending to {node}: {e}")
                    continue  # Continue to next node even if this one fails

            # Move to sent buffer
            os.rename(pending_path, sent_path)

        except Exception as e:
            self.logger.error(f"Error processing outgoing: {e}")

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
                lora_nodes = [
                    node["hostname"] 
                    for node in status.get("nodes", {}).values()
                    if node.get("mode") == "LORA"
                ]
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
            with open(peer_discovery_path, 'r') as f:
                content = f.read()
                if not content.strip():
                    self.logger.error(f"Peer discovery file is empty: {peer_discovery_path}")
                    return []
                peer_status = json.loads(content)
                return [
                    node for node in lora_nodes
                    if node in peer_status.get("peers", {})
                ]
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

        # Get peer identity from peer_discovery
        peer_identity = self.peer_discovery.get_peer_identity(hostname)
        if not peer_identity:
            self.logger.error(f"No identity found for {hostname}")
            return False

        # Create outbound destination
        destination = RNS.Destination(
            peer_identity,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            config.APP_NAME,
            config.ASPECT
        )

        # Add log message before sending
        self.logger.info(f"Sending packet {filename} to node {hostname}")

        # Create and send packet with proof tracking
        packet = RNS.Packet(destination, data)
        receipt = packet.send()

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
                        self.delivery_status[filename]["nodes"][hostname] = True
                        # Check if all nodes received
                        if all(self.delivery_status[filename]["nodes"].values()):
                            # Remove file from sent buffer
                            sent_path = os.path.join(self.sent_buffer, filename)
                            try:
                                os.remove(sent_path)
                                del self.delivery_status[filename]
                                self.logger.info(f"All nodes received {filename} - removed from sent buffer")
                            except Exception as e:
                                self.logger.error(f"Error removing {filename} from sent buffer: {e}")

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
