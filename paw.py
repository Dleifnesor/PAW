#!/usr/bin/env python3

import os
import sys
import json
import time
import shlex
import logging
import argparse
import configparser
import subprocess
from pathlib import Path
from datetime import datetime
import httpx
import importlib.util
import re
import socket

# Add rich library for fancy UI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.layout import Layout
    RICH_AVAILABLE = True
except ImportError:
    print("For a better experience, install rich: pip install rich")
    RICH_AVAILABLE = False

# Add the PAW lib directory to the Python path
sys.path.append('/usr/local/share/paw/lib')

try:
    from ascii_art import display_ascii_art
    from tools_registry import get_tools_registry
except ImportError:
    # For development/local environment
    from ascii_art import display_ascii_art
    from tools_registry import get_tools_registry

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger('PAW')

# Configuration
CONFIG_PATH = "/etc/paw/config.ini"
config = configparser.ConfigParser()

if os.path.exists(CONFIG_PATH):
    config.read(CONFIG_PATH)
else:
    logger.error(f"Configuration file not found: {CONFIG_PATH}")
    sys.exit(1)

MODEL = config['DEFAULT'].get('model', 'qwen2.5-coder:7b')
OLLAMA_HOST = config['DEFAULT'].get('ollama_host', 'http://localhost:11434')
EXPLAIN_COMMANDS = config['DEFAULT'].getboolean('explain_commands', True)
LOG_COMMANDS = config['DEFAULT'].getboolean('log_commands', True)
LOG_DIRECTORY = config['DEFAULT'].get('log_directory', '/var/log/paw')
# Configurable timeout (default: 180 seconds)
LLM_TIMEOUT = float(config['DEFAULT'].get('llm_timeout', '180.0'))
# Theme configuration
THEME = config['DEFAULT'].get('theme', 'cyberpunk').lower()

# Create log directory if it doesn't exist
os.makedirs(LOG_DIRECTORY, exist_ok=True)

# Theme colors
THEMES = {
    'cyberpunk': {
        'primary': '#FF00FF',  # Magenta
        'secondary': '#00FFFF', # Cyan
        'accent': '#FFFF00',   # Yellow
        'success': '#00FF00',  # Green
        'error': '#FF0000',    # Red
        'info': '#0000FF',     # Blue
        'border_style': 'bold magenta',
        'title_style': 'bold cyan',
        'code_theme': 'monokai'
    },
    'hacker': {
        'primary': '#00FF00',  # Green
        'secondary': '#FFFFFF', # White
        'accent': '#00FFFF',   # Cyan
        'success': '#00FF00',  # Green
        'error': '#FF0000',    # Red
        'info': '#00FFFF',     # Cyan
        'border_style': 'bold green',
        'title_style': 'bold green',
        'code_theme': 'vim'
    },
    'dracula': {
        'primary': '#BD93F9',  # Purple
        'secondary': '#F8F8F2', # White
        'accent': '#FF79C6',   # Pink
        'success': '#50FA7B',  # Green
        'error': '#FF5555',    # Red
        'info': '#8BE9FD',     # Cyan
        'border_style': 'bold purple',
        'title_style': 'bold cyan',
        'code_theme': 'dracula'
    }
}

# Use default theme if configured theme is not available
if THEME not in THEMES:
    THEME = 'cyberpunk'

# Initialize rich console if available
if RICH_AVAILABLE:
    console = Console()
else:
    console = None

def rich_print(message, style=None, highlight=False):
    """Print with rich formatting if available, otherwise fallback to print"""
    if RICH_AVAILABLE:
        console.print(message, style=style, highlight=highlight)
    else:
        print(message)

def show_fancy_header(title, subtitle=None):
    """Display a fancy header for PAW operations"""
    if RICH_AVAILABLE:
        theme_colors = THEMES[THEME]
        grid = Table.grid(expand=True)
        grid.add_column(justify="center")
        
        grid.add_row("")
        grid.add_row(Panel(
            f"[{theme_colors['title_style']}]{title}[/]",
            border_style=theme_colors['border_style'],
            padding=(1, 10),
        ))
        if subtitle:
            grid.add_row(f"[{theme_colors['accent']}]{subtitle}[/]")
        grid.add_row("")
        
        console.print(grid)
    else:
        print("\n" + "=" * 60)
        print(f"  {title}")
        if subtitle:
            print(f"  {subtitle}")
        print("=" * 60 + "\n")

class PAW:
    def __init__(self):
        self.tools_registry = get_tools_registry()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(LOG_DIRECTORY, f"paw_session_{self.session_id}.log")
        self.theme = THEMES[THEME]
        
        if LOG_COMMANDS:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
        
        # Get config for adaptive mode
        self.adaptive_mode = config['DEFAULT'].getboolean('adaptive_mode', False)
    
    def generate_llm_response(self, prompt):
        """Generate a response from the LLM using Ollama."""
        try:
            logger.info(f"Sending prompt to LLM: {prompt[:50]}...")
            
            # Use fancy spinner for thinking animation if rich is available
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold cyan]Thinking...[/]"),
                    TimeElapsedColumn(),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("Thinking...", total=None)
                    
                    response = httpx.post(
                        f"{OLLAMA_HOST}/api/generate",
                        json={
                            "model": MODEL,
                            "prompt": prompt,
                            "system": "You are PAW, a Prompt Assisted Workflow tool for Kali Linux. Your job is to help users perform cybersecurity tasks by translating natural language requests into a sequence of commands. For each request, output a JSON object with the following structure: {\"plan\": [string], \"commands\": [string], \"explanation\": [string]}. The 'plan' should outline the steps to achieve the user's goal, 'commands' should list the actual Linux commands to execute (one per line), and 'explanation' should provide context for what each command does.",
                            "stream": False,
                        },
                        timeout=LLM_TIMEOUT
                    )
            else:
                print(f"\033[1;34m[*] Thinking...\033[0m (timeout: {LLM_TIMEOUT}s)")
                response = httpx.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={
                        "model": MODEL,
                        "prompt": prompt,
                        "system": "You are PAW, a Prompt Assisted Workflow tool for Kali Linux. Your job is to help users perform cybersecurity tasks by translating natural language requests into a sequence of commands. For each request, output a JSON object with the following structure: {\"plan\": [string], \"commands\": [string], \"explanation\": [string]}. The 'plan' should outline the steps to achieve the user's goal, 'commands' should list the actual Linux commands to execute (one per line), and 'explanation' should provide context for what each command does.",
                        "stream": False,
                    },
                    timeout=LLM_TIMEOUT
                )
            
            if response.status_code != 200:
                logger.error(f"Error from Ollama: {response.text}")
                return {"error": f"Ollama API error: {response.status_code}"}
            
            result = response.json()
            return self.extract_json_from_response(result.get("response", ""))
            
        except httpx.TimeoutException:
            logger.error(f"LLM request timed out after {LLM_TIMEOUT} seconds")
            return {"error": f"LLM request timed out after {LLM_TIMEOUT} seconds. Try setting a longer timeout in /etc/paw/config.ini."}
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return {"error": str(e)}
    
    def extract_json_from_response(self, text):
        """Extract JSON from the LLM response."""
        try:
            # Find JSON in the response (might be surrounded by markdown code blocks)
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = text[json_start:json_end]
                return json.loads(json_str)
            
            # If no JSON found, try to create a structured response from the text
            return {
                "plan": ["Process the request"],
                "commands": [text.strip()],
                "explanation": ["Generated command based on your request"]
            }
            
        except json.JSONDecodeError:
            # If JSON parsing fails, use the whole response as a command
            return {
                "plan": ["Process the request"],
                "commands": [text.strip()],
                "explanation": ["Generated command based on your request"]
            }
    
    def extract_variables(self, stdout):
        """Extract potential variables from command output."""
        variables = {}
        
        # Look for IP addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, stdout)
        if ips:
            variables['ip_addresses'] = ips
            variables['target_ip'] = ips[0]  # First IP as default target
            if len(ips) > 1:
                variables['target_ip_range'] = f"{ips[0]}/24"  # Assume subnet
        
        # Look for hostnames
        host_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
        hosts = re.findall(host_pattern, stdout)
        if hosts:
            variables['hostnames'] = hosts
            variables['target_host'] = hosts[0]
        
        # Look for ports
        port_pattern = r'(\d+)\/(?:tcp|udp)\s+(?:open|filtered)'
        ports = re.findall(port_pattern, stdout)
        if ports:
            variables['ports'] = ports
            variables['target_port'] = ports[0]
        
        # Look for URLs
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        urls = re.findall(url_pattern, stdout)
        if urls:
            variables['urls'] = urls
            variables['target_url'] = urls[0]

        # Extract host status information from nmap
        if "host seems down" in stdout.lower():
            variables['host_status'] = "down"
        elif "0 hosts up" in stdout.lower():
            variables['host_status'] = "down"
        elif "hosts up" in stdout.lower():
            variables['host_status'] = "up"
            
        return variables
    
    def get_local_ip(self):
        """Get the local IP address for the machine."""
        try:
            # Create a socket to determine the local IP used for internet connection
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Doesn't need to be reachable, just used to determine interface
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            # Fallback to loopback if detection fails
            return "127.0.0.1"
    
    def substitute_variables(self, command, variables):
        """Replace placeholders in commands with actual values from previous results."""
        # Add local IP to variables if not already present
        if 'your_ip' not in variables and 'local_ip' not in variables:
            variables['your_ip'] = self.get_local_ip()
            variables['local_ip'] = variables['your_ip']
        
        # Replace direct placeholders like <target_ip>
        for var_name, var_value in variables.items():
            if isinstance(var_value, list):
                if var_value:  # If list is not empty
                    command = command.replace(f"<{var_name}>", " ".join(var_value))
            else:
                command = command.replace(f"<{var_name}>", str(var_value))
        
        return command
    
    def fix_failed_command(self, command, stderr, variables):
        """Attempt to fix a failed command based on error message."""
        fixed_command = command
        suggestion = None
        
        # Common error patterns and fixes
        if "No such file" in stderr or "not found" in stderr:
            # Check for unresolved variables
            placeholders = re.findall(r'<(\w+)>', command)
            if placeholders:
                suggestion = f"Command failed because it contains unresolved placeholders: {', '.join(placeholders)}"
                # Try to substitute with any variables we have
                for placeholder in placeholders:
                    if placeholder in variables:
                        fixed_command = fixed_command.replace(f"<{placeholder}>", str(variables[placeholder]))
                    elif placeholder == "your_ip" or placeholder == "local_ip":
                        # Get local IP address
                        local_ip = self.get_local_ip()
                        variables[placeholder] = local_ip
                        fixed_command = fixed_command.replace(f"<{placeholder}>", local_ip)
                    else:
                        # Ask user for input for this variable
                        if RICH_AVAILABLE:
                            user_value = Prompt.ask(f"[bold yellow]Enter value for[/] [bold cyan]<{placeholder}>[/]")
                        else:
                            user_value = input(f"Enter value for <{placeholder}>: ")
                        variables[placeholder] = user_value
                        fixed_command = fixed_command.replace(f"<{placeholder}>", user_value)
        
        elif "Failed to resolve" in stderr:
            # Target resolution issue
            if RICH_AVAILABLE:
                user_ip = Prompt.ask("[bold yellow]Enter a valid IP address or hostname to scan[/]")
            else:
                user_ip = input("Enter a valid IP address or hostname to scan: ")
            variables['target_ip'] = user_ip
            fixed_command = command.replace("<target_ip>", user_ip).replace("<target_ip_range>", user_ip)
            if "/24" not in fixed_command and "scan" in fixed_command:
                fixed_command = fixed_command.replace(user_ip, f"{user_ip}/24")
                variables['target_ip_range'] = f"{user_ip}/24"
        
        elif "host seems down" in stderr.lower() or "no route to host" in stderr.lower():
            # Host is down or unreachable - add -Pn to nmap or try different approach
            if "nmap" in command and "-Pn" not in command:
                fixed_command = command.replace("nmap ", "nmap -Pn ")
                suggestion = "Host appears to be down or blocking ping. Adding -Pn to bypass ping discovery."
            else:
                # For non-nmap commands, inform user the host is unreachable
                suggestion = "The target host appears to be unreachable. Check connectivity or try a different target."
                if RICH_AVAILABLE:
                    user_ip = Prompt.ask("[bold yellow]Enter an alternative target IP address[/]", default=re.findall(ip_pattern, command)[0] if re.findall(ip_pattern, command) else "")
                else:
                    user_ip = input("Enter an alternative target IP address: ")
                
                if user_ip:
                    # Replace IP in command
                    old_ip = re.findall(ip_pattern, command)
                    if old_ip:
                        fixed_command = command.replace(old_ip[0], user_ip)
                        variables['target_ip'] = user_ip
        
        elif "permission denied" in stderr.lower() or "privileges" in stderr.lower():
            # Permission issue
            fixed_command = "sudo " + command
            suggestion = "This command requires elevated privileges. Added sudo."
        
        elif "Syntax error" in stderr:
            # Syntax error - try to fix basic issues
            for placeholder in re.findall(r'<(\w+)>', command):
                if placeholder == "your_ip" or placeholder == "local_ip":
                    # Get local IP address
                    local_ip = self.get_local_ip()
                    variables[placeholder] = local_ip
                    fixed_command = fixed_command.replace(f"<{placeholder}>", local_ip)
                else:
                    if RICH_AVAILABLE:
                        user_value = Prompt.ask(f"[bold yellow]Enter value for[/] [bold cyan]<{placeholder}>[/]")
                    else:
                        user_value = input(f"Enter value for <{placeholder}>: ")
                    variables[placeholder] = user_value
                    fixed_command = fixed_command.replace(f"<{placeholder}>", user_value)
        
        return fixed_command, suggestion, variables
    
    def execute_command(self, command, variables=None):
        """Execute a shell command and return the output."""
        if variables is None:
            variables = {}
            
        # Apply variable substitution
        if variables:
            original_command = command
            command = self.substitute_variables(command, variables)
            if command != original_command:
                if RICH_AVAILABLE:
                    console.print(f"[dim]Substituted command:[/] {command}")
        
        try:
            logger.info(f"Executing command: {command}")
            
            # Log the command
            if LOG_COMMANDS:
                with open(self.log_file, 'a') as f:
                    f.write(f"\n[COMMAND] {datetime.now()}: {command}\n")
            
            # Show fancy indicator if rich is available
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold yellow]Executing...[/]"),
                    BarColumn(),
                    TimeElapsedColumn(),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("Executing...", total=100)
                    
                    # Execute the command
                    process = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Simulate progress while command is running
                    progress_value = 0
                    while process.poll() is None and progress_value < 90:
                        progress_value += 1
                        progress.update(task, completed=progress_value)
                        time.sleep(0.1)
                    
                    # Complete progress bar
                    progress.update(task, completed=100)
                    stdout, stderr = process.communicate()
            else:
                # Execute the command
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate()
            
            # Log the output
            if LOG_COMMANDS:
                with open(self.log_file, 'a') as f:
                    f.write(f"[STDOUT]\n{stdout}\n")
                    if stderr:
                        f.write(f"[STDERR]\n{stderr}\n")
            
            # Extract variables from command output if command was successful
            if process.returncode == 0:
                new_variables = self.extract_variables(stdout)
                # Merge with existing variables, preserving existing ones if there's overlap
                for key, value in new_variables.items():
                    if key not in variables:
                        variables[key] = value
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "command": command,
                "variables": variables
            }
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e),
                "command": command,
                "variables": variables
            }
    
    def display_plan(self, plan):
        """Display the action plan with fancy formatting."""
        if RICH_AVAILABLE:
            steps_text = "\n".join(f"• {step}" for step in plan)
            console.print(Panel(
                steps_text,
                title="[bold]Action Plan[/]",
                border_style=self.theme['border_style'],
                padding=(1, 2)
            ))
        else:
            print("\n\033[1;34m[*] Plan:\033[0m")
            for step in plan:
                print(f"  - {step}")
    
    def display_commands(self, commands, explanations):
        """Display proposed commands with fancy formatting."""
        if RICH_AVAILABLE:
            table = Table(
                show_header=True,
                header_style=f"bold {self.theme['primary']}", 
                border_style=self.theme['border_style'],
                padding=(0, 1)
            )
            table.add_column("#", style="dim", width=3)
            table.add_column("Command", style="bold yellow")
            table.add_column("Explanation")
            
            for i, (cmd, explanation) in enumerate(zip(commands, explanations), 1):
                table.add_row(str(i), Syntax(cmd, "bash", theme=self.theme['code_theme']), explanation)
            
            console.print(Panel(
                table,
                title="[bold]Proposed Commands[/]",
                border_style=self.theme['border_style'],
                padding=(1, 1)
            ))
        else:
            print("\n\033[1;34m[*] Proposed commands:\033[0m")
            for i, (cmd, explanation) in enumerate(zip(commands, explanations), 1):
                print(f"\n  \033[1;33m[{i}] Command:\033[0m {cmd}")
                print(f"      \033[1;32mExplanation:\033[0m {explanation}")
    
    def display_result(self, result, command_index, total_commands):
        """Display command execution result with fancy formatting."""
        if RICH_AVAILABLE:
            # Create a panel for the output
            panel_title = f"[bold]Command {command_index}/{total_commands} Result[/]"
            panel_style = self.theme['success'] if result["exit_code"] == 0 else self.theme['error']
            
            # Format the output
            content = []
            if result["exit_code"] == 0:
                content.append(f"[bold green]✓ Command completed successfully[/]")
            else:
                content.append(f"[bold red]✗ Command failed with exit code {result['exit_code']}[/]")
            
            # Add command output
            if result["stdout"].strip():
                content.append("\n[bold]Output:[/]")
                # Limit output length to prevent huge displays
                stdout = result["stdout"].strip()
                if len(stdout) > 2000:  # Limit to 2000 chars
                    stdout = stdout[:1997] + "..."
                content.append(stdout)
            
            # Add error output if any
            if result["stderr"].strip():
                content.append("\n[bold red]Error output:[/]")
                stderr = result["stderr"].strip()
                if len(stderr) > 500:  # Limit to 500 chars for errors
                    stderr = stderr[:497] + "..."
                content.append(stderr)
                
            # Display the panel
            console.print(Panel(
                "\n".join(content),
                title=panel_title,
                border_style=panel_style,
                padding=(1, 2),
                expand=False
            ))
        else:
            print(f"\n\033[1;33m[{command_index}/{total_commands}] Executing:\033[0m {cmd}")
            
            # Print result
            if result["exit_code"] == 0:
                print("\033[1;32m[+] Command completed successfully\033[0m")
            else:
                print(f"\033[1;31m[!] Command failed with exit code {result['exit_code']}\033[0m")
            
            print("\033[1;36m[*] Output:\033[0m")
            print(result["stdout"])
            
            if result["stderr"]:
                print("\033[1;31m[*] Error output:\033[0m")
                print(result["stderr"])
    
    def generate_next_command(self, request, previous_command, previous_output, variables):
        """Generate the next command based on the output of the previous command."""
        # Create a context that includes the original request and previous results
        context = f"""
As PAW (Prompt Assisted Workflow), I need you to generate the NEXT command in a cybersecurity workflow.

REQUEST: {request}

PREVIOUS COMMAND: {previous_command}

COMMAND OUTPUT:
{previous_output}

Available variables detected:
{json.dumps(variables, indent=2)}

IMPORTANT NOTES:
- If the previous command indicates the host is down or unreachable, suggest a command to troubleshoot connectivity or try an alternative approach.
- If the previous command was nmap and showed the host is down, suggest adding -Pn flag.
- Do not use <your_ip> placeholders in commands, directly use the detected local IP.
- Always adapt based on previous output and errors.

Based on the previous command and its output, generate the next most logical command to continue this workflow.
Respond with a JSON object containing:
{{
  "command": "the next command to run",
  "explanation": "explanation of what this command does and why it's appropriate next"
}}

The command should directly use the values from the previous output when appropriate, not placeholders.
"""
        
        response = self.generate_llm_response(context)
        
        if "error" in response:
            return None, None
        
        # Extract the next command and explanation
        next_command = response.get("command", "")
        if isinstance(next_command, list) and next_command:
            next_command = next_command[0]
        
        explanation = response.get("explanation", "")
        if isinstance(explanation, list) and explanation:
            explanation = explanation[0]

        # Substitute any remaining placeholders
        next_command = self.substitute_variables(next_command, variables)
            
        return next_command, explanation
    
    def interactive_command_selection(self, commands, explanations):
        """Allow user to selectively run or edit commands."""
        selected_commands = []
        
        if RICH_AVAILABLE:
            console.print("\n[bold cyan]Would you like to run these commands?[/]")
            
            options = [
                "Run all commands",
                "Select commands to run",
                "Edit commands before running", 
                "Run commands one at a time (progressive mode)",
                "Cancel execution"
            ]
            
            choice = Prompt.ask(
                "Choose an option",
                choices=["1", "2", "3", "4", "5"],
                default="1"
            )
            
            if choice == "1":
                self.adaptive_mode = False
                return commands, self.adaptive_mode  # Run all commands
            elif choice == "2":
                # Select which commands to run
                self.adaptive_mode = False
                for i, (cmd, explanation) in enumerate(zip(commands, explanations), 1):
                    console.print(f"\n[bold]{i}.[/] {cmd}")
                    console.print(f"   [dim]{explanation}[/]")
                    run_cmd = Confirm.ask(f"Run this command?", default=True)
                    if run_cmd:
                        selected_commands.append(cmd)
                return selected_commands, self.adaptive_mode
            elif choice == "3":
                # Edit commands before running
                self.adaptive_mode = False
                for i, (cmd, explanation) in enumerate(zip(commands, explanations), 1):
                    console.print(f"\n[bold]{i}.[/] [yellow]{cmd}[/]")
                    console.print(f"   [dim]{explanation}[/]")
                    edit = Confirm.ask(f"Edit this command?", default=False)
                    if edit:
                        edited_cmd = Prompt.ask("Enter edited command", default=cmd)
                        selected_commands.append(edited_cmd)
                    else:
                        selected_commands.append(cmd)
                return selected_commands, self.adaptive_mode
            elif choice == "4":
                # Run adaptively, one at a time
                self.adaptive_mode = True
                # Only return the first command
                if commands:
                    return [commands[0]], self.adaptive_mode
                return [], self.adaptive_mode
            else:
                return [], False  # Cancel execution
        else:
            console.print("\n[*] Options:")
            console.print("  1. Run all commands")
            console.print("  2. Run commands one at a time (progressive mode)")
            console.print("  3. Cancel execution")
            
            choice = input("\033[1;35m[?] Choose an option (1/2/3): \033[0m")
            
            if choice == "1":
                self.adaptive_mode = False
                return commands, self.adaptive_mode  # Run all commands
            elif choice == "2":
                self.adaptive_mode = True
                # Only return the first command
                if commands:
                    return [commands[0]], self.adaptive_mode
                return [], self.adaptive_mode
            else:
                return [], False  # Cancel execution
    
    def retry_failed_command(self, result, variables):
        """Handle failed command with retry options."""
        if RICH_AVAILABLE:
            console.print(Panel(
                f"[bold red]Command failed:[/] {result['command']}\n\n[bold]Error:[/] {result['stderr']}",
                title="[bold red]Error[/]",
                border_style="red"
            ))
            
            fixed_command, suggestion, updated_vars = self.fix_failed_command(result['command'], result['stderr'], variables)
            
            if suggestion:
                console.print(f"[bold yellow]Suggestion:[/] {suggestion}")
            
            if fixed_command != result['command']:
                console.print(f"[bold green]Suggested fix:[/] {fixed_command}")
                
                options = [
                    "Use suggested fix",
                    "Edit command manually",
                    "Skip this command",
                    "Abort execution"
                ]
                
                choice = Prompt.ask(
                    "How would you like to proceed?",
                    choices=["1", "2", "3", "4"],
                    default="1"
                )
                
                if choice == "1":
                    return self.execute_command(fixed_command, updated_vars), True
                elif choice == "2":
                    manual_cmd = Prompt.ask("Enter fixed command", default=fixed_command)
                    return self.execute_command(manual_cmd, updated_vars), True
                elif choice == "3":
                    return result, False  # Skip but continue workflow
                else:
                    return result, None  # Abort entirely
            else:
                # Couldn't auto-fix, ask user
                options = [
                    "Edit command manually",
                    "Skip this command",
                    "Abort execution"
                ]
                
                choice = Prompt.ask(
                    "How would you like to proceed?",
                    choices=["1", "2", "3"],
                    default="1"
                )
                
                if choice == "1":
                    manual_cmd = Prompt.ask("Enter fixed command", default=result['command'])
                    return self.execute_command(manual_cmd, variables), True
                elif choice == "2":
                    return result, False
                else:
                    return result, None
        else:
            # Basic terminal UI version
            print(f"\033[1;31m[!] Command failed: {result['command']}\033[0m")
            print(f"\033[1;31m[!] Error: {result['stderr']}\033[0m")
            
            fixed_command, suggestion, updated_vars = self.fix_failed_command(result['command'], result['stderr'], variables)
            
            if suggestion:
                print(f"\033[1;33m[*] Suggestion: {suggestion}\033[0m")
            
            if fixed_command != result['command']:
                print(f"\033[1;32m[+] Suggested fix: {fixed_command}\033[0m")
                
                choice = input("\033[1;35m[?] Use suggested fix (y), edit manually (e), skip (s), or abort (a)? \033[0m").lower()
                
                if choice == 'y':
                    return self.execute_command(fixed_command, updated_vars), True
                elif choice == 'e':
                    manual_cmd = input(f"\033[1;35m[?] Enter fixed command: \033[0m")
                    return self.execute_command(manual_cmd, updated_vars), True
                elif choice == 's':
                    return result, False
                else:
                    return result, None
            else:
                choice = input("\033[1;35m[?] Edit manually (e), skip (s), or abort (a)? \033[0m").lower()
                
                if choice == 'e':
                    manual_cmd = input(f"\033[1;35m[?] Enter fixed command: \033[0m")
                    return self.execute_command(manual_cmd, variables), True
                elif choice == 's':
                    return result, False
                else:
                    return result, None
    
    def process_request(self, request, adaptive_override=None):
        """Process a natural language request."""
        # Override adaptive mode if specified
        if adaptive_override is not None:
            self.adaptive_mode = adaptive_override
            
        # Clean up the request
        request = request.replace('\r', '').strip()
        
        # Generate LLM response
        context = f"""
As PAW (Prompt Assisted Workflow), analyze this cybersecurity request and provide a plan of action:

REQUEST: {request}

Consider the following Kali Linux tools when appropriate:
- Network scanning: nmap, masscan, netdiscover
- Web scanning: nikto, dirb, gobuster, wpscan
- Vulnerability scanning: openvas, nessus, lynis
- Exploitation: metasploit, sqlmap, hydra
- Reconnaissance: whois, theHarvester, recon-ng, maltego
- Password attacks: hashcat, john, crunch
- Wireless: aircrack-ng, wifite, kismet
- Forensics: volatility, autopsy, foremost

Design your commands to work sequentially as a workflow, where later commands build on the results of earlier ones.
For commands that need input from previous commands, use placeholders like <target_ip> or <discovered_hosts>.
Provide the specific commands that would accomplish this task, explaining what each command does.
"""
        
        response = self.generate_llm_response(context + request)
        
        if "error" in response:
            if RICH_AVAILABLE:
                console.print(f"[bold red]Error:[/] {response['error']}")
            else:
                print(f"\033[1;31m[!] Error: {response['error']}\033[0m")
            return
        
        # Display the plan
        plan = response.get("plan", [])
        self.display_plan(plan)
        
        # Get commands and explanations
        commands = response.get("commands", [])
        explanations = response.get("explanation", [""] * len(commands))
        
        if not commands:
            if RICH_AVAILABLE:
                console.print("[bold yellow]No commands were generated for this request.[/]")
            else:
                print("\033[1;33m[!] No commands were generated for this request.\033[0m")
            return
        
        # Display proposed commands
        if EXPLAIN_COMMANDS:
            self.display_commands(commands, explanations)
            
            # Interactive command selection
            commands, adaptive_mode = self.interactive_command_selection(commands, explanations)
            
            if not commands:
                if RICH_AVAILABLE:
                    console.print("[bold red]Execution cancelled[/]")
                else:
                    print("\n\033[1;31m[!] Execution cancelled\033[0m")
                return
        
        # Execute commands
        results = []
        variables = {}  # Store variables for command chaining
        
        if RICH_AVAILABLE:
            mode_str = "[bold cyan]Progressive Mode[/]" if self.adaptive_mode else "[bold]Sequential Mode[/]"
            console.print(Panel(f"[bold]Executing Commands[/] in {mode_str}", 
                                border_style=self.theme['border_style']))
        else:
            mode_str = "Progressive Mode" if self.adaptive_mode else "Sequential Mode"
            print(f"\n\033[1;34m[*] Executing commands in {mode_str}:\033[0m")
        
        command_index = 0
        while command_index < len(commands):
            cmd = commands[command_index]
            command_index += 1  # Increment for next command
            
            if RICH_AVAILABLE:
                if self.adaptive_mode:
                    console.print(Panel(f"[bold yellow]Command {command_index}:[/] {cmd}", 
                                       title="[bold cyan]Current Command[/]",
                                       border_style=self.theme['border_style']))
                else:
                    console.print(f"[bold yellow]Command {command_index}/{len(commands)}:[/] {cmd}")
            else:
                if self.adaptive_mode:
                    print(f"\n\033[1;33m[{command_index}] Executing:\033[0m {cmd}")
                else:
                    print(f"\n\033[1;33m[{command_index}/{len(commands)}] Executing:\033[0m {cmd}")
            
            # Execute with current variables from previous commands
            result = self.execute_command(cmd, variables)
            
            # Update variables with new ones from this command
            variables = result["variables"]
            
            # Handle command failures with retry
            if result["exit_code"] != 0:
                retry_result, should_continue = self.retry_failed_command(result, variables)
                
                if should_continue is None:  # User chose to abort
                    if RICH_AVAILABLE:
                        console.print("[bold red]Execution aborted by user[/]")
                    else:
                        print("\n\033[1;31m[!] Execution aborted by user\033[0m")
                    return
                
                if should_continue:  # User chose to retry with fix
                    # Replace the failed result with retry result
                    result = retry_result
                    # Update variables with any new ones from retry
                    variables = result["variables"]
            
            # Store the result for summary
            results.append(result)
            
            # Display result
            self.display_result(result, command_index, len(commands) if not self.adaptive_mode else "?")
            
            # In adaptive mode, generate the next command based on the current result
            if self.adaptive_mode and result["exit_code"] == 0:
                # Format previous output for prompt
                prev_output = f"STDOUT:\n{result['stdout']}\n\nSTDERR:\n{result['stderr']}"
                
                # Ask if user wants to continue
                if RICH_AVAILABLE:
                    console.print("\n[bold cyan]Command completed successfully[/]")
                    continue_workflow = Confirm.ask("Generate next command based on this output?", default=True)
                else:
                    print("\n\033[1;36m[*] Command completed successfully\033[0m")
                    continue_workflow = input("\n\033[1;35m[?] Generate next command based on this output? (y/n): \033[0m").lower() == 'y'
                
                if continue_workflow:
                    if RICH_AVAILABLE:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[bold cyan]Generating next command...[/]"),
                            console=console,
                            transient=True
                        ) as progress:
                            task = progress.add_task("Thinking...", total=None)
                            next_cmd, next_explanation = self.generate_next_command(
                                request, result["command"], prev_output, variables
                            )
                    else:
                        print("\n\033[1;34m[*] Generating next command...\033[0m")
                        next_cmd, next_explanation = self.generate_next_command(
                            request, result["command"], prev_output, variables
                        )
                    
                    if next_cmd:
                        # Display the suggested next command
                        if RICH_AVAILABLE:
                            console.print(Panel(
                                f"[bold]Suggested next command:[/]\n{next_cmd}\n\n[bold]Explanation:[/]\n{next_explanation}",
                                title="[bold cyan]Next Command[/]",
                                border_style=self.theme['border_style']
                            ))
                            
                            # Ask user if they want to use this command, edit it, or finish
                            options = [
                                "Use this command",
                                "Edit this command",
                                "End workflow"
                            ]
                            
                            next_choice = Prompt.ask(
                                "How would you like to proceed?",
                                choices=["1", "2", "3"],
                                default="1"
                            )
                            
                            if next_choice == "1":
                                # Add the command to our execution list
                                commands.append(next_cmd)
                                explanations.append(next_explanation)
                            elif next_choice == "2":
                                # Let user edit the command
                                edited_cmd = Prompt.ask("Enter edited command", default=next_cmd)
                                commands.append(edited_cmd)
                                explanations.append(next_explanation)
                            else:
                                # End the workflow
                                break
                        else:
                            print(f"\n\033[1;36m[*] Suggested next command:\033[0m {next_cmd}")
                            print(f"\033[1;32m[*] Explanation:\033[0m {next_explanation}")
                            
                            next_choice = input("\n\033[1;35m[?] Use this command (u), edit it (e), or end workflow (q)? \033[0m").lower()
                            
                            if next_choice == 'u':
                                # Add the command to our execution list
                                commands.append(next_cmd)
                                explanations.append(next_explanation)
                            elif next_choice == 'e':
                                # Let user edit the command
                                edited_cmd = input(f"\n\033[1;35m[?] Enter edited command: \033[0m")
                                commands.append(edited_cmd)
                                explanations.append(next_explanation)
                            else:
                                # End the workflow
                                break
                    else:
                        if RICH_AVAILABLE:
                            console.print("[bold yellow]Could not generate a next command.[/]")
                            if Confirm.ask("End workflow?", default=True):
                                break
                        else:
                            print("\033[1;33m[!] Could not generate a next command.\033[0m")
                            if input("\n\033[1;35m[?] End workflow? (y/n): \033[0m").lower() == 'y':
                                break
                else:
                    # User chose not to continue
                    break
        
        # Final summary
        if RICH_AVAILABLE:
            console.print(Panel("[bold green]Workflow completed[/]", 
                               border_style=self.theme['success']))
        else:
            print("\n\033[1;32m[+] Workflow completed\033[0m")
        
        # Generate summary if there are multiple commands
        if len(results) > 1:
            summary_prompt = f"""
Request: {request}

Commands executed:
{chr(10).join([r["command"] for r in results])}

Results overview:
{chr(10).join([f"Command {i+1}: Exit code {r['exit_code']}" for i, r in enumerate(results)])}

Please provide a brief summary of the results and what was accomplished.
"""
            summary = self.generate_llm_response(summary_prompt)
            
            if RICH_AVAILABLE:
                console.print(Panel(
                    "\n".join([f"• {point}" for point in summary.get("plan", [])]),
                    title="[bold]Summary[/]",
                    border_style=self.theme['border_style'],
                    padding=(1, 2)
                ))
            else:
                print("\n\033[1;34m[*] Summary:\033[0m")
                if "error" in summary:
                    print(f"  Error generating summary: {summary['error']}")
                else:
                    for point in summary.get("plan", []):
                        print(f"  - {point}")

def main():
    parser = argparse.ArgumentParser(description="PAW - Prompt Assisted Workflow for Kali Linux")
    parser.add_argument("request", nargs="?", help="Natural language request")
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--timeout", type=float, help="Set LLM request timeout in seconds")
    parser.add_argument("--theme", choices=list(THEMES.keys()), help="Set UI theme")
    
    # Create a mutually exclusive group for progressive mode options
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--adaptive", action="store_true", help="Generate each command based on previous results (same as --prog)")
    mode_group.add_argument("--prog", action="store_true", help="Progressive mode: generate commands one at a time based on previous output")
    
    args = parser.parse_args()
    
    if args.version:
        if RICH_AVAILABLE:
            console.print("[bold cyan]PAW - Prompt Assisted Workflow v1.0[/]")
        else:
            print("PAW - Prompt Assisted Workflow v1.0")
        sys.exit(0)
    
    # Override timeout if specified
    global LLM_TIMEOUT
    if args.timeout:
        LLM_TIMEOUT = args.timeout
        if RICH_AVAILABLE:
            console.print(f"[bold blue]LLM timeout set to {LLM_TIMEOUT} seconds[/]")
        else:
            print(f"\033[1;34m[*] LLM timeout set to {LLM_TIMEOUT} seconds\033[0m")
    
    # Override theme if specified
    global THEME
    if args.theme and args.theme in THEMES:
        THEME = args.theme
    
    # Display ASCII art
    display_ascii_art()
    
    # Show fancy header if rich is available
    if RICH_AVAILABLE:
        show_fancy_header(
            "Prompt Assisted Workflow", 
            "Your AI-powered Kali Linux assistant"
        )
    
    paw = PAW()
    
    if args.request:
        # Process the request with adaptive mode if specified
        # --prog is an alternative to --adaptive
        adaptive_mode = args.adaptive or args.prog
        paw.process_request(args.request, adaptive_mode)
    else:
        if RICH_AVAILABLE:
            console.print("[bold cyan]Welcome to PAW - Prompt Assisted Workflow[/]")
            console.print("[cyan]Type 'exit' or 'quit' to exit[/]")
        else:
            print("\033[1;34m[*] Welcome to PAW - Prompt Assisted Workflow\033[0m")
            print("\033[1;34m[*] Type 'exit' or 'quit' to exit\033[0m")
        
        while True:
            try:
                if RICH_AVAILABLE:
                    request = Prompt.ask("\n[bold magenta]PAW[/]")
                else:
                    request = input("\n\033[1;35mPAW> \033[0m")
                
                # Strip out any carriage returns and whitespace
                request = request.replace('\r', '').replace('^M', '').strip()
                
                if request.lower() in ["exit", "quit"]:
                    if RICH_AVAILABLE:
                        console.print("[bold cyan]Goodbye![/]")
                    else:
                        print("\033[1;34m[*] Goodbye!\033[0m")
                    break
                
                if request.strip():
                    paw.process_request(request)
                    
            except KeyboardInterrupt:
                if RICH_AVAILABLE:
                    console.print("\n[bold cyan]Execution interrupted[/]")
                else:
                    print("\n\033[1;34m[*] Execution interrupted[/]")
                continue
                
            except Exception as e:
                if RICH_AVAILABLE:
                    console.print(f"\n[bold red]Error: {str(e)}[/]")
                else:
                    print(f"\n\033[1;31m[!] Error: {str(e)}\033[0m")
                # Clean up any remaining ^M characters from stdout/stderr
                if hasattr(e, 'stdout') and e.stdout:
                    e.stdout = e.stdout.replace('\r', '')
                if hasattr(e, 'stderr') and e.stderr:
                    e.stderr = e.stderr.replace('\r', '')
                continue

if __name__ == "__main__":
    main() 