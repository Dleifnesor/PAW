#!/usr/bin/env python3

import os
import sys
import json
import argparse
from pathlib import Path

def add_tool(name, category, description, common_usage, examples):
    """Add a custom tool to the PAW registry."""
    # Create directory if it doesn't exist
    custom_registry_dir = "/usr/local/share/paw/tools"
    custom_registry_path = os.path.join(custom_registry_dir, "custom_registry.json")
    
    os.makedirs(custom_registry_dir, exist_ok=True)
    
    # Load existing registry or create a new one
    if os.path.exists(custom_registry_path):
        try:
            with open(custom_registry_path, 'r') as f:
                custom_registry = json.load(f)
        except Exception:
            custom_registry = {}
    else:
        custom_registry = {}
    
    # Add the new tool
    custom_registry[name] = {
        "category": category,
        "description": description,
        "common_usage": common_usage,
        "examples": examples
    }
    
    # Save the updated registry
    with open(custom_registry_path, 'w') as f:
        json.dump(custom_registry, f, indent=4)
    
    print(f"Tool '{name}' added to PAW registry successfully!")
    return True

def list_tools():
    """List all custom tools in the PAW registry."""
    custom_registry_path = "/usr/local/share/paw/tools/custom_registry.json"
    
    if not os.path.exists(custom_registry_path):
        print("No custom tools registered yet.")
        return
    
    with open(custom_registry_path, 'r') as f:
        custom_registry = json.load(f)
    
    if not custom_registry:
        print("No custom tools registered yet.")
        return
    
    print("\nCustom Tools in PAW Registry:")
    print("============================\n")
    
    for name, info in custom_registry.items():
        print(f"Tool: {name}")
        print(f"Category: {info['category']}")
        print(f"Description: {info['description']}")
        print(f"Common Usage: {info['common_usage']}")
        if info['examples']:
            print("Examples:")
            for example in info['examples']:
                print(f"  - {example}")
        print()

def main():
    parser = argparse.ArgumentParser(description="Add or list custom tools in the PAW registry")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Add tool command
    add_parser = subparsers.add_parser("add", help="Add a new tool to the registry")
    add_parser.add_argument("--name", required=True, help="Name of the tool")
    add_parser.add_argument("--category", required=True, help="Category of the tool (e.g., network_scanning, exploitation)")
    add_parser.add_argument("--description", required=True, help="Description of the tool")
    add_parser.add_argument("--usage", required=True, help="Common usage pattern of the tool")
    add_parser.add_argument("--examples", nargs="+", default=[], help="Example commands (can specify multiple)")
    
    # List tools command
    list_parser = subparsers.add_parser("list", help="List all custom tools in the registry")
    
    args = parser.parse_args()
    
    if args.command == "add":
        add_tool(
            args.name,
            args.category,
            args.description,
            args.usage,
            args.examples
        )
    elif args.command == "list":
        list_tools()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 