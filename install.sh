#!/bin/bash
# PAW Installation Script
# This script installs the PAW (Prompt Assisted Workflow) tool and makes it available as a system-wide command

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Print banner
echo -e "${BLUE}"
echo "██████╗  █████╗ ██╗    ██╗"
echo "██╔══██╗██╔══██╗██║    ██║"
echo "██████╔╝███████║██║ █╗ ██║"
echo "██╔═══╝ ██╔══██║██║███╗██║"
echo "██║     ██║  ██║╚███╔███╔╝"
echo "╚═╝     ╚═╝  ╚═╝ ╚══╝╚══╝ "
echo "Prompt Assisted Workflow"
echo -e "${NC}"

# Check if running as root (sudo)
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run this script with sudo:${NC} sudo $0"
  exit 1
fi

# Check dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed.${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 is installed.${NC}"
        return 0
    fi
}

# Check for required commands
check_command python3 || { echo -e "${RED}Please install Python 3 before continuing.${NC}"; exit 1; }
check_command pip3 || { echo -e "${RED}Please install pip3 before continuing.${NC}"; exit 1; }

# Check if xclip is installed (for clipboard functionality)
if ! check_command xclip; then
    echo -e "${YELLOW}Warning: xclip is not installed. Clipboard functionality will be disabled.${NC}"
    echo -e "${YELLOW}To enable clipboard support, install xclip:${NC} apt-get install xclip"
fi

# Check if Ollama is installed and operational
if ! check_command ollama; then
    echo -e "${YELLOW}Warning: Ollama is not installed. This is required for PAW to work.${NC}"
    echo -e "${YELLOW}Please install Ollama from https://ollama.ai/download before using PAW.${NC}"
else
    echo -e "${BLUE}Checking if Ollama is operational...${NC}"
    if ! ollama list &>/dev/null; then
        echo -e "${YELLOW}Warning: Ollama seems to be installed but is not responding properly.${NC}"
        echo -e "${YELLOW}Make sure the Ollama service is running before using PAW.${NC}"
    else
        # Check if there are any models
        models=$(ollama list 2>/dev/null)
        if [ -z "$models" ] || ! echo "$models" | grep -q "NAME"; then
            echo -e "${YELLOW}Warning: No Ollama models found. Please download at least one model.${NC}"
            echo -e "${YELLOW}You can download a model using:${NC} ollama pull llama3"
        else
            echo -e "${GREEN}✓ Ollama is operational with models available.${NC}"
            echo "$models"
        fi
    fi
fi

# Convert Windows line endings to Unix for all script files
echo -e "${BLUE}Converting line endings (Windows to Unix)...${NC}"
if command -v dos2unix &> /dev/null; then
    dos2unix "$SCRIPT_DIR/paw.py" 2>/dev/null
    dos2unix "$SCRIPT_DIR/paw-config.py" 2>/dev/null
    dos2unix "$SCRIPT_DIR/context_lib.py" 2>/dev/null
    dos2unix "$SCRIPT_DIR/install.sh" 2>/dev/null
    dos2unix "$SCRIPT_DIR/uninstall.sh" 2>/dev/null
    echo -e "${GREEN}✓ Line endings converted successfully.${NC}"
else
    echo -e "${YELLOW}Warning: dos2unix not found. Attempting manual conversion...${NC}"
    for file in "$SCRIPT_DIR/paw.py" "$SCRIPT_DIR/paw-config.py" "$SCRIPT_DIR/context_lib.py" "$SCRIPT_DIR/install.sh" "$SCRIPT_DIR/uninstall.sh"; do
        if [ -f "$file" ]; then
            # Create a temporary file
            temp_file=$(mktemp)
            # Convert CRLF to LF
            tr -d '\r' < "$file" > "$temp_file"
            # Replace the original file
            mv "$temp_file" "$file"
        fi
    done
    echo -e "${GREEN}✓ Line endings converted manually.${NC}"
fi

# Make scripts executable in the current directory
echo -e "${BLUE}Setting executable permissions on scripts...${NC}"
chmod +x "$SCRIPT_DIR/paw.py"
chmod +x "$SCRIPT_DIR/paw-config.py"
chmod +x "$SCRIPT_DIR/install.sh"
chmod +x "$SCRIPT_DIR/uninstall.sh"

# Install required Python packages
echo -e "${BLUE}Installing required Python packages...${NC}"
pip3 install -q configparser

# Create installation directories
echo -e "${BLUE}Creating installation directories...${NC}"
INSTALL_DIR="/usr/local/lib/paw"
CONFIG_DIR="/etc/paw"

mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"

# Copy files to installation directory
echo -e "${BLUE}Copying files to installation directory...${NC}"
cp "$SCRIPT_DIR/paw.py" "$INSTALL_DIR/paw.py"
cp "$SCRIPT_DIR/context_lib.py" "$INSTALL_DIR/context_lib.py"
cp "$SCRIPT_DIR/paw-config.py" "$INSTALL_DIR/paw-config.py"

# Set executable permissions on installed files
echo -e "${BLUE}Setting executable permissions on installed files...${NC}"
chmod +x "$INSTALL_DIR/paw.py"
chmod +x "$INSTALL_DIR/paw-config.py"

# Create symbolic links for the commands
echo -e "${BLUE}Creating symbolic links for commands...${NC}"
ln -sf "$INSTALL_DIR/paw.py" "/usr/local/bin/paw"
ln -sf "$INSTALL_DIR/paw-config.py" "/usr/local/bin/paw-config"

# Create a default configuration file if it doesn't exist
if [ ! -f "$CONFIG_DIR/config.ini" ]; then
    echo -e "${BLUE}Creating default configuration file...${NC}"
    cat > "$CONFIG_DIR/config.ini" << EOF
[general]
model = llama3
temperature = 0.7
max_tokens = 500
show_thinking = false
save_history = true
use_last_output = true
max_last_output_lines = 20
EOF
fi

echo -e "${GREEN}Installation completed successfully!${NC}"
echo -e "${YELLOW}Usage:${NC}"
echo -e "  ${BLUE}paw${NC} \"your prompt here\"     - Generate a command from a prompt"
echo -e "  ${BLUE}paw${NC} -e \"your prompt here\"  - Generate and execute a command"
echo -e "  ${BLUE}paw${NC} -n \"your prompt here\"  - Generate without using last output as context"
echo -e "  ${BLUE}paw-config${NC} show            - Show current configuration"
echo -e "  ${BLUE}paw-config${NC} set --section general --key model --value llama3 - Change settings"
echo -e "  ${BLUE}paw-config${NC} toggle-context  - Toggle using last command output as context"
echo -e "  ${BLUE}paw-config${NC} show-output     - Display the last command output saved"
echo -e ""
echo -e "${YELLOW}Example Workflow:${NC}"
echo -e "  ${BLUE}paw${NC} -e \"scan my local network\"              # First command"
echo -e "  ${BLUE}paw${NC} -e \"filter the results to show only web servers\"  # Uses previous output"
echo -e ""
echo -e "${GREEN}Happy hacking with PAW!${NC}" 