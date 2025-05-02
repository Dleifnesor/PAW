#!/usr/bin/env python3
# Simple autocomplete module for PAW testing

import readline
import os
import sys

class Completer:
    def __init__(self, options):
        self.options = options
        self.matches = []
    
    def complete(self, text, state):
        if state == 0:
            # This is the first time for this text, so build a match list
            if text:
                self.matches = [s for s in self.options if s.startswith(text)]
            else:
                self.matches = self.options[:]
        
        # Return match indexed by state
        try:
            return self.matches[state]
        except IndexError:
            return None

def setup_completion(keywords):
    """
    Setup readline completion with the given keywords
    
    Args:
        keywords: List of keywords to use for completion
    """
    completer = Completer(keywords)
    readline.set_completer(completer.complete)
    
    # Use different bind settings based on OS
    if 'libedit' in readline.__doc__:
        # macOS uses libedit instead of GNU readline
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    
def main():
    """Test the autocomplete functionality"""
    # Sample keywords for wireless hacking
    keywords = [
        "airmon-ng", "airodump-ng", "aireplay-ng", "aircrack-ng",
        "wifite", "reaver", "bully", "kismet", "nmap", "hydra",
        "monitor mode", "scan network", "capture handshake", "crack password",
        "deauth", "scan port", "change mac", "wps attack"
    ]
    
    # Setup completion
    setup_completion(keywords)
    
    # Simple loop to test completion
    print("PAW Autocomplete Test")
    print("====================")
    print("Type partial commands and press TAB to complete")
    print("Press Ctrl+C to exit")
    print()
    
    history_file = os.path.expanduser("~/.paw_history")
    
    # Try to load history file
    try:
        readline.read_history_file(history_file)
        # Set history length
        readline.set_history_length(50)
    except FileNotFoundError:
        pass
        
    try:
        while True:
            user_input = input("PAW> ")
            if user_input.lower() in ['exit', 'quit', 'q']:
                break
            print(f"You entered: {user_input}")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Save history
        try:
            readline.write_history_file(history_file)
        except Exception as e:
            print(f"Error saving history: {e}")

if __name__ == "__main__":
    main() 