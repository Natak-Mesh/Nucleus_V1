#!/usr/bin/env python3
"""
TAK Protocol v1 Compressor using Zstandard

This module provides a clean, importable interface for compressing TAK Protocol v1 (CoT) packets
using Zstandard compression with a pre-trained dictionary.

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

# Default compression level
DEFAULT_COMPRESSION_LEVEL = 22

# Default maximum compressed packet size (bytes)
DEFAULT_MAX_COMPRESSED_SIZE = 350

class CoTZstdCompressor:
    """
    Compressor for TAK Protocol v1 (CoT) packets using Zstandard compression.
    """
    
    def __init__(self, dict_path=DEFAULT_DICT_PATH, level=DEFAULT_COMPRESSION_LEVEL, 
                 max_compressed_size=DEFAULT_MAX_COMPRESSED_SIZE):
        """
        Initialize the compressor.
        
        Args:
            dict_path: Path to the Zstd dictionary file
            level: Compression level (1-22, higher = better compression but slower)
            max_compressed_size: Maximum allowed size for compressed packets (bytes)
        """
        self.dict_path = dict_path
        self.level = level
        self.max_compressed_size = max_compressed_size
        
        # Load dictionary and create compressor
        self.dict_data = self._load_dictionary()
        self.compressor = zstd.ZstdCompressor(level=self.level, dict_data=self.dict_data)
        
        # Stats
        self.packets_processed = 0
        self.packets_compressed = 0
        self.packets_skipped = 0
        self.total_original_bytes = 0
        self.total_compressed_bytes = 0
        
    def _load_dictionary(self):
        """Load the Zstd dictionary from file."""
        if not os.path.exists(self.dict_path):
            raise FileNotFoundError(f"Dictionary file not found: {self.dict_path}")
            
        with open(self.dict_path, 'rb') as f:
            dict_data = f.read()
            
        return zstd.ZstdCompressionDict(dict_data)
        
    def compress_packet(self, packet_data):
        """
        Compress a single CoT packet.
        
        Args:
            packet_data: Raw binary packet data (bytes)
            
        Returns:
            Compressed packet data (bytes) if successful and compressed size <= max_compressed_size
            None if compressed packet is too large or compression fails
        """
        self.packets_processed += 1
        
        # Record original size
        original_size = len(packet_data)
        self.total_original_bytes += original_size
            
        # Compress the packet
        try:
            compressed_data = self.compressor.compress(packet_data)
            compressed_size = len(compressed_data)
            
            # Check compressed size
            if compressed_size > self.max_compressed_size:
                self.packets_skipped += 1
                return None
                
            self.total_compressed_bytes += compressed_size
            self.packets_compressed += 1
            
            return compressed_data
            
        except Exception as e:
            print(f"Compression error: {e}")
            self.packets_skipped += 1
            return None
            
    def get_stats(self):
        """Get compression statistics."""
        if self.packets_processed == 0:
            return {
                'packets_processed': 0,
                'packets_compressed': 0,
                'packets_skipped': 0,
                'compression_ratio': 0,
                'avg_original_size': 0,
                'avg_compressed_size': 0
            }
            
        return {
            'packets_processed': self.packets_processed,
            'packets_compressed': self.packets_compressed,
            'packets_skipped': self.packets_skipped,
            'compression_ratio': self.total_original_bytes / self.total_compressed_bytes if self.total_compressed_bytes > 0 else 0,
            'avg_original_size': self.total_original_bytes / self.packets_processed,
            'avg_compressed_size': self.total_compressed_bytes / self.packets_compressed if self.packets_compressed > 0 else 0
        }
        
    def print_stats(self):
        """Print compression statistics."""
        stats = self.get_stats()
        
        print("\nCompression Statistics:")
        print(f"Packets processed: {stats['packets_processed']}")
        print(f"Packets compressed: {stats['packets_compressed']}")
        print(f"Packets skipped (too large): {stats['packets_skipped']}")
        
        if stats['packets_compressed'] > 0:
            print(f"Average original size: {stats['avg_original_size']:.2f} bytes")
            print(f"Average compressed size: {stats['avg_compressed_size']:.2f} bytes")
            print(f"Compression ratio: {stats['compression_ratio']:.2f}x")
            
# Module-level function for easy importing
def compress_cot_packet(raw_packet_bytes, dict_path=DEFAULT_DICT_PATH, 
                       level=DEFAULT_COMPRESSION_LEVEL, max_size=DEFAULT_MAX_COMPRESSED_SIZE):
    """
    Compress a raw CoT packet.
    
    Args:
        raw_packet_bytes: The raw binary CoT packet
        dict_path: Path to the Zstd dictionary file
        level: Compression level (1-22, higher = better compression but slower)
        max_size: Maximum allowed size for compressed packet (bytes)
        
    Returns:
        Compressed packet bytes if successful and compressed size <= max_size
        None if compressed packet is too large or compression fails
    """
    # Load dictionary and create compressor
    try:
        with open(dict_path, 'rb') as f:
            dict_data = f.read()
            
        dict_obj = zstd.ZstdCompressionDict(dict_data)
        compressor = zstd.ZstdCompressor(level=level, dict_data=dict_obj)
        
        # Compress the packet
        compressed_data = compressor.compress(raw_packet_bytes)
        
        # Check compressed size
        if len(compressed_data) > max_size:
            return None
            
        return compressed_data
        
    except Exception as e:
        print(f"Compression error: {e}")
        return None

# Standalone script functionality
def run_multicast_listener(compressor, multicast_addrs, ports, output_dir=None):
    """
    Run a multicast listener that compresses CoT packets.
    
    Args:
        compressor: CoTZstdCompressor instance
        multicast_addrs: List of multicast addresses to listen on
        ports: List of ports to listen on
        output_dir: Directory to save compressed packets (optional)
    """
    # Create output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    # Set up sockets
    sockets = []
    for addr, port in zip(multicast_addrs, ports):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', port))
        
        # Add socket to multicast group
        mreq = struct.pack("4sl", socket.inet_aton(addr), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        sockets.append((sock, addr, port))
        print(f"Listening on {addr}:{port}")
        
    print("\nCompressing CoT packets... Press Ctrl+C to stop\n")
    
    try:
        while True:
            for sock, addr, port in sockets:
                sock.settimeout(0.1)  # Small timeout for non-blocking
                try:
                    data, src = sock.recvfrom(65535)
                    
                    # Compress the packet
                    compressed_data = compressor.compress_packet(data)
                    
                    # Print info
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if compressed_data:
                        compression_ratio = len(data) / len(compressed_data)
                        print(f"[{timestamp}] Compressed packet: {len(data)} → {len(compressed_data)} bytes ({compression_ratio:.2f}x)")
                        
                        # Save compressed packet if output directory specified
                        if output_dir:
                            filename = f"compressed_{timestamp.replace(' ', '_').replace(':', '-')}_{addr}_{port}.bin"
                            filepath = os.path.join(output_dir, filename)
                            with open(filepath, 'wb') as f:
                                f.write(compressed_data)
                    else:
                        print(f"[{timestamp}] Skipped packet: {len(data)} bytes (too large)")
                        
                except socket.timeout:
                    continue
                    
    except KeyboardInterrupt:
        compressor.print_stats()
        
    finally:
        # Clean up sockets
        for sock, _, _ in sockets:
            sock.close()

def main():
    """Main function for standalone script."""
    parser = argparse.ArgumentParser(description='Compress TAK Protocol v1 (CoT) packets using Zstandard')
    parser.add_argument('--dict-path', default=DEFAULT_DICT_PATH, help='Path to the Zstd dictionary file')
    parser.add_argument('--level', type=int, default=DEFAULT_COMPRESSION_LEVEL, help='Compression level (1-22)')
    parser.add_argument('--max-size', type=int, default=DEFAULT_MAX_COMPRESSED_SIZE, help='Maximum compressed packet size (bytes)')
    parser.add_argument('--output-dir', help='Directory to save compressed packets')
    
    args = parser.parse_args()
    
    print("TAK Protocol v1 Compression with Zstandard")
    print("=" * 50)
    
    # Create compressor
    compressor = CoTZstdCompressor(
        dict_path=args.dict_path,
        level=args.level,
        max_compressed_size=args.max_size
    )
    
    # ATAK multicast addresses and ports
    multicast_addrs = ["224.10.10.1", "239.2.3.1", "239.5.5.55"]
    ports = [17012, 6969, 7171]
    
    # Run multicast listener
    run_multicast_listener(compressor, multicast_addrs, ports, args.output_dir)

if __name__ == "__main__":
    main()
