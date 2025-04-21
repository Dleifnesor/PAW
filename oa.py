#!/usr/bin/env python3

# Import necessary modules
import os          # For file and directory operations
import json        # For working with JSON files
import requests    # For making HTTP requests to Ollama
import subprocess  # For running shell commands
import readline    # For command history
import atexit      # For saving history when program exits
from colorama import Fore, Style, init  # For colored terminal output

# Initialize colorama for colored text
init()

# Constants - values that don't change
OLLAMA_URL = "http://localhost:11434/api/generate"  # Ollama API endpoint
DEFAULT_MODEL = "codellama"  # Default AI model to use
HISTORY_FILE = os.path.expanduser("~/.oa_history")  # File to store command history
SAVED_COMMANDS_FILE = os.path.expanduser("~/.oa_saved_commands")  # File to store saved commands

def print_banner():
    """Print a colorful banner at the start of the program."""
    banner = f"""
{Fore.GREEN}╔═══════════════════════════════════════════════════════════╗
║ {Fore.CYAN}OA - Ollama Assistant{Fore.GREEN}                                      ║
║ {Fore.CYAN}An AI-powered command generator for Kali Linux{Fore.GREEN}            ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def print_help():
    """Print help information about available commands."""
    help_text = f"""
{Fore.YELLOW}COMMANDS:{Style.RESET_ALL}
  {Fore.CYAN}!help{Style.RESET_ALL}           - Show this help message
  {Fore.CYAN}!exit{Style.RESET_ALL}           - Exit OA
  {Fore.CYAN}!save{Style.RESET_ALL} [name]    - Save the last command with optional name
  {Fore.CYAN}!list{Style.RESET_ALL}           - List all saved commands
  {Fore.CYAN}!load{Style.RESET_ALL} [number]  - Load and execute a saved command
  {Fore.CYAN}!clear{Style.RESET_ALL}          - Clear the screen
  {Fore.CYAN}!model{Style.RESET_ALL} [name]   - Change the Ollama model (default: codellama)
  {Fore.CYAN}!explain{Style.RESET_ALL} [cmd]  - Explain what a command does

{Fore.YELLOW}USAGE:{Style.RESET_ALL}
  Enter your prompt and OA will generate a command to execute.
  Review the command and type {Fore.GREEN}'y'{Style.RESET_ALL} to execute it, {Fore.RED}'n'{Style.RESET_ALL} to reject it,
  or {Fore.CYAN}'e'{Style.RESET_ALL} to edit the command before execution.
"""
    print(help_text)

def load_history():
    """Load command history from file if it exists."""
    if os.path.exists(HISTORY_FILE):
        readline.read_history_file(HISTORY_FILE)

def save_history():
    """Save command history to file."""
    readline.write_history_file(HISTORY_FILE)

def load_saved_commands():
    """Load saved commands from file."""
    if os.path.exists(SAVED_COMMANDS_FILE):
        try:
            with open(SAVED_COMMANDS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_commands(commands):
    """Save commands to file."""
    with open(SAVED_COMMANDS_FILE, 'w') as f:
        json.dump(commands, f, indent=2)

def generate_command(prompt, model):
    """Ask Ollama to generate a command based on the user's prompt."""
    print(f"{Fore.YELLOW}Generating command...{Style.RESET_ALL}")
    
    # Create a prompt that tells Ollama exactly what we want
    enhanced_prompt = f"""
You are a Linux command line expert. Generate a valid command for Kali Linux based on this request:
"{prompt}"
Respond with ONLY the command, no explanation, no markdown, no additional text.
"""
    
    try:
        # Send request to Ollama
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": enhanced_prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            # Get the command from the response
            result = response.json()
            command = result.get("response", "").strip()
            # Clean up the command
            command = command.replace("```bash", "").replace("```", "").strip()
            return command
        else:
            print(f"{Fore.RED}Error: API returned status code {response.status_code}{Style.RESET_ALL}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error connecting to Ollama: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Make sure Ollama is running with: systemctl status ollama{Style.RESET_ALL}")
        return None

def explain_command(command, model):
    """Ask Ollama to explain what a command does."""
    print(f"{Fore.YELLOW}Analyzing command...{Style.RESET_ALL}")
    
    prompt = f"""
Explain what this Linux command does in detail:
{command}

Break down each part of the command and explain its purpose. Highlight any potential security implications or risks.
"""
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        else:
            print(f"{Fore.RED}Error: API returned status code {response.status_code}{Style.RESET_ALL}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error connecting to Ollama: {e}{Style.RESET_ALL}")
        return None

def execute_command(command):
    """Run a shell command and return the result."""
    try:
        # Run the command and capture its output
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def main():
    """Main function that runs the OA tool."""
    # Print the banner
    print_banner()
    print(f"{Fore.CYAN}Type '!help' for usage information{Style.RESET_ALL}\n")
    
    # Set up command history
    load_history()
    atexit.register(save_history)
    
    # Initialize variables
    current_model = DEFAULT_MODEL
    last_command = None
    saved_commands = load_saved_commands()
    
    # Main loop
    while True:
        try:
            # Get user input
            user_input = input(f"{Fore.GREEN}OA> {Style.RESET_ALL}").strip()
            
            # Handle special commands
            if user_input == "!exit":
                break
            elif user_input == "!help":
                print_help()
                continue
            elif user_input == "!clear":
                os.system('cls' if os.name == 'nt' else 'clear')
                print_banner()
                continue
            elif user_input.startswith("!model"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    current_model = parts[1]
                    print(f"{Fore.GREEN}Model set to: {current_model}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}Current model: {current_model}{Style.RESET_ALL}")
                continue
            elif user_input == "!save":
                if last_command:
                    saved_commands.append({
                        "name": f"Command {len(saved_commands) + 1}",
                        "command": last_command
                    })
                    save_commands(saved_commands)
                    print(f"{Fore.GREEN}Command saved as 'Command {len(saved_commands)}'{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}No command to save{Style.RESET_ALL}")
                continue
            elif user_input.startswith("!save "):
                if last_command:
                    name = user_input[6:].strip()
                    saved_commands.append({
                        "name": name,
                        "command": last_command
                    })
                    save_commands(saved_commands)
                    print(f"{Fore.GREEN}Command saved as '{name}'{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}No command to save{Style.RESET_ALL}")
                continue
            elif user_input == "!list":
                if saved_commands:
                    print(f"{Fore.CYAN}Saved commands:{Style.RESET_ALL}")
                    for i, cmd in enumerate(saved_commands, 1):
                        print(f"{Fore.YELLOW}{i}.{Style.RESET_ALL} {cmd['name']}: {Fore.CYAN}{cmd['command']}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}No saved commands{Style.RESET_ALL}")
                continue
            elif user_input.startswith("!load "):
                try:
                    index = int(user_input[6:].strip()) - 1
                    if 0 <= index < len(saved_commands):
                        cmd = saved_commands[index]["command"]
                        print(f"{Fore.CYAN}Command: {cmd}{Style.RESET_ALL}")
                        confirm = input(f"{Fore.YELLOW}Execute this command? (y/n): {Style.RESET_ALL}").lower()
                        if confirm == 'y':
                            success, output = execute_command(cmd)
                            if success:
                                print(f"{Fore.GREEN}Command executed successfully:{Style.RESET_ALL}")
                                print(output)
                            else:
                                print(f"{Fore.RED}Command failed:{Style.RESET_ALL}")
                                print(output)
                            last_command = cmd
                    else:
                        print(f"{Fore.RED}Invalid command index{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}Invalid command index{Style.RESET_ALL}")
                continue
            elif user_input.startswith("!explain"):
                cmd_to_explain = user_input[9:].strip()
                if not cmd_to_explain and last_command:
                    cmd_to_explain = last_command
                
                if cmd_to_explain:
                    explanation = explain_command(cmd_to_explain, current_model)
                    if explanation:
                        print(f"{Fore.CYAN}Command: {cmd_to_explain}{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}Explanation:{Style.RESET_ALL}")
                        print(explanation)
                else:
                    print(f"{Fore.YELLOW}No command to explain{Style.RESET_ALL}")
                continue
            
            # Handle regular command generation
            if not user_input:
                continue
                
            # Generate command from user's prompt
            generated_command = generate_command(user_input, current_model)
            
            if not generated_command:
                continue
                
            print(f"{Fore.CYAN}Generated command: {Fore.YELLOW}{generated_command}{Style.RESET_ALL}")
            
            # Ask user what to do with the command
            confirm = input(f"{Fore.GREEN}Execute? (y/n/e to edit): {Style.RESET_ALL}").lower()
            
            if confirm == 'e':
                # Let user edit the command
                readline.add_history(generated_command)
                edited_command = input(f"{Fore.YELLOW}Edit command: {Style.RESET_ALL}")
                if edited_command:
                    generated_command = edited_command
                    print(f"{Fore.CYAN}Command to execute: {Fore.YELLOW}{generated_command}{Style.RESET_ALL}")
                    confirm = input(f"{Fore.GREEN}Execute edited command? (y/n): {Style.RESET_ALL}").lower()
            
            if confirm == 'y':
                # Execute the command
                success, output = execute_command(generated_command)
                if success:
                    print(f"{Fore.GREEN}Command executed successfully:{Style.RESET_ALL}")
                    print(output)
                else:
                    print(f"{Fore.RED}Command failed:{Style.RESET_ALL}")
                    print(output)
                last_command = generated_command
            else:
                print(f"{Fore.YELLOW}Command execution cancelled{Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Use !exit to quit{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}Goodbye!{Style.RESET_ALL}")

# Start the program
if __name__ == "__main__":
    main() 