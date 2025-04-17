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
# Try local lib first, then system path
current_dir = os.path.dirname(os.path.abspath(__file__))
local_lib_path = os.path.join(current_dir, 'lib')
if os.path.exists(local_lib_path):
    sys.path.append(local_lib_path)
else:
    sys.path.append('/usr/local/share/paw/lib')

try:
    from ascii_art import display_ascii_art
    from tools_registry import get_tools_registry
except ImportError:
    # Fall back to trying current directory imports
    try:
        sys.path.append('.')
        from ascii_art import display_ascii_art
        from tools_registry import get_tools_registry
    except ImportError:
        print("Error: Could not import required modules. Please make sure you're running from the correct directory.")
        sys.exit(1)

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
# Check for environment variable for config path first, otherwise use default
CONFIG_PATH = os.environ.get("PAW_CONFIG", "/etc/paw/config.ini")
config = configparser.ConfigParser()

# Check if the specified config file exists
if os.path.exists(CONFIG_PATH):
    config.read(CONFIG_PATH)
else:
    # Try a local config file in the current directory if the environment variable isn't set
    # or the specified file doesn't exist
    if not os.environ.get("PAW_CONFIG") and os.path.exists("./paw-local-config.ini"):
        CONFIG_PATH = "./paw-local-config.ini"
        config.read(CONFIG_PATH)
    else:
        logger.error(f"Configuration file not found: {CONFIG_PATH}")
        sys.exit(1)

MODEL = config['DEFAULT'].get('model', 'qwen2.5-coder:7b')
OLLAMA_HOST = config['DEFAULT'].get('ollama_host', 'http://localhost:11434')
EXPLAIN_COMMANDS = config['DEFAULT'].getboolean('explain_commands', True)
LOG_COMMANDS = config['DEFAULT'].getboolean('log_commands', True)
LOG_DIRECTORY = config['DEFAULT'].get('log_directory', '/var/log/paw')
# Configurable timeout (default: 600 seconds)
LLM_TIMEOUT = float(config['DEFAULT'].get('llm_timeout', '600.0'))
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
    
    def get_network_interfaces(self):
        """Get a list of all available network interfaces on the system."""
        interfaces = []
        try:
            # Try to use the 'ip' command first (more modern)
            process = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
            if process.returncode == 0:
                # Parse output to extract interface names
                output = process.stdout
                for line in output.split('\n'):
                    if ': ' in line and not line.startswith(' '):
                        interface = line.split(': ')[1].split(':')[0]
                        interfaces.append(interface)
            else:
                # Fallback to ifconfig
                process = subprocess.run(['ifconfig', '-a'], capture_output=True, text=True)
                if process.returncode == 0:
                    output = process.stdout
                    for line in output.split('\n'):
                        if line and not line.startswith(' ') and not line.startswith('\t'):
                            interface = line.split(':')[0].split()[0]
                            if interface:
                                interfaces.append(interface)
        except Exception as e:
            logger.error(f"Error detecting network interfaces: {e}")
            # Add common interface names as fallback
            interfaces = ['eth0', 'wlan0', 'enp0s3', 'lo', 'wlp0s20f3']
        
        # Remove loopback from being the primary interface
        if 'lo' in interfaces:
            interfaces.remove('lo')
            interfaces.append('lo')  # Add it back at the end
            
        return interfaces
    
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
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        
        # Handle missing interface error
        if "cannot open interface" in stderr or "No such device" in stderr:
            # This is likely an issue with a network interface placeholder
            interfaces = self.get_network_interfaces()
            suggestion = f"Available network interfaces: {', '.join(interfaces)}"
            
            if interfaces:
                # Try to replace the interface in the command
                for placeholder in ["<interface>", "eth0", "wlan0"]:
                    if placeholder in command:
                        fixed_command = command.replace(placeholder, interfaces[0])
                        variables['interface'] = interfaces[0]
                        return fixed_command, suggestion, variables
                
                # If no placeholder was found but we have interfaces, prompt the user
                if RICH_AVAILABLE:
                    selected_interface = Prompt.ask(
                        "[bold yellow]Enter interface name[/]", 
                        choices=interfaces, 
                        default=interfaces[0]
                    )
                else:
                    print(f"\033[1;33m[*] Available interfaces: {', '.join(interfaces)}\033[0m")
                    selected_interface = input(f"Enter interface name [{interfaces[0]}]: ").strip()
                    if not selected_interface:
                        selected_interface = interfaces[0]
                
                variables['interface'] = selected_interface
                
                # Try to find the interface name in the command
                interface_pattern = r'\b([a-zA-Z0-9]+)\b'
                # Replace the first occurrence of what looks like an interface name
                interface_match = re.search(interface_pattern, command)
                if interface_match:
                    fixed_command = command.replace(interface_match.group(0), selected_interface)
                return fixed_command, suggestion, variables
        
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
            
            # Define default command timeout (3 minutes, or configurable)
            command_timeout = float(config['DEFAULT'].get('command_timeout', '600.0'))
            
            # Show fancy indicator if rich is available
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold yellow]Executing...[/]"),
                    TimeElapsedColumn(),
                    console=console,
                    transient=False
                ) as progress:
                    task = progress.add_task("Executing...", total=None)
                    
                    # Execute the command
                    process = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Wait for command with timeout
                    start_time = time.time()
                    stdout_data = []
                    stderr_data = []
                    
                    # Set up non-blocking I/O
                    import fcntl
                    import os
                    import select
                    
                    # Make stdout and stderr non-blocking
                    for f in [process.stdout, process.stderr]:
                        flags = fcntl.fcntl(f.fileno(), fcntl.F_GETFL)
                        fcntl.fcntl(f.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)
                    
                    # Poll for results or timeout
                    while process.poll() is None:
                        # Check if we need to allow user to abort
                        elapsed = time.time() - start_time
                        if elapsed > 10:  # After 10 seconds, show abort option
                            progress.stop()
                            if Confirm.ask(f"Command running for {int(elapsed)}s. Abort?", default=False):
                                process.kill()
                                console.print("[bold red]Command aborted by user[/]")
                                return {
                                    "exit_code": -1,
                                    "stdout": "".join(stdout_data),
                                    "stderr": "Command aborted by user after timeout",
                                    "command": command,
                                    "variables": variables
                                }
                            # Resume progress and reset timer to wait another 10s before asking again
                            progress.start()
                            start_time = time.time()
                        
                        # Check for output
                        readable, _, _ = select.select([process.stdout, process.stderr], [], [], 0.5)
                        for stream in readable:
                            line = stream.readline()
                            if line:
                                if stream == process.stdout:
                                    stdout_data.append(line)
                                else:
                                    stderr_data.append(line)
                        
                        # Check for timeout
                        if time.time() - start_time > command_timeout:
                            process.kill()
                            console.print(f"[bold red]Command timed out after {command_timeout} seconds[/]")
                            return {
                                "exit_code": -1,
                                "stdout": "".join(stdout_data),
                                "stderr": f"Command timed out after {command_timeout} seconds",
                                "command": command,
                                "variables": variables
                            }
                    
                    # Get any remaining output
                    stdout, stderr = process.communicate()
                    stdout_data.append(stdout)
                    stderr_data.append(stderr)
                    
                    # Combine output
                    stdout = "".join(stdout_data)
                    stderr = "".join(stderr_data)
            else:
                # Execute the command with timeout for non-rich UI
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                print(f"\033[1;33m[*] Executing (press Ctrl+C to abort)...\033[0m")
                
                try:
                    stdout, stderr = process.communicate(timeout=command_timeout)
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"\033[1;31m[!] Command timed out after {command_timeout} seconds\033[0m")
                    return {
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": f"Command timed out after {command_timeout} seconds",
                        "command": command,
                        "variables": variables
                    }
            
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
            
        except KeyboardInterrupt:
            # Handle keyboard interrupt
            if RICH_AVAILABLE:
                console.print("[bold red]Command interrupted by user[/]")
            else:
                print("\n\033[1;31m[!] Command interrupted by user\033[0m")
                
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Command was interrupted by user",
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
    
    def display_single_command(self, command, explanation, command_index, total_commands):
        """Display a single command with its explanation and ask for y/n confirmation."""
        if RICH_AVAILABLE:
            table = Table(
                show_header=True,
                header_style=f"bold {self.theme['primary']}", 
                border_style=self.theme['border_style'],
                padding=(0, 1)
            )
            table.add_column("Command", style="bold yellow")
            table.add_column("Explanation")
            
            table.add_row(Syntax(command, "bash", theme=self.theme['code_theme']), explanation)
            
            console.print(Panel(
                table,
                title=f"[bold]Command {command_index}/{total_commands}[/]",
                border_style=self.theme['border_style'],
                padding=(1, 1)
            ))
            
            # Use a single prompt and return directly
            return Confirm.ask("Execute this command?", default=True)
        else:
            print(f"\n  \033[1;33m[{command_index}/{total_commands}] Command:\033[0m {command}")
            print(f"      \033[1;32mExplanation:\033[0m {explanation}")
            
            # Use a single prompt and return directly
            run_cmd = input("\033[1;35m[?] Execute this command? [y/n] (y): \033[0m").strip().lower()
            return run_cmd == "" or run_cmd == "y"
    
    def handle_failed_command(self, cmd, result, variables, command_index, total_commands):
        """Handle a failed command by trying to fix it or asking user what to do."""
        # Try to fix the command
        fixed_cmd, suggestion, updated_vars = self.fix_failed_command(cmd, result["stderr"], variables)
        
        if fixed_cmd != cmd:
            if suggestion:
                if RICH_AVAILABLE:
                    console.print(f"[bold yellow]Suggestion:[/] {suggestion}")
                else:
                    print(f"\033[1;33m[*] Suggestion:\033[0m {suggestion}")
                    
            if RICH_AVAILABLE:
                console.print(f"[bold yellow]Suggested fix:[/] {fixed_cmd}")
                retry = Confirm.ask("Try the fixed command?", default=True)
            else:
                print(f"\033[1;33m[*] Suggested fix:\033[0m {fixed_cmd}")
                retry = input("\033[1;35m[?] Try the fixed command? (y/n): \033[0m").strip().lower()
                retry = retry == "" or retry == "y"
                
            if retry:
                result = self.execute_command(fixed_cmd, updated_vars)
                self.display_result(result, command_index, total_commands)
                return result, updated_vars
                
        return result, variables
    
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
                
        return result["exit_code"] == 0
    
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
        """Allow user to selectively run commands one by one with y/n confirmation."""
        selected_commands = []
        
        # Always use progressive mode with one-by-one execution
        self.adaptive_mode = True
        
        # Only return the first command if approved
        if commands and explanations:
            if self.display_single_command(commands[0], explanations[0], 1, len(commands)):
                return [commands[0]], self.adaptive_mode
        
        # If user doesn't approve the first command or there are no commands
        return [], self.adaptive_mode
    
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
                
                run_fixed = Prompt.ask("Execute this fixed command?", choices=["y", "n"], default="y")
                if run_fixed == "y":
                    return self.execute_command(fixed_command, updated_vars), True
                else:
                    return result, False
            else:
                # No automated fix available
                console.print("[bold yellow]No automated fix available for this error.[/]")
                skip_cmd = Prompt.ask("Skip this command?", choices=["y", "n"], default="n")
                
                if skip_cmd == "y":
                    return result, False
                else:
                    return result, None  # Abort execution
        else:
            print(f"\033[1;31m[!] Command failed: {result['command']}\033[0m")
            print(f"\033[1;31m[!] Error: {result['stderr']}\033[0m")
            
            fixed_command, suggestion, updated_vars = self.fix_failed_command(result['command'], result['stderr'], variables)
            
            if suggestion:
                print(f"\033[1;33m[*] Suggestion: {suggestion}\033[0m")
            
            if fixed_command != result['command']:
                print(f"\033[1;32m[+] Suggested fix: {fixed_command}\033[0m")
                
                run_fixed = input("\033[1;35m[?] Execute this fixed command? [y/n] (y): \033[0m").strip().lower()
                if run_fixed == "" or run_fixed == "y":
                    return self.execute_command(fixed_command, updated_vars), True
                else:
                    return result, False
            else:
                # No automated fix available
                print("\033[1;33m[!] No automated fix available for this error.\033[0m")
                skip_cmd = input("\033[1;35m[?] Skip this command? [y/n] (n): \033[0m").strip().lower()
                
                if skip_cmd == "y":
                    return result, False
                else:
                    return result, None  # Abort execution
    
    def process_request(self, request, adaptive_override=None):
        """Process a natural language request."""
        # Override adaptive mode if specified
        if adaptive_override is not None:
            self.adaptive_mode = adaptive_override
        else:
            # Always use adaptive mode for the new one-by-one execution flow
            self.adaptive_mode = True
            
        # Clean up the request
        request = request.strip()
        
        # Get initial variables
        variables = {
            'local_ip': self.get_local_ip()
        }
        
        # Add network interfaces
        interfaces = self.get_network_interfaces()
        if interfaces:
            variables['network_interfaces'] = interfaces
            variables['interface'] = interfaces[0]  # Use first interface as default
        
        # Generate LLM response
        context = f"""
As PAW (Prompt Assisted Workflow), analyze this cybersecurity request and provide a plan of action:

REQUEST: {request}

Consider the following Kali Linux tools and their key options when appropriate:

1. Network scanning:
   - nmap: -sS (stealth scan), -sV (version detection), -O (OS detection), -A (aggressive), -p (port range), -Pn (skip discovery)
   - masscan: -p (ports), --rate (packets per second), --range (scan range), --banners (capture banners)
   - netdiscover: -r (range), -i (interface), -p (passive mode)

2. Web scanning:
   - nikto: -h (host), -port (port to scan), -ssl, -Tuning (scan tuning)
   - dirb: [url] [wordlist], -a (user agent), -z (delay), -o (output file)
   - gobuster: -u (url), -w (wordlist), -x (extensions), -t (threads)
   - wpscan: --url (WordPress URL), --api-token, -e (enumerate)

3. Vulnerability scanning:
   - openvas: -u (user), -p (password), -T (target)
   - nessus: similar to OpenVAS with web interface
   - lynis: audit system, --pentest (pentest mode)

4. Exploitation:
   - metasploit: use (module), set (option), exploit/run, sessions
   - sqlmap: -u (URL), --data (POST data), --dbms (database type), --dump
   - hydra: -l/-L (login), -p/-P (password), -t (tasks), service://server

5. Reconnaissance:
   - whois: [domain], -h (host)
   - theHarvester: -d (domain), -b (source), -l (limit)
   - recon-ng: use (module), set (option), run
   - maltego: GUI-based with transforms

6. Password attacks:
   - hashcat: -m (hash type), -a (attack mode), -o (output file)
   - john: --wordlist (wordlist file), --rules, --format (hash type)
   - crunch: [min] [max] [charset], -t (pattern), -o (output)

7. Wireless:
   - aircrack-ng: -w (wordlist), -b (BSSID)
   - wifite: -wpa (attack WPA), -wep (attack WEP), -wps (attack WPS)
   - kismet: -c (interface), -f (file), -s (server mode)

8. Forensics and analysis:
   - volatility: -f (file), --profile (OS profile), plugin commands
   - autopsy: GUI-based forensic platform
   - wireshark/tshark: -i (interface), -c (packet count), -r (read file)
   - tcpdump: -i (interface), -n (don't resolve), -w (write to file)

9. Specialized tools:
   - binwalk: -e (extract), -M (recursive scan)
   - steghide: embed/extract, -sf (stego file), -p (passphrase)
   - macchanger: -r (random MAC), -m (specified MAC)
   - enum4linux: -a (all enumeration), -u (user), -p (pass)
   - msfvenom: -p (payload), -f (format), -e (encoder)

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
        
        # Execute commands one by one
        variables = {}  # Store variables for command chaining
        command_index = 0
        total_commands = len(commands)
        
        # Pre-populate with network interface information before starting
        local_ip = self.get_local_ip()
        variables['your_ip'] = local_ip
        variables['local_ip'] = local_ip
        
        # Add network interfaces
        interfaces = self.get_network_interfaces()
        if interfaces:
            variables['network_interfaces'] = interfaces
            variables['interface'] = interfaces[0]  # Use first interface as default
        
        for cmd, explanation in zip(commands, explanations):
            command_index += 1
            
            # Clean up the command (remove comments and whitespace)
            cmd = cmd.split("//")[0].strip()
            
            # Substitute variables
            cmd = self.substitute_variables(cmd, variables)
            
            # Display command and get confirmation in a single step
            execute = self.display_single_command(cmd, explanation, command_index, total_commands)
            
            if not execute:
                continue
            
            # Execute command
            result = self.execute_command(cmd, variables)
            
            # Store output for potential use in next commands
            prev_output = result["stdout"] + result["stderr"]
            
            # Display result
            success = self.display_result(result, command_index, total_commands)
            
            # If command failed, try to fix it
            if not success:
                result, variables = self.handle_failed_command(cmd, result, variables, command_index, total_commands)
                prev_output = result["stdout"] + result["stderr"]
                success = (result["exit_code"] == 0)
            
            # Only continue if the command was successful
            if success:
                # Ask if user wants to continue
                if RICH_AVAILABLE:
                    console.print("\nCommand completed successfully")
                    continue_workflow = Confirm.ask("Generate next command based on this output?", default=True)
                else:
                    print("\n\033[1;36m[*] Command completed successfully\033[0m")
                    continue_workflow = input("\033[1;35m[?] Generate next command based on this output? (y/n): \033[0m").strip().lower()
                    continue_workflow = continue_workflow == "" or continue_workflow == "y"
                
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
                        commands.append(next_cmd)
                        explanations.append(next_explanation)
                        total_commands += 1
                else:
                    # User chose not to continue
                    break
        
        # Final summary
        if RICH_AVAILABLE:
            console.print(Panel("[bold green]Workflow completed[/]", 
                               border_style=self.theme['success']))
        else:
            print("\n\033[1;32m[+] Workflow completed\033[0m")

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