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
import getpass
import tempfile

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
        
        # Try to load extensive Kali tools if available
        self.kali_tools_loaded = False
        try:
            # First try to import the module
            sys.path.append('/usr/local/share/paw')
            if os.path.exists('/usr/local/share/paw/kali_tools_extension.py'):
                try:
                    import kali_tools_extension
                    self.kali_tools = kali_tools_extension.get_all_kali_tools()
                    self.kali_tools_loaded = True
                    logger.info("Loaded extensive Kali tools module")
                except ImportError:
                    # If import fails, try the local file
                    logger.warning("Could not import kali_tools_extension module, trying local file")
                    if os.path.exists('./kali_tools_extension.py'):
                        sys.path.append('.')
                        try:
                            import kali_tools_extension
                            self.kali_tools = kali_tools_extension.get_all_kali_tools()
                            self.kali_tools_loaded = True
                            logger.info("Loaded local extensive Kali tools module")
                        except ImportError:
                            logger.warning("Could not import local kali_tools_extension module")
                    elif os.path.exists('./kali_tools_extension.py'):
                        # Try loading the kali_tools_extension instead
                        sys.path.append('.')
                        try:
                            # Rename module temporarily for import
                            import kali_tools_extension as kali_tools_extension
                            self.kali_tools = kali_tools_extension.get_all_kali_tools()
                            self.kali_tools_loaded = True
                            logger.info("Loaded kali_tools_extension module")
                        except (ImportError, AttributeError):
                            logger.warning("Could not import kali_tools_extension module or it's missing get_all_kali_tools()")
        except Exception as e:
            logger.warning(f"Error loading Kali tools extension: {e}")
            self.kali_tools = []
    
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
        
        # Define ip_pattern for use in this method
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        
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
                    
                    # Check if command requires sudo
                    if command.startswith('sudo '):
                        # Get sudo password from user
                        if RICH_AVAILABLE:
                            sudo_password = Prompt.ask("[bold red]Enter sudo password[/]", password=True)
                        else:
                            sudo_password = getpass.getpass("Enter sudo password: ")
                        
                        # Create a temporary file for the password
                        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                            f.write(sudo_password)
                            pass_file = f.name
                        
                        try:
                            # Execute sudo command with password
                            process = subprocess.Popen(
                                f"cat {pass_file} | sudo -S {command[5:]}",
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True
                            )
                        finally:
                            # Clean up the temporary file
                            os.unlink(pass_file)
                    else:
                        # Execute normal command
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
                if command.startswith('sudo '):
                    sudo_password = getpass.getpass("Enter sudo password: ")
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                        f.write(sudo_password)
                        pass_file = f.name
                    try:
                        process = subprocess.Popen(
                            f"cat {pass_file} | sudo -S {command[5:]}",
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                    finally:
                        os.unlink(pass_file)
                else:
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
            
            run_cmd = Prompt.ask("Execute this command?", choices=["y", "n"], default="y")
            return run_cmd == "y"
        else:
            print(f"\n  \033[1;33m[{command_index}/{total_commands}] Command:\033[0m {command}")
            print(f"      \033[1;32mExplanation:\033[0m {explanation}")
            
            run_cmd = input("\033[1;35m[?] Execute this command? [y/n] (y): \033[0m").strip().lower()
            return run_cmd == "" or run_cmd == "y"
    
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
                content.append(result["stdout"].strip())
            
            # Add error output if any
            if result["stderr"].strip():
                content.append("\n[bold red]Error output:[/]")
                content.append(result["stderr"].strip())
                
            # Display the panel
            console.print(Panel(
                "\n".join(content),
                title=panel_title,
                border_style=panel_style,
                padding=(1, 2),
                expand=False
            ))
        else:
            print(f"\n\033[1;33m[{command_index}/{total_commands}] Executing:\033[0m {result['command']}")
            
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
    
    def _get_tool_descriptions_by_category(self):
        """Generate detailed tool descriptions by category for context"""
        if not self.kali_tools_loaded:
            # Return basic tool info if extensive tools not available
            return ""
        
        # Group tools by category
        categories = {}
        for tool in self.kali_tools:
            category = tool.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(tool)
        
        # Build the detailed context
        context = ""
        for category, tools in categories.items():
            context += f"\n{category.replace('_', ' ').title()}:\n"
            for tool in tools[:5]:  # Limit to 5 tools per category to keep context manageable
                name = tool.get('name', 'unknown')
                description = tool.get('description', '')
                common_usage = tool.get('common_usage', '')
                
                # Add an example if available
                examples = tool.get('examples', [])
                example = f"Example: {examples[0]}" if examples else ""
                
                context += f"  - {name}: {description}\n    Usage: {common_usage}\n    {example}\n"
        
        return context

    def _get_relevant_tool_info(self, request):
        """Extract relevant tool information based on keywords in the request"""
        if not self.kali_tools_loaded:
            return ""
            
        # Common security task keywords mapped to tool categories
        keyword_mappings = {
            'scan': ['network_scanning', 'vulnerability_scanning'],
            'recon': ['reconnaissance', 'information_gathering'],
            'discover': ['network_scanning', 'information_gathering'],
            'enumerate': ['information_gathering', 'web_application_analysis'],
            'exploit': ['exploitation', 'post_exploitation'],
            'crack': ['password_attacks', 'exploitation'],
            'wireless': ['wireless_attacks', 'bluetooth_attacks'],
            'wifi': ['wireless_attacks'],
            'web': ['web_application_analysis', 'vulnerability_scanning'],
            'sql': ['database_assessment', 'web_application_analysis'],
            'forensic': ['forensics', 'digital_forensics'],
            'network': ['network_scanning', 'sniffing_and_spoofing'],
            'password': ['password_attacks'],
            'hash': ['password_attacks', 'cryptography'],
            'sniff': ['sniffing_and_spoofing', 'wireless_attacks'],
            'spoof': ['sniffing_and_spoofing'],
            'social': ['social_engineering'],
            'phish': ['social_engineering'],
            'analyze': ['forensics', 'vulnerability_scanning'],
            'reverse': ['reverse_engineering'],
            'decrypt': ['cryptography', 'password_attacks'],
            'encrypt': ['cryptography'],
        }
        
        # Find matching categories based on keywords in the request
        relevant_categories = set()
        request_lower = request.lower()
        
        for keyword, categories in keyword_mappings.items():
            if keyword in request_lower:
                for category in categories:
                    relevant_categories.add(category)
        
        # If no specific categories found, include a baseline set
        if not relevant_categories:
            relevant_categories = {'information_gathering', 'network_scanning', 'vulnerability_scanning'}
        
        # Get tools from relevant categories
        relevant_tools = []
        for tool in self.kali_tools:
            category = tool.get('category', '').lower().replace(' ', '_')
            if category in relevant_categories:
                relevant_tools.append(tool)
        
        # Format the relevant tools information
        if not relevant_tools:
            return ""
            
        tools_info = "\nRelevant tools for this task:\n"
        for tool in relevant_tools[:15]:  # Limit to 15 most relevant tools
            name = tool.get('name', 'unknown')
            description = tool.get('description', '')
            common_usage = tool.get('common_usage', '')
            examples = tool.get('examples', [])
            
            tools_info += f"  - {name}: {description}\n"
            tools_info += f"    Usage: {common_usage}\n"
            if examples:
                tools_info += f"    Example: {examples[0]}\n"
        
        return tools_info

    def discover_target_values(self, request):
        """Discover target values needed for the request."""
        variables = {}
        
        # Check if we need to discover WiFi targets
        if any(word in request.lower() for word in ['wifi', 'wireless', 'network', 'bssid']):
            # First, check if we have a monitor mode interface
            if RICH_AVAILABLE:
                console.print("[bold yellow]Checking for wireless interfaces...[/]")
            else:
                print("\033[1;33m[*] Checking for wireless interfaces...\033[0m")
            
            # List wireless interfaces
            result = self.execute_command("iwconfig")
            if result["exit_code"] == 0:
                # Look for interfaces in monitor mode
                monitor_interfaces = []
                for line in result["stdout"].split('\n'):
                    if 'Mode:Monitor' in line:
                        interface = line.split()[0]
                        monitor_interfaces.append(interface)
                
                if monitor_interfaces:
                    if RICH_AVAILABLE:
                        console.print(f"[bold green]Found monitor mode interfaces: {', '.join(monitor_interfaces)}[/]")
                    else:
                        print(f"\033[1;32m[+] Found monitor mode interfaces: {', '.join(monitor_interfaces)}\033[0m")
                    variables['monitor_interface'] = monitor_interfaces[0]
                else:
                    # No monitor mode interfaces found, need to create one
                    if RICH_AVAILABLE:
                        console.print("[bold yellow]No monitor mode interfaces found. Creating one...[/]")
                    else:
                        print("\033[1;33m[*] No monitor mode interfaces found. Creating one...\033[0m")
                    
                    # List available interfaces
                    result = self.execute_command("iw dev")
                    if result["exit_code"] == 0:
                        interfaces = []
                        for line in result["stdout"].split('\n'):
                            if 'Interface' in line:
                                interfaces.append(line.split()[1])
                        
                        if interfaces:
                            if RICH_AVAILABLE:
                                interface = Prompt.ask("[bold cyan]Select wireless interface[/]", choices=interfaces)
                            else:
                                print(f"Available interfaces: {', '.join(interfaces)}")
                                interface = input("Select wireless interface: ")
                            
                            # Put interface in monitor mode
                            commands = [
                                f"sudo airmon-ng check kill",
                                f"sudo airmon-ng start {interface}",
                                f"sudo iwconfig {interface}mon"
                            ]
                            
                            for cmd in commands:
                                result = self.execute_command(cmd)
                                if result["exit_code"] != 0:
                                    if RICH_AVAILABLE:
                                        console.print(f"[bold red]Failed to set up monitor mode: {result['stderr']}[/]")
                                    else:
                                        print(f"\033[1;31m[!] Failed to set up monitor mode: {result['stderr']}\033[0m")
                                    return variables
                            
                            variables['monitor_interface'] = f"{interface}mon"
            
            # Scan for networks if we have a monitor interface
            if 'monitor_interface' in variables:
                if RICH_AVAILABLE:
                    console.print("[bold yellow]Scanning for wireless networks...[/]")
                else:
                    print("\033[1;33m[*] Scanning for wireless networks...\033[0m")
                
                # Start airodump-ng in background
                scan_cmd = f"sudo airodump-ng {variables['monitor_interface']} -w scan --output-format csv"
                result = self.execute_command(scan_cmd)
                
                if result["exit_code"] == 0:
                    # Parse scan results
                    networks = []
                    for line in result["stdout"].split('\n'):
                        if ':' in line and 'BSSID' not in line:  # Skip header
                            parts = line.split(',')
                            if len(parts) >= 2:
                                bssid = parts[0].strip()
                                essid = parts[13].strip() if len(parts) > 13 else ''
                                if essid:
                                    networks.append((bssid, essid))
                
                    if networks:
                        if RICH_AVAILABLE:
                            table = Table(show_header=True, header_style="bold magenta")
                            table.add_column("BSSID")
                            table.add_column("ESSID")
                            for bssid, essid in networks:
                                table.add_row(bssid, essid)
                            console.print(table)
                        else:
                            print("\nAvailable networks:")
                            for bssid, essid in networks:
                                print(f"BSSID: {bssid}, ESSID: {essid}")
                        
                        # Let user select target
                        if RICH_AVAILABLE:
                            target = Prompt.ask("[bold cyan]Select target BSSID[/]")
                        else:
                            target = input("Select target BSSID: ")
                        
                        variables['target_bssid'] = target
                        
                        # Find associated clients
                        if RICH_AVAILABLE:
                            console.print("[bold yellow]Scanning for associated clients...[/]")
                        else:
                            print("\033[1;33m[*] Scanning for associated clients...\033[0m")
                        
                        client_cmd = f"sudo airodump-ng --bssid {target} {variables['monitor_interface']} -w clients --output-format csv"
                        result = self.execute_command(client_cmd)
                        
                        if result["exit_code"] == 0:
                            clients = []
                            for line in result["stdout"].split('\n'):
                                if ':' in line and 'BSSID' not in line and 'Station' not in line:
                                    parts = line.split(',')
                                    if len(parts) >= 1:
                                        client = parts[0].strip()
                                        if client:
                                            clients.append(client)
                        
                            if clients:
                                if RICH_AVAILABLE:
                                    table = Table(show_header=True, header_style="bold magenta")
                                    table.add_column("Client MAC")
                                    for client in clients:
                                        table.add_row(client)
                                    console.print(table)
                                else:
                                    print("\nAssociated clients:")
                                    for client in clients:
                                        print(f"Client MAC: {client}")
                                
                                # Let user select client
                                if RICH_AVAILABLE:
                                    client = Prompt.ask("[bold cyan]Select target client MAC[/]")
                                else:
                                    client = input("Select target client MAC: ")
                                
                                variables['client_mac'] = client
    
        return variables

    def process_request(self, request, adaptive_override=None):
        """Process a natural language request."""
        # Override adaptive mode if specified
        if adaptive_override is not None:
            self.adaptive_mode = adaptive_override
        else:
            # Always use adaptive mode for the new one-by-one execution flow
            self.adaptive_mode = True
            
        # Clean up the request
        request = request.replace('\r', '').strip()
        
        # Discover target values
        variables = self.discover_target_values(request)
        
        # Get relevant tool information based on request keywords
        relevant_tools_info = self._get_relevant_tool_info(request)
        
        # Generate LLM response with enhanced context from Kali tools extension
        context = f"""
As PAW (Prompt Assisted Workflow), analyze this cybersecurity request and provide a plan of action:

REQUEST: {request}

Available target information:
{json.dumps(variables, indent=2)}

Consider the following Kali Linux tools and their key options when appropriate:

{relevant_tools_info}

Design your commands to work sequentially as a workflow, where later commands build on the results of earlier ones.
For commands that need input from previous commands, use placeholders like <target_ip> or <discovered_hosts>.
Provide the specific commands that would accomplish this task, explaining what each command does.
"""
        
        response = self.generate_llm_response(context)
        
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
        
        while command_index < total_commands:
            cmd = commands[command_index]
            explanation = explanations[command_index] if command_index < len(explanations) else ""
            
            # Display the command and ask for confirmation
            if self.display_single_command(cmd, explanation, command_index + 1, total_commands):
                # Execute with current variables from previous commands
                result = self.execute_command(cmd, variables)
                
                # Update variables with new ones from this command
                variables = result["variables"]
                
                # Display result
                self.display_result(result, command_index + 1, total_commands)
                
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
                            # Add the command to our list and continue loop
                            commands.append(next_cmd)
                            explanations.append(next_explanation)
                            total_commands = len(commands)
                            # Do not increment command_index yet - we'll show this command for approval first
                        else:
                            # No next command could be generated
                            if RICH_AVAILABLE:
                                console.print("[bold yellow]Could not generate a next command. Workflow complete.[/]")
                            else:
                                print("\033[1;33m[!] Could not generate a next command. Workflow complete.\033[0m")
                            break
                    else:
                        # User chose not to continue
                        break
            else:
                # User skipped this command, move to the next one
                if RICH_AVAILABLE:
                    console.print("[yellow]Command skipped[/]")
                else:
                    print("\033[1;33m[*] Command skipped\033[0m")
            
            # Move to the next command
            command_index += 1
        
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
    parser.add_argument("--iterative", action="store_true", help="Generate and execute commands one at a time")
    
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
        adaptive_mode = args.adaptive or args.prog or args.iterative
        paw.process_request(args.request, adaptive_mode)
    else:
        if RICH_AVAILABLE:
            console.print("[bold cyan]Welcome to PAW - Prompt Assisted Workflow[/]")
            console.print("[cyan]Type 'exit' or 'quit' to exit[/]")
            if args.iterative:
                console.print("[yellow]Running in iterative mode - commands will be generated and executed one at a time[/]")
        else:
            print("\033[1;34m[*] Welcome to PAW - Prompt Assisted Workflow\033[0m")
            print("\033[1;34m[*] Type 'exit' or 'quit' to exit\033[0m")
            if args.iterative:
                print("\033[1;33m[*] Running in iterative mode - commands will be generated and executed one at a time\033[0m")
        
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
                    paw.process_request(request, args.iterative)
                    
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