#!/bin/bash

# Ollama Local Installer Script
# This script installs Ollama in the current directory and configures 
# it to store models in the current directory.
set -e

echo "Installing Ollama locally in the current directory..."

# Define installation paths
CURRENT_DIR=$(pwd)
OLLAMA_DIR="${CURRENT_DIR}/ollama"
OLLAMA_BIN="${OLLAMA_DIR}/bin"
OLLAMA_MODELS="${CURRENT_DIR}/models"
OLLAMA_CONFIG="${OLLAMA_DIR}/config"

# Create directories
echo "Creating directories..."
mkdir -p "${OLLAMA_BIN}"
mkdir -p "${OLLAMA_MODELS}"
mkdir -p "${OLLAMA_CONFIG}"

# Check for required tools
if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
    echo "Neither curl nor wget found. Installing wget..."
    apt-get update && apt-get install -y wget
fi

# Detect architecture
ARCH=$(uname -m)
if [[ "${ARCH}" == "x86_64" ]]; then
    OLLAMA_PACKAGE="ollama-linux-amd64"
elif [[ "${ARCH}" == "aarch64" ]]; then
    OLLAMA_PACKAGE="ollama-linux-arm64"
else
    echo "Unsupported architecture: ${ARCH}"
    exit 1
fi

# Get the latest GitHub release version (with fallback)
LATEST_VERSION="v0.1.27"
if command -v curl &> /dev/null; then
    VERSION=$(curl -s https://api.github.com/repos/ollama/ollama/releases/latest | grep -o '"tag_name": "[^"]*"' | cut -d'"' -f4)
    if [ -n "$VERSION" ]; then
        LATEST_VERSION=$VERSION
    fi
elif command -v wget &> /dev/null; then
    VERSION=$(wget -qO- https://api.github.com/repos/ollama/ollama/releases/latest | grep -o '"tag_name": "[^"]*"' | cut -d'"' -f4)
    if [ -n "$VERSION" ]; then
        LATEST_VERSION=$VERSION
    fi
fi

echo "Using Ollama version: ${LATEST_VERSION}"

# Define direct download URL to the binary
DOWNLOAD_URL="https://github.com/ollama/ollama/releases/download/${LATEST_VERSION}/${OLLAMA_PACKAGE}"
echo "Download URL: ${DOWNLOAD_URL}"

# Attempt download with different methods
echo "Downloading Ollama binary..."
download_success=false

# Try wget first if available
if command -v wget &> /dev/null && ! $download_success; then
    echo "Attempting download with wget..."
    if wget -q --show-progress "${DOWNLOAD_URL}" -O "${OLLAMA_BIN}/ollama"; then
        download_success=true
        echo "Download with wget successful!"
    else
        echo "wget download failed."
    fi
fi

# Try curl if wget failed or isn't available
if command -v curl &> /dev/null && ! $download_success; then
    echo "Attempting download with curl..."
    if curl -L -f -o "${OLLAMA_BIN}/ollama" "${DOWNLOAD_URL}"; then
        download_success=true
        echo "Download with curl successful!"
    else
        echo "curl download failed."
    fi
fi

# Check if download succeeded
if ! $download_success; then
    echo "ERROR: Failed to download Ollama binary."
    echo "Attempting to use a fixed version as fallback..."
    
    # Try with a specific working version as fallback
    FIXED_VERSION="v0.1.27"
    FIXED_URL="https://github.com/ollama/ollama/releases/download/${FIXED_VERSION}/${OLLAMA_PACKAGE}"
    echo "Trying fixed URL: ${FIXED_URL}"
    
    if command -v wget &> /dev/null; then
        if wget -q --show-progress "${FIXED_URL}" -O "${OLLAMA_BIN}/ollama"; then
            download_success=true
            echo "Download with fixed version successful!"
        fi
    elif command -v curl &> /dev/null; then
        if curl -L -f -o "${OLLAMA_BIN}/ollama" "${FIXED_URL}"; then
            download_success=true
            echo "Download with fixed version successful!"
        fi
    fi
    
    if ! $download_success; then
        echo "ERROR: All download attempts failed."
        echo "Please manually download Ollama from https://github.com/ollama/ollama/releases"
        echo "and place it in ${OLLAMA_BIN}/ollama"
        exit 1
    fi
fi

# Make the binary executable
chmod +x "${OLLAMA_BIN}/ollama"

# Verify binary starts with ELF header (quick check that it's a binary, not HTML/text)
if ! head -c 4 "${OLLAMA_BIN}/ollama" | grep -q "ELF"; then
    echo "ERROR: Downloaded file is not a valid binary executable."
    echo "File content starts with:"
    head -n 1 "${OLLAMA_BIN}/ollama"
    echo "Removing invalid file..."
    rm "${OLLAMA_BIN}/ollama"
    echo "Please try running the script again or download manually."
    exit 1
fi

# Get binary size
file_size=$(stat -c%s "${OLLAMA_BIN}/ollama" 2>/dev/null || stat -f%z "${OLLAMA_BIN}/ollama")
echo "Ollama binary downloaded successfully (${file_size} bytes)"

# Create wrapper script with environment variables
cat > "${OLLAMA_DIR}/run_ollama.sh" << 'EOF'
#!/bin/bash
# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
CURRENT_DIR=$(pwd)

# Set Ollama environment variables
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_MODELS="${CURRENT_DIR}/models"

# Start Ollama server
"${SCRIPT_DIR}/bin/ollama" serve
EOF

# Create client script
cat > "${OLLAMA_DIR}/ollama" << 'EOF'
#!/bin/bash
# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
CURRENT_DIR=$(pwd)

# Set Ollama environment variables
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_MODELS="${CURRENT_DIR}/models"

# Run Ollama command
"${SCRIPT_DIR}/bin/ollama" "$@"
EOF

# Make scripts executable
chmod +x "${OLLAMA_DIR}/run_ollama.sh"
chmod +x "${OLLAMA_DIR}/ollama"

# Create PAW configuration for local Ollama
cat > "${CURRENT_DIR}/paw-local-config.ini" << EOF
[DEFAULT]
model = qwen2.5-coder:7b
ollama_host = http://127.0.0.1:11434
explain_commands = true
log_commands = true
log_directory = ${CURRENT_DIR}/logs
llm_timeout = 180.0
command_timeout = 180.0
auto_retry = true
chain_commands = true
adaptive_mode = true
theme = cyberpunk
EOF

# Create a directory for logs
mkdir -p "${CURRENT_DIR}/logs"

# Create runner for PAW with local config
cat > "${CURRENT_DIR}/run_paw.sh" << EOF
#!/bin/bash
CURRENT_DIR=\$(pwd)

# Set environment variable for PAW configuration
export PAW_CONFIG="\${CURRENT_DIR}/paw-local-config.ini"

# Run PAW with local config
python3 "\${CURRENT_DIR}/paw.py" "\$@"
EOF

chmod +x "${CURRENT_DIR}/run_paw.sh"

# Check if pull_model.sh exists and make it executable
if [ -f "${CURRENT_DIR}/pull_model.sh" ]; then
    chmod +x "${CURRENT_DIR}/pull_model.sh"
    
    # Also update pull_model.sh script to use readlink -f
    cp "${CURRENT_DIR}/pull_model.sh" "${CURRENT_DIR}/pull_model.sh.bak"
    cat > "${CURRENT_DIR}/pull_model.sh" << 'EOF'
#!/bin/bash

# Pull a model with the local Ollama installation

if [ $# -eq 0 ]; then
  echo "Usage: $0 <model_name>"
  echo "Example: $0 qwen2.5-coder:7b"
  exit 1
fi

MODEL_NAME="$1"
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if Ollama is installed locally
if [ ! -d "${CURRENT_DIR}/ollama" ]; then
  echo "Error: Local Ollama installation not found!"
  echo "Please run ./install_local_ollama.sh first."
  exit 1
fi

# Make sure OLLAMA_MODELS env var is set
export OLLAMA_MODELS="${CURRENT_DIR}/models"

echo "Pulling model: ${MODEL_NAME}"
echo "Models will be stored in: ${OLLAMA_MODELS}"
echo ""

# Run Ollama pull
"${CURRENT_DIR}/ollama/ollama" pull "${MODEL_NAME}"

echo ""
echo "Model downloaded successfully!"
echo "You can now use this model with PAW by editing paw-local-config.ini"
echo ""
EOF
    chmod +x "${CURRENT_DIR}/pull_model.sh"
    
    # Ask if the user wants to pull the recommended model
    MODEL=$(grep "^model" "${CURRENT_DIR}/paw-local-config.ini" | cut -d'=' -f2- | tr -d ' ')
    echo ""
    echo "Local Ollama installation complete."
    echo "The PAW configuration is set to use model: ${MODEL}"
    read -p "Would you like to pull this model now? (y/n): " pull_model
    
    if [[ "$pull_model" =~ ^[Yy]$ ]]; then
        echo "Pulling model ${MODEL}..."
        echo ""
        echo "This will start a background Ollama server if needed."
        
        # Check if server is running, if not start it in background
        if ! curl -s --connect-timeout 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
            echo "Starting Ollama server in background..."
            # Start the server using the full path
            nohup "${OLLAMA_DIR}/run_ollama.sh" > "${CURRENT_DIR}/ollama_server.log" 2>&1 &
            
            # Wait for server to start
            echo "Waiting for Ollama server to start..."
            for i in {1..30}; do
                if curl -s --connect-timeout 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
                    echo "Ollama server is running."
                    break
                fi
                sleep 1
                echo -n "."
            done
            echo ""
        fi
        
        # Pull the model
        "${CURRENT_DIR}/pull_model.sh" "${MODEL}"
        
        echo "You can now use PAW with this model."
    else
        echo "You can pull the model later by running: ./pull_model.sh ${MODEL}"
    fi
fi

# Print instructions
echo ""
echo "Ollama has been installed locally!"
echo ""
echo "To start the Ollama server:"
echo "  ${OLLAMA_DIR}/run_ollama.sh"
echo ""
echo "To use Ollama client:"
echo "  ${OLLAMA_DIR}/ollama <command>"
echo ""
echo "To pull a model:"
echo "  ./pull_model.sh <model_name>"
echo ""
echo "To run PAW with local Ollama configuration:"
echo "  ./run_paw.sh \"your prompt\""
echo ""
echo "Models will be stored in: ${OLLAMA_MODELS}"
echo "" 