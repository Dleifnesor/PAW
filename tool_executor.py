#!/usr/bin/env python3
# PAW Tool Executor
# Handles execution of external tools and command parsing

import subprocess
import re
import shlex
from typing import List, Dict, Tuple, Optional, Any

def parse_tool_command(command: str) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Parse a user command and convert it to a proper shell command.
    
    Args:
        command: The user's command string
        
    Returns:
        Tuple of (command_list, explanation) or (None, None) if invalid
    """
    # Strip the command
    command = command.strip()
    
    # Handle aircrack-ng suite commands
    if command.startswith("aircrack") or command.startswith("aireplay") or \
       command.startswith("airodump") or command.startswith("airmon"):
        
        # Extract the actual command parts
        parts = shlex.split(command)
        tool = parts[0]
        
        # Provide explanations based on common command patterns
        explanation = None
        
        if tool == "airmon-ng":
            if len(parts) >= 2 and parts[1] == "start":
                explanation = "Enabling monitor mode on wireless interface"
            elif len(parts) >= 2 and parts[1] == "stop":
                explanation = "Disabling monitor mode on wireless interface"
            elif len(parts) >= 2 and parts[1] == "check":
                if len(parts) >= 3 and parts[2] == "kill":
                    explanation = "Killing processes that might interfere with monitor mode"
                else:
                    explanation = "Checking for processes that might interfere with monitor mode"
            else:
                explanation = "Listing wireless interfaces"
                
        elif tool == "airodump-ng":
            explanation = "Capturing wireless packets"
            if "--bssid" in command:
                explanation = "Capturing packets for a specific access point"
            if "-w" in command or "--write" in command:
                explanation += " and saving to file"
                
        elif tool == "aireplay-ng":
            if "-0" in command or "--deauth" in command:
                explanation = "Performing deauthentication attack"
            elif "-1" in command or "--fakeauth" in command:
                explanation = "Performing fake authentication"
            elif "-3" in command or "--arpreplay" in command:
                explanation = "Performing ARP replay attack"
            else:
                explanation = "Performing packet injection"
                
        elif tool == "aircrack-ng":
            explanation = "Attempting to crack wireless keys"
            if "-w" in command:
                explanation += " using a wordlist"
                
        # Return the command as is - it's a valid tool
        return parts, explanation
    
    # If we get here, the command wasn't recognized
    return None, None

def execute_tool_command(command: List[str]) -> str:
    """
    Execute a command and return the output.
    
    Args:
        command: List containing the command and its arguments
        
    Returns:
        String output from the command
    """
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Check for errors
        if result.returncode != 0 and result.stderr:
            return f"Error: {result.stderr}"
            
        # Return stdout, or stderr if stdout is empty, or a success message
        return result.stdout or result.stderr or "Command executed successfully."
    
    except FileNotFoundError:
        return f"Error: Command '{command[0]}' not found. Make sure it's installed."
    except subprocess.SubprocessError as e:
        return f"Error executing command: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    # Test parsing and execution
    test_commands = [
        "airmon-ng start wlan0",
        "airodump-ng --bssid 00:11:22:33:44:55 -c 1 -w capture wlan0mon",
        "aireplay-ng -0 10 -a 00:11:22:33:44:55 -c FF:FF:FF:FF:FF:FF wlan0mon",
        "aircrack-ng -w /usr/share/wordlists/rockyou.txt capture*.cap"
    ]
    
    for cmd in test_commands:
        print(f"Command: {cmd}")
        parsed, explanation = parse_tool_command(cmd)
        if parsed:
            print(f"Parsed: {parsed}")
            print(f"Explanation: {explanation}")
        else:
            print("Invalid command")
        print() 