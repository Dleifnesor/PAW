#!/usr/bin/env python3
"""
Test script to verify that only extensive_kali_tools.py is being used
as the source for tool information.
"""

import sys
import os
import json

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the required modules
try:
    from tools_registry import get_tools_registry
    import extensive_kali_tools
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def main():
    # Get tools from tools_registry
    registry_tools = get_tools_registry()
    
    # Get tools directly from extensive_kali_tools
    kali_tools = extensive_kali_tools.get_all_kali_tools()
    
    # Compare the tools
    registry_count = len(registry_tools)
    kali_count = len(kali_tools)
    
    print(f"Number of tools from tools_registry: {registry_count}")
    print(f"Number of tools from extensive_kali_tools: {kali_count}")
    
    # Check if they are the same tools
    if registry_count == kali_count:
        print("✅ Tools count matches between tools_registry and extensive_kali_tools.")
        
        # Check if tools_registry is actually using extensive_kali_tools
        sample_tool = None
        if registry_tools:
            sample_tool = registry_tools[0]['name']
            print(f"Sample tool from registry: {sample_tool}")
            
            # Compare a sample tool from both sources
            tool_in_registry = next((t for t in registry_tools if t['name'] == sample_tool), None)
            tool_in_kali = next((t for t in kali_tools if t['name'] == sample_tool), None)
            
            if tool_in_registry and tool_in_kali:
                if tool_in_registry == tool_in_kali:
                    print("✅ Sample tool data matches between sources.")
                else:
                    print("❌ Sample tool data differs between sources.")
            else:
                print("❌ Could not find sample tool in both sources.")
    else:
        print("❌ Tools count differs between tools_registry and extensive_kali_tools.")
    
    print("\nVerification complete. If all checks pass, tools_registry is correctly using extensive_kali_tools.")

if __name__ == "__main__":
    main() 