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

# Add extensive_kali_tools import
try:
    from extensive_kali_tools import get_all_kali_tools, get_tool_categories, get_tools_by_category, get_tool_info
    KALI_TOOLS_AVAILABLE = True
except ImportError:
    KALI_TOOLS_AVAILABLE = False
    print("Warning: extensive_kali_tools.py not found or cannot be imported. Some features will be limited.")

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
        
        # Initialize Kali tools database if available
        self.init_kali_tools()
    
    def init_kali_tools(self):
        """Initialize the Kali tools database for use in command generation."""
        if KALI_TOOLS_AVAILABLE:
            try:
                if RICH_AVAILABLE:
                    console.print("[bold cyan]Loading Kali Linux tools database...[/]")
                else:
                    print("\033[1;34m[*] Loading Kali Linux tools database...\033[0m")
                
                # Load all Kali tools to ensure they're initialized
                all_tools = get_all_kali_tools()
                categories = get_tool_categories()
                
                if RICH_AVAILABLE:
                    console.print(f"[bold green]Loaded {len(all_tools)} Kali Linux tools across {len(categories)} categories[/]")
                else:
                    print(f"\033[1;32m[+] Loaded {len(all_tools)} Kali Linux tools across {len(categories)} categories\033[0m")
                
                # Log successful tool loading
                logger.info(f"Loaded {len(all_tools)} Kali Linux tools across {len(categories)} categories")
                return True
            except Exception as e:
                logger.error(f"Error initializing Kali tools database: {e}")
                if RICH_AVAILABLE:
                    console.print(f"[bold red]Error loading Kali Linux tools database: {str(e)}[/]")
                else:
                    print(f"\033[1;31m[!] Error loading Kali Linux tools database: {str(e)}\033[0m")
                return False
        return False
    
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
    
    def detect_network_interface(self):
        """Detect the primary network interface for the system."""
        interfaces = self.get_network_interfaces()
        if interfaces:
            # Return the first non-loopback interface
            for interface in interfaces:
                if interface != 'lo':
                    return interface
            # If only loopback is available, return it
            return interfaces[0]
        else:
            # Default to a common interface name if detection fails
            return "eth0"
    
    def generate_llm_response(self, prompt):
        """Generate a response from the LLM using Ollama."""
        try:
            logger.info(f"Sending prompt to LLM: {prompt[:50]}...")
            
            # Don't use fancy spinner for thinking animation to avoid display conflicts
            if RICH_AVAILABLE:
                console.print("[bold cyan]Thinking...[/]", end="")
                    
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
                
                # Clear the line
                console.print("\r" + " " * 50 + "\r", end="")
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
            # First, try to directly parse the entire text as JSON
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
                
            # Find JSON in the response (might be surrounded by markdown code blocks)
            # Look for JSON enclosed in triple backtick code blocks
            json_pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```"
            match = re.search(json_pattern, text)
            
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
                
            # Try to extract any JSON object from the text
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_str = text[json_start:json_end]
                try:
                return json.loads(json_str)
                except json.JSONDecodeError:
                    # If parsing fails, try to clean the JSON string
                    # Some models might add escape characters that break JSON
                    cleaned_json = re.sub(r'\\([^"])', r'\1', json_str)
                    try:
                        return json.loads(cleaned_json)
                    except:
                        pass
            
            # If no JSON found, look for key components to construct a response
            plan_match = re.search(r"(Plan|Steps|Strategy):\s*\n((?:.+\n)+)", text, re.IGNORECASE)
            cmd_match = re.search(r"(Command|Commands|Execution|Run):\s*\n((?:.+\n)+)", text, re.IGNORECASE)
            exp_match = re.search(r"(Explanation|Description|Details):\s*\n((?:.+\n)+)", text, re.IGNORECASE)
            
            if cmd_match:  # If we at least found commands
                plan = []
                if plan_match:
                    plan = [line.strip('- \t') for line in plan_match.group(2).strip().split('\n') if line.strip('- \t')]
                
                commands = [line.strip('- \t') for line in cmd_match.group(2).strip().split('\n') if line.strip('- \t')]
                # Filter out non-commands (often numbered lists with explanations mixed in)
                commands = [cmd for cmd in commands if not cmd.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '0.'))]
                
                explanation = []
                if exp_match:
                    explanation = [line.strip('- \t') for line in exp_match.group(2).strip().split('\n') if line.strip('- \t')]
                
                return {
                    "plan": plan or ["Execute the requested task"],
                    "commands": commands,
                    "explanation": explanation or ["Execute the command to perform the requested task"] * len(commands)
                }
            
            # If we couldn't find JSON or structured content, try to extract command lines
            # Look for lines that look like shell commands (start with common command prefixes)
            command_prefixes = ['sudo', 'apt', 'cd', 'ls', 'cat', 'grep', 'find', 'chmod', 'mkdir', 'rm', 
                              'cp', 'mv', 'touch', 'echo', 'curl', 'wget', 'git', 'python', 'bash', 'sh',
                              'nmap', 'nikto', 'hydra', 'john', 'hashcat', 'dirb', 'gobuster', 'wpscan',
                              'sqlmap', 'msfconsole', 'msfvenom', 'tcpdump', 'wireshark', 'ifconfig',
                              'ip', 'ssh', 'netstat', 'nc', 'ping', 'traceroute', 'whois', 'dig', 'host']
            
            potential_commands = []
            for line in text.split('\n'):
                line = line.strip()
                if line and any(line.startswith(prefix) for prefix in command_prefixes):
                    potential_commands.append(line)
            
            if potential_commands:
                return {
                    "plan": ["Execute the requested commands"],
                    "commands": potential_commands,
                    "explanation": [f"Executing command: {cmd}" for cmd in potential_commands]
                }
            
            # If still no commands found, use the original approach - whole text as command
            # But first check if it actually looks like a command rather than just text
            if any(text.strip().startswith(prefix) for prefix in command_prefixes):
            return {
                "plan": ["Process the request"],
                "commands": [text.strip()],
                "explanation": ["Generated command based on your request"]
            }
            else:
                # If text doesn't look like a command, don't execute anything
                return {
                    "plan": ["No executable commands found in response"],
                    "commands": [],
                    "explanation": ["The model didn't generate a valid command. Please try rephrasing your request."]
                }
            
        except json.JSONDecodeError:
            # If JSON parsing fails, log it and return empty result rather than executing whole text
            logger.error(f"Failed to parse JSON from response: {text[:100]}...")
            return {
                "plan": ["Failed to parse response from LLM"],
                "commands": [],
                "explanation": ["The response from the AI model couldn't be interpreted as valid commands. Please try again with a clearer request."]
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
    
    def extract_file_paths(self, text):
        """Extract potential file paths from text, handling paths with spaces and quotes."""
        # Try to match quoted paths first (handles spaces in paths)
        quoted_paths = re.findall(r'["\']((?:/|\.)[^"\']+)["\']', text)
        if quoted_paths:
            return quoted_paths
            
        # Try to match unquoted paths
        unquoted_paths = re.findall(r'(?<=\s|^)((?:/|\.)[^\s]+)(?=\s|$)', text)
        
        # For paths that might contain spaces
        space_paths = []
        if "New Folder" in text or "new folder" in text:
            # Try to reconstruct paths with spaces
            potential_paths = re.findall(r'(?:/[^\s/]+)+(?:\s+[^\s/]+)+\.[a-zA-Z0-9]+', text, re.IGNORECASE)
            if potential_paths:
                space_paths.extend(potential_paths)
        
        return quoted_paths + unquoted_paths + space_paths

    def suggest_alternative_command(self, failed_cmd, stderr, variables):
        """Suggest a completely different approach based on the failed command and error output."""
        # Create context for generating alternative commands
        context = f"""
I need to suggest an ALTERNATIVE COMMAND for a failed cybersecurity operation.

FAILED COMMAND: {failed_cmd}

ERROR MESSAGE:
{stderr}

ORIGINAL REQUEST: {variables.get('request', 'No request information available')}

Available variables: {json.dumps(variables, indent=2)}

Based on this error, suggest a COMPLETELY DIFFERENT APPROACH using a different tool or technique.
DO NOT simply fix syntax errors in the original command - provide a fundamentally different approach.

Here are examples of alternative tools for different categories:

1. Network scanning alternatives:
   - If nmap failed, try masscan, netdiscover, or unicornscan
   - If port scanning failed, try a different scan type or tool

2. Web scanning alternatives:
   - If nikto failed, try dirb, gobuster, or wpscan
   - If dirb failed, try gobuster or ffuf
   - If a web vulnerability scanner failed, try a different scanner or manual techniques

3. Password cracking alternatives:
   - If hashcat failed, try john or hydra
   - If john failed, try hashcat
   - If a specific wordlist didn't work, try a different wordlist or technique

4. Exploitation alternatives:
   - If metasploit failed, try a direct exploit or manual technique
   - If a specific exploit failed, try a different exploit or approach

5. Information gathering alternatives:
   - If one reconnaissance tool failed, suggest an alternative
   - If whois failed, try host, dig, or other DNS tools

Respond with a JSON object containing:
{{
  "command": "alternative command to try",
  "explanation": "why this alternative approach might work better"
}}

Make sure the alternative is genuinely different and appropriate for the task at hand.
"""
        try:
            if RICH_AVAILABLE:
                console.print("[bold cyan]Generating alternative approach...[/]")
            
            response = self.generate_llm_response(context)
            
            if "error" in response or not response:
                return None, None
                
            alt_command = response.get("command", "")
            if isinstance(alt_command, list) and alt_command:
                alt_command = alt_command[0]
                
            explanation = response.get("explanation", "")
            if isinstance(explanation, list) and explanation:
                explanation = explanation[0]
                
            # Make sure we don't return the exact same command
            if alt_command and alt_command != failed_cmd:
                # Substitute variables in the alternative command
                alt_command = self.substitute_variables(alt_command, variables)
                return alt_command, explanation
                
        except Exception as e:
            logger.error(f"Error generating alternative command: {e}")
            
        return None, None

    def handle_failed_command(self, cmd, result, variables, command_index, total_commands):
        """Handle a failed command by trying to fix it or asking user what to do."""
        # Try to fix the command
        fixed_cmd, suggestion, updated_vars = self.fix_failed_command(cmd, result["stderr"], variables)
        
        # Special handling for hashcat info command failure
        if "hashcat: unrecognized option '--info'" in result["stderr"]:
            if RICH_AVAILABLE:
                console.print("[bold yellow]Hashcat doesn't support the --info option on this system.[/]")
                console.print("[bold cyan]Trying alternative commands for GPG password cracking...[/]")
            else:
                print("\033[1;33m[*] Hashcat doesn't support the --info option on this system.\033[0m")
                print("\033[1;36m[*] Trying alternative commands for GPG password cracking...\033[0m")
            
            # Suggest a different command based on the file extension
            if ".gpg" in str(variables.get('request', '')):
                gpg_file = None
                
                # Extract file paths from the request
                extracted_paths = self.extract_file_paths(variables.get('request', ''))
                
                for path in extracted_paths:
                    if ".gpg" in path:
                        gpg_file = path
                        break
                
                if not gpg_file and 'request' in variables:
                    # Try to extract the filename from the request with regex
                    matches = re.findall(r'([^\s]+\.(?:tar\.)?gpg)', str(variables['request']))
                    if matches:
                        gpg_file = matches[0]
                
                if gpg_file:
                    # Properly quote the file path if it contains spaces
                    if ' ' in gpg_file and not (gpg_file.startswith('"') or gpg_file.startswith("'")):
                        gpg_file = f'"{gpg_file}"'
                    
                    fixed_cmd = f"gpg2john {gpg_file} > hash.txt"
                    suggestion = "Using gpg2john to extract the hash from the GPG file for cracking"
                    if RICH_AVAILABLE:
                        retry = Confirm.ask(f"Try using gpg2john on {gpg_file}?", default=True)
                    else:
                        print(f"\033[1;33m[*] Suggested fix: Use gpg2john on {gpg_file}\033[0m")
                        retry = input("\033[1;35m[?] Try this approach? (y/n): \033[0m").strip().lower()
                        retry = retry == "" or retry == "y"
                    
                    if retry:
                        result = self.execute_command(fixed_cmd, updated_vars)
                        self.display_result(result, command_index, total_commands)
                        return result, updated_vars

        # Special handling for file not found errors
        if "No such file" in result["stderr"] or "not found" in result["stderr"]:
            if ".gpg" in str(variables.get('request', '')):
                # Ask user to provide the correct path to the GPG file
                if RICH_AVAILABLE:
                    gpg_file = Prompt.ask("[bold yellow]Enter the full path to the GPG file[/]")
                else:
                    gpg_file = input("\033[1;35m[?] Enter the full path to the GPG file: \033[0m").strip()
                
                if gpg_file:
                    variables['gpg_file'] = gpg_file
                    if "gpg2john" in cmd:
                        fixed_cmd = f"gpg2john {gpg_file} > hash.txt"
                        result = self.execute_command(fixed_cmd, variables)
                        self.display_result(result, command_index, total_commands)
                        return result, variables
        
        # Present options to the user for handling the failure
        options = []
        
        # Option 1: Try the fixed command (if available)
        has_fixed_cmd = fixed_cmd != cmd
        if has_fixed_cmd:
            options.append(("Fix the current command", fixed_cmd, suggestion))
            
        # Option 2: Try a completely different approach
        alt_cmd, alt_explanation = self.suggest_alternative_command(cmd, result["stderr"], variables)
        has_alt_cmd = alt_cmd is not None
        if has_alt_cmd:
            options.append(("Try a different approach", alt_cmd, alt_explanation))
            
        # Option 3: Skip this command
        options.append(("Skip this command", None, "Skip this command and continue the workflow"))
        
        # If we have multiple options, present them to the user
        if len(options) > 1:
            if RICH_AVAILABLE:
                console.print("[bold yellow]Command failed. Here are your options:[/]")
                for i, (option_name, option_cmd, option_explanation) in enumerate(options, 1):
                    console.print(f"[bold]{i}.[/] {option_name}")
                    if option_cmd:
                        console.print(f"   Command: [bold yellow]{option_cmd}[/]")
                    if option_explanation:
                        console.print(f"   [dim]{option_explanation}[/]")
                    
                choice = Prompt.ask(
                    "[bold yellow]Choose an option[/]", 
                    choices=[str(i) for i in range(1, len(options) + 1)],
                    default="1"
                )
                choice_idx = int(choice) - 1
            else:
                print("\033[1;33m[*] Command failed. Here are your options:\033[0m")
                for i, (option_name, option_cmd, option_explanation) in enumerate(options, 1):
                    print(f"{i}. {option_name}")
                    if option_cmd:
                        print(f"   Command: {option_cmd}")
                    if option_explanation:
                        print(f"   {option_explanation}")
                
                choice = input("\033[1;35m[?] Choose an option [1]: \033[0m").strip()
                if not choice:
                    choice = "1"
                choice_idx = int(choice) - 1
                
            # Execute the chosen option
            option_name, option_cmd, option_explanation = options[choice_idx]
            
            if option_cmd is None:  # Skip command
                return result, variables
            
            # Execute the selected command
            if RICH_AVAILABLE:
                console.print(f"[bold cyan]Executing: {option_cmd}[/]")
                console.print(f"[dim]{option_explanation}[/]")
            else:
                print(f"\033[1;36m[*] Executing: {option_cmd}\033[0m")
                print(f"\033[1;36m[*] {option_explanation}\033[0m")
                
            result = self.execute_command(option_cmd, updated_vars if option_cmd == fixed_cmd else variables)
            self.display_result(result, command_index, total_commands)
            return result, updated_vars if option_cmd == fixed_cmd else variables
            
        # If we only have one option (fixed command), use the old behavior
        elif has_fixed_cmd:
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
        # Check for specific patterns in previous command and output to provide better next steps
        
        # Handle gpg2john output
        if "gpg2john" in previous_command and "hash.txt" in previous_command:
            # After extracting hash with gpg2john, suggest using john to crack it
            if os.path.exists("hash.txt"):
                next_cmd = "john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt"
                explanation = "Using John the Ripper with rockyou.txt wordlist to crack the GPG password hash"
                return next_cmd, explanation
        
        # Handle john password cracking results
        if "john" in previous_command and "hash.txt" in previous_command:
            if "password hashes cracked" in previous_output or "password hash cracked" in previous_output:
                next_cmd = "john --show hash.txt"
                explanation = "Displaying the cracked password(s)"
                return next_cmd, explanation
        
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
- For password cracking tasks, prefer using john or hashcat with the rockyou.txt wordlist (/usr/share/wordlists/rockyou.txt).
- For GPG files, use gpg2john to extract the hash, then use john to crack it.

Based on the previous command and its output, generate the next most logical command to continue this workflow.
Respond with a JSON object containing:
{{
  "command": "the next command to run",
  "explanation": "explanation of what this command does and why it's appropriate next"
}}

The command should directly use the values from the previous output when appropriate, not placeholders.
"""
        
        try:
            # Use direct call to generate response without using Progress
            if RICH_AVAILABLE:
                console.print("[bold cyan]Generating next command...[/]")
        
        response = self.generate_llm_response(context)
        
        if "error" in response:
                logger.error(f"Error generating next command: {response['error']}")
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
        except Exception as e:
            logger.error(f"Error generating next command: {e}")
            return None, None
    
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
    
    def validate_commands_for_prompt(self, request, commands, explanations):
        """Validate that the generated commands match the user's intent"""
        if not commands:
            return {
                "is_valid": False,
                "feedback": "No commands were generated.",
                "suggested_commands": []
            }
            
        # Construct validation context
        validation_context = {
            "user_request": request,
            "generated_commands": commands,
            "command_explanations": explanations
        }
        
        # Check for relevance to the request
        request_terms = set(request.lower().split())
        
        # First use extensive_kali_tools if available
        relevant_tools = []
        if KALI_TOOLS_AVAILABLE:
            try:
                # Extract keywords from request
                keywords = [word.lower() for word in request.split() if len(word) > 3]
                
                # Find relevant tool categories based on request
                relevant_categories = set()
                for keyword in keywords:
                    # Common category mappings
                    if any(term in keyword for term in ["network", "scan", "port", "discover"]):
                        relevant_categories.add("Information Gathering")
                    elif any(term in keyword for term in ["vuln", "exploit", "attack"]):
                        relevant_categories.add("Vulnerability Analysis")
                        relevant_categories.add("Exploitation Tools")
                    elif any(term in keyword for term in ["web", "http", "site"]):
                        relevant_categories.add("Web Application Analysis")
                    elif any(term in keyword for term in ["password", "crack", "hash"]):
                        relevant_categories.add("Password Attacks")
                    elif any(term in keyword for term in ["wifi", "wireless"]):
                        relevant_categories.add("Wireless Attacks")
                
                # Get recommended tools from these categories
                for category in relevant_categories:
                    try:
                        category_tools = get_tools_by_category(category)
                        if category_tools:
                            for tool in category_tools:
                                if "name" in tool:
                                    relevant_tools.append(tool["name"])
                    except Exception as e:
                        logger.error(f"Error getting tools for category {category}: {e}")
            except Exception as e:
                logger.error(f"Error using Kali tools for validation: {e}")
        
        # Fallback to hardcoded common tools if no relevant tools found or no Kali tools available
        if not relevant_tools:
            common_tools = {
                "mac address": ["macchanger", "ifconfig", "ip"],
                "scan": ["nmap", "nikto", "dirb"],
                "password": ["john", "hashcat", "hydra"],
                "web": ["dirb", "gobuster", "nikto", "curl", "wget"],
                "file": ["ls", "cat", "grep", "find"],
                "network": ["ping", "traceroute", "netstat", "ss"]
            }
            
            # Check if appropriate tools are being used for the request
            for key, tools in common_tools.items():
                if key in request.lower():
                    relevant_tools.extend(tools)
        
        # Check if any of the relevant tools are in the commands
        tools_used = []
        for cmd in commands:
            for tool in relevant_tools:
                if tool in cmd:
                    tools_used.append(tool)
        
        # Check for critical steps that might be missing
        required_steps = {}
        if "mac" in request.lower() and "change" in request.lower():
            required_steps = {
                "check_current": any("ifconfig" in cmd or "ip link" in cmd for cmd in commands),
                "change_mac": any("macchanger" in cmd for cmd in commands),
                "verify_change": any(("ifconfig" in cmd or "ip link" in cmd) and cmd != commands[0] for cmd in commands)
            }
        
        # Evaluate validation
        is_valid = True
        feedback = "Commands are appropriate for the request."
        suggested_commands = []
        
        # Check if required tools are missing
        if relevant_tools and not tools_used:
            is_valid = False
            feedback = f"Commands may not use the appropriate tools for this request. Consider using: {', '.join(relevant_tools[:5])}"
            
            # Suggest appropriate commands based on the request type
            if "mac" in request.lower() and "change" in request.lower():
                interface = self.detect_network_interface() or "eth0"
                suggested_commands = [
                    f"sudo ifconfig {interface} | grep ether",
                    f"sudo macchanger -r {interface}",
                    f"sudo ifconfig {interface} | grep ether"
                ]
            elif "scan" in request.lower() and "port" in request.lower():
                target = "target_ip"
                for word in request.split():
                    if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', word):
                        target = word
                        break
                suggested_commands = [f"sudo nmap -sS -p- {target}"]
            elif KALI_TOOLS_AVAILABLE:
                # Try to get example commands from Kali tools database
                for tool_name in relevant_tools[:2]:  # Get examples from top 2 tools
                    try:
                        tool_info = get_tool_info(tool_name)
                        if tool_info and "examples" in tool_info:
                            examples = tool_info["examples"]
                            if examples:
                                if isinstance(examples[0], dict):
                                    # New format with description and command
                                    suggested_commands.append(examples[0]["command"])
                                else:
                                    # Old format with just command strings
                                    suggested_commands.append(examples[0])
                    except Exception as e:
                        logger.error(f"Error getting examples for tool {tool_name}: {e}")
            
        # Check for missing critical steps
        if required_steps and not all(required_steps.values()):
            is_valid = False
            missing_steps = [step for step, present in required_steps.items() if not present]
            feedback = f"Commands are missing critical steps: {', '.join(missing_steps)}"
        
        return {
            "is_valid": is_valid,
            "feedback": feedback,
            "suggested_commands": suggested_commands
        }

    def process_request(self, request, adaptive_mode=None):
        """Generate a response from the model and execute the commands"""
        # Extract any command placeholders or key terms for specialized handling
        interface_pattern = r'\b(?:eth[0-9]|wlan[0-9]|tun[0-9]|lo)\b'
        mac_pattern = r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        
        # Extract key terms from the request
        interfaces = re.findall(interface_pattern, request)
        mac_addresses = re.findall(mac_pattern, request)
        ip_addresses = re.findall(ip_pattern, request)
        
        # Special handling for specific operations
        is_mac_change_request = any(term in request.lower() for term in ['mac', 'mac address', 'change mac', 'spoof mac'])
        is_password_request = any(term in request.lower() for term in ['password', 'crack', 'decrypt', 'gpg'])
        
        # Use provided adaptive_mode or fall back to the instance variable
        if adaptive_mode is None:
            adaptive_mode = self.adaptive_mode

        # Get local machine details for command substitution
        detected_interface = self.detect_network_interface()
        local_ip = self.get_local_ip()
        
        # Build context for command generation
        context = [
            "You are a helpful Linux command assistant. Generate appropriate commands based on the user's request.",
            "You must return a JSON object with the following structure: {\"plan\": [steps], \"commands\": [commands], \"explanation\": [explanations]}",
            "IMPORTANT: Your commands MUST directly address the user's request and be appropriate for their system.",
            "Use the correct tools based on the user's request (e.g., macchanger for MAC address changes, nmap for scanning).",
            f"ALWAYS run commands as root (use sudo) when accessing privileged resources.",
            "If a command requires an interface, use: " + (interfaces[0] if interfaces else detected_interface or "eth0"),
            "If a command requires a local IP, use: " + (ip_addresses[0] if ip_addresses else local_ip or "127.0.0.1"),
        ]
        
        # Add specialized guidance for specific request types
        if is_mac_change_request:
            context.append("For MAC address changes, use macchanger. First check the current MAC with ifconfig or ip link, then use macchanger -r <interface> for a random MAC.")
        
        if is_password_request and "gpg" in request.lower():
            context.append("For GPG password cracking, use gpg2john to extract the hash, then john to crack it.")
        
        # Add Kali tools guidance from extensive_kali_tools if available
        if KALI_TOOLS_AVAILABLE:
            try:
                # Get all available Kali tools
                all_kali_tools = get_all_kali_tools()
                
                # Extract keywords from request
                keywords = [word.lower() for word in request.split() if len(word) > 3]
                
                # Find relevant tool categories based on request
                relevant_categories = set()
                for keyword in keywords:
                    # Common category mappings
                    if any(term in keyword for term in ["network", "scan", "port", "discover"]):
                        relevant_categories.add("Information Gathering")
                    elif any(term in keyword for term in ["vuln", "exploit", "attack"]):
                        relevant_categories.add("Vulnerability Analysis")
                        relevant_categories.add("Exploitation Tools")
                    elif any(term in keyword for term in ["web", "http", "site"]):
                        relevant_categories.add("Web Application Analysis")
                    elif any(term in keyword for term in ["password", "crack", "hash"]):
                        relevant_categories.add("Password Attacks")
                    elif any(term in keyword for term in ["wifi", "wireless"]):
                        relevant_categories.add("Wireless Attacks")
                
                # If no specific categories identified, suggest some based on common tasks
                if not relevant_categories:
                    relevant_categories = {"Information Gathering", "Vulnerability Analysis"}
                
                # Build tool recommendations for context
                tool_recommendations = []
                
                # Add category-specific tool recommendations
                for category in relevant_categories:
                    try:
                        category_tools = get_tools_by_category(category)
                        if category_tools and len(category_tools) > 0:
                            # Get up to 3 tools from each category
                            sample_tools = category_tools[:3]
                            
                            # Add category header
                            tool_recommendations.append(f"\nFor {category}, consider these tools:")
                            
                            # Add details for each tool
                            for tool in sample_tools:
                                tool_name = tool.get("name", "")
                                description = tool.get("description", "")
                                common_usage = tool.get("common_usage", "")
                                examples = tool.get("examples", [])
                                
                                # Add tool details
                                tool_recommendations.append(f"- {tool_name}: {description}")
                                tool_recommendations.append(f"  Usage: {common_usage}")
                                
                                # Add 1-2 examples if available
                                if examples and len(examples) > 0:
                                    if isinstance(examples[0], dict):
                                        # New format: list of dictionaries with description and command
                                        for i, example in enumerate(examples[:2]):
                                            tool_recommendations.append(f"  Example: {example.get('command')} - {example.get('description')}")
                        else:
                                        # Old format: list of example command strings
                                        for i, example in enumerate(examples[:2]):
                                            tool_recommendations.append(f"  Example: {example}")
                    except Exception as e:
                        logger.error(f"Error getting tools for category {category}: {e}")
                
                # Add tool recommendations to context if any were found
                if tool_recommendations:
                    context.append("\nRECOMMENDED KALI LINUX TOOLS FOR THIS REQUEST:")
                    context.extend(tool_recommendations)
                    
                    # Add reminder to use these tools
                    context.append("\nIMPORTANT: Please use the appropriate tools from the list above when generating commands.")
            except Exception as e:
                logger.error(f"Error loading Kali tools information: {e}")
                
        # Generate the response
        response = self.generate_llm_response("\n".join(context) + "\n\nRequest: " + request)
        if "error" in response:
                    if RICH_AVAILABLE:
                console.print(f"[bold red]{response['error']}[/]")
                    else:
                print(f"\033[1;31m[!] {response['error']}\033[0m")
            return response
        
        try:
            # Extract the plan, commands, and explanations
            plan = response.get("plan", ["Execute the requested task"])
            commands = response.get("commands", [])
            explanations = response.get("explanation", [])

            # Make sure explanations match commands in length
            if len(explanations) < len(commands):
                explanations.extend(["Execute the command"] * (len(commands) - len(explanations)))
            
            # Validate that the commands match the user's intent
            validation = self.validate_commands_for_prompt(request, commands, explanations)
            
            # If validation suggests improvements, show them to the user
            if validation.get("suggested_commands") and not validation.get("is_valid"):
                logger.info(f"Command validation suggested improvements: {validation['feedback']}")
                print(f"\n\033[93mValidation feedback: {validation['feedback']}\033[0m")
                print("\033[93mSuggested commands:\033[0m")
                for i, cmd in enumerate(validation.get("suggested_commands", [])):
                    print(f"\033[93m{i+1}. {cmd}\033[0m")
                print("\033[93mConsider using these commands instead.\033[0m\n")
            
            # Display the plan
            self.display_plan(plan)
            
            # If we have commands, display and execute them
            if commands:
                # Display the commands with their explanations
                self.display_commands(commands, explanations)
                
                # If in adaptive mode, let the user select commands one by one
                if adaptive_mode:
                    # Handle commands one at a time, generating follow-up commands
                    variables = {"request": request}
                    selected_commands, _ = self.interactive_command_selection(commands, explanations)
                    
                    for i, cmd in enumerate(selected_commands, 1):
                        # Execute the command and capture its output
                        result = self.execute_command(cmd, variables)
                        self.display_result(result, i, len(selected_commands))
                        
                        # Update variables with any values extracted from the output
                        variables.update(result.get("variables", {}))
                        else:
                    # Execute all commands in sequence with y/n confirmation
                    variables = {"request": request}
                    for i, (cmd, explanation) in enumerate(zip(commands, explanations), 1):
                        if self.display_single_command(cmd, explanation, i, len(commands)):
                            # Execute the command
                            result = self.execute_command(cmd, variables)
                            self.display_result(result, i, len(commands))
                            
                            # If command failed and we need to handle it
                            if result["exit_code"] != 0:
                                result, variables = self.handle_failed_command(cmd, result, variables, i, len(commands))
                            
                            # Update variables with any values extracted from the output
                            variables.update(result.get("variables", {}))
                        else:
                            # User chose not to execute this command
                            if RICH_AVAILABLE:
                                console.print(f"[yellow]Skipping command: {cmd}[/]")
                            else:
                                print(f"\033[1;33m[*] Skipping command: {cmd}\033[0m")
                    else:
                # No commands were generated
                if RICH_AVAILABLE:
                    console.print("[bold yellow]No commands were generated for this request.[/]")
                else:
                    print("\033[1;33m[!] No commands were generated for this request.\033[0m")
            
            return response
        except Exception as e:
            logger.error(f"Failed to process response: {e}")
        if RICH_AVAILABLE:
                console.print(f"[bold red]Error: {str(e)}[/]")
        else:
                print(f"\033[1;31m[!] Error: {str(e)}\033[0m")
            return {"error": f"Failed to process response: {e}"}

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