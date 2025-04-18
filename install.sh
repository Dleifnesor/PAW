#!/bin/bash

# PAW Installer Script
#
# This script installs the Prompt Assisted Workflow (PAW) tool 
# system-wide for all users.

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

# Check if the local Ollama installer exists
if [ -f "./install_local_ollama.sh" ]; then
  echo ""
  echo "Local Ollama installer detected."
  read -p "Would you like to install Ollama locally in the current directory instead of system-wide? (y/n): " install_local
  
  if [[ "$install_local" =~ ^[Yy]$ ]]; then
    echo "Running local Ollama installer..."
    chmod +x ./install_local_ollama.sh
    ./install_local_ollama.sh
    
    echo ""
    echo "Local Ollama installation completed."
    echo "To start using PAW with the local Ollama installation:"
    echo "1. Start Ollama: ./ollama/run_ollama.sh"
    echo "2. Run PAW: ./run_paw.sh \"your query\""
    echo ""
    exit 0
  else
    echo "Continuing with system-wide installation..."
  fi
fi

# Define installation paths
INSTALL_DIR="/usr/local/share/paw"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="/etc/paw"
DOC_DIR="/usr/local/share/doc/paw"
LOG_DIR="/var/log/paw"

# Check if Ollama is installed
if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is not installed, which is required for PAW."
  read -p "Would you like to install Ollama now? (y/n): " install_ollama
  
  if [[ "$install_ollama" =~ ^[Yy]$ ]]; then
    echo "Installing Ollama..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
      # Linux
      curl -fsSL https://ollama.com/install.sh | sh
      
      # Start Ollama service
      echo "Starting Ollama service..."
      systemctl enable ollama --now 2>/dev/null || ollama serve &
      
      # Wait for Ollama to start
      echo "Waiting for Ollama to start..."
      sleep 5
      
      # Check if Ollama is running
      if ! curl -s --connect-timeout 5 http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "WARNING: Ollama installation completed but service may not be running."
        echo "Please start Ollama manually: ollama serve"
      else
        echo "Ollama is now running."
      fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS
      echo "Please download and install Ollama from https://ollama.com/download"
      echo "After installation, launch Ollama and continue with PAW installation."
      read -p "Press Enter to continue once Ollama is installed..." 
    else
      echo "Unsupported OS for automatic Ollama installation."
      echo "Please visit https://ollama.ai/download for installation instructions."
      read -p "Press Enter to continue with PAW installation..." 
    fi
  else
    echo "Continuing without installing Ollama. Note that PAW requires Ollama to function."
    echo "Please visit https://ollama.ai/download to install Ollama manually."
  fi
fi

echo "Installing PAW - Prompt Assisted Workflow..."

# Create directories
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/lib"
mkdir -p "$INSTALL_DIR/tools"
mkdir -p "$INSTALL_DIR/custom_commands"
mkdir -p "$CONFIG_DIR"
mkdir -p "$DOC_DIR"
mkdir -p "$LOG_DIR"

# Copy files
echo "Copying files..."
cp -r lib/* "$INSTALL_DIR/lib/" 2>/dev/null || mkdir -p "$INSTALL_DIR/lib"
cp -r custom_commands/* "$INSTALL_DIR/custom_commands/" 2>/dev/null || echo "Note: No custom commands found, creating empty directory"
cp paw.py "$INSTALL_DIR/"
cp add_custom_tool.py "$INSTALL_DIR/"
cp extensive_kali_tools.py "$INSTALL_DIR/" 2>/dev/null || echo "Note: extensive_kali_tools.py not found, Kali tools functionality may be limited"
cp add_kali_tools.py "$INSTALL_DIR/" 2>/dev/null || echo "Note: add_kali_tools.py not found, skipping"
cp add_tools_example.py "$INSTALL_DIR/" 2>/dev/null || echo "Note: add_tools_example.py not found, skipping"
cp ascii_art.py "$INSTALL_DIR/"
cp tools_registry.py "$INSTALL_DIR/"
cp ascii_art.py "$INSTALL_DIR/lib/"
cp tools_registry.py "$INSTALL_DIR/lib/"
cp paw-config "$INSTALL_DIR/paw_config.py" 2>/dev/null || echo "Note: paw-config script not found as a Python file, using bash script instead"
cp README.md "$DOC_DIR/"
cp examples.md "$DOC_DIR/" 2>/dev/null || echo "Note: examples.md not found, skipping"
cp README_KALI_TOOLS.md "$DOC_DIR/" 2>/dev/null || echo "Note: README_KALI_TOOLS.md not found, skipping"

# Create __init__.py files for proper importing
touch "$INSTALL_DIR/lib/__init__.py"
touch "$INSTALL_DIR/custom_commands/__init__.py"

# Create commands
echo "Creating commands..."
cat > "$BIN_DIR/PAW" << 'EOF'
#!/bin/bash
PYTHONPATH="/usr/local/share/paw:/usr/local/share/paw/lib" python3 /usr/local/share/paw/paw.py "$@"
EOF
chmod +x "$BIN_DIR/PAW"

# Also create lowercase command for compatibility
cat > "$BIN_DIR/paw" << 'EOF'
#!/bin/bash
PYTHONPATH="/usr/local/share/paw:/usr/local/share/paw/lib" python3 /usr/local/share/paw/paw.py "$@"
EOF
chmod +x "$BIN_DIR/paw"

cat > "$BIN_DIR/add-paw-tool" << 'EOF'
#!/bin/bash
PYTHONPATH="/usr/local/share/paw:/usr/local/share/paw/lib" python3 /usr/local/share/paw/add_custom_tool.py "$@"
EOF
chmod +x "$BIN_DIR/add-paw-tool"

cat > "$BIN_DIR/paw-kali-tools" << 'EOF'
#!/bin/bash
PYTHONPATH="/usr/local/share/paw:/usr/local/share/paw/lib" python3 /usr/local/share/paw/extensive_kali_tools.py "$@"
EOF
chmod +x "$BIN_DIR/paw-kali-tools"

# Check if paw-config is a bash script or needs to be created
if [ -f "paw-config" ] && head -n 1 "paw-config" | grep -q "bash"; then
  cp paw-config "$BIN_DIR/paw-config"
  chmod +x "$BIN_DIR/paw-config"
else
  cat > "$BIN_DIR/paw-config" << 'EOF'
#!/bin/bash
python3 /usr/local/share/paw/paw_config.py "$@"
EOF
  chmod +x "$BIN_DIR/paw-config"
fi

# Make custom command scripts executable
chmod +x "$INSTALL_DIR/custom_commands"/*.py 2>/dev/null || echo "No custom commands to make executable"

# Create default configuration
if [ ! -f "$CONFIG_DIR/config.ini" ]; then
  echo "Creating default configuration..."
  cat > "$CONFIG_DIR/config.ini" << 'EOF'
[DEFAULT]
model = qwen2.5-coder:7b
ollama_host = http://localhost:11434
explain_commands = true
log_commands = true
log_directory = /var/log/paw
llm_timeout = 180.0
command_timeout = 180.0
auto_retry = true
chain_commands = true
adaptive_mode = true
EOF
fi

# Set permissions
echo "Setting permissions..."
chown -R root:root "$INSTALL_DIR"
chown -R root:root "$CONFIG_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod 644 "$CONFIG_DIR/config.ini"
chmod -R 777 "$LOG_DIR"  # Allow all users to write logs
chmod -R 755 "$DOC_DIR"

# Check if Kali Linux is detected
if [ -f "/etc/os-release" ] && grep -q "Kali" /etc/os-release; then
  echo "Kali Linux detected. Setting up Kali tools integration..."
  
  # Check for required Kali tools
  echo "Checking for required Kali tools..."
  REQUIRED_TOOLS=("nmap" "hydra" "sqlmap" "metasploit-framework" "aircrack-ng" "john" "hashcat")
  MISSING_TOOLS=()
  
  for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      MISSING_TOOLS+=("$tool")
    fi
  done
  
  if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo "Some recommended Kali tools are not installed: ${MISSING_TOOLS[*]}"
    read -p "Would you like to install these tools? (y/n): " install_tools
    if [[ "$install_tools" =~ ^[Yy]$ ]]; then
      echo "Installing recommended Kali tools..."
      apt-get update
      apt-get install -y "${MISSING_TOOLS[@]}"
    fi
  fi
fi

# Run extensive_kali_tools.py to populate the tool registry
if [ -f "$INSTALL_DIR/extensive_kali_tools.py" ]; then
  echo "Populating Kali Linux tools registry..."
  
  # Set PYTHONPATH to include both the installation directory and lib directory
  PYTHONPATH="$INSTALL_DIR:$INSTALL_DIR/lib" python3 "$INSTALL_DIR/extensive_kali_tools.py"
  
  if [ $? -eq 0 ]; then
    echo "Kali tools registry populated successfully."
  else
    echo "Warning: Failed to populate Kali tools registry. You can run 'paw-kali-tools' manually after installation."
    echo "Error details:"
    PYTHONPATH="$INSTALL_DIR:$INSTALL_DIR/lib" python3 "$INSTALL_DIR/extensive_kali_tools.py"
  fi
else
  echo "Note: extensive_kali_tools.py not found. Kali tools functionality will be limited."
  echo "You can manually add Kali tools later using 'paw-kali-tools' if you install the file."
fi

# Verifying installation...
echo "Verifying installation..."

# Check commands
echo -n "Checking command availability: "
COMMANDS_OK=true
for cmd in "PAW" "paw" "add-paw-tool" "paw-config" "paw-kali-tools"; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "WARNING: $cmd command is not in path."
    COMMANDS_OK=false
  fi
done

if [ "$COMMANDS_OK" = true ]; then
  echo "All commands are available."
fi

# Check Python modules
echo -n "Checking Python modules: "
if python3 -c "import sys; sys.path.append('$INSTALL_DIR'); sys.path.append('$INSTALL_DIR/lib'); import os; print('Python path:'); [print(f'  - {p}') for p in sys.path]; try: import tools_registry, ascii_art; print('Module imports successful'); except ImportError as e: print(f'Module import failed: {e}'); sys.exit(1)" 2>/dev/null; then
  echo "All required Python modules can be imported."
else 
  echo "WARNING: Python modules could not be imported. Attempting to fix..."
  
  # Create a symbolic link as a fallback
  echo "Creating symbolic links for modules in lib directory..."
  ln -sf "$INSTALL_DIR/tools_registry.py" "$INSTALL_DIR/lib/tools_registry.py" 2>/dev/null
  ln -sf "$INSTALL_DIR/ascii_art.py" "$INSTALL_DIR/lib/ascii_art.py" 2>/dev/null
  
  # Check again after fix
  if python3 -c "import sys; sys.path.append('$INSTALL_DIR'); sys.path.append('$INSTALL_DIR/lib'); import tools_registry, ascii_art; print('OK')" 2>/dev/null; then
    echo "Module import issue fixed."
  else
    echo "WARNING: Python modules still could not be imported. Please check your installation manually."
  fi
fi

# Install the rich library for improved UI
echo -n "Checking for rich library: "
if python3 -c "import rich" 2>/dev/null; then
  echo "rich library is already installed."
else
  echo "rich library not found."
  read -p "Would you like to install the rich library for enhanced UI? (y/n): " install_rich
  if [[ "$install_rich" =~ ^[Yy]$ ]]; then
    echo "Installing rich library..."
    pip3 install rich || {
      echo "Failed to install using pip3, trying with pip..."
      pip install rich || echo "WARNING: Failed to install rich library. PAW will use basic UI."
    }
  else
    echo "Skipping rich library installation. PAW will use basic UI."
  fi
fi

# Add theme to configuration if it doesn't exist
if ! grep -q "^theme" "$CONFIG_DIR/config.ini"; then
  echo "theme = cyberpunk" >> "$CONFIG_DIR/config.ini"
  echo "Added theme configuration (cyberpunk)"
fi

# Check if Ollama is installed and running
echo -n "Checking Ollama availability: "
if command -v ollama >/dev/null 2>&1; then
  echo "Ollama is installed."
  
  # Check if Ollama service is running
  if curl -s --connect-timeout 5 http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama service is running."
    
    # Check if the configured model exists
    MODEL=$(grep "^model" "$CONFIG_DIR/config.ini" | cut -d'=' -f2- | tr -d ' ')
    echo "Checking for model: $MODEL"
    if curl -s http://localhost:11434/api/tags | grep -q "\"name\":\"$MODEL\""; then
      echo "Configured model '$MODEL' is available."
    else
      echo "WARNING: Configured model '$MODEL' is not available in Ollama."
      read -p "Would you like to pull this model now? (y/n): " pull_model
      if [[ "$pull_model" =~ ^[Yy]$ ]]; then
        echo "Pulling model $MODEL (this may take a while)..."
        ollama pull "$MODEL"
      else
        echo "You can pull the model later with: ollama pull $MODEL"
        echo "Or change the model in /etc/paw/config.ini with: sudo paw-config"
      fi
    fi
  else
    echo "WARNING: Ollama service is not running."
    echo "Start with: ollama serve"
  fi
else
  echo "WARNING: Ollama is not installed. PAW requires Ollama to function."
  echo "Visit https://ollama.ai/download for installation instructions."
fi

# Add Kali tools configuration if it doesn't exist
if ! grep -q "^\[KALI_TOOLS\]" "$CONFIG_DIR/config.ini"; then
  echo "
[KALI_TOOLS]
enabled = true
auto_update = true
categories = Information Gathering,Vulnerability Analysis,Web Application Analysis,Database Assessment,Password Attacks,Wireless Attacks,Bluetooth Attacks,Reverse Engineering,Exploitation Tools,Sniffing & Spoofing,Post Exploitation,Forensics,Reporting Tools,Social Engineering Tools,System Services,Cryptography,Hardware Hacking" >> "$CONFIG_DIR/config.ini"
  echo "Added Kali tools configuration"
fi

echo ""
echo "Installation complete!"
echo "PAW is now installed system-wide and can be executed from anywhere."
echo ""
echo "Usage:"
echo "  PAW \"your natural language command\""
echo ""
echo "Additional tools:"
echo "  add-paw-tool - Register custom tools"
echo "  paw-config   - Configure PAW settings"
echo ""
echo "Documentation: /usr/local/share/doc/paw/"
echo ""
echo "Thank you for installing PAW!" 