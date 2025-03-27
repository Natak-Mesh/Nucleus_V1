#!/usr/bin/env python3

"""
Compression utilities for ATAK packet handling.
Uses the existing cot_zstd_compressor and decompressor implementations.
"""

from typing import Optional
from .cot_zstd_compressor import compress_cot_packet as _compress_cot_packet
from .cot_zstd_decompressor import decompress_cot_packet as _decompress_cot_packet

def compress_cot_packet(data: bytes, dict_path: Optional[str] = None, max_size: int = 350) -> Optional[bytes]:
    """Compress a CoT packet using zstd with dictionary support"""
    return _compress_cot_packet(data, max_size=max_size)

def decompress_cot_packet(data: bytes, dict_path: Optional[str] = None) -> Optional[bytes]:
    """Decompress a CoT packet using zstd with dictionary support"""
    return _decompress_cot_packet(data)
