#!/bin/bash

# Uninstall local Ollama installation

CURRENT_DIR=$(pwd)
OLLAMA_DIR="${CURRENT_DIR}/ollama"
MODELS_DIR="${CURRENT_DIR}/models"

echo "Uninstalling local Ollama installation..."

# Check if Ollama directory exists
if [ ! -d "${OLLAMA_DIR}" ]; then
  echo "Local Ollama installation not found. Nothing to uninstall."
  exit 0
fi

# Check if there are models and ask if they should be removed
if [ -d "${MODELS_DIR}" ] && [ "$(ls -A "${MODELS_DIR}" 2>/dev/null)" ]; then
  echo "WARNING: Downloaded models were found in ${MODELS_DIR}"
  read -p "Do you want to remove all downloaded models? (y/n): " remove_models
  
  if [[ "${remove_models}" =~ ^[Yy]$ ]]; then
    echo "Removing model files..."
    rm -rf "${MODELS_DIR}"
    echo "Models removed."
  else
    echo "Keeping model files."
  fi
fi

# Remove Ollama directory
echo "Removing Ollama installation..."
rm -rf "${OLLAMA_DIR}"

# Remove configuration file
if [ -f "${CURRENT_DIR}/paw-local-config.ini" ]; then
  read -p "Do you want to remove the local PAW configuration file? (y/n): " remove_config
  
  if [[ "${remove_config}" =~ ^[Yy]$ ]]; then
    rm -f "${CURRENT_DIR}/paw-local-config.ini"
    echo "Local PAW configuration removed."
  else
    echo "Keeping local PAW configuration."
  fi
fi

# Remove log directory
if [ -d "${CURRENT_DIR}/logs" ]; then
  read -p "Do you want to remove the logs directory? (y/n): " remove_logs
  
  if [[ "${remove_logs}" =~ ^[Yy]$ ]]; then
    rm -rf "${CURRENT_DIR}/logs"
    echo "Logs directory removed."
  else
    echo "Keeping logs directory."
  fi
fi

# Remove wrapper script
if [ -f "${CURRENT_DIR}/run_paw.sh" ]; then
  rm -f "${CURRENT_DIR}/run_paw.sh"
  echo "PAW wrapper script removed."
fi

echo ""
echo "Local Ollama installation has been uninstalled."
echo "" 