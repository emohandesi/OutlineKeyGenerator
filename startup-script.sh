#!/bin/bash

# Vultr startup script
# This script will run automatically when deploying a new instance

# Update package lists and upgrade existing packages
sudo apt-get update -y && sudo apt-get upgrade -y

# Install tmux, vnstat, and dnsutils
sudo apt-get install tmux vnstat dnsutils -y

# Install net-tools
sudo apt-get install net-tools -y

# Optional: Log completion
echo "Startup script completed successfully at $(date)" >> /var/log/startup-script.log