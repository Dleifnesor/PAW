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

# Download Ollama - fixed URL and added error checking
echo "Downloading Ollama..."
DOWNLOAD_URL="https://github.com/ollama/ollama/releases/latest/download/${OLLAMA_PACKAGE}"
if ! curl -L "${DOWNLOAD_URL}" -o "${OLLAMA_BIN}/ollama"; then
    echo "Error: Failed to download Ollama from ${DOWNLOAD_URL}"
    exit 1
fi

# Make the binary executable
chmod +x "${OLLAMA_BIN}/ollama"
if [ ! -x "${OLLAMA_BIN}/ollama" ]; then
    echo "Error: Failed to make Ollama executable"
    exit 1
fi

echo "Ollama binary downloaded successfully"

# Create wrapper script with environment variables
cat > "${OLLAMA_DIR}/run_ollama.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
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
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
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

# Verify installation
if [ ! -f "${OLLAMA_BIN}/ollama" ]; then
    echo "Error: Ollama installation failed. Binary not found."
    exit 1
fi

# Check if pull_model.sh exists and make it executable
if [ -f "${CURRENT_DIR}/pull_model.sh" ]; then
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
echo "  ./ollama/run_ollama.sh"
echo ""
echo "To use Ollama client:"
echo "  ./ollama/ollama <command>"
echo ""
echo "To pull a model:"
echo "  ./pull_model.sh <model_name>"
echo ""
echo "To run PAW with local Ollama configuration:"
echo "  ./run_paw.sh \"your prompt\""
echo ""
echo "Models will be stored in: ${OLLAMA_MODELS}"
echo "" 