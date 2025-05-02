#!/usr/bin/env python3
# Test script for PAW's suggest mode functionality

import sys
import subprocess

def main():
    """
    Test the PAW suggest mode functionality with various wireless hacking queries
    """
    test_queries = [
        "How do I enable monitor mode?",
        "How to scan for wireless networks?",
        "How to capture a WPA handshake?",
        "How to crack a wifi password?",
        "How to deauthenticate a client?",
        "How to scan for open ports on a target?",
        "How to change my MAC address?"
    ]
    
    print("PAW Suggest Mode Test")
    print("=====================\n")
    
    if len(sys.argv) > 1:
        # Run with custom query if provided
        query = " ".join(sys.argv[1:])
        print(f"Testing suggest mode with: '{query}'\n")
        try:
            result = subprocess.run(["python", "paw.py", "-s", query], 
                                   capture_output=True, text=True, check=True)
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error running PAW with suggest mode: {e}")
            print(e.stdout)
            print(e.stderr)
    else:
        # Run through all test queries
        for i, query in enumerate(test_queries, 1):
            print(f"\n=== Test {i}: '{query}' ===\n")
            try:
                result = subprocess.run(["python", "paw.py", "-s", query], 
                                       capture_output=True, text=True, check=True)
                print(result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"Error running PAW with suggest mode: {e}")
        
        print("\nAll tests completed.")
        print("\nTo test with your own query:")
        print("python test_suggest.py 'your query here'")

if __name__ == "__main__":
    main() 