#!/usr/bin/env python3

"""
File operations manager for the Reticulum handler.
Handles saving incoming files, processing outgoing files, and directory management.
"""

import os
import shutil
from datetime import datetime
from . import config
from . import logger

class FileManager:
    """
    Manages all file operations for the Reticulum handler.
    
    This includes:
    - Creating and managing directories
    - Saving incoming message data to files
    - Processing files in the pending directory
    """
    
    def __init__(self):
        """Initialize the file manager"""
        self.logger = logger.get_logger("FileManager")
        
        # Directory paths
        self.incoming_dir = config.INCOMING_DIR
        self.pending_dir = config.PENDING_DIR
        self.processing_dir = config.PROCESSING_DIR
        self.sent_buffer_dir = config.SENT_BUFFER_DIR
        
        # Create directories on initialization
        self.create_directories()
    
    def create_directories(self):
        """Ensure all required directories exist"""
        try:
            directories = [
                self.incoming_dir,
                self.pending_dir,
                self.processing_dir,
                self.sent_buffer_dir
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                
            self.logger.debug(f"Created all required directories")
        except Exception as e:
            self.logger.error(f"Error creating directories: {e}")
    
    def save_incoming_file(self, data, source_hostname="unknown"):
        """
        Save incoming message data to a file
        
        Args:
            data (bytes): Raw message data
            source_hostname (str): Source hostname for logging
            
        Returns:
            tuple: (success, filename) - success is a boolean, filename is the saved filename
        """
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"incoming_{timestamp}.zst"
            file_path = os.path.join(self.incoming_dir, filename)
            
            # Write data to file
            with open(file_path, 'wb') as f:
                f.write(data)
            
            self.logger.info(f"SAVED: Message from {source_hostname} saved to {filename}")
            return True, filename
            
        except Exception as e:
            self.logger.error(f"Error saving incoming file from {source_hostname}: {e}")
            return False, None
    
    def save_to_buffer(self, data, filename):
        """
        Save a copy of outgoing data to the buffer directory for retry purposes
        
        Args:
            data (bytes): Raw message data
            filename (str): Filename to use
            
        Returns:
            tuple: (success, buffer_path) - success is a boolean, buffer_path is the path in buffer
        """
        try:
            buffer_path = os.path.join(self.sent_buffer_dir, filename)
            
            with open(buffer_path, 'wb') as f:
                f.write(data)
                
            self.logger.debug(f"Saved {filename} to buffer directory for potential retries")
            return True, buffer_path
            
        except Exception as e:
            self.logger.error(f"Error saving file to buffer: {e}")
            return False, None
    
    def delete_buffer_file(self, buffer_path):
        """Delete a file from the buffer directory"""
        try:
            if os.path.exists(buffer_path):
                os.remove(buffer_path)
                self.logger.debug(f"Removed buffer file: {os.path.basename(buffer_path)}")
                return True
        except Exception as e:
            self.logger.error(f"Error removing buffer file: {e}")
        
        return False
    
    def get_pending_files(self, sort=True):
        """
        Get list of files in the pending directory
        
        Args:
            sort (bool): Whether to sort files by timestamp (default True)
            
        Returns:
            list: List of filenames in the pending directory
        """
        try:
            # Get list of .zst files in pending directory
            pending_files = [f for f in os.listdir(self.pending_dir) if f.endswith('.zst')]
            
            # Sort by timestamp (assuming filename contains timestamp)
            if sort and pending_files:
                pending_files.sort()
                
            return pending_files
            
        except Exception as e:
            self.logger.error(f"Error listing pending files: {e}")
            return []
    
    def move_to_processing(self, filename):
        """
        Move a file from pending to processing directory
        
        Args:
            filename (str): The filename to move
            
        Returns:
            tuple: (success, processing_path) - success is a boolean, processing_path is the new path
        """
        try:
            pending_path = os.path.join(self.pending_dir, filename)
            processing_path = os.path.join(self.processing_dir, filename)
            
            # Check if file exists
            if not os.path.exists(pending_path):
                self.logger.warning(f"File not found in pending directory: {filename}")
                return False, None
            
            # Atomic move
            os.rename(pending_path, processing_path)
            self.logger.debug(f"Moved {filename} from pending to processing")
            
            return True, processing_path
            
        except Exception as e:
            self.logger.error(f"Error moving file to processing: {e}")
            return False, None
    
    def read_processing_file(self, filename):
        """
        Read data from a file in the processing directory
        
        Args:
            filename (str): The filename to read
            
        Returns:
            tuple: (success, data) - success is a boolean, data is the file contents or None
        """
        try:
            processing_path = os.path.join(self.processing_dir, filename)
            
            if not os.path.exists(processing_path):
                self.logger.warning(f"File not found in processing directory: {filename}")
                return False, None
            
            with open(processing_path, 'rb') as f:
                data = f.read()
                
            return True, data
            
        except Exception as e:
            self.logger.error(f"Error reading processing file: {e}")
            return False, None
    
    def remove_processing_file(self, filename):
        """
        Remove a file from the processing directory
        
        Args:
            filename (str): The filename to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            processing_path = os.path.join(self.processing_dir, filename)
            
            if os.path.exists(processing_path):
                os.remove(processing_path)
                self.logger.debug(f"Removed file from processing: {filename}")
                return True
            else:
                self.logger.warning(f"File not found in processing directory: {filename}")
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing processing file: {e}")
            return False
