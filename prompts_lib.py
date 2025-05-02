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
        "common_tools": ["iwconfig", "iw", "wavemon", "kismet"],
        "examples": [
            "iwconfig wlan0                          # Display wireless settings",
            "iw dev wlan0 scan                       # Scan for networks",
            "kismet -c wlan0                         # Start Kismet wireless monitor"
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