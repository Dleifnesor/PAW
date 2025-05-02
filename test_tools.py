#!/usr/bin/env python3
# Test script for Kali tools context functionality

import sys
from context_lib import get_context_for_prompt

def main():
    """Test the Kali tools context functionality"""
    # List of tool names/queries to test
    test_queries = [
        "aircrack-ng",
        "nmap",
        "metasploit",
        "hashcat",
        "wireshark",
        "sqlmap",
        "how to use hydra",
        "how to crack wifi passwords",
        "network scanning tools",
        "wireless hacking",
        "password cracking"
    ]
    
    if len(sys.argv) > 1:
        # Use command line argument if provided
        custom_query = " ".join(sys.argv[1:])
        print(f"\n=== Looking up information for: {custom_query} ===\n")
        context = get_context_for_prompt(custom_query)
        if context:
            print(context)
        else:
            print("No relevant context found for your query.")
        return
    
    # Run through test queries
    print("Testing Kali tools context library...\n")
    
    for query in test_queries:
        print(f"=== Query: {query} ===")
        context = get_context_for_prompt(query)
        if context:
            # Print just the first few lines to avoid overwhelming output
            lines = context.split('\n')
            print('\n'.join(lines[:5]))
            if len(lines) > 5:
                print(f"... ({len(lines) - 5} more lines)")
        else:
            print("No context found")
        print()
    
    print("Test complete. Run with a specific query to see full details.")
    print("Example: python test_tools.py how to use aircrack-ng")

if __name__ == "__main__":
    main() 