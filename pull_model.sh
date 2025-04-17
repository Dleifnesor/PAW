#!/bin/bash

# Pull a model with the local Ollama installation

if [ $# -eq 0 ]; then
  echo "Usage: $0 <model_name>"
  echo "Example: $0 qwen2.5-coder:7b"
  exit 1
fi

MODEL_NAME="$1"
CURRENT_DIR=$(pwd)

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