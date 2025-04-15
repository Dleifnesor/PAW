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
# Create lib directory if it doesn't exist
mkdir -p "$INSTALL_DIR/lib"

# Copy Python files to lib directory
cp ascii_art.py "$INSTALL_DIR/lib/"
cp tools_registry.py "$INSTALL_DIR/lib/"
cp extensive_kali_tools.py "$INSTALL_DIR/lib/"

# Copy other files
cp -r custom_commands/* "$INSTALL_DIR/custom_commands/" 2>/dev/null || echo "Note: No custom commands found, creating empty directory"
cp paw.py "$INSTALL_DIR/"
cp add_custom_tool.py "$INSTALL_DIR/"

# Handle paw-config
if [ -f "paw-config" ]; then
  if head -n 1 "paw-config" | grep -q "bash"; then
    cp paw-config "$INSTALL_DIR/paw_config.sh"
  else
    cp paw-config "$INSTALL_DIR/paw_config.py"
  fi
else
  echo "Note: paw-config script not found"
fi

# Copy documentation
cp README.md "$DOC_DIR/"
cp examples.md "$DOC_DIR/" 2>/dev/null || echo "Note: examples.md not found, skipping"

# Create __init__.py files for proper importing
touch "$INSTALL_DIR/lib/__init__.py"
touch "$INSTALL_DIR/custom_commands/__init__.py"

# Create commands
echo "Creating commands..."
cat > "$BIN_DIR/PAW" << 'EOF'
#!/bin/bash
export PYTHONPATH=/usr/local/share/paw/lib:$PYTHONPATH
python3 /usr/local/share/paw/paw.py "$@"
EOF
chmod +x "$BIN_DIR/PAW"

# Also create lowercase command for compatibility
cat > "$BIN_DIR/paw" << 'EOF'
#!/bin/bash
export PYTHONPATH=/usr/local/share/paw/lib:$PYTHONPATH
python3 /usr/local/share/paw/paw.py "$@"
EOF
chmod +x "$BIN_DIR/paw"

cat > "$BIN_DIR/add-paw-tool" << 'EOF'
#!/bin/bash
export PYTHONPATH=/usr/local/share/paw/lib:$PYTHONPATH
python3 /usr/local/share/paw/add_custom_tool.py "$@"
EOF
chmod +x "$BIN_DIR/add-paw-tool"

# Check if paw-config is a bash script or needs to be created
if [ -f "$INSTALL_DIR/paw_config.sh" ]; then
  cat > "$BIN_DIR/paw-config" << 'EOF'
#!/bin/bash
export PYTHONPATH=/usr/local/share/paw/lib:$PYTHONPATH
/usr/local/share/paw/paw_config.sh "$@"
EOF
  chmod +x "$BIN_DIR/paw-config"
elif [ -f "$INSTALL_DIR/paw_config.py" ]; then
  cat > "$BIN_DIR/paw-config" << 'EOF'
#!/bin/bash
export PYTHONPATH=/usr/local/share/paw/lib:$PYTHONPATH
python3 /usr/local/share/paw/paw_config.py "$@"
EOF
  chmod +x "$BIN_DIR/paw-config"
else
  echo "WARNING: paw-config script not found, creating default configuration script"
  cat > "$BIN_DIR/paw-config" << 'EOF'
#!/bin/bash
echo "PAW configuration tool"
echo "Usage: paw-config [option]"
echo ""
echo "Options:"
echo "  --model <model_name>    Set the default model"
echo "  --theme <theme_name>    Set the UI theme"
echo "  --help                  Show this help message"
EOF
  chmod +x "$BIN_DIR/paw-config"
fi

# Create a Python environment file
echo "Creating Python environment file..."
cat > "$INSTALL_DIR/lib/paw_env.py" << 'EOF'
import os
import sys

# Add the lib directory to Python path
lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib')
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)
EOF

# Make sure the lib directory is in Python path
echo "Setting up Python path..."
cat > "$INSTALL_DIR/lib/__init__.py" << 'EOF'
import os
import sys

# Add the lib directory to Python path
lib_dir = os.path.dirname(os.path.abspath(__file__))
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

# Import environment setup
try:
    from paw_env import *
except ImportError:
    pass
EOF

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
llm_timeout = 600.0
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
    
    # Get configured model
    MODEL=$(grep "^model" "$CONFIG_DIR/config.ini" | cut -d'=' -f2- | tr -d ' ')
    echo "Checking for model: $MODEL"
    
    # Get list of available models
    AVAILABLE_MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
    
    if echo "$AVAILABLE_MODELS" | grep -q "^$MODEL$"; then
      echo "Configured model '$MODEL' is available."
    else
      echo "WARNING: Configured model '$MODEL' is not available in Ollama."
      
      # Try to find first available model if Qwen is not available
      FIRST_AVAILABLE_MODEL=$(echo "$AVAILABLE_MODELS" | head -n1)
      
      if [ -n "$FIRST_AVAILABLE_MODEL" ]; then
        echo "Found available model: $FIRST_AVAILABLE_MODEL"
        read -p "Would you like to use $FIRST_AVAILABLE_MODEL instead? (y/n): " use_available
        if [[ "$use_available" =~ ^[Yy]$ ]]; then
          # Update config with first available model
          sed -i "s/^model = .*/model = $FIRST_AVAILABLE_MODEL/" "$CONFIG_DIR/config.ini"
          echo "Updated configuration to use $FIRST_AVAILABLE_MODEL"
        else
          read -p "Would you like to pull the configured model ($MODEL) now? (y/n): " pull_model
          if [[ "$pull_model" =~ ^[Yy]$ ]]; then
            echo "Pulling model $MODEL (this may take a while)..."
            ollama pull "$MODEL"
          else
            echo "You can pull the model later with: ollama pull $MODEL"
            echo "Or change the model in /etc/paw/config.ini with: sudo paw-config"
          fi
        fi
      else
        echo "No models are currently available in Ollama."
        read -p "Would you like to pull the configured model ($MODEL) now? (y/n): " pull_model
        if [[ "$pull_model" =~ ^[Yy]$ ]]; then
          echo "Pulling model $MODEL (this may take a while)..."
          ollama pull "$MODEL"
        else
          echo "You can pull the model later with: ollama pull $MODEL"
          echo "Or change the model in /etc/paw/config.ini with: sudo paw-config"
        fi
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