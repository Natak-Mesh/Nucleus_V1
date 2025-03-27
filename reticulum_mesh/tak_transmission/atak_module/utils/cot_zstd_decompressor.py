#!/usr/bin/env python3
"""
TAK Protocol v1 Decompressor using Zstandard

This module provides a clean, importable interface for decompressing TAK Protocol v1 (CoT) packets
that were compressed using Zstandard compression with a pre-trained dictionary.

It can be used as a standalone script or imported as a module by other scripts.
"""

import os
import zstandard as zstd
import socket
import struct
import argparse
import time
from datetime import datetime

# Default dictionary path
DEFAULT_DICT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                'cot_dict_131072.zstd')

class CoTZstdDecompressor:
    """
    Decompressor for TAK Protocol v1 (CoT) packets using Zstandard compression.
    """
    
    def __init__(self, dict_path=DEFAULT_DICT_PATH):
        """
        Initialize the decompressor.
        
        Args:
            dict_path: Path to the Zstd dictionary file
        """
        self.dict_path = dict_path
        
        # Load dictionary and create decompressor
        self.dict_data = self._load_dictionary()
        self.decompressor = zstd.ZstdDecompressor(dict_data=self.dict_data)
        
        # Stats
        self.packets_processed = 0
        self.packets_decompressed = 0
        self.packets_failed = 0
        self.total_compressed_bytes = 0
        self.total_decompressed_bytes = 0
        
    def _load_dictionary(self):
        """Load the Zstd dictionary from file."""
        if not os.path.exists(self.dict_path):
            raise FileNotFoundError(f"Dictionary file not found: {self.dict_path}")
            
        with open(self.dict_path, 'rb') as f:
            dict_data = f.read()
            
        return zstd.ZstdCompressionDict(dict_data)
        
    def decompress_packet(self, compressed_data):
        """
        Decompress a single compressed CoT packet.
        
        Args:
            compressed_data: Compressed binary packet data (bytes)
            
        Returns:
            Decompressed packet data (bytes) if successful
            None if decompression fails
        """
        self.packets_processed += 1
        
        # Update stats
        compressed_size = len(compressed_data)
        self.total_compressed_bytes += compressed_size
        
        # Decompress the packet
        try:
            decompressed_data = self.decompressor.decompress(compressed_data)
            decompressed_size = len(decompressed_data)
            self.total_decompressed_bytes += decompressed_size
            self.packets_decompressed += 1
            
            return decompressed_data
            
        except Exception as e:
            print(f"Decompression error: {e}")
            self.packets_failed += 1
            return None
            
    def get_stats(self):
        """Get decompression statistics."""
        if self.packets_processed == 0:
            return {
                'packets_processed': 0,
                'packets_decompressed': 0,
                'packets_failed': 0,
                'expansion_ratio': 0,
                'avg_compressed_size': 0,
                'avg_decompressed_size': 0
            }
            
        return {
            'packets_processed': self.packets_processed,
            'packets_decompressed': self.packets_decompressed,
            'packets_failed': self.packets_failed,
            'expansion_ratio': self.total_decompressed_bytes / self.total_compressed_bytes if self.total_compressed_bytes > 0 else 0,
            'avg_compressed_size': self.total_compressed_bytes / self.packets_processed,
            'avg_decompressed_size': self.total_decompressed_bytes / self.packets_decompressed if self.packets_decompressed > 0 else 0
        }
        
    def print_stats(self):
        """Print decompression statistics."""
        stats = self.get_stats()
        
        print("\nDecompression Statistics:")
        print(f"Packets processed: {stats['packets_processed']}")
        print(f"Packets decompressed: {stats['packets_decompressed']}")
        print(f"Packets failed: {stats['packets_failed']}")
        
        if stats['packets_decompressed'] > 0:
            print(f"Average compressed size: {stats['avg_compressed_size']:.2f} bytes")
            print(f"Average decompressed size: {stats['avg_decompressed_size']:.2f} bytes")
            print(f"Expansion ratio: {stats['expansion_ratio']:.2f}x")
            
# Module-level function for easy importing
def decompress_cot_packet(compressed_packet_bytes, dict_path=DEFAULT_DICT_PATH):
    """
    Decompress a compressed CoT packet.
    
    Args:
        compressed_packet_bytes: The compressed binary packet
        dict_path: Path to the Zstd dictionary file
        
    Returns:
        Original raw CoT packet bytes if successful
        None if decompression fails
    """
    # Load dictionary and create decompressor
    try:
        with open(dict_path, 'rb') as f:
            dict_data = f.read()
            
        dict_obj = zstd.ZstdCompressionDict(dict_data)
        decompressor = zstd.ZstdDecompressor(dict_data=dict_obj)
        
        # Decompress the packet
        return decompressor.decompress(compressed_packet_bytes)
        
    except Exception as e:
        print(f"Decompression error: {e}")
        return None

# Standalone script functionality
def process_compressed_directory(decompressor, input_dir, output_dir=None, forward_to=None):
    """
    Process a directory of compressed packets.
    
    Args:
        decompressor: CoTZstdDecompressor instance
        input_dir: Directory containing compressed packets
        output_dir: Directory to save decompressed packets (optional)
        forward_to: Tuple of (host, port) to forward decompressed packets to (optional)
    """
    # Check input directory
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
    # Create output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    # Create forwarding socket if specified
    forward_socket = None
    if forward_to:
        forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    # Get compressed packet files
    compressed_files = [f for f in os.listdir(input_dir) if f.endswith('.bin')]
    if not compressed_files:
        print(f"No compressed packet files found in {input_dir}")
        return
        
    print(f"Found {len(compressed_files)} compressed packet files")
    
    # Process each file
    for filename in compressed_files:
        filepath = os.path.join(input_dir, filename)
        
        # Read compressed data
        with open(filepath, 'rb') as f:
            compressed_data = f.read()
            
        # Decompress the packet
        decompressed_data = decompressor.decompress_packet(compressed_data)
        
        if decompressed_data:
            # Print info
            compression_ratio = len(decompressed_data) / len(compressed_data)
            print(f"Decompressed packet: {len(compressed_data)} → {len(decompressed_data)} bytes ({compression_ratio:.2f}x)")
            
            # Save decompressed packet if output directory specified
            if output_dir:
                output_filename = f"decompressed_{filename}"
                output_filepath = os.path.join(output_dir, output_filename)
                with open(output_filepath, 'wb') as f:
                    f.write(decompressed_data)
                    
            # Forward decompressed packet if specified
            if forward_socket and forward_to:
                forward_socket.sendto(decompressed_data, forward_to)
                print(f"Forwarded to {forward_to[0]}:{forward_to[1]}")
        else:
            print(f"Failed to decompress packet: {filename}")
            
    # Print stats
    decompressor.print_stats()
    
    # Clean up
    if forward_socket:
        forward_socket.close()

def run_udp_listener(decompressor, listen_port, forward_to=None, output_dir=None):
    """
    Run a UDP listener that decompresses incoming compressed CoT packets.
    
    Args:
        decompressor: CoTZstdDecompressor instance
        listen_port: Port to listen on for compressed packets
        forward_to: Tuple of (host, port) to forward decompressed packets to (optional)
        output_dir: Directory to save decompressed packets (optional)
    """
    # Create output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    # Create listening socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', listen_port))
    
    # Create forwarding socket if specified
    forward_socket = None
    if forward_to:
        forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    print(f"Listening for compressed packets on port {listen_port}")
    if forward_to:
        print(f"Forwarding decompressed packets to {forward_to[0]}:{forward_to[1]}")
        
    print("\nDecompressing CoT packets... Press Ctrl+C to stop\n")
    
    try:
        while True:
            try:
                data, src = sock.recvfrom(65535)
                
                # Decompress the packet
                decompressed_data = decompressor.decompress_packet(data)
                
                # Print info
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if decompressed_data:
                    expansion_ratio = len(decompressed_data) / len(data)
                    print(f"[{timestamp}] Decompressed packet from {src[0]}:{src[1]}: {len(data)} → {len(decompressed_data)} bytes ({expansion_ratio:.2f}x)")
                    
                    # Save decompressed packet if output directory specified
                    if output_dir:
                        filename = f"decompressed_{timestamp.replace(' ', '_').replace(':', '-')}_{src[0]}_{src[1]}.bin"
                        filepath = os.path.join(output_dir, filename)
                        with open(filepath, 'wb') as f:
                            f.write(decompressed_data)
                            
                    # Forward decompressed packet if specified
                    if forward_socket and forward_to:
                        forward_socket.sendto(decompressed_data, forward_to)
                else:
                    print(f"[{timestamp}] Failed to decompress packet from {src[0]}:{src[1]}")
                    
            except socket.timeout:
                continue
                
    except KeyboardInterrupt:
        decompressor.print_stats()
        
    finally:
        # Clean up sockets
        sock.close()
        if forward_socket:
            forward_socket.close()

def main():
    """Main function for standalone script."""
    parser = argparse.ArgumentParser(description='Decompress TAK Protocol v1 (CoT) packets using Zstandard')
    parser.add_argument('--dict-path', default=DEFAULT_DICT_PATH, help='Path to the Zstd dictionary file')
    parser.add_argument('--input-dir', help='Directory containing compressed packets to process')
    parser.add_argument('--output-dir', help='Directory to save decompressed packets')
    parser.add_argument('--listen-port', type=int, help='Port to listen on for compressed packets')
    parser.add_argument('--forward-host', help='Host to forward decompressed packets to')
    parser.add_argument('--forward-port', type=int, help='Port to forward decompressed packets to')
    
    args = parser.parse_args()
    
    print("TAK Protocol v1 Decompression with Zstandard")
    print("=" * 50)
    
    # Create decompressor
    decompressor = CoTZstdDecompressor(dict_path=args.dict_path)
    
    # Determine forwarding target
    forward_to = None
    if args.forward_host and args.forward_port:
        forward_to = (args.forward_host, args.forward_port)
        
    # Process input directory or run UDP listener
    if args.input_dir:
        process_compressed_directory(decompressor, args.input_dir, args.output_dir, forward_to)
    elif args.listen_port:
        run_udp_listener(decompressor, args.listen_port, forward_to, args.output_dir)
    else:
        print("Error: Either --input-dir or --listen-port must be specified")
        parser.print_help()

if __name__ == "__main__":
    main()
