# PAW - Prompt Assistant for Wireless

PAW (Prompt Assistant for Wireless) is a command-line tool that provides context-aware assistance for wireless penetration testing and network security tasks in Kali Linux.

## Overview

PAW serves as an assistant for wireless network testing, providing:

1. Context-sensitive guidance for common wireless security tools
2. Interface management (enabling monitor mode, etc.)
3. Network scanning and capture capabilities 
4. Deauthentication attack functionality
5. MAC address management with macchanger
6. Database management for discovered networks

PAW is designed for educational purposes to help security professionals and students better understand wireless security tools and techniques.

## Features

- **Interactive Console**: Easy-to-use command console with help system
- **Context Library**: Provides detailed information about wireless tools based on user queries
- **Interface Management**: Easily switch between managed and monitor modes
- **Network Scanning**: Simplified wrappers around aircrack-ng functionality
- **Attack Modules**: Clean interface for common wireless attacks
- **MAC Address Management**: Simple interface for changing and managing MAC addresses
- **Rich Output**: Uses rich formatting when available (can be used without rich)

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/paw.git
cd paw
```

2. Install required dependencies:
```
pip install -r requirements.txt
```

3. Run PAW:
```
sudo python3 paw.py
```

**Note**: PAW requires root privileges for most functionality since it needs to manipulate network interfaces.

## Usage

PAW is primarily used in interactive mode:

```
sudo python3 paw.py
```

### Available Commands

- `help` - Show available commands
- `interface list` - List available wireless interfaces
- `interface monitor <interface>` - Set interface to monitor mode
- `interface managed <interface>` - Set interface to managed mode
- `scan networks <interface>` - Scan for wireless networks
- `capture start <interface> <bssid> <channel>` - Start packet capture
- `capture stop` - Stop active packet capture
- `attack deauth <interface> <bssid> <client> [count]` - Send deauth packets
- `db list` - List saved networks
- `db export <filename>` - Export network database to CSV
- `macchanger <options> <interface>` - Modify MAC address

You can also type natural language questions about wireless security tasks, and PAW will provide relevant context from its knowledge base.

### MAC Address Management

PAW provides an easy interface to macchanger with the following options:

```
macchanger <interface>          # Set random MAC address
macchanger -r <interface>       # Set fully random MAC
macchanger -a <interface>       # Set random MAC of same device type
macchanger -A <interface>       # Set random vendor MAC
macchanger -p <interface>       # Reset to original hardware MAC
macchanger -m XX:XX:XX:XX:XX:XX <interface>  # Set specific MAC
macchanger -s <interface>       # Show current MAC
macchanger -l                   # List known vendors
```

## Examples

Here are some examples of using PAW:

```
# List available interfaces
interface list

# Enable monitor mode
interface monitor wlan0

# Scan for networks
scan networks wlan0mon

# Start capturing packets for a specific AP
capture start wlan0mon 00:11:22:33:44:55 6

# Send deauth packets
attack deauth wlan0mon 00:11:22:33:44:55 broadcast 10

# Change MAC address to random
macchanger -r wlan0

# Show current MAC address
macchanger -s wlan0

# Ask for context about a tool
How do I crack WPA handshakes?
```

## Requirements

- Python 3.6+
- Kali Linux or similar distribution with wireless tools installed
- Root privileges for most functionality
- Python packages: rich (optional, for improved display)

## License

This project is licensed under MIT License - see the LICENSE file for details.

## Disclaimer

This tool is designed for educational purposes and authorized security testing only. Unauthorized network testing is illegal. Always obtain proper authorization before testing any networks you don't own. 