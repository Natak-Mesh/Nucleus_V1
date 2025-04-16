#!/bin/bash

# Clean up old packet files
rm -f /home/natak/reticulum_mesh/tak_transmission/shared/pending/*.zst
rm -f /home/natak/reticulum_mesh/tak_transmission/shared/sent_buffer/*.zst
rm -f /home/natak/reticulum_mesh/tak_transmission/shared/processing/*.zst
rm -f /home/natak/reticulum_mesh/tak_transmission/shared/incoming/*.zst

cd /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation
export PYTHONPATH=$PYTHONPATH:/home/natak/.local/lib/python3.11/site-packages
exec python3 -u test_setup.py
