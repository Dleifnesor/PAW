#!/bin/bash

# PAW Uninstaller Script
#
# This script removes the Prompt Assisted Workflow (PAW) tool
# and all its components from the system.

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./uninstall.sh)"
  exit 1
fi

# Define installation paths
INSTALL_DIR="/usr/local/share/paw"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="/etc/paw"
DOC_DIR="/usr/local/share/doc/paw"
LOG_DIR="/var/log/paw"
PROFILE_DIR="/etc/profile.d"

# Check for Kali Linux
is_kali=false
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" == "kali" ]]; then
        is_kali=true
        echo "Kali Linux detected. Optimizing uninstallation for Kali..."
    fi
fi

# Function to safely remove a directory
safe_remove_dir() {
    if [ -d "$1" ]; then
        echo "Removing directory: $1"
        rm -rf "$1"
    fi
}

# Function to safely remove a file
safe_remove_file() {
    if [ -f "$1" ]; then
        echo "Removing file: $1"
        rm -f "$1"
    fi
}

# Function to safely remove a symlink
safe_remove_symlink() {
    if [ -L "$1" ]; then
        echo "Removing symlink: $1"
        rm -f "$1"
    fi
}

# Stop any running PAW processes
echo "Stopping any running PAW processes..."
pkill -f "paw.py"
pkill -f "PAW"

# Remove commands
echo "Removing PAW commands..."
safe_remove_symlink "$BIN_DIR/PAW"
safe_remove_symlink "$BIN_DIR/paw"
safe_remove_symlink "$BIN_DIR/add-paw-tool"
safe_remove_symlink "$BIN_DIR/paw-kali-tools"
safe_remove_symlink "$BIN_DIR/paw-config"

# Remove directories
echo "Removing PAW directories..."
safe_remove_dir "$INSTALL_DIR"
safe_remove_dir "$CONFIG_DIR"
safe_remove_dir "$DOC_DIR"
safe_remove_dir "$LOG_DIR"

# Remove Python packages
echo "Removing PAW Python packages..."
pip3 uninstall -y paw-tools 2>/dev/null || true

# Remove configuration files
echo "Removing configuration files..."
safe_remove_file "$PROFILE_DIR/paw.sh"

# Remove desktop entry (Kali Linux specific)
if [ "$is_kali" = true ]; then
    echo "Removing desktop entry..."
    safe_remove_file "/usr/share/applications/paw.desktop"
    
    # Update desktop database
    if command -v update-desktop-database >/dev/null 2>&1; then
        echo "Updating desktop database..."
        update-desktop-database /usr/share/applications
    fi
fi

# Remove Python path modifications
echo "Removing Python path modifications..."
if [ -f "$PROFILE_DIR/paw.sh" ]; then
    sed -i '/export PYTHONPATH.*paw/d' "$PROFILE_DIR/paw.sh"
    if [ ! -s "$PROFILE_DIR/paw.sh" ]; then
        rm -f "$PROFILE_DIR/paw.sh"
    fi
fi

# Remove from PATH
echo "Removing from PATH..."
sed -i '/\/usr\/local\/share\/paw/d' /etc/environment

# Clean up any remaining files
echo "Cleaning up remaining files..."
find /usr/local -name "*paw*" -exec rm -rf {} \; 2>/dev/null || true
find /etc -name "*paw*" -exec rm -rf {} \; 2>/dev/null || true

# Remove log files
echo "Removing log files..."
find /var/log -name "*paw*" -exec rm -rf {} \; 2>/dev/null || true

# Remove temporary files
echo "Removing temporary files..."
find /tmp -name "*paw*" -exec rm -rf {} \; 2>/dev/null || true
find /var/tmp -name "*paw*" -exec rm -rf {} \; 2>/dev/null || true

# Verify removal
echo "Verifying removal..."
if [ ! -d "$INSTALL_DIR" ] && \
   [ ! -d "$CONFIG_DIR" ] && \
   [ ! -d "$DOC_DIR" ] && \
   [ ! -d "$LOG_DIR" ] && \
   [ ! -f "$BIN_DIR/PAW" ] && \
   [ ! -f "$BIN_DIR/paw" ] && \
   [ ! -f "$BIN_DIR/add-paw-tool" ] && \
   [ ! -f "$BIN_DIR/paw-kali-tools" ] && \
   [ ! -f "$BIN_DIR/paw-config" ]; then
    echo "PAW has been successfully uninstalled."
else
    echo "Warning: Some PAW components may still remain on the system."
    echo "Please check the following locations manually:"
    echo "- $INSTALL_DIR"
    echo "- $CONFIG_DIR"
    echo "- $DOC_DIR"
    echo "- $LOG_DIR"
    echo "- $BIN_DIR/PAW"
    echo "- $BIN_DIR/paw"
    echo "- $BIN_DIR/add-paw-tool"
    echo "- $BIN_DIR/paw-kali-tools"
    echo "- $BIN_DIR/paw-config"
fi

# Final message
echo ""
echo "PAW uninstallation complete!"
echo "If you want to reinstall PAW, run the install.sh script."
echo ""
echo "Note: If you installed any custom tools or configurations,"
echo "you may need to remove them manually." 