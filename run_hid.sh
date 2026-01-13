#!/bin/bash

# Run the HID setup script with sudo
sudo sh /home/hid.sh
# Wait for a moment to ensure the HID devices are set up
sleep 1
# Navigate to the project directory
cd /home/igor/Desktop/Talk_to_spech_HID/
# Activate the virtual environment and run the main Python script with sudo
sudo  ./venv/bin/python3 main.py