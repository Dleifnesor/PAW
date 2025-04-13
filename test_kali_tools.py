#!/usr/bin/env python3
"""
Test script to verify that Kali Linux tools have been properly integrated with PAW.
This script checks if tools are registered and displays sample queries that would use them.
"""

import sys
import random
from typing import List, Dict, Any, Optional

# Try to import required modules
try:
    from tools_registry import get_tools_registry
except ImportError:
    print("Error: Could not import PAW tools_registry module.")
    print("Make sure PAW is installed correctly and this script is in the correct directory.")
    sys.exit(1)

def get_kali_tools() -> List[Dict[str, Any]]:
    """
    Get all Kali Linux tools from the registry.
    
    Returns:
        List of Kali tools
    """
    registry = get_tools_registry()
    
    # Filter for common Kali tool categories
    kali_categories = [
        "Information Gathering",
        "Vulnerability Analysis",
        "Web Application Analysis",
        "Database Assessment",
        "Password Attacks",
        "Wireless Attacks",
        "Reverse Engineering",
        "Exploitation Tools",
        "Sniffing & Spoofing",
        "Post Exploitation",
        "Forensics",
        "Reporting Tools",
        "Social Engineering Tools"
    ]
    
    return [tool for tool in registry if tool.get("category") in kali_categories]

def display_tool_stats(tools: List[Dict[str, Any]]) -> None:
    """
    Display statistics about the tools.
    
    Args:
        tools: List of tool dictionaries
    """
    if not tools:
        print("No Kali Linux tools found in the registry.")
        print("Please run 'python3 extensive_kali_tools.py' to add tools first.")
        return
    
    # Count tools by category
    categories = {}
    for tool in tools:
        category = tool.get("category", "Uncategorized")
        if category not in categories:
            categories[category] = []
        categories[category].append(tool)
    
    # Display summary
    print(f"Found {len(tools)} Kali Linux tools in {len(categories)} categories:")
    
    for category, cat_tools in sorted(categories.items()):
        print(f"  - {category}: {len(cat_tools)} tools")

def get_sample_tool(tools: List[Dict[str, Any]], category: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get a random sample tool, optionally filtered by category.
    
    Args:
        tools: List of tool dictionaries
        category: Optional category to filter by
        
    Returns:
        A random tool dictionary or None if no tools match
    """
    if category:
        filtered_tools = [tool for tool in tools if tool.get("category") == category]
    else:
        filtered_tools = tools
    
    if not filtered_tools:
        return None
    
    return random.choice(filtered_tools)

def display_sample_queries() -> None:
    """
    Display sample natural language queries that would use Kali tools.
    """
    print("\nSample Natural Language Queries for PAW:")
    print("---------------------------------------")
    
    queries = [
        "Scan the network 192.168.1.0/24 for open ports",
        "Find vulnerabilities on the web server at example.com",
        "Check if the WordPress site at example.org has security issues",
        "Perform a SQL injection test on http://example.com/page.php?id=1",
        "Crack the password hash 5f4dcc3b5aa765d61d8327deb882cf99",
        "Capture and analyze network traffic on interface eth0",
        "Look for subdomains of example.com",
        "Test the wireless network for vulnerabilities",
        "Check if the SSH server has any exploitable vulnerabilities",
        "Recover deleted files from the disk image",
        "Generate a comprehensive penetration testing report",
        "Perform a man-in-the-middle attack on the local network",
        "Create a wordlist for password cracking"
    ]
    
    for query in queries:
        print(f"  • \"{query}\"")

def display_sample_tool_usage(tools: List[Dict[str, Any]]) -> None:
    """
    Display sample usage for a few random tools.
    
    Args:
        tools: List of tool dictionaries
    """
    if not tools:
        return
    
    print("\nSample Tool Usage:")
    print("-----------------")
    
    # Try to get tools from different categories
    categories = ["Information Gathering", "Web Application Analysis", "Password Attacks"]
    
    for category in categories:
        tool = get_sample_tool(tools, category)
        if tool:
            print(f"\n{tool['name']} ({category}):")
            print(f"  Description: {tool['description']}")
            print(f"  Usage: {tool['common_usage']}")
            
            if tool.get("examples"):
                if isinstance(tool["examples"][0], dict):  # New format with description/command
                    example = tool["examples"][0]
                    print(f"  Example: {example['description']}")
                    print(f"    $ {example['command']}")
                else:  # Old format with just command strings
                    print(f"  Example: {tool['examples'][0]}")
                    
def main() -> None:
    """
    Main function to test Kali tools integration.
    """
    print("\n" + "="*50)
    print("PAW Kali Linux Tools Integration Test")
    print("="*50)
    
    # Get all Kali Linux tools from registry
    kali_tools = get_kali_tools()
    
    # Display statistics
    display_tool_stats(kali_tools)
    
    # Display sample tool usage
    display_sample_tool_usage(kali_tools)
    
    # Display sample natural language queries
    display_sample_queries()
    
    # Provide conclusion
    if kali_tools:
        print("\nTest passed! Kali Linux tools are properly integrated with PAW.")
        print("You can now use these tools through natural language queries in PAW.")
    else:
        print("\nTest failed! No Kali Linux tools found in the registry.")
        print("Please run 'python3 extensive_kali_tools.py' to add the tools first.")

if __name__ == "__main__":
    main() 