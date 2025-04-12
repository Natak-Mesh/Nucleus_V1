#!/usr/bin/env python3

"""
Enhanced logging system for the Reticulum handler.
Provides consistent logging across all components.
"""

import os
import logging
from datetime import datetime
from . import config

class RotatingHandler(logging.FileHandler):
    """Custom file handler that maintains last N lines"""
    def __init__(self, filename, mode='a', encoding=None, delay=False, max_lines=100):
        super().__init__(filename, mode, encoding, delay)
        self.max_lines = max_lines
        
    def emit(self, record):
        try:
            # Read existing lines
            lines = []
            if os.path.exists(self.baseFilename):
                with open(self.baseFilename, 'r') as f:
                    lines = f.readlines()
            
            # Add new line
            lines.append(self.format(record) + '\n')
            
            # Keep only last max_lines
            lines = lines[-self.max_lines:]
            
            # Write back to file
            with open(self.baseFilename, 'w') as f:
                f.writelines(lines)
        except Exception:
            self.handleError(record)

def setup_logger(name, log_file=None, level=None):
    """Set up a logger with console and optional file output"""
    # Ensure log directory exists
    os.makedirs(config.LOG_DIR, exist_ok=True)
    
    # Create logger with the specified name
    logger = logging.getLogger(name)
    
    # Set log level from config or parameter
    log_level = level or getattr(logging, config.LOG_LEVEL)
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers if this logger was already set up
    if logger.handlers:
        return logger
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create formatter and add to console handler
    formatter = logging.Formatter(config.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # Add file handler if a log file is specified
    if log_file:
        file_path = os.path.join(config.LOG_DIR, log_file)
        file_handler = RotatingHandler(
            file_path,
            max_lines=config.PACKET_LOG_MAX_LINES
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(file_handler)
    
    return logger

def get_logger(component_name, log_file=None):
    """Get a configured logger for a component"""
    return setup_logger(component_name, log_file)
