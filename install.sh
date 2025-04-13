#!/bin/bash

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
 _______   ______  __      __
|       \ /      \|  \    /  \
| $$$$$$$|  $$$$$$\\$$\  /  $$
| $$__/ $| $$__| $$ \$$\/  $$
| $$    $| $$    $$  \$$  $$
| $$$$$$$| $$$$$$$$   \$$$$
| $$     | $$  | $$   | $$
| $$     | $$  | $$   | $$
 \$$      \$$   \$$    \$$

Prompt Assisted Workflow
EOF
echo -e "${NC}"

echo -e "${GREEN}[*] Installing PAW - Prompt Assisted Workflow...${NC}"

# Check if running on Kali Linux
if ! grep -q 'Kali' /etc/os-release; then
    echo -e "${YELLOW}[!] Warning: This script is designed for Kali Linux. Results on other distributions may vary.${NC}"
fi

# Create directory structure
echo -e "${BLUE}[*] Creating directory structure...${NC}"
mkdir -p ~/.paw/tools
mkdir -p ~/.paw/logs
mkdir -p ~/.paw/custom_commands

# Install Python dependencies
echo -e "${BLUE}[*] Installing Python dependencies...${NC}"
pip install requests openai python-dotenv rich httpx

# Install Ollama
echo -e "${BLUE}[*] Installing Ollama...${NC}"
curl -fsSL https://ollama.com/install.sh | sh

# Wait for Ollama to start
echo -e "${BLUE}[*] Starting Ollama service...${NC}"
sleep 2

# Pull the required model
echo -e "${BLUE}[*] Downloading LLM model (this may take a while)...${NC}"
ollama pull MartinRizzo/Ayla-Light-v2:12b-q4_K_M

# Set executable permissions for Python files
echo -e "${BLUE}[*] Setting executable permissions...${NC}"
chmod +x paw.py ascii_art.py tools_registry.py add_custom_tool.py
chmod +x custom_commands/recon_suite.py

# Copy PAW Python scripts to installation directory
echo -e "${BLUE}[*] Setting up PAW...${NC}"
cp ./paw.py ~/.paw/
cp ./tools_registry.py ~/.paw/
cp ./ascii_art.py ~/.paw/
cp ./add_custom_tool.py ~/.paw/
cp -r ./custom_commands/* ~/.paw/custom_commands/

# Create the paw command
echo -e "${BLUE}[*] Creating PAW command...${NC}"
cat > /tmp/paw << 'EOF'
#!/bin/bash
python3 ~/.paw/paw.py "$@"
EOF

sudo mv /tmp/paw /usr/local/bin/
sudo chmod +x /usr/local/bin/paw

# Register custom commands
echo -e "${BLUE}[*] Registering custom commands...${NC}"
python3 ~/.paw/add_custom_tool.py add --name "recon-suite" --category "reconnaissance" \
    --description "Advanced reconnaissance suite for target domains" \
    --usage "recon-suite [options] {target}" \
    --examples "recon-suite -f domains.txt" "recon-suite -d example.com -o report.txt"

# Create default config file
echo -e "${BLUE}[*] Creating configuration file...${NC}"
cat > ~/.paw/config.ini << EOF
[DEFAULT]
model=MartinRizzo/Ayla-Light-v2:12b-q4_K_M
ollama_host=http://localhost:11434
explain_commands=true
log_commands=true
log_directory=~/.paw/logs

[TOOLS]
tools_registry=~/.paw/tools_registry.py
EOF

echo -e "${GREEN}[+] Installation complete!${NC}"
echo -e "${YELLOW}[*] To start using PAW, simply type 'paw' in your terminal.${NC}" 