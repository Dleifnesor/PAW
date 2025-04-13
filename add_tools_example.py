#!/usr/bin/env python3
"""
Example script to demonstrate how to use the extensive_kali_tools module.
This script shows how to add Kali Linux tools to the PAW registry.
"""

import sys
from typing import Dict, List, Any

# Try to import the module
try:
    from extensive_kali_tools import add_extensive_kali_tools, categorize_tools, print_categorized_tools
except ImportError:
    print("Error: Could not import extensive_kali_tools module.")
    print("Make sure the script is in the same directory as this example.")
    sys.exit(1)

def main() -> None:
    """
    Main function to demonstrate tool addition.
    """
    # Print header
    print("\n" + "="*50)
    print("PAW Kali Linux Tools Extension - Example Script")
    print("="*50)
    
    # Check available tools without adding them
    print("\nChecking available Kali Linux tools...")
    tools_to_add = add_extensive_kali_tools(only_show=True)
    
    if not tools_to_add:
        print("\nAll Kali Linux tools are already registered in PAW.")
        print("No new tools to add.")
        return
    
    # Categorize the tools
    categorized_tools = categorize_tools(tools_to_add)
    
    # Print summary
    total_tools = len(tools_to_add)
    total_categories = len(categorized_tools)
    
    print(f"\nFound {total_tools} tools across {total_categories} categories that can be added to PAW:")
    
    # Print categories summary
    for category, tools in sorted(categorized_tools.items()):
        print(f"  - {category}: {len(tools)} tools")
    
    # Print detailed tool list by category
    print_categorized_tools(categorized_tools)
    
    # Ask user for confirmation
    user_input = input("\nWould you like to add these tools to PAW? (yes/no): ")
    
    if user_input.lower() == "yes":
        print("\nAdding tools to PAW registry...")
        add_extensive_kali_tools(only_show=False)
        print(f"\nSuccessfully added {total_tools} Kali Linux tools to the PAW registry.")
        print("You can now use these tools in your workflow.")
    else:
        print("\nNo tools were added to the PAW registry.")
        print("To add these tools later, run this script again or use 'python3 extensive_kali_tools.py'")

if __name__ == "__main__":
    main() 