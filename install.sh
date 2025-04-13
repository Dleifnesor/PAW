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
cp ascii_art.py "$INSTALL_DIR/lib/"
cp tools_registry.py "$INSTALL_DIR/lib/"
cp paw-config "$INSTALL_DIR/paw_config.py" 2>/dev/null || echo "Note: paw-config script not found as a Python file, using bash script instead"
cp README.md "$DOC_DIR/"
cp examples.md "$DOC_DIR/" 2>/dev/null || echo "Note: examples.md not found, skipping"

# Create __init__.py files for proper importing
touch "$INSTALL_DIR/lib/__init__.py"
touch "$INSTALL_DIR/custom_commands/__init__.py"

# Create commands
echo "Creating commands..."
cat > "$BIN_DIR/PAW" << 'EOF'
#!/bin/bash
python3 /usr/local/share/paw/paw.py "$@"
EOF
chmod +x "$BIN_DIR/PAW"

# Also create lowercase command for compatibility
cat > "$BIN_DIR/paw" << 'EOF'
#!/bin/bash
python3 /usr/local/share/paw/paw.py "$@"
EOF
chmod +x "$BIN_DIR/paw"

cat > "$BIN_DIR/add-paw-tool" << 'EOF'
#!/bin/bash
python3 /usr/local/share/paw/add_custom_tool.py "$@"
EOF
chmod +x "$BIN_DIR/add-paw-tool"

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

# Verifying installation...
echo "Verifying installation..."

# Check commands
echo -n "Checking command availability: "
COMMANDS_OK=true
for cmd in "PAW" "paw" "add-paw-tool" "paw-config"; do
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
if python3 -c "import sys; sys.path.append('$INSTALL_DIR/lib'); import ascii_art, tools_registry; print('OK')" 2>/dev/null; then
  echo "All required Python modules can be imported."
else 
  echo "WARNING: Python modules could not be imported. Check your installation."
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