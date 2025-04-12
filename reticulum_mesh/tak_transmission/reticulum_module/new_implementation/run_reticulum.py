#!/usr/bin/env python3

"""
Entry point script for running the Reticulum handler.
"""

import sys
import os
import signal

# Add the parent directory to path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from new_implementation.reticulum_handler import ReticulumHandler

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down...")
    sys.exit(0)

def main():
    """Main entry point"""
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Starting Reticulum Handler...")
    
    try:
        # Create and start handler
        handler = ReticulumHandler()
        
        # Run the handler
        handler.run()
    except Exception as e:
        print(f"Error starting Reticulum Handler: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
