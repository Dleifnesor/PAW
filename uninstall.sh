#!/bin/bash
# PAW Uninstallation Script
# This script removes the PAW (Prompt Assisted Workflow) tool from the system

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${RED}"
echo "██████╗  █████╗ ██╗    ██╗"
echo "██╔══██╗██╔══██╗██║    ██║"
echo "██████╔╝███████║██║ █╗ ██║"
echo "██╔═══╝ ██╔══██║██║███╗██║"
echo "██║     ██║  ██║╚███╔███╔╝"
echo "╚═╝     ╚═╝  ╚═╝ ╚══╝╚══╝ "
echo "UNINSTALLER"
echo -e "${NC}"

# Check if running as root (sudo)
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run this script with sudo:${NC} sudo $0"
  exit 1
fi

# Ask for confirmation
echo -e "${YELLOW}This will uninstall PAW (Prompt Assisted Workflow) from your system.${NC}"
read -p "Are you sure you want to continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Uninstallation cancelled.${NC}"
    exit 0
fi

# Installation directories
INSTALL_DIR="/usr/local/lib/paw"
CONFIG_DIR="/etc/paw"
USER_CONFIG_DIR="$HOME/.config/paw"
USER_DATA_DIR="$HOME/.local/share/paw"

# Remove symbolic links
echo -e "${BLUE}Removing symbolic links...${NC}"
rm -f "/usr/local/bin/paw"
rm -f "/usr/local/bin/paw-config"

# Remove installation directory
echo -e "${BLUE}Removing installation directory...${NC}"
rm -rf "$INSTALL_DIR"

# Ask if user wants to remove configuration files
echo -e "${YELLOW}Do you want to remove PAW configuration files?${NC}"
read -p "This includes your settings and preferences. (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Removing system-wide configuration...${NC}"
    rm -rf "$CONFIG_DIR"
    
    echo -e "${BLUE}Removing user configuration...${NC}"
    rm -rf "$USER_CONFIG_DIR"
    
    echo -e "${GREEN}Configuration files removed.${NC}"
else
    echo -e "${GREEN}Configuration files preserved.${NC}"
fi

# Ask if user wants to remove history and user data
echo -e "${YELLOW}Do you want to remove PAW history and user data?${NC}"
read -p "This includes your command history. (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Removing user data...${NC}"
    rm -rf "$USER_DATA_DIR"
    
    echo -e "${GREEN}User data removed.${NC}"
else
    echo -e "${GREEN}User data preserved.${NC}"
fi

echo -e "${GREEN}PAW has been successfully uninstalled.${NC}"
echo -e "${BLUE}Thank you for using PAW!${NC}" 