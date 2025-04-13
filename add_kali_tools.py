#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path to import the tools_registry module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from tools_registry import add_tool_to_registry, get_tools_registry

def add_kali_tools():
    """Add additional Kali Linux tools to the PAW registry."""
    
    # First, let's get existing tools to avoid duplication
    existing_tools = get_tools_registry()
    
    # Define new tools to add
    new_tools = {
        # Exploitation Framework
        "searchsploit": {
            "category": "exploitation",
            "description": "Search for exploits in Exploit-DB archive",
            "common_usage": "searchsploit [options] {search_term}",
            "examples": [
                "searchsploit apache 2.4.7",
                "searchsploit -t oracle windows"
            ]
        },
        
        # Web Application Analysis
        "burpsuite": {
            "category": "web_scanning",
            "description": "Web application security testing platform",
            "common_usage": "burpsuite",
            "examples": [
                "burpsuite",
                "java -jar /usr/share/burpsuite/burpsuite.jar"
            ]
        },
        "owasp-zap": {
            "category": "web_scanning",
            "description": "OWASP Zed Attack Proxy for web app security testing",
            "common_usage": "owasp-zap",
            "examples": [
                "owasp-zap",
                "zaproxy"
            ]
        },
        
        # Password Attacks
        "medusa": {
            "category": "password_attacks",
            "description": "Parallel network login auditor",
            "common_usage": "medusa -h {host} -u {user} -P {password_file} -M {module}",
            "examples": [
                "medusa -h 192.168.1.1 -u admin -P passwords.txt -M ssh",
                "medusa -H hosts.txt -U users.txt -P passwords.txt -M http -m DIR:/admin"
            ]
        },
        "ophcrack": {
            "category": "password_attacks",
            "description": "Windows password cracker using rainbow tables",
            "common_usage": "ophcrack [options]",
            "examples": [
                "ophcrack -d /path/to/tables -t vista_free -f dump.txt"
            ]
        },
        
        # Sniffing & Spoofing
        "wireshark": {
            "category": "sniffing_spoofing",
            "description": "Network protocol analyzer",
            "common_usage": "wireshark [options]",
            "examples": [
                "wireshark",
                "wireshark -i eth0 -k -w capture.pcap"
            ]
        },
        "ettercap": {
            "category": "sniffing_spoofing",
            "description": "Network packet and content sniffer/interceptor",
            "common_usage": "ettercap [options]",
            "examples": [
                "ettercap -G",
                "ettercap -T -q -i eth0 -M arp:remote /192.168.1.1/ /192.168.1.2/"
            ]
        },
        
        # OSINT
        "maltego": {
            "category": "reconnaissance",
            "description": "Open source intelligence and forensics tool",
            "common_usage": "maltego",
            "examples": [
                "maltego"
            ]
        },
        "osrframework": {
            "category": "reconnaissance",
            "description": "Set of tools for OSINT",
            "common_usage": "osrframework-cli [tool] [options]",
            "examples": [
                "usufy.py -n username",
                "searchfy.py -q 'John Smith'"
            ]
        },
        
        # Reporting
        "faraday": {
            "category": "reporting",
            "description": "Collaborative penetration test and vulnerability management platform",
            "common_usage": "faraday [options]",
            "examples": [
                "faraday-server",
                "faraday-client"
            ]
        },
        "dradis": {
            "category": "reporting",
            "description": "Collaboration and reporting platform for infosec professionals",
            "common_usage": "dradis [options]",
            "examples": [
                "dradis"
            ]
        }
    }
    
    # Add each tool to the registry if it doesn't already exist
    added_tools = []
    for name, info in new_tools.items():
        if name not in existing_tools:
            add_tool_to_registry(
                name=name,
                category=info["category"],
                description=info["description"],
                common_usage=info["common_usage"],
                examples=info["examples"]
            )
            added_tools.append(name)
    
    return added_tools

if __name__ == "__main__":
    added_tools = add_kali_tools()
    
    if added_tools:
        print(f"Added {len(added_tools)} new tools to the PAW registry:")
        for tool in added_tools:
            print(f" - {tool}")
    else:
        print("No new tools were added. They may already exist in the registry.") 