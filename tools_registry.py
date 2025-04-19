#!/usr/bin/env python3

import os
import json
import shutil
from pathlib import Path
import sys
import importlib.util

# Get the absolute path of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define possible installation paths
POSSIBLE_INSTALL_PATHS = [
    '/usr/local/share/paw',  # System-wide installation
    os.path.join(SCRIPT_DIR, 'lib'),  # Local development
    SCRIPT_DIR,  # Current directory
]

# Add all possible paths to Python path, avoiding duplicates
for path in POSSIBLE_INSTALL_PATHS:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

# Clear any existing duplicate paths
sys.path = list(dict.fromkeys(sys.path))

# Try importing the extensive_kali_tools module
try:
    import extensive_kali_tools
except ImportError:
    print("Error: Could not import extensive_kali_tools module.")
    sys.exit(1)

def get_tools_registry():
    """Get the tools registry from extensive_kali_tools."""
    try:
        # Use get_all_kali_tools function from extensive_kali_tools
        return extensive_kali_tools.get_all_kali_tools()
    except Exception as e:
        print(f"Error loading tools from extensive_kali_tools: {e}")
        return []

def register_tool(tool):
    """
    Register a new tool in the registry.
    
    Args:
        tool: Dictionary containing tool information
        
    Returns:
        Boolean indicating success
    """
    # This functionality is disabled as we're only using extensive_kali_tools now
    print("Warning: Custom tool registration is disabled. Using only extensive_kali_tools.")
    return False

def get_tools_by_category(category=None):
    """
    Get all tools or filter by category.
    
    Args:
        category: Optional category to filter by
        
    Returns:
        List of tools or filtered list by category
    """
    if category:
        try:
            return extensive_kali_tools.get_tools_by_category(category)
        except Exception as e:
            print(f"Error getting tools by category: {e}")
            return []
    else:
        return get_tools_registry()

def check_tool_availability():
    """
    Check which tools from the registry are available on the system.
    
    Returns:
        Dictionary mapping tool names to availability status (boolean)
    """
    tools = get_tools_registry()
    availability = {}
    
    for tool in tools:
        if isinstance(tool, dict) and "name" in tool:
            # Check if the tool is in the PATH
            tool_name = tool["name"]
            tool_path = shutil.which(tool_name)
            availability[tool_name] = bool(tool_path)
    
    return availability

def add_tool_to_registry(name, category, description, common_usage, examples=None):
    """
    Add a new tool to the registry (legacy function for backward compatibility).
    
    Args:
        name: Tool name
        category: Tool category
        description: Tool description
        common_usage: Tool common usage pattern
        examples: Optional list of example commands
        
    Returns:
        Boolean indicating success
    """
    # This functionality is disabled as we're only using extensive_kali_tools now
    print("Warning: Custom tool registration is disabled. Using only extensive_kali_tools.")
    return False

if __name__ == "__main__":
    # Print the tools registry when run directly
    tools = get_tools_registry()
    print(json.dumps(tools, indent=4)) 