#!/usr/bin/env python3

"""
Configuration settings for the Reticulum handler.
This module centralizes all constants and configuration values.
"""

import os

# Reticulum configuration
APP_NAME = "atak"
ASPECT = "cot"
ANNOUNCE_INTERVAL = 60  # 1 minute
PEER_TIMEOUT = 300      # 5 minutes
STARTUP_DELAY = 10      # 10 seconds for LoRa radio
LINK_TIMEOUT = 600      # 10 minutes link inactivity timeout
LINK_KEEPALIVE = 120    # 2 minutes - more frequent keepalives for better link maintenance

# File paths
BASE_DIR = "/home/natak/reticulum_mesh"
NODE_STATUS_PATH = f"{BASE_DIR}/ogm_monitor/node_status.json"
IDENTITY_MAP_PATH = f"{BASE_DIR}/identity_handler/identity_map.json"
PEER_STATUS_PATH = f"{BASE_DIR}/tak_transmission/reticulum_module/new_implementation/peer_status.json"
LINK_STATUS_PATH = f"{BASE_DIR}/tak_transmission/reticulum_module/new_implementation/link_status.json"
LOG_DIR = f"{BASE_DIR}/logs"

# Data directories
INCOMING_DIR = f"{BASE_DIR}/tak_transmission/shared/incoming"
PENDING_DIR = f"{BASE_DIR}/tak_transmission/shared/pending"
PROCESSING_DIR = f"{BASE_DIR}/tak_transmission/shared/processing"
SENT_BUFFER_DIR = f"{BASE_DIR}/tak_transmission/shared/sent_buffer"

# Retry mechanism configuration
RETRY_INITIAL_DELAY = 10     # seconds - Base delay for first retry
RETRY_BACKOFF_FACTOR = 2     # Multiplier for delay increase (doubles each time)
RETRY_MAX_DELAY = 120        # seconds - Maximum allowed delay between retries
RETRY_JITTER = 0.3           # +/- 30% randomness added to calculated delay
RETRY_MAX_ATTEMPTS = 5       # Max number of retry attempts before giving up
RETRY_RATE_LIMIT = 1         # Max number of retries per second

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
PACKET_LOG_MAX_LINES = 100

# Thread sleep intervals (in seconds)
LINK_MONITOR_INTERVAL = 60   # Check link status every minute
NODE_MONITOR_INTERVAL = 5    # Check node modes every 5 seconds
RETRY_CHECK_INTERVAL = 1     # Check for pending retries every second
