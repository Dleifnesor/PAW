#!/usr/bin/env python3

import os
import json
import shutil
from pathlib import Path

# Default tools registry
DEFAULT_TOOLS = {
    # Network scanning tools
    "nmap": {
        "category": "network_scanning",
        "description": "Network discovery and security auditing",
        "common_usage": "nmap [scan type] [options] {target}",
        "examples": [
            "nmap -sS -p 1-1000 192.168.1.0/24",
            "nmap -sV -p- 10.0.0.1",
            "nmap -A 192.168.1.1"
        ]
    },
    "masscan": {
        "category": "network_scanning",
        "description": "Fast port scanner",
        "common_usage": "masscan [options] {target}",
        "examples": [
            "masscan -p22,80,443 192.168.1.0/24 --rate=10000",
            "masscan -p0-65535 10.0.0.0/8 --rate=1000000"
        ]
    },
    "netdiscover": {
        "category": "network_scanning",
        "description": "ARP scanner for host discovery",
        "common_usage": "netdiscover [options]",
        "examples": [
            "netdiscover -r 192.168.1.0/24",
            "netdiscover -i eth0 -P"
        ]
    },
    
    # Web scanning tools
    "nikto": {
        "category": "web_scanning",
        "description": "Web server scanner",
        "common_usage": "nikto -h {target}",
        "examples": [
            "nikto -h 192.168.1.1",
            "nikto -h https://example.com -p 443"
        ]
    },
    "dirb": {
        "category": "web_scanning",
        "description": "Web content scanner",
        "common_usage": "dirb {url} [wordlist]",
        "examples": [
            "dirb http://example.com",
            "dirb https://example.com /usr/share/wordlists/dirb/big.txt"
        ]
    },
    "gobuster": {
        "category": "web_scanning",
        "description": "Directory/file enumeration tool",
        "common_usage": "gobuster [mode] [options]",
        "examples": [
            "gobuster dir -u http://example.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
            "gobuster dns -d example.com -w /usr/share/wordlists/dnsenum/subdomains-top1mil-5000.txt"
        ]
    },
    "wpscan": {
        "category": "web_scanning",
        "description": "WordPress vulnerability scanner",
        "common_usage": "wpscan --url {url} [options]",
        "examples": [
            "wpscan --url https://wordpress-site.com",
            "wpscan --url https://wordpress-site.com --enumerate u"
        ]
    },
    
    # Vulnerability scanning tools
    "openvas": {
        "category": "vulnerability_scanning",
        "description": "Open Vulnerability Assessment Scanner",
        "common_usage": "gvm-cli [options]",
        "examples": [
            "gvm-cli socket --socketpath /var/run/gvmd.sock --xml '<get_tasks/>'"
        ]
    },
    "lynis": {
        "category": "vulnerability_scanning",
        "description": "Security auditing tool for UNIX-based systems",
        "common_usage": "lynis [options]",
        "examples": [
            "lynis audit system",
            "lynis audit system --pentest"
        ]
    },
    
    # Exploitation tools
    "metasploit": {
        "category": "exploitation",
        "description": "Penetration testing framework",
        "common_usage": "msfconsole",
        "examples": [
            "msfconsole -q",
            "msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f exe -o payload.exe"
        ]
    },
    "sqlmap": {
        "category": "exploitation",
        "description": "Automatic SQL injection tool",
        "common_usage": "sqlmap -u {url} [options]",
        "examples": [
            "sqlmap -u 'http://example.com/page.php?id=1'",
            "sqlmap -u 'http://example.com/page.php?id=1' --dbs"
        ]
    },
    "hydra": {
        "category": "exploitation",
        "description": "Fast and flexible online password cracking tool",
        "common_usage": "hydra -l {username} -P {password_list} {target} {protocol}",
        "examples": [
            "hydra -l admin -P /usr/share/wordlists/rockyou.txt 192.168.1.1 ssh",
            "hydra -L users.txt -P passwords.txt ftp://192.168.1.1"
        ]
    },
    
    # Reconnaissance tools
    "whois": {
        "category": "reconnaissance",
        "description": "Domain registration information lookup",
        "common_usage": "whois {domain}",
        "examples": [
            "whois example.com",
            "whois 93.184.216.34"
        ]
    },
    "theHarvester": {
        "category": "reconnaissance",
        "description": "Email, subdomain and name harvester",
        "common_usage": "theHarvester -d {domain} -b {source}",
        "examples": [
            "theHarvester -d example.com -b google",
            "theHarvester -d example.com -b all"
        ]
    },
    "recon-ng": {
        "category": "reconnaissance",
        "description": "Full-featured reconnaissance framework",
        "common_usage": "recon-ng",
        "examples": [
            "recon-ng",
            "echo 'workspaces add example' | recon-ng"
        ]
    },
    
    # Password attack tools
    "hashcat": {
        "category": "password_attacks",
        "description": "Advanced password recovery tool",
        "common_usage": "hashcat -m {hash_type} -a {attack_mode} {hash_file} {wordlist}",
        "examples": [
            "hashcat -m 0 -a 0 hashes.txt /usr/share/wordlists/rockyou.txt",
            "hashcat -m 1000 -a 3 hashes.txt ?a?a?a?a?a?a"
        ]
    },
    "john": {
        "category": "password_attacks",
        "description": "Password cracking tool",
        "common_usage": "john [options] {password_file}",
        "examples": [
            "john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt",
            "john --incremental --format=sha512crypt hashes.txt"
        ]
    },
    "crunch": {
        "category": "password_attacks",
        "description": "Wordlist generator",
        "common_usage": "crunch {min} {max} {charset} -o {output_file}",
        "examples": [
            "crunch 8 8 0123456789ABCDEF -o wordlist.txt",
            "crunch 4 6 abcdefghijklmnopqrstuvwxyz -o wordlist.txt"
        ]
    },
    
    # Wireless tools
    "aircrack-ng": {
        "category": "wireless",
        "description": "Wireless network security toolset",
        "common_usage": "aircrack-ng [options] {capture_file}",
        "examples": [
            "aircrack-ng -w /usr/share/wordlists/rockyou.txt capture.cap",
            "airmon-ng start wlan0"
        ]
    },
    "wifite": {
        "category": "wireless",
        "description": "Automated wireless attack tool",
        "common_usage": "wifite [options]",
        "examples": [
            "wifite",
            "wifite --kill"
        ]
    },
    "kismet": {
        "category": "wireless",
        "description": "Wireless network detector and sniffer",
        "common_usage": "kismet",
        "examples": [
            "kismet",
            "kismet -c wlan0"
        ]
    },
    
    # Forensics tools
    "volatility": {
        "category": "forensics",
        "description": "Memory forensics framework",
        "common_usage": "volatility -f {memory_image} {plugin}",
        "examples": [
            "volatility -f memory.dmp imageinfo",
            "volatility -f memory.dmp --profile=Win10x64_17134 pslist"
        ]
    },
    "foremost": {
        "category": "forensics",
        "description": "File carving tool",
        "common_usage": "foremost -i {input_file} -o {output_directory}",
        "examples": [
            "foremost -i disk.img -o recovered",
            "foremost -t pdf,jpg,doc -i disk.img -o recovered"
        ]
    },
    
    # Custom tools
    "custom_script": {
        "category": "custom",
        "description": "Custom script example",
        "common_usage": "python /path/to/script.py [options]",
        "examples": [
            "python /path/to/script.py --help"
        ]
    }
}

def get_tools_registry():
    """Get the tools registry."""
    # Check if a custom registry exists
    custom_registry_path = "/usr/local/share/paw/tools/custom_registry.json"
    
    if os.path.exists(custom_registry_path):
        try:
            with open(custom_registry_path, 'r') as f:
                custom_registry = json.load(f)
                # Merge with default registry
                merged_registry = DEFAULT_TOOLS.copy()
                merged_registry.update(custom_registry)
                return merged_registry
        except Exception as e:
            print(f"Error loading custom registry: {e}")
            return DEFAULT_TOOLS
    
    return DEFAULT_TOOLS

def add_tool_to_registry(name, category, description, common_usage, examples=None):
    """Add a new tool to the registry."""
    if examples is None:
        examples = []
    
    # Create directory if it doesn't exist
    custom_registry_dir = "/usr/local/share/paw/tools"
    custom_registry_path = os.path.join(custom_registry_dir, "custom_registry.json")
    
    os.makedirs(custom_registry_dir, exist_ok=True)
    
    # Load existing registry or create a new one
    if os.path.exists(custom_registry_path):
        try:
            with open(custom_registry_path, 'r') as f:
                custom_registry = json.load(f)
        except Exception:
            custom_registry = {}
    else:
        custom_registry = {}
    
    # Add the new tool
    custom_registry[name] = {
        "category": category,
        "description": description,
        "common_usage": common_usage,
        "examples": examples
    }
    
    # Save the updated registry
    with open(custom_registry_path, 'w') as f:
        json.dump(custom_registry, f, indent=4)
    
    return True

def get_tools_by_category(category=None):
    """Get all tools or filter by category."""
    tools = get_tools_registry()
    
    if category:
        return {name: info for name, info in tools.items() if info.get("category") == category}
    
    return tools

def check_tool_availability():
    """Check which tools from the registry are available on the system."""
    tools = get_tools_registry()
    availability = {}
    
    for tool_name in tools:
        # Check if the tool is in the PATH
        tool_path = shutil.which(tool_name)
        availability[tool_name] = bool(tool_path)
    
    return availability

if __name__ == "__main__":
    # Print the tools registry when run directly
    tools = get_tools_registry()
    print(json.dumps(tools, indent=4)) 