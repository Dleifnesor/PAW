#!/bin/bash

# PAW Installation Fix Script
#
# This script attempts to fix common issues with the PAW installation.
# Run this script with sudo if you encounter errors when running PAW.

echo "PAW (Prompt Assisted Workflow) Fix Script"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./fix_paw.sh)"
  exit 1
fi

# Paths
INSTALL_DIR="/usr/local/share/paw"
LIB_DIR="$INSTALL_DIR/lib"
BIN_DIR="/usr/local/bin"

echo "Checking installation directories..."
if [ ! -d "$INSTALL_DIR" ]; then
  echo "ERROR: Main installation directory ($INSTALL_DIR) is missing!"
  echo "PAW is not properly installed. Please run the install.sh script first."
  exit 1
fi

if [ ! -d "$LIB_DIR" ]; then
  echo "Creating missing lib directory..."
  mkdir -p "$LIB_DIR"
fi

# Fix tools_registry.py
echo "Checking tools_registry.py..."
if [ -f "tools_registry.py" ]; then
  echo "Found tools_registry.py in current directory, copying to installation directories..."
  cp tools_registry.py "$LIB_DIR/"
  cp tools_registry.py "$INSTALL_DIR/"
  echo "  ✓ Copied tools_registry.py to lib directory"
elif [ -f "$INSTALL_DIR/tools_registry.py" ] && [ ! -f "$LIB_DIR/tools_registry.py" ]; then
  echo "Found tools_registry.py in main directory, copying to lib directory..."
  cp "$INSTALL_DIR/tools_registry.py" "$LIB_DIR/"
  echo "  ✓ Copied tools_registry.py to lib directory"
elif [ ! -f "$INSTALL_DIR/tools_registry.py" ] && [ ! -f "$LIB_DIR/tools_registry.py" ]; then
  echo "ERROR: tools_registry.py not found in any location!"
  echo "Please make sure you have the original PAW files available."
  exit 1
fi

# Create proper __init__.py files
echo "Creating __init__.py files..."
echo "# PAW lib package" > "$LIB_DIR/__init__.py"
echo "# PAW custom commands package" > "$INSTALL_DIR/custom_commands/__init__.py"

# Fix command wrappers
echo "Fixing command wrappers..."

# Fix PAW command
cat > "$BIN_DIR/PAW" << 'EOF'
#!/bin/bash

# Ensure lib directory is in Python path
INSTALL_DIR="/usr/local/share/paw"
LIB_DIR="$INSTALL_DIR/lib"

# Set Python path to include all necessary directories
export PYTHONPATH="$INSTALL_DIR:$LIB_DIR:$PYTHONPATH"

# Check if tools_registry.py exists
if [ ! -f "$LIB_DIR/tools_registry.py" ] && [ -f "$INSTALL_DIR/tools_registry.py" ]; then
  # Create symlink from main dir to lib dir
  ln -sf "$INSTALL_DIR/tools_registry.py" "$LIB_DIR/tools_registry.py"
fi

python3 "$INSTALL_DIR/paw.py" "$@"
EOF
chmod +x "$BIN_DIR/PAW"

# Fix paw command (lowercase)
cat > "$BIN_DIR/paw" << 'EOF'
#!/bin/bash

# Ensure lib directory is in Python path
INSTALL_DIR="/usr/local/share/paw"
LIB_DIR="$INSTALL_DIR/lib"

# Set Python path to include all necessary directories
export PYTHONPATH="$INSTALL_DIR:$LIB_DIR:$PYTHONPATH"

# Check if tools_registry.py exists
if [ ! -f "$LIB_DIR/tools_registry.py" ] && [ -f "$INSTALL_DIR/tools_registry.py" ]; then
  # Create symlink from main dir to lib dir
  ln -sf "$INSTALL_DIR/tools_registry.py" "$LIB_DIR/tools_registry.py"
fi

python3 "$INSTALL_DIR/paw.py" "$@"
EOF
chmod +x "$BIN_DIR/paw"

# Set correct permissions
echo "Setting correct permissions..."
chown -R root:root "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod 644 "$LIB_DIR/tools_registry.py"
chmod 644 "$INSTALL_DIR/tools_registry.py"

echo "Fixing Python path in paw.py..."
# Ensure paw.py has the correct import paths
TMP_FILE=$(mktemp)
cat "$INSTALL_DIR/paw.py" | sed 's/sys.path.append/sys.path.insert(0,/g' > "$TMP_FILE"
cp "$TMP_FILE" "$INSTALL_DIR/paw.py"
rm "$TMP_FILE"

echo "Verifying fix..."
echo "Running: PYTHONPATH=$LIB_DIR python3 -c 'import tools_registry; print(\"✓ Successfully imported tools_registry\")'"
if PYTHONPATH="$LIB_DIR" python3 -c 'import tools_registry; print("✓ Successfully imported tools_registry")'; then
  echo "Fix appears to be successful!"
  echo "You should now be able to run PAW using the 'paw' command."
else
  echo "There was a problem importing tools_registry module."
  echo "Please check the errors above for more information."
fi

echo "Fix script completed." 