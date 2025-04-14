# PAW Kali Linux Tools Extension

This extension adds extensive Kali Linux penetration testing tools support to the Prompt Assisted Workflow (PAW) framework, enabling security professionals to use natural language to run complex security tasks.

## Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Tool Categories](#tool-categories)
- [Example Scripts](#example-scripts)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- **100+ Security Tools**: Adds extensive penetration testing tools from Kali Linux
- **Detailed Descriptions**: Each tool includes purpose, usage, and example commands
- **Logical Categorization**: Tools organized by function (network scanning, web testing, etc.)
- **Easy Integration**: Simple installation process that integrates with PAW
- **Import/Export**: Share tool configurations between systems
- **Sample Queries**: Natural language examples for common security tasks

## Prerequisites

Before installing, ensure you have:

- PAW (Prompt Assisted Workflow) installed and configured
- Python 3.6 or higher
- Administrator/root access (for system-wide installation)
- Kali Linux OS (recommended) or the specific tools installed if using another Linux distribution

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/paw-kali-tools.git
cd paw-kali-tools
```

### 2. Install the extension

There are two ways to install:

#### A. Using the provided script
```bash
python3 add_tools_example.py
```

#### B. Direct installation
```bash
python3 extensive_kali_tools.py
```

### 3. Verify installation

To verify that the tools were added correctly:
```bash
python3 test_kali_tools.py
```

## Usage

Once installed, you can use natural language queries in PAW to execute security tasks:

### Basic Examples

- "Scan the network 192.168.1.0/24 for open ports and vulnerabilities"
- "Check if the website example.com has SQL injection vulnerabilities"
- "Perform a brute force attack on the login page at http://example.com/login"
- "Crack the password hash 5f4dcc3b5aa765d61d8327deb882cf99"

### Advanced Options

#### Preview Tools
To see what tools would be added without actually adding them:
```bash
python3 extensive_kali_tools.py --show
```

#### Export Tools
To export your tools configuration:
```bash
python3 extensive_kali_tools.py --export kali_tools.json
```

#### Import Tools
To import tools from a configuration file:
```bash
python3 extensive_kali_tools.py --import kali_tools.json
```

## Tool Categories

The extension includes tools in the following categories:

- **Information Gathering**: nmap, dmitry, recon-ng, theHarvester
- **Vulnerability Analysis**: nikto, lynis
- **Web Application Analysis**: sqlmap, wpscan, dirb
- **Password Attacks**: hydra, john, hashcat
- **Wireless Attacks**: aircrack-ng, wifite
- **Exploitation Tools**: metasploit, searchsploit
- **Sniffing & Spoofing**: wireshark, ettercap
- **Post Exploitation**: empire
- **Forensics**: autopsy, foremost
- **Reporting Tools**: dradis

## Example Scripts

The extension includes example scripts to help you get started:

- **add_tools_example.py**: Interactive demo of adding tools to PAW
- **test_kali_tools.py**: Verifies tools are properly installed and shows sample queries

## Development

### Adding Custom Tools

To add your own custom tools, modify the `KALI_TOOLS` list in `extensive_kali_tools.py` or create a JSON file with your tool definitions and import them.

Each tool should follow this format:
```python
{
    "name": "tool_name",
    "category": "Tool Category",
    "description": "Description of what the tool does",
    "common_usage": "Common command-line usage pattern",
    "examples": [
        {"description": "Example task", "command": "tool_name -option target"}
    ]
}
```

### Contribution Guidelines

If you'd like to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

- **Import errors**: Make sure PAW is installed correctly and its modules are in your Python path
- **Missing tools**: Some tools may need to be installed separately if you're not using Kali Linux
- **Permission issues**: Ensure you have write access to the PAW configuration directory

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 