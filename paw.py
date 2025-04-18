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
from typing import List, Dict
import platform

# Get the absolute path of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define possible installation paths
POSSIBLE_INSTALL_PATHS = [
    '/usr/local/share/paw',  # System-wide installation
    os.path.join(SCRIPT_DIR, 'lib'),  # Local development
    SCRIPT_DIR,  # Current directory
]

# Add all possible paths to Python path, avoiding duplicates
for path in POSSIBLE_INSTALL_PATHS:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

# Clear any existing duplicate paths
sys.path = list(dict.fromkeys(sys.path))

# Try importing required modules with fallbacks
try:
    import tools_registry
except ImportError:
    try:
        from lib import tools_registry
    except ImportError:
        print("Error: Could not import PAW tools_registry module.")
        print("Current Python path:")
        for path in sys.path:
            print(f"  - {path}")
        print("\nMake sure PAW is installed correctly.")
        sys.exit(1)

try:
    import ascii_art
except ImportError:
    try:
        from lib import ascii_art
    except ImportError:
        print("Warning: Could not import ascii_art module. Some features may be limited.")
        ascii_art = None

try:
    import extensive_kali_tools
except ImportError:
    print("Warning: Could not import extensive_kali_tools module. Kali tools functionality will be limited.")
    extensive_kali_tools = None

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
        # Create default config
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, 'w') as f:
                f.write("""[DEFAULT]
model = qwen2.5-coder:7b
ollama_host = http://localhost:11434
explain_commands = true
log_commands = true
log_directory = /var/log/paw
llm_timeout = 600.0
command_timeout = 600.0
theme = cyberpunk
adaptive_mode = false
use_sudo = false
""")
            print(f"Created default config at {CONFIG_PATH}")
            config.read(CONFIG_PATH)
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
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
        # Initialize tools registry
        self.tools_registry = tools_registry.get_tools_registry()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(LOG_DIRECTORY, f"paw_session_{self.session_id}.log")
        self.theme = THEMES[THEME]
        
        if LOG_COMMANDS:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
        
        # Get config for adaptive mode
        self.adaptive_mode = config['DEFAULT'].getboolean('adaptive_mode', False)
        
        # Check if sudo should be used without prompting (avoid sudo password problems)
        # Default to False to prevent password prompts
        self.use_sudo = config['DEFAULT'].getboolean('use_sudo', False)
        
        # Initialize Kali tools if available
        self.kali_tools = None
        self.kali_categories = None
        if extensive_kali_tools:
            try:
                self.kali_tools = extensive_kali_tools.get_all_kali_tools()
                self.kali_categories = extensive_kali_tools.get_tool_categories()
                print("Kali tools integration initialized successfully.")
            except Exception as e:
                print(f"Warning: Could not initialize Kali tools: {e}")
                self.kali_tools = None
                self.kali_categories = None

    def init_kali_tools(self):
        """Initialize the Kali tools database for use in command generation."""
        if extensive_kali_tools:
            try:
                if RICH_AVAILABLE:
                    console.print("[bold green]Initializing Kali tools database...[/bold green]")
                else:
                    print("Initializing Kali tools database...")
                
                # Load all Kali tools to ensure they're initialized
                self.kali_tools = extensive_kali_tools.get_all_kali_tools()
                self.kali_categories = extensive_kali_tools.get_tool_categories()
                
                if RICH_AVAILABLE:
                    console.print(f"[green]Loaded {len(self.kali_tools)} Kali tools across {len(self.kali_categories)} categories[/green]")
                else:
                    print(f"Loaded {len(self.kali_tools)} Kali tools across {len(self.kali_categories)} categories")
                
                return True
            except Exception as e:
                if RICH_AVAILABLE:
                    console.print(f"[yellow]Warning: Could not initialize Kali tools: {e}[/yellow]")
                else:
                    print(f"Warning: Could not initialize Kali tools: {e}")
                return False
        return False

    def get_relevant_kali_tools(self, request: str) -> List[str]:
        """Get relevant Kali tools based on the request."""
        if not extensive_kali_tools or not self.kali_tools:
            return []
            
        try:
            # Extract keywords from request
            keywords = request.lower().split()
            
            # Get relevant categories
            relevant_categories = []
            for category in self.kali_categories:
                if any(keyword in category.lower() for keyword in keywords):
                    relevant_categories.append(category)
            
            # Get tools from relevant categories
            relevant_tools = []
            for category in relevant_categories:
                try:
                    category_tools = extensive_kali_tools.get_tools_by_category(category)
                    if category_tools:
                        for tool in category_tools:
                            if tool["name"] not in relevant_tools:
                                relevant_tools.append(tool["name"])
                except Exception as e:
                    print(f"Warning: Error getting tools for category {category}: {e}")
            
            return relevant_tools
        except Exception as e:
            print(f"Warning: Error getting relevant Kali tools: {e}")
            return []

    def suggest_alternative_command(self, failed_cmd: str, stderr: str, variables: Dict[str, str]) -> List[str]:
        """Suggest alternative commands based on the error and available tools."""
        suggested_commands = []
        
        # First use extensive_kali_tools if available
        relevant_tools = []
        if extensive_kali_tools and self.kali_tools:
            try:
                # Extract keywords from error message
                keywords = stderr.lower().split()
                
                # Get relevant categories
                relevant_categories = []
                for category in self.kali_categories:
                    if any(keyword in category.lower() for keyword in keywords):
                        relevant_categories.append(category)
                
                # Get tools from relevant categories
                for category in relevant_categories:
                    try:
                        category_tools = extensive_kali_tools.get_tools_by_category(category)
                        if category_tools:
                            for tool in category_tools:
                                if tool["name"] not in relevant_tools:
                                    relevant_tools.append(tool["name"])
                    except Exception as e:
                        print(f"Warning: Error getting tools for category {category}: {e}")
                
                # Try to get example commands from Kali tools database
                for tool_name in relevant_tools[:2]:  # Get examples from top 2 tools
                    try:
                        tool_info = extensive_kali_tools.get_tool_info(tool_name)
                        if tool_info and "examples" in tool_info:
                            examples = tool_info["examples"]
                            for example in examples:
                                if "command" in example:
                                    suggested_commands.append(example["command"])
                    except Exception as e:
                        print(f"Warning: Error getting tool info for {tool_name}: {e}")
            except Exception as e:
                print(f"Warning: Error suggesting alternative commands: {e}")
        
        # If no suggestions from Kali tools, add some generic ones
        if not suggested_commands:
            if "nmap" in failed_cmd:
                suggested_commands = [f"sudo nmap -sS -p- {variables.get('target', 'TARGET_IP')}"]
            elif "hydra" in failed_cmd:
                suggested_commands = [f"hydra -L users.txt -P passwords.txt {variables.get('target', 'TARGET_IP')} ssh"]
            else:
                suggested_commands = [f"sudo {failed_cmd}"]
        
        return suggested_commands

    def generate_next_command(self, request: str, previous_command: str, previous_output: str, variables: Dict[str, str]) -> str:
        """Generate the next command based on the request and previous output."""
        # First use extensive_kali_tools if available
        if extensive_kali_tools and self.kali_tools:
            try:
                # Get all available Kali tools
                all_kali_tools = self.kali_tools
                
                # Extract keywords from request
                keywords = request.lower().split()
                
                # Get relevant categories
                relevant_categories = []
                for category in self.kali_categories:
                    if any(keyword in category.lower() for keyword in keywords):
                        relevant_categories.append(category)
                
                # Get tools from relevant categories
                relevant_tools = []
                for category in relevant_categories:
                    try:
                        category_tools = extensive_kali_tools.get_tools_by_category(category)
                        if category_tools and len(category_tools) > 0:
                            # Get up to 3 tools from each category
                            relevant_tools.extend([tool["name"] for tool in category_tools[:3]])
                    except Exception as e:
                        print(f"Warning: Error getting tools for category {category}: {e}")
                
                # If we found relevant tools, use them
                if relevant_tools:
                    # Get the first tool's example command
                    tool_info = extensive_kali_tools.get_tool_info(relevant_tools[0])
                    if tool_info and "examples" in tool_info and tool_info["examples"]:
                        command = tool_info["examples"][0]["command"]
                        # Ensure command starts with sudo if it doesn't already
                        if not command.strip().startswith("sudo "):
                            return f"sudo {command}"
                        return command
            except Exception as e:
                print(f"Warning: Error generating command from Kali tools: {e}")
        
        # Fallback to default command generation if Kali tools failed
        return f"sudo {request}"
    
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
        
        # Handle sudo password or permissions errors
        if "sudo: 3 incorrect password attempts" in stderr or "sudo: incorrect password" in stderr:
            # This happens when password prompts occur and fail
            if RICH_AVAILABLE:
                console.print("[bold red]Sudo password authentication failed.[/]")
                console.print("[bold yellow]Attempting to run the command without sudo.[/]")
            else:
                print("\033[1;31m[!] Sudo password authentication failed.\033[0m")
                print("\033[1;33m[*] Attempting to run the command without sudo.\033[0m")
            
            # Remove sudo from the command
            if command.strip().startswith("sudo "):
                fixed_command = command.replace("sudo ", "", 1)
                suggestion = "Running the command without sudo to avoid password prompts."
                
                # If this would set use_sudo to False globally
                self.use_sudo = False
                return fixed_command, suggestion, variables
        
        # Handle permission issues
        elif "permission denied" in stderr.lower() or "privileges" in stderr.lower():
            # Permission issue
            if self.use_sudo:
                fixed_command = "sudo " + command if not command.startswith("sudo ") else command
                suggestion = "This command requires elevated privileges. Added sudo."
            else:
                # If sudo is disabled, suggest running as user
                suggestion = "Permission denied. This command might require elevated privileges, but sudo is disabled."
                
                # Suggest alternative approaches for common permission issues
                if "cannot open" in stderr.lower() and ("/dev/" in command or "/proc/" in command or "/sys/" in command):
                    suggestion += " Consider using alternative tools that don't require system access."
                elif "device or resource busy" in stderr.lower():
                    suggestion += " The resource might be in use by another process."
                
                fixed_command = command  # Keep command unchanged if sudo is disabled
        
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
    
    def execute_command(self, command, shell=True):
        """Execute a shell command and return the output.
        
        Args:
            command (str): The command to execute
            shell (bool): Whether to execute the command through the shell
            
        Returns:
            tuple: (stdout, stderr, exit_code)
        """
        if not command:
            return "", "", 0
            
        # Handle sudo requirements but preserve explicit sudo if user already included it
        if not command.startswith("sudo "):
            command = self.handle_sudo(command)
        
        # For sudo commands, run them interactively to allow password entry
        if command.startswith("sudo "):
            try:
                # Use a separate process to allow interactive password prompts
                print(f"\nExecuting: {command}")
                process = subprocess.run(
                    command,
                    shell=shell,
                    text=True,
                    capture_output=False  # Don't capture output to allow terminal interaction
                )
                return "", "", process.returncode
            except Exception as e:
                return "", str(e), 1
        else:
            # For non-sudo commands, capture output as before
            try:
                process = subprocess.Popen(
                    command,
                    shell=shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate()
                return stdout, stderr, process.returncode
            except Exception as e:
                return "", str(e), 1
    
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
                    
                    fixed_cmd = f"sudo gpg2john {gpg_file} > hash.txt"
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
                        
        # Special handling for GPG decryption failures 
        if "gpg: gcry_kdf_derive failed" in result["stderr"] or "gpg: decryption failed" in result["stderr"] or ("gpg" in cmd and "encrypted" in result["stderr"]):
            if RICH_AVAILABLE:
                console.print("[bold yellow]GPG decryption failed - the file is encrypted with a password.[/]")
                console.print("[bold cyan]Switching to John the Ripper for password cracking...[/]")
            else:
                print("\033[1;33m[*] GPG decryption failed - the file is encrypted with a password.\033[0m")
                print("\033[1;36m[*] Switching to John the Ripper for password cracking...\033[0m")
            
            # Extract the GPG file path from the command
            gpg_file_match = re.search(r'(/[^\s]+\.gpg|\w+\.gpg|/home/[^\s]+\.gpg)', cmd)
            gpg_file = gpg_file_match.group(0) if gpg_file_match else None
            
            if not gpg_file and 'request' in variables:
                # Try to extract the filename from the request with regex
                matches = re.findall(r'([^\s]+\.(?:tar\.)?gpg)', str(variables['request']))
                if matches:
                    gpg_file = matches[0]
            
            if gpg_file:
                # Properly quote the file path if it contains spaces
                if ' ' in gpg_file and not (gpg_file.startswith('"') or gpg_file.startswith("'")):
                    gpg_file = f'"{gpg_file}"'
                
                # Create a workflow of commands for John the Ripper
                fixed_cmd = f"sudo gpg2john {gpg_file} > hash.txt"
                suggestion = "Using John the Ripper workflow to crack the GPG password"
                
                if RICH_AVAILABLE:
                    retry = Confirm.ask(f"Try cracking the password with John the Ripper?", default=True)
                else:
                    print(f"\033[1;33m[*] Suggested fix: Use John the Ripper to crack the password\033[0m")
                    retry = input("\033[1;35m[?] Try this approach? (y/n): \033[0m").strip().lower()
                    retry = retry == "" or retry == "y"
                
                if retry:
                    # Execute gpg2john first
                    result = self.execute_command(fixed_cmd, updated_vars)
                    self.display_result(result, command_index, total_commands)
                    
                    # If successful, run john on the hash file
                    if result["exit_code"] == 0:
                        john_cmd = "sudo john hash.txt"
                        if RICH_AVAILABLE:
                            console.print("[bold green]Hash extraction successful. Running John the Ripper to crack the password...[/]")
                        else:
                            print("\033[1;32m[*] Hash extraction successful. Running John the Ripper to crack the password...\033[0m")
                        
                        result = self.execute_command(john_cmd, updated_vars)
                        self.display_result(result, command_index, total_commands)
                        
                        # Show the results
                        show_cmd = "sudo john --show hash.txt"
                        if RICH_AVAILABLE:
                            console.print("[bold green]Displaying cracked password(s)...[/]")
                        else:
                            print("\033[1;32m[*] Displaying cracked password(s)...\033[0m")
                        
                        result = self.execute_command(show_cmd, updated_vars)
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
            # Special handling for GPG password decryption
            if ".gpg" in cmd and ("decrypt" in variables.get('request', '') or "password" in variables.get('request', '')):
                gpg_file_match = re.search(r'(/[^\s]+\.gpg|\w+\.gpg|/home/[^\s]+\.gpg)', cmd)
                gpg_file = gpg_file_match.group(0) if gpg_file_match else None
                
                if gpg_file:
                    alt_cmd = f"sudo gpg2john {gpg_file} > hash.txt && sudo john hash.txt && sudo john --show hash.txt"
                    alt_explanation = "Extracting the password hash from the GPG file and attempting to crack it with John the Ripper"
            
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
            # Preserve the command as-is, including sudo if present
            command = commands[0]
            
            if self.display_single_command(command, explanations[0], 1, len(commands)):
                return [command], self.adaptive_mode
        
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
        if extensive_kali_tools and extensive_kali_tools.KALI_TOOLS_AVAILABLE:
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
                        category_tools = tools_registry.get_tools_by_category(category)
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
            elif any(term in request.lower() for term in ["password", "decrypt", "crack"]):
                # Check if it's for a GPG file
                gpg_file = None
                for word in request.split():
                    if ".gpg" in word:
                        gpg_file = word
                        break
                
                if gpg_file or "gpg" in request.lower():
                    # If no specific GPG file is mentioned, use a placeholder
                    if not gpg_file:
                        gpg_file = "/path/to/file.gpg"
                    
                    suggested_commands = [
                        f"sudo gpg2john {gpg_file} > hash.txt",
                        "sudo john hash.txt",
                        "sudo john --show hash.txt"
                    ]
                else:
                    # General password cracking guidance
                    suggested_commands = [
                        "sudo john --format=raw-md5 hash.txt",
                        "sudo hashcat -m 0 hash.txt /usr/share/wordlists/rockyou.txt"
                    ]
            elif extensive_kali_tools and extensive_kali_tools.KALI_TOOLS_AVAILABLE:
                # Try to get example commands from Kali tools database
                for tool_name in relevant_tools[:2]:  # Get examples from top 2 tools
                    try:
                        tool_info = tools_registry.get_tool_info(tool_name)
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

    def build_context(self, request, placeholders, session_context=None):
        """Build context for command generation based on user request.
        
        Args:
            request (str): The user's request
            placeholders (dict): Dictionary of placeholders extracted from request
            session_context (dict): Dictionary of session context variables
            
        Returns:
            dict: Context for command generation
        """
        # Initialize context with core information
        context = {
            "request": request,
            "placeholders": placeholders,
            "command_type": "shell",
            "os": "kali",
            "use_sudo": self.use_sudo
        }
        
        # Add session context if available
        if session_context:
            context.update(session_context)
        
        # Get relevant Kali tools directly from extensive_kali_tools module
        # instead of using the context library
        kali_tools = []
        if extensive_kali_tools:
            # Get all tools that might be relevant to the request
            kali_tools = self.get_relevant_kali_tools(request)
            
            if kali_tools:
                # Enhanced tool information with examples from extensive_kali_tools
                enhanced_tools = []
                for tool in kali_tools:
                    # Get detailed tool info including examples and common usage
                    tool_info = extensive_kali_tools.get_tool_info(tool['name'])
                    if tool_info:
                        # Add examples from the tools to make commands more accurate
                        examples = []
                        if 'examples' in tool_info:
                            for example in tool_info['examples'][:3]:  # Limit to 3 examples
                                examples.append({
                                    'description': example['description'],
                                    'command': example['command']
                                })
                        
                        enhanced_tool = {
                            'name': tool_info['name'],
                            'description': tool_info['description'],
                            'common_usage': tool_info.get('common_usage', ''),
                            'examples': examples
                        }
                        enhanced_tools.append(enhanced_tool)
                
                context["kali_tools"] = enhanced_tools
        
        # Instead of using the context library, gather relevant command examples 
        # directly from the Kali tools based on request type
        examples = []
        
        # Detect specific security tasks from the request
        request_lower = request.lower()
        
        # Match request to categories of tools in extensive_kali_tools
        categories_to_check = []
        
        # Map common request keywords to Kali tool categories
        keyword_category_map = {
            "scan": "Information Gathering",
            "enumerate": "Information Gathering",
            "recon": "Information Gathering",
            "information": "Information Gathering",
            "gather": "Information Gathering",
            "vulnerability": "Vulnerability Analysis",
            "vuln": "Vulnerability Analysis",
            "web": "Web Application Analysis",
            "sql": "Web Application Analysis",
            "injection": "Web Application Analysis",
            "password": "Password Attacks", 
            "crack": "Password Attacks",
            "brute": "Password Attacks",
            "wireless": "Wireless Attacks",
            "wifi": "Wireless Attacks",
            "exploit": "Exploitation Tools",
            "reverse": "Reverse Engineering",
            "forensic": "Forensics",
            "sniff": "Sniffing & Spoofing",
            "spoof": "Sniffing & Spoofing",
            "post": "Post Exploitation",
            "social": "Social Engineering Tools",
            "crypto": "Cryptography",
            "database": "Database Assessment",
            "bluetooth": "Bluetooth Attacks"
        }
        
        # Check for matches in the request
        for keyword, category in keyword_category_map.items():
            if keyword in request_lower and category not in categories_to_check:
                categories_to_check.append(category)
        
        # If no specific categories matched, use these default categories
        if not categories_to_check:
            categories_to_check = ["Information Gathering", "Vulnerability Analysis", "Password Attacks"]
        
        # Get tool examples from each relevant category
        if extensive_kali_tools:
            for category in categories_to_check:
                category_tools = extensive_kali_tools.get_tools_by_category(category)
                for tool in category_tools[:2]:  # Limit to 2 tools per category
                    tool_info = extensive_kali_tools.get_tool_info(tool['name'])
                    if tool_info and 'examples' in tool_info:
                        for example in tool_info['examples'][:2]:  # Limit to 2 examples per tool
                            examples.append(f"{tool_info['name']}: {example['command']} - {example['description']}")
        
        # Add examples to context
        context["examples"] = examples
        
        # Handle special case for GPG password cracking
        if "crack" in request_lower and ("gpg" in request_lower or ".gpg" in request_lower):
            gpg_examples = [
                "gpg2john file.gpg > hash.txt - Extract hash from GPG file",
                "john hash.txt - Attempt to crack with John the Ripper",
                "john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt - Use rockyou wordlist",
                "john --show hash.txt - Show cracked passwords"
            ]
            context["examples"] = gpg_examples + context["examples"]
        
        return context

    def extract_placeholders(self, text):
        """Extract command placeholders like {ip}, {file}, etc. from text.
        
        Args:
            text (str): The text to extract placeholders from
            
        Returns:
            dict: Dictionary of placeholders and their values
        """
        placeholders = {}
        
        # Extract IP addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ip_addresses = re.findall(ip_pattern, text)
        if ip_addresses:
            placeholders['ip'] = ip_addresses[0]
            if len(ip_addresses) > 1:
                placeholders['target_ip'] = ip_addresses[1]
        
        # Extract file paths 
        file_paths = self.extract_file_paths(text)
        if file_paths:
            placeholders['file'] = file_paths[0]
            if len(file_paths) > 1:
                placeholders['output_file'] = file_paths[1]
        
        # Extract ports
        port_pattern = r'\b(port\s+(\d+))|(\b\d{1,5}\/(?:tcp|udp))|:(\d{1,5})\b'
        port_matches = re.findall(port_pattern, text, re.IGNORECASE)
        if port_matches:
            # Extract the port number from whichever group matched
            for match in port_matches:
                # Find the first non-empty group which would be the port
                for group in match[1:]:
                    if group:
                        # Clean up port number to remove /tcp or /udp if present
                        port = group.split('/')[0] if '/' in group else group
                        placeholders['port'] = port
                        break
                if 'port' in placeholders:
                    break
        
        # Extract interfaces
        network_interfaces = self.get_network_interfaces()
        for interface in network_interfaces:
            if interface in text.lower():
                placeholders['interface'] = interface
                break
        
        # Add local IP as a placeholder
        placeholders['local_ip'] = self.get_local_ip()
        
        return placeholders

    def get_response(self, context):
        """Generate a response based on context using the LLM.
        
        Args:
            context (dict): Context for generating the response
            
        Returns:
            str: The generated response
        """
        # Build prompt from context
        prompt = self.build_prompt(context)
        
        # Use LLM to generate response
        response = self.generate_llm_response(prompt)
        
        return response
    
    def build_prompt(self, context):
        """Build a prompt for the LLM based on context.
        
        Args:
            context (dict): Context for building the prompt
            
        Returns:
            str: The prompt for the LLM
        """
        # Extract information from context
        request = context["request"]
        examples = context.get("examples", [])
        
        # Build prompt with clear instructions
        prompt = f"""Generate precise Kali Linux commands to: {request}

I need specific command-line instructions that will work on Kali Linux. 
Include exact syntax and all necessary parameters.
Return the commands that will help me accomplish this task effectively.

"""
        
        # Add examples if available
        if examples:
            prompt += "Related command examples:\n"
            for example in examples[:5]:  # Limit to 5 examples to keep prompt size reasonable
                prompt += f"- {example}\n"
        
        # Add detailed tool guidance if available
        if "kali_tools" in context:
            tools = context["kali_tools"]
            prompt += "\nRelevant Kali tools with usage examples:\n"
            
            for tool in tools:
                prompt += f"\n{tool['name']}: {tool['description']}\n"
                prompt += f"Common usage: {tool.get('common_usage', '')}\n"
                
                if 'examples' in tool and tool['examples']:
                    prompt += "Examples:\n"
                    for example in tool['examples']:
                        prompt += f"  - {example['command']} ({example['description']})\n"
        
        # Add specific instructions for handling file paths and complex commands
        prompt += """
Important notes:
1. Use absolute paths for files and directories
2. Include all necessary flags and parameters
3. Provide commands that can be run directly in the terminal
4. For commands requiring sudo, include the sudo prefix
5. For multi-step processes, provide each command separately

Please ensure the commands are accurate and follow Kali Linux best practices.
"""
        
        return prompt
    
    def extract_commands(self, response):
        """Extract commands from the model response.
        
        Args:
            response (str): The model's response text
            
        Returns:
            tuple: (commands, explanations)
        """
        commands = []
        explanations = []
        
        # Ensure response is a string
        if isinstance(response, dict):
            # If response is already a dictionary, extract commands directly
            if "commands" in response:
                commands = response["commands"]
                explanations = response.get("explanations", [""] * len(commands))
                return commands, explanations
            # Convert dict to string if it doesn't have commands
            response = str(response)
        
        try:
            # Try to extract as JSON
            data = self.extract_json_from_response(response)
            if data and "commands" in data:
                commands = data["commands"]
                if "explanations" in data:
                    explanations = data["explanations"]
                else:
                    explanations = [""] * len(commands)
                return commands, explanations
        except:
            pass
            
        try:
            # Look for ```bash or ```shell code blocks
            import re
            code_blocks = re.findall(r'```(?:bash|shell)?\s*([\s\S]*?)```', response)
            if code_blocks:
                for block in code_blocks:
                    # Extract non-empty lines that don't start with # (comments)
                    lines = [line.strip() for line in block.split('\n') if line.strip() and not line.strip().startswith('#')]
                    if lines:
                        commands.extend(lines)
                        explanations.extend([""] * len(lines))
                return commands, explanations
        except:
            pass
            
        try:
            # Look for command: patterns or numbered lists
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith(("```", "#", "-", "*", ">")):
                    if ":" in line:
                        parts = line.split(":", 1)
                        command = parts[1].strip()
                        explanation = parts[0].strip()
                        commands.append(command)
                        explanations.append(explanation)
                    else:
                        commands.append(line)
                        explanations.append("")
        except Exception as e:
            pass
            
        # If all extraction methods fail, return the response as a single command
        if not commands:
            if isinstance(response, str):
                commands = [response.split('\n')[0]]
            else:
                commands = [str(response)]
            explanations = ["Extracted command"]
        
        return commands, explanations
    
    def process_request(self, request, session_context=None):
        """Process a user request and generate a response."""
        # Extract command placeholders from request
        placeholders = self.extract_placeholders(request)
        
        # Initialize context
        if session_context is None:
            session_context = {}
            
        # Check for special request types
        if "MAC" in request.upper() and "CHANGE" in request.upper():
            return self.handle_mac_address_change_request(request)
            
        if "PASSWORD" in request.upper() and any(word in request.upper() for word in ["GENERATE", "CREATE", "MAKE"]):
            return self.handle_password_request(request)
            
        # Handle GPG password cracking requests specifically
        if "CRACK" in request.upper() and any(word in request.upper() for word in ["GPG", ".GPG"]):
            return self.handle_gpg_crack_request(request)
        
        # Build context for command generation
        context = self.build_context(request, placeholders, session_context)
        
        # Get response from AI
        response = self.get_response(context)
        
        # Extract and format commands
        commands, explanations = self.extract_commands(response)
        
        # If adaptive mode is enabled and there's at least one command, execute the first one
        if self.adaptive_mode and commands:
            selected_command, self.adaptive_mode = self.interactive_command_selection(commands, explanations)
            
            if selected_command:
                stdout, stderr, return_code = self.execute_command(selected_command)
                
                # Process and display the results
                result_display = self.format_command_results(selected_command, stdout, stderr, return_code)
                
                # Update response with results
                response += "\n\n" + result_display
        
        # Set up Kali tools recommendation based on request
        if "kali_tools" in context:
            kali_recs = []
            for tool in context["kali_tools"]:
                kali_recs.append(f"- {tool['name']}: {tool['description']}")
            
            if kali_recs:
                response += "\n\nRecommended Kali Tools:\n" + "\n".join(kali_recs)
        
        return response
        
    def handle_gpg_crack_request(self, request):
        """Handle requests to crack GPG file passwords.
        
        Args:
            request (str): The user's request
            
        Returns:
            str: The response with GPG password cracking instructions
        """
        # Extract file path from request
        file_paths = self.extract_file_paths(request)
        gpg_file = file_paths[0] if file_paths else "/home/kali/Downloads/wa.gpg"
        
        # Ensure the path is properly quoted to handle spaces in filenames
        gpg_file_quoted = f'"{gpg_file}"'
        
        # Generate an output file path for the hash
        hash_file = "/tmp/gpg_hash.txt"
        
        # Generate commands for GPG password cracking
        commands = [
            f"gpg2john {gpg_file_quoted} > {hash_file}",
            f"john {hash_file}",
            f"john --show {hash_file}",
            "# If the above doesn't work, try with the standard wordlist",
            f"john --wordlist=/usr/share/wordlists/rockyou.txt {hash_file}",
            "# For more advanced cracking, try with rules",
            f"john --rules --wordlist=/usr/share/wordlists/rockyou.txt {hash_file}",
            "# After cracking the password, you can decrypt the file",
            f"gpg --decrypt {gpg_file_quoted}"
        ]
        
        explanations = [
            "Extract hash from GPG file",
            "Attempt to crack the password with default settings",
            "Show any cracked passwords",
            "Alternative approach comment",
            "Try cracking with the rockyou wordlist",
            "Advanced option comment",
            "Use word mangling rules with the wordlist for more complex passwords",
            "Decryption comment",
            "Decrypt the file using the cracked password"
        ]
        
        # Format response
        response = f"""## GPG Password Cracking Process

To crack the password for the GPG file **{gpg_file}**, follow these steps:

"""
        # Add the commands with explanations
        current_step = 1
        for i, (cmd, exp) in enumerate(zip(commands, explanations)):
            # Skip comments in the command list
            if cmd.startswith("#"):
                response += f"\n**{exp}**\n"
                continue
            response += f"{current_step}. {exp}:\n   ```\n   {cmd}\n   ```\n\n"
            current_step += 1
        
        # Add additional information about the tools
        response += """
### Notes:
- GPG password cracking can be time-consuming depending on password complexity
- John the Ripper will automatically select optimal settings based on your CPU
- For stronger passwords, consider creating a custom wordlist based on target information
- If the standard methods fail, try hashcat with GPU acceleration:
  ```
  hashcat -m 16700 -a 0 hash.txt /usr/share/wordlists/rockyou.txt
  ```

John the Ripper is automatically installed on Kali Linux. These commands will work directly without additional setup.
"""
        
        return response

    def handle_sudo(self, command):
        """Determine whether to apply or remove the sudo prefix.
        
        Args:
            command: The command to check
            
        Returns:
            str: Command with appropriate sudo prefix
        """
        if not command:
            return command
            
        command = command.strip()
        
        # If the command already has sudo, respect the user's intention
        if command.startswith("sudo "):
            return command
            
        # Common commands that typically don't need sudo
        safe_commands = [
            "ls", "cd", "pwd", "echo", "cat", "grep", "find", "which", "whereis",
            "man", "info", "help", "history", "clear", "exit", "logout", "whoami",
            "id", "hostname", "uname", "ifconfig", "ip", "netstat", "ss", "ps",
            "top", "htop", "free", "df", "du", "date", "cal", "uptime", "w", "finger",
            "wget", "curl", "ping", "traceroute", "dig", "nslookup", "whois",
            "ssh", "scp", "sftp", "telnet", "nc", "ncat", "python", "python3", "pip", "pip3"
        ]
        
        # Check if the command starts with any of the safe commands
        command_parts = command.split()
        if not command_parts:
            return command
            
        base_command = command_parts[0]
        
        # If self.use_sudo is True and the command isn't a safe command, apply sudo
        if self.use_sudo and base_command not in safe_commands:
            return f"sudo {command}"
            
        return command

    def handle_mac_address_change_request(self, request):
        """Handle requests to change MAC address.
        
        Args:
            request (str): The user's request
            
        Returns:
            str: The response with MAC address changing instructions
        """
        # Extract network interface from request or use default
        network_interfaces = self.get_network_interfaces()
        interface = None
        
        # Try to find the interface mentioned in the request
        for iface in network_interfaces:
            if iface in request:
                interface = iface
                break
        
        # If no interface was found, use the first one or a default
        if not interface:
            if network_interfaces:
                interface = network_interfaces[0]
            else:
                interface = "eth0"  # Default fallback for Kali Linux
        
        # Generate commands for MAC address changing
        commands = [
            f"ifconfig {interface} down",
            f"macchanger -r {interface}",
            f"ifconfig {interface} up",
            f"macchanger -s {interface}"
        ]
        
        explanations = [
            "Disable the network interface",
            "Change the MAC address to a random one",
            "Enable the network interface again",
            "Verify the new MAC address"
        ]
        
        # Format response
        response = f"## MAC Address Change for {interface}\n\n"
        response += "To change the MAC address on your Kali Linux system, follow these steps:\n\n"
        
        for i, (cmd, exp) in enumerate(zip(commands, explanations)):
            response += f"{i+1}. {exp}:\n   ```\n   {cmd}\n   ```\n\n"
        
        response += """
### Notes:
- You may need root privileges to change MAC addresses
- Some network interfaces may require you to disconnect from networks first
- If the above commands don't work, try using `ip` instead of `ifconfig`:
  ```
  ip link set dev eth0 down
  ip link set dev eth0 address XX:XX:XX:XX:XX:XX
  ip link set dev eth0 up
  ```
"""
        
        return response

    def handle_password_request(self, request):
        """Handle requests to generate secure passwords.
        
        Args:
            request (str): The user's request
            
        Returns:
            str: The response with password generation instructions
        """
        # Determine password complexity from request
        length = 12  # Default length
        
        # Check if a specific length was requested
        import re
        length_match = re.search(r'(\d+)\s*characters?', request)
        if length_match:
            length = int(length_match.group(1))
            if length < 8:
                length = 8  # Minimum recommended length
            elif length > 64:
                length = 64  # Reasonable maximum
        
        # Generate commands for password generation
        commands = [
            f"openssl rand -base64 {length}",
            f"tr -dc 'A-Za-z0-9!@#$%^&*()' < /dev/urandom | head -c {length}",
            f"pwgen -s {length} 1",
            f"dd if=/dev/urandom bs=1 count={length*2} 2>/dev/null | tr -dc 'a-zA-Z0-9!@#$%^&*()_+{{}}|:<>?=' | head -c {length}"
        ]
        
        explanations = [
            "Generate a secure password with OpenSSL",
            "Create a random password using /dev/urandom",
            "Use pwgen for a secure, easy-to-remember password",
            "Generate a highly random password with complex characters"
        ]
        
        # Format response
        response = f"## Secure Password Generation\n\n"
        response += f"To generate a secure password of {length} characters on Kali Linux, you can use any of these commands:\n\n"
        
        for i, (cmd, exp) in enumerate(zip(commands, explanations)):
            response += f"{i+1}. {exp}:\n   ```\n   {cmd}\n   ```\n\n"
        
        response += """
### Password Storage Best Practices:
- Use a password manager like KeePassXC to store complex passwords
- Don't reuse passwords across different services
- For system passwords, consider using:
  ```
  sudo passwd username
  ```
  and paste a generated secure password
"""
        
        return response

    def format_command_results(self, command, stdout, stderr, return_code):
        """Format command execution results for display.
        
        Args:
            command (str): The executed command
            stdout (str): The standard output
            stderr (str): The standard error
            return_code (int): The command return code
            
        Returns:
            str: Formatted result text
        """
        result = f"## Command Execution Results\n\n"
        result += f"Command: `{command}`\n\n"
        
        if return_code == 0:
            result += "### Output:\n"
            if stdout:
                # Limit output to reasonable size
                if len(stdout) > 2000:
                    stdout = stdout[:2000] + "...\n[Output truncated]"
                result += f"```\n{stdout}\n```\n"
            else:
                result += "Command executed successfully with no output.\n"
        else:
            result += f"### Error (Exit Code: {return_code}):\n"
            if stderr:
                result += f"```\n{stderr}\n```\n"
            else:
                result += "Command failed without error message.\n"
                
            # Try to provide suggestions
            suggestions = self.suggest_alternative_command(command, stderr, {})
            if suggestions:
                result += "\n### Suggestions:\n"
                for i, suggestion in enumerate(suggestions):
                    result += f"{i+1}. Try: `{suggestion}`\n"
        
        return result

    def format_commands_list(self, commands, explanations):
        """Format a list of commands and explanations into a readable response.
        
        Args:
            commands (list): List of commands
            explanations (list): List of explanations for each command
            
        Returns:
            str: Formatted response with commands and explanations
        """
        response = "## Recommended Commands\n\n"
        
        for i, (cmd, exp) in enumerate(zip(commands, explanations)):
            response += f"{i+1}. {exp}:\n   ```\n   {cmd}\n   ```\n\n"
        
        return response

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
    if ascii_art:
        ascii_art.display_ascii_art()
    
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