#!/bin/bash

# Script to check bandwidth usage on multiple servers using vnstat -m
# Usage: ./check_server_bandwidth.sh [server_list_file]
# If no file is provided, it will read from servers.txt

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default server list file
SERVER_LIST="${1:-servers.txt}"

# Check if server list file exists
if [ ! -f "$SERVER_LIST" ]; then
    echo -e "${RED}Error: Server list file '$SERVER_LIST' not found!${NC}"
    echo ""
    echo "Usage: $0 [server_list_file]"
    echo ""
    echo "Create a file with one server per line (domain or IP):"
    echo "Example:"
    echo "  server1.example.com"
    echo "  192.168.1.10"
    echo "  user@server2.example.com"
    echo "  root@203.0.113.5"
    exit 1
fi

# Read servers into array
mapfile -t SERVERS < "$SERVER_LIST"

# Check if array is empty
if [ ${#SERVERS[@]} -eq 0 ]; then
    echo -e "${RED}Error: No servers found in '$SERVER_LIST'${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Checking bandwidth usage on ${#SERVERS[@]} server(s)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Loop through each server
for server in "${SERVERS[@]}"; do
    # Skip empty lines and comments
    [[ -z "$server" || "$server" =~ ^[[:space:]]*# ]] && continue
    
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Server: $server${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Try to connect and run vnstat
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$server" "vnstat -m" 2>/dev/null; then
        echo ""
    else
        echo -e "${RED}Failed to connect to $server or vnstat not available${NC}"
        echo -e "${YELLOW}Troubleshooting tips:${NC}"
        echo "  - Check SSH connectivity: ssh $server"
        echo "  - Verify vnstat is installed: ssh $server 'which vnstat'"
        echo "  - Check SSH keys are properly configured"
        echo ""
    fi
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Bandwidth check complete${NC}"
echo -e "${BLUE}========================================${NC}"
