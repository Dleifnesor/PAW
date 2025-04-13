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
CONFIG_PATH = os.path.expanduser("~/.paw/config.ini")
config = configparser.ConfigParser()

if os.path.exists(CONFIG_PATH):
    config.read(CONFIG_PATH)
else:
    logger.error(f"Configuration file not found: {CONFIG_PATH}")
    sys.exit(1)

MODEL = config['DEFAULT'].get('model', 'MartinRizzo/Ayla-Light-v2:12b-q4_K_M')
OLLAMA_HOST = config['DEFAULT'].get('ollama_host', 'http://localhost:11434')
EXPLAIN_COMMANDS = config['DEFAULT'].getboolean('explain_commands', True)
LOG_COMMANDS = config['DEFAULT'].getboolean('log_commands', True)
LOG_DIRECTORY = os.path.expanduser(config['DEFAULT'].get('log_directory', '~/.paw/logs'))

# Create log directory if it doesn't exist
os.makedirs(LOG_DIRECTORY, exist_ok=True)

class PAW:
    def __init__(self):
        self.tools_registry = get_tools_registry()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(LOG_DIRECTORY, f"paw_session_{self.session_id}.log")
        
        if LOG_COMMANDS:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
    
    def generate_llm_response(self, prompt):
        """Generate a response from the LLM using Ollama."""
        try:
            logger.info(f"Sending prompt to LLM: {prompt[:50]}...")
            
            response = httpx.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "system": "You are PAW, a Prompt Assisted Workflow tool for Kali Linux. Your job is to help users perform cybersecurity tasks by translating natural language requests into a sequence of commands. For each request, output a JSON object with the following structure: {\"plan\": [string], \"commands\": [string], \"explanation\": [string]}. The 'plan' should outline the steps to achieve the user's goal, 'commands' should list the actual Linux commands to execute (one per line), and 'explanation' should provide context for what each command does.",
                    "stream": False,
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                logger.error(f"Error from Ollama: {response.text}")
                return {"error": f"Ollama API error: {response.status_code}"}
            
            result = response.json()
            return self.extract_json_from_response(result.get("response", ""))
            
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
    
    def execute_command(self, command):
        """Execute a shell command and return the output."""
        try:
            logger.info(f"Executing command: {command}")
            
            # Log the command
            if LOG_COMMANDS:
                with open(self.log_file, 'a') as f:
                    f.write(f"\n[COMMAND] {datetime.now()}: {command}\n")
            
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
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout,
                "stderr": stderr
            }
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def process_request(self, request):
        """Process a natural language request."""
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

Provide the specific commands that would accomplish this task, explaining what each command does.
"""
        
        response = self.generate_llm_response(context + request)
        
        if "error" in response:
            print(f"Error: {response['error']}")
            return
        
        # Display the plan
        print("\n\033[1;34m[*] Plan:\033[0m")
        for step in response.get("plan", []):
            print(f"  - {step}")
        
        # Ask for confirmation if explanation is enabled
        commands = response.get("commands", [])
        explanations = response.get("explanation", [""] * len(commands))
        
        if EXPLAIN_COMMANDS:
            print("\n\033[1;34m[*] Proposed commands:\033[0m")
            for i, (cmd, explanation) in enumerate(zip(commands, explanations), 1):
                print(f"\n  \033[1;33m[{i}] Command:\033[0m {cmd}")
                print(f"      \033[1;32mExplanation:\033[0m {explanation}")
            
            confirm = input("\n\033[1;35m[?] Execute these commands? (y/n): \033[0m")
            if confirm.lower() != 'y':
                print("\n\033[1;31m[!] Execution cancelled\033[0m")
                return
        
        # Execute commands
        results = []
        print("\n\033[1;34m[*] Executing commands:\033[0m")
        
        for i, cmd in enumerate(commands, 1):
            print(f"\n\033[1;33m[{i}/{len(commands)}] Executing:\033[0m {cmd}")
            result = self.execute_command(cmd)
            results.append(result)
            
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
        
        print("\n\033[1;32m[+] All commands executed\033[0m")
        
        # Generate summary if there are multiple commands
        if len(commands) > 1:
            summary_prompt = f"""
Request: {request}

Commands executed:
{chr(10).join(commands)}

Results overview:
{chr(10).join([f"Command {i+1}: Exit code {r['exit_code']}" for i, r in enumerate(results)])}

Please provide a brief summary of the results and what was accomplished.
"""
            summary = self.generate_llm_response(summary_prompt)
            
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
    
    args = parser.parse_args()
    
    if args.version:
        print("PAW - Prompt Assisted Workflow v1.0")
        sys.exit(0)
    
    # Display ASCII art
    display_ascii_art()
    
    paw = PAW()
    
    if args.request:
        paw.process_request(args.request)
    else:
        print("\033[1;34m[*] Welcome to PAW - Prompt Assisted Workflow\033[0m")
        print("\033[1;34m[*] Type 'exit' or 'quit' to exit\033[0m")
        
        while True:
            try:
                request = input("\n\033[1;35mPAW> \033[0m")
                
                if request.lower() in ["exit", "quit"]:
                    print("\033[1;34m[*] Goodbye!\033[0m")
                    break
                
                if request.strip():
                    paw.process_request(request)
                    
            except KeyboardInterrupt:
                print("\n\033[1;34m[*] Execution interrupted\033[0m")
                break
            except Exception as e:
                print(f"\n\033[1;31m[!] Error: {e}\033[0m")

if __name__ == "__main__":
    main() 