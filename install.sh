#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[+] OA (Ollama Assistant) installation script${NC}"
echo -e "${YELLOW}[*] This script will install Ollama and set up the OA tool${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[!] Please run as root${NC}"
    exit 1
fi

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo -e "${YELLOW}[*] Installing curl...${NC}"
    apt-get update
    apt-get install -y curl
fi

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}[*] Installing Python3...${NC}"
    apt-get update
    apt-get install -y python3 python3-pip
fi

# Install required Python packages
echo -e "${YELLOW}[*] Installing required Python packages...${NC}"
pip3 install requests colorama

# Install Ollama
echo -e "${YELLOW}[*] Installing Ollama...${NC}"
curl -fsSL https://ollama.com/install.sh | sh

# Wait for Ollama service to start
echo -e "${YELLOW}[*] Waiting for Ollama service to start...${NC}"
sleep 5

# Pull the code model (codellama)
echo -e "${YELLOW}[*] Downloading the CodeLlama model (this may take some time)...${NC}"
ollama pull codellama

# Create the OA directory
INSTALL_DIR="/opt/oa"
echo -e "${YELLOW}[*] Creating installation directory at $INSTALL_DIR...${NC}"
mkdir -p $INSTALL_DIR

# Copy the Python script
echo -e "${YELLOW}[*] Installing OA script...${NC}"
cp oa.py $INSTALL_DIR/oa.py
chmod +x $INSTALL_DIR/oa.py

# Create the wrapper script
echo -e "${YELLOW}[*] Creating OA command wrapper...${NC}"
cat > /usr/local/bin/OA << 'EOF'
#!/bin/bash
python3 /opt/oa/oa.py "$@"
EOF
chmod +x /usr/local/bin/OA

echo -e "${GREEN}[+] Installation complete!${NC}"
echo -e "${GREEN}[+] Run 'OA' to start Ollama Assistant${NC}" 