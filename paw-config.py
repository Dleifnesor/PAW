#!/usr/bin/env python3
# PAW Configuration Utility
# Configure settings for the PAW (Prompt Assisted Workflow) tool

import argparse
import configparser
import os
import sys
from pathlib import Path

# Default configuration values
DEFAULT_CONFIG = {
    'general': {
        'model': 'llama3',
        'temperature': '0.7',
        'max_tokens': '500',
        'show_thinking': 'false',
        'save_history': 'true',
        'use_last_output': 'true',
        'max_last_output_lines': '20'
    }
}

def get_config_path():
    """Return the path to the config file."""
    return os.path.expanduser("~/.config/paw/config.ini")

def load_config():
    """Load the configuration from the config file."""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    
    # Set default configuration
    for section, options in DEFAULT_CONFIG.items():
        if not config.has_section(section):
            config.add_section(section)
        for key, value in options.items():
            if not config.has_option(section, key):
                config.set(section, key, value)
    
    # Read the config file if it exists
    if os.path.exists(config_path):
        config.read(config_path)
    
    return config

def save_config(config):
    """Save the configuration to the config file."""
    config_path = get_config_path()
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        config.write(f)

def show_config(config):
    """Display the current configuration."""
    print("Current PAW Configuration:")
    for section in config.sections():
        print(f"\n[{section}]")
        for key, value in config.items(section):
            print(f"{key} = {value}")

def set_config(config, section, key, value):
    """Set a configuration value."""
    if not config.has_section(section):
        config.add_section(section)
    
    config.set(section, key, value)
    save_config(config)
    print(f"Updated {section}.{key} = {value}")

def reset_config():
    """Reset the configuration to default values."""
    config = configparser.ConfigParser()
    
    # Set default configuration
    for section, options in DEFAULT_CONFIG.items():
        config.add_section(section)
        for key, value in options.items():
            config.set(section, key, value)
    
    save_config(config)
    print("Configuration has been reset to default values.")

def list_available_models():
    """List available ollama models."""
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        print("Available Ollama Models:")
        print(result.stdout)
    except Exception as e:
        print(f"Error listing models: {e}")
        print("Make sure ollama is installed and accessible in your PATH.")

def clear_command_history():
    """Clear the saved command history."""
    history_dir = os.path.expanduser("~/.local/share/paw/history")
    history_file = os.path.join(history_dir, "commands_history.txt")
    
    if os.path.exists(history_file):
        try:
            os.remove(history_file)
            print("Command history has been cleared.")
        except Exception as e:
            print(f"Error clearing command history: {e}")
    else:
        print("No command history found.")

def clear_last_output():
    """Clear the saved last command output."""
    last_output_file = os.path.expanduser("~/.local/share/paw/last_output.txt")
    
    if os.path.exists(last_output_file):
        try:
            os.remove(last_output_file)
            print("Last command output has been cleared.")
        except Exception as e:
            print(f"Error clearing last command output: {e}")
    else:
        print("No saved command output found.")

def show_last_output():
    """Display the saved last command output."""
    last_output_file = os.path.expanduser("~/.local/share/paw/last_output.txt")
    
    if os.path.exists(last_output_file):
        try:
            with open(last_output_file, 'r') as f:
                content = f.read()
            if content.strip():
                print("Last Command Output:")
                print("--------------------")
                print(content)
                print("--------------------")
            else:
                print("Last command output is empty.")
        except Exception as e:
            print(f"Error reading last command output: {e}")
    else:
        print("No saved command output found.")

def main():
    parser = argparse.ArgumentParser(description="PAW Configuration Utility")
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show current configuration")
    
    # Set command
    set_parser = subparsers.add_parser("set", help="Set a configuration value")
    set_parser.add_argument("--section", required=True, help="Configuration section")
    set_parser.add_argument("--key", required=True, help="Configuration key")
    set_parser.add_argument("--value", required=True, help="Configuration value")
    
    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset configuration to default values")
    
    # Models command
    models_parser = subparsers.add_parser("models", help="List available ollama models")
    
    # Clear history command
    clear_history_parser = subparsers.add_parser("clear-history", help="Clear command history")
    
    # Clear last output command
    clear_output_parser = subparsers.add_parser("clear-output", help="Clear last command output")
    
    # Show last output command
    show_output_parser = subparsers.add_parser("show-output", help="Show last command output")
    
    # Toggle context usage
    toggle_context_parser = subparsers.add_parser("toggle-context", help="Toggle using last output as context")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Execute command
    if args.command == "show":
        show_config(config)
    elif args.command == "set":
        set_config(config, args.section, args.key, args.value)
    elif args.command == "reset":
        reset_config()
    elif args.command == "models":
        list_available_models()
    elif args.command == "clear-history":
        clear_command_history()
    elif args.command == "clear-output":
        clear_last_output()
    elif args.command == "show-output":
        show_last_output()
    elif args.command == "toggle-context":
        current = config.getboolean('general', 'use_last_output')
        new_value = 'false' if current else 'true'
        set_config(config, 'general', 'use_last_output', new_value)
        state = "enabled" if new_value == 'true' else "disabled"
        print(f"Using last command output as context is now {state}")
    else:
        # If no command is provided, show the current configuration
        show_config(config)
        parser.print_help()

if __name__ == "__main__":
    main() 