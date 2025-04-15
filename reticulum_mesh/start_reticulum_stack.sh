#!/bin/bash
cd /home/natak/reticulum_mesh/tak_transmission/reticulum_module/new_implementation
export PYTHONPATH=$PYTHONPATH:/home/natak/.local/lib/python3.11/site-packages
exec python3 -u test_setup.py
