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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger('PAW')

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
script_dir = os.path.dirname(os.path.realpath(__file__))
if os.path.exists(os.path.join(script_dir, 'tools_registry.py')):
    # For local development - use current directory
    sys.path.append(script_dir)
else:
    # For system installations - use installed lib directory
    sys.path.append('/usr/local/share/paw')
    sys.path.append('/usr/local/share/paw/tools')
    # Also add the script directory itself
    sys.path.append(script_dir)

try:
    import tools_registry
    from tools_registry import get_tools_registry
    # Import functions instead of direct data
    try:
        from extensive_kali_tools import (
            get_all_kali_tools, 
            get_tool_categories, 
            get_tools_by_category,
            get_tool_info as get_external_tool_info
        )
    except ImportError:
        logger.warning("extensive_kali_tools module not found. Limited tool information will be available.")
        
        # Define minimal fallback functions for when extensive_kali_tools is not available
        def get_all_kali_tools():
            """Fallback function to return a minimal set of common Kali tools."""
            return [
                # Basic set of the most common tools - minimized for readability
                {"name": "nmap", "category": "Information Gathering", "description": "Network scanner"},
                {"name": "nikto", "category": "Web Application Analysis", "description": "Web server scanner"},
                {"name": "dirb", "category": "Web Application Analysis", "description": "Web content scanner"},
                {"name": "hydra", "category": "Password Attacks", "description": "Password cracking tool"}
            ]
            
        def get_tool_categories():
            """Fallback function to return basic tool categories."""
            return [
                "Information Gathering",
                "Vulnerability Analysis",
                "Web Application Analysis",
                "Password Attacks"
            ]
            
        def get_tools_by_category(category):
            """Fallback function to return tools in a specific category."""
            tools = get_all_kali_tools()
            return [tool for tool in tools if tool["category"] == category]
            
        def get_external_tool_info(tool_name):
            """Fallback function to return information about a specific tool."""
            tools = get_all_kali_tools()
            for tool in tools:
                if tool["name"].lower() == tool_name.lower():
                    return tool
            return None
except ImportError as e:
    print(f"Error: Could not import PAW modules: {e}")
    print("Make sure PAW is installed correctly and this script is in the correct directory.")
    print("You can install PAW by running: bash install.sh")
    sys.exit(1)

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
        
        # Cache for tool information
        self.tool_info_cache = {}
        
        # Initialize our tool database by calling the external module
        self.all_kali_tools = get_all_kali_tools()
        self.tool_categories = get_tool_categories()
    
    def get_relevant_tools_for_request(self, request):
        """Dynamically extract relevant tool information based on the user request"""
        # Use a cache to prevent regenerating for the same request
        if request in self.tool_info_cache:
            return self.tool_info_cache[request]
            
        relevant_tools = []
        request_lower = request.lower()
        
        # Keywords that map to categories
        category_keywords = {
            "scan": ["Information Gathering", "Vulnerability Analysis"],
            "network": ["Information Gathering", "Sniffing & Spoofing"],
            "web": ["Web Application Analysis", "Information Gathering"],
            "vulnerability": ["Vulnerability Analysis"],
            "exploit": ["Exploitation Tools"],
            "password": ["Password Attacks"],
            "wireless": ["Wireless Attacks"],
            "reverse": ["Reverse Engineering"],
            "forensic": ["Forensics"],
            "database": ["Database Assessment"],
            "recon": ["Information Gathering", "Reconnaissance"],
            "brute": ["Password Attacks"],
            "crack": ["Password Attacks"],
            "sniff": ["Sniffing & Spoofing"],
            "spoof": ["Sniffing & Spoofing"],
            "footprint": ["Information Gathering"],
            "enumerate": ["Information Gathering"],
            "social": ["Social Engineering Tools"]
        }
        
        # Common tools to always include
        important_tools = ["nmap", "hydra", "sqlmap", "metasploit", "dirb", "nikto", "wireshark", "hashcat"]
        
        # Find matching categories based on request keywords
        matching_categories = set()
        for keyword, categories in category_keywords.items():
            if keyword in request_lower:
                for category in categories:
                    matching_categories.add(category)
        
        # If no categories match, include a default set
        if not matching_categories:
            matching_categories = {"Information Gathering", "Vulnerability Analysis"}
            
        # Select tools from matching categories
        tools_added = set()
        for tool in self.all_kali_tools:
            # Always include important tools
            if tool["name"] in important_tools and tool["name"] not in tools_added:
                relevant_tools.append(tool)
                tools_added.add(tool["name"])
                continue
                
            # Include tools from matching categories
            if tool["category"] in matching_categories and tool["name"] not in tools_added:
                relevant_tools.append(tool)
                tools_added.add(tool["name"])
                
            # Include tools specifically mentioned in the request
            if tool["name"] in request_lower and tool["name"] not in tools_added:
                relevant_tools.append(tool)
                tools_added.add(tool["name"])
                
        # Cache the result
        self.tool_info_cache[request] = relevant_tools
        return relevant_tools
    
    def format_tools_for_context(self, tools):
        """Format tool information for inclusion in the LLM context"""
        if not tools:
            return "No specific tools identified for this request."
            
        formatted_text = "Available Kali Linux Tools for this task:\n\n"
        
        # Group tools by category
        tools_by_category = {}
        for tool in tools:
            category = tool["category"]
            if category not in tools_by_category:
                tools_by_category[category] = []
            tools_by_category[category].append(tool)
            
        # Format each category and its tools
        for category, category_tools in tools_by_category.items():
            formatted_text += f"{category}:\n"
            for tool in category_tools:
                formatted_text += f"  - {tool['name']}: {tool['description']}\n"
                
                # Add example commands if available
                if "examples" in tool and tool["examples"]:
                    formatted_text += "    Examples:\n"
                    # Limit to 3 examples to keep context manageable
                    for i, example in enumerate(tool["examples"][:3]):
                        formatted_text += f"      * {example['description']}: {example['command']}\n"
                formatted_text += "\n"
        
        return formatted_text
    
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
                            "system": "You are PAW, a Prompt Assisted Workflow tool for Kali Linux. You can access detailed information about security tools by using the special syntax: [TOOL:tool_name] or [CATEGORY:category_name]. Output JSON with {\"plan\": [string], \"commands\": [string], \"explanation\": [string]}. Be concise and focus on practical commands.",
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
                        "system": "You are PAW, a Prompt Assisted Workflow tool for Kali Linux. You can access detailed information about security tools by using the special syntax: [TOOL:tool_name] or [CATEGORY:category_name]. Output JSON with {\"plan\": [string], \"commands\": [string], \"explanation\": [string]}. Be concise and focus on practical commands.",
                        "stream": False,
                    },
                    timeout=LLM_TIMEOUT
                )
            
            if response.status_code != 200:
                logger.error(f"Error from Ollama: {response.text}")
                return {"error": f"Ollama API error: {response.status_code}"}
            
            result = response.json()
            response_text = result.get("response", "")
            
            # Process any tool queries in the response
            processed_response = self.process_tool_queries(response_text)
            
            # If tool queries were found, send the processed response back to the LLM
            if processed_response != response_text:
                logger.info("Tool queries detected, sending follow-up request")
                return self.generate_llm_response(processed_response)
            
            return self.extract_json_from_response(response_text)
            
        except httpx.TimeoutException:
            logger.error(f"LLM request timed out after {LLM_TIMEOUT} seconds")
            return {"error": f"LLM request timed out after {LLM_TIMEOUT} seconds. Try setting a longer timeout in /etc/paw/config.ini."}
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return {"error": str(e)}
    
    def process_tool_queries(self, text):
        """Process any tool or category queries in the text and replace with actual tool information."""
        # Check for tool queries using [TOOL:tool_name] syntax
        tool_pattern = r'\[TOOL:(.*?)\]'
        tool_queries = re.findall(tool_pattern, text)
        
        # Check for category queries using [CATEGORY:category_name] syntax
        category_pattern = r'\[CATEGORY:(.*?)\]'
        category_queries = re.findall(category_pattern, text)
        
        # If no queries found, return the original text
        if not tool_queries and not category_queries:
            return text
            
        # Process tool queries
        for tool_name in tool_queries:
            tool_name = tool_name.strip().lower()
            tool_info = self.get_tool_info(tool_name)
            text = text.replace(f"[TOOL:{tool_name}]", tool_info)
            
        # Process category queries
        for category_name in category_queries:
            category_name = category_name.strip()
            category_info = self.get_category_info(category_name)
            text = text.replace(f"[CATEGORY:{category_name}]", category_info)
            
        return text
        
    def get_tool_info(self, tool_name):
        """Get detailed information about a specific tool."""
        # First, try to get tool info from the external module
        tool = get_external_tool_info(tool_name)
        
        if tool:
            tool_info = f"TOOL: {tool['name']} ({tool['category']})\n"
            tool_info += f"DESCRIPTION: {tool['description']}\n"
            
            if "common_usage" in tool:
                tool_info += f"USAGE: {tool['common_usage']}\n"
                
            if "examples" in tool and tool["examples"]:
                tool_info += "EXAMPLES:\n"
                for example in tool["examples"][:5]:  # Limit to 5 examples
                    tool_info += f"- {example['description']}: {example['command']}\n"
                    
            return tool_info
            
        # If tool not found, find similar tools
        similar_tools = []
        for tool in self.all_kali_tools:
            if tool_name in tool["name"].lower() or tool["name"].lower() in tool_name:
                similar_tools.append(tool["name"])
                
        if similar_tools:
            return f"Tool '{tool_name}' not found. Did you mean: {', '.join(similar_tools)}?"
        else:
            return f"Tool '{tool_name}' not found in the database."
            
    def get_category_info(self, category_name):
        """Get information about tools in a specific category."""
        category_info = ""
        
        # Try to find exact category match
        category_match = None
        for category in self.tool_categories:
            if category.lower() == category_name.lower():
                category_match = category
                break
                
        if category_match:
            # Get tools in this category using the external module
            category_tools = get_tools_by_category(category_match)
            
            if category_tools:
                category_info = f"CATEGORY: {category_match}\n"
                category_info += f"Available Tools ({len(category_tools)}):\n"
                
                for tool in category_tools[:10]:  # Limit to 10 tools per category
                    category_info += f"- {tool['name']}: {tool['description']}\n"
                    
                if len(category_tools) > 10:
                    category_info += f"... and {len(category_tools) - 10} more tools\n"
            else:
                category_info = f"No tools found in category '{category_match}'."
        else:
            # If category not found, suggest similar categories
            similar_categories = []
            for category in self.tool_categories:
                if category_name.lower() in category.lower():
                    similar_categories.append(category)
                    
            if similar_categories:
                category_info = f"Category '{category_name}' not found. Did you mean: {', '.join(similar_categories)}?"
            else:
                category_info = f"Category '{category_name}' not found. Available categories: {', '.join(self.tool_categories[:5])}..."
                
        return category_info
    
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
                        if elapsed > 30:  # After 30 seconds, show abort option once
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
                            # Resume progress and don't ask again
                            progress.start()
                            break  # Exit the prompt loop after first check
                        
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

You have access to a comprehensive database of Kali Linux security tools. To look up information about specific tools or categories, use these special commands:
- [TOOL:tool_name] - Get detailed information about a specific tool (e.g., [TOOL:nmap])
- [CATEGORY:category_name] - See available tools in a category (e.g., [CATEGORY:Information Gathering])

IMPORTANT NOTES FOR SCANNING AND SECURITY:
1. Host Status Handling:
   - If host is down/unreachable: Try -Pn flag with nmap or ping sweep first
   - If no response: Consider firewall evasion techniques (-f, -sS, etc.)
   - Always verify target is legitimate and authorized

2. Port Scanning Strategy:
   - Start with basic port scan if no ports known
   - Use service detection (-sV) on open ports
   - Consider timing (-T4) and intensity based on target
   - Use NSE scripts for deeper analysis

3. Command Adaptation:
   - Analyze previous output for errors and warnings
   - Adjust scan intensity if timeouts occur
   - Use variables from previous results (ports, services, etc.)
   - Don't repeat failed approaches

Based on the previous command and its output, generate the next most logical command to continue this workflow.
Respond with a JSON object containing:
{{
  "command": "the next command to run",
  "explanation": "explanation of what this command does and why it's appropriate next"
}}

The command should directly use the values from the previous output when appropriate, not placeholders.
"""
        
        try:
            # Generate response without using a live display
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
        except Exception as e:
            logger.error(f"Error generating next command: {e}")
            return None, None
    
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
            
            # Default to progressive mode (option 4) if already in adaptive/progressive mode
            default_choice = "4" if self.adaptive_mode else "1"
            
            choice = Prompt.ask(
                "Choose an option",
                choices=["1", "2", "3", "4", "5"],
                default=default_choice
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
                # Run progressively, one at a time
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
            
            # Default to progressive mode if already in adaptive/progressive mode
            default_choice = "2" if self.adaptive_mode else "1"
            choice_prompt = f"\033[1;35m[?] Choose an option (1/2/3) [{default_choice}]: \033[0m"
            
            choice_input = input(choice_prompt).strip()
            choice = choice_input if choice_input else default_choice
            
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
        else:
            # Default to adaptive/progressive mode
            self.adaptive_mode = True
            
        # Clean up the request
        request = request.replace('\r', '').strip()
        
        # Generate initial LLM response with tool-querying capability
        context = f"""
As PAW (Prompt Assisted Workflow), analyze this cybersecurity request and provide a plan of action:

REQUEST: {request}

You have access to a comprehensive database of Kali Linux security tools. To look up information about specific tools or categories, use these special commands:
- [TOOL:tool_name] - Get detailed information about a specific tool (e.g., [TOOL:nmap])
- [CATEGORY:category_name] - See available tools in a category (e.g., [CATEGORY:Information Gathering])

Available categories include: Information Gathering, Vulnerability Analysis, Web Application Analysis, 
Database Assessment, Password Attacks, Wireless Attacks, Exploitation Tools, Sniffing & Spoofing, 
Reverse Engineering, and more.

Common tools include: nmap, nikto, dirb, hydra, sqlmap, metasploit, wireshark, aircrack-ng, hashcat, 
john, and many others. You can query for more specific tools as needed.

IMPORTANT SCANNING GUIDELINES:
1. Always start with common ports (1-1024) or specific service ports
2. Use -sS (stealth scan) by default for nmap
3. Add -sV only after finding open ports
4. Use -Pn if host is blocking ping
5. For web services, focus on ports 80,443,8080
6. Use appropriate timing templates (-T4 for most scans)

Design your commands to work sequentially as a workflow, where later commands build on the results of earlier ones.
For commands that need input from previous commands, use placeholders like <target_ip>.

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
        
        # Get initial command and explanation
        commands = response.get("commands", [])
        explanations = response.get("explanation", [""] * len(commands))
        
        if not commands:
            if RICH_AVAILABLE:
                console.print("[bold yellow]No commands were generated for this request.[/]")
            else:
                print("\033[1;33m[!] No commands were generated for this request.\033[0m")
            return
        
        # Display mode indicator
        if RICH_AVAILABLE:
            console.print(Panel(
                "[bold cyan]PROGRESSIVE MODE ACTIVE[/] - Commands will be executed one at a time",
                border_style=self.theme['border_style'],
                padding=(1, 2)
            ))
        else:
            print("\n\033[1;36m[*] PROGRESSIVE MODE ACTIVE - Commands will be executed one at a time\033[0m")
        
        # Execute commands one at a time
        results = []
        variables = {}  # Store variables for command chaining
        command_index = 0
        
        while command_index < len(commands):
            cmd = commands[command_index]
            command_index += 1
            
            if RICH_AVAILABLE:
                console.print(Panel(f"[bold yellow]Command {command_index}:[/] {cmd}", 
                                   title="[bold cyan]Current Command[/]",
                                   border_style=self.theme['border_style']))
            else:
                print(f"\n\033[1;33m[{command_index}] Executing:\033[0m {cmd}")
            
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
                    result = retry_result
                    variables = result["variables"]
            
            # Store the result for summary
            results.append(result)
            
            # Display result
            self.display_result(result, command_index, "?")
            
            # Generate next command based on current result
            if result["exit_code"] == 0:
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