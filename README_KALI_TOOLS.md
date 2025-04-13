# PAW Kali Linux Tools Extension

This extension adds extensive Kali Linux penetration testing tools support to the Prompt Assisted Workflow (PAW) framework.

## Features

- Adds 100+ professionally categorized Kali Linux security tools
- Includes detailed descriptions and usage examples for each tool
- Organizes tools into logical categories (network scanning, web app testing, etc.)
- Provides import/export functionality to share tool configurations

## Installation

1. Make sure you have PAW installed and configured correctly
2. Place `extensive_kali_tools.py` in your PAW installation directory
3. Run the script to add the tools to your PAW registry:

```bash
python3 extensive_kali_tools.py
```

## Usage

### Adding Tools to PAW

To add all the Kali Linux tools to your PAW registry:

```bash
python3 extensive_kali_tools.py
```

To preview which tools would be added without actually adding them:

```bash
python3 extensive_kali_tools.py --show
```

### Exporting Tools

You can export the tools to a JSON file for sharing or backup:

```bash
python3 extensive_kali_tools.py --export kali_tools.json
```

### Importing Tools

To import tools from a JSON file:

```bash
python3 extensive_kali_tools.py --import kali_tools.json
```

## Using Tools with PAW

Once installed, you can use natural language to request penetration testing tasks. PAW will automatically select the appropriate tools based on your request.

Examples:

- "Scan the network 192.168.1.0/24 for open ports and vulnerabilities"
- "Perform a comprehensive web application scan on example.com"
- "Check for common wireless network vulnerabilities"
- "Perform a complete network reconnaissance of the target 10.10.10.10"

## Tool Categories

The extension includes tools for the following categories:

- Network Scanning
- Web Application Analysis
- Vulnerability Analysis
- Password Attacks
- Wireless Attacks
- Exploitation Tools
- Sniffing & Spoofing
- Post Exploitation
- Forensics
- Reverse Engineering
- Reporting Tools
- Social Engineering Tools
- Information Gathering

## Example Script

An example script (`add_tools_example.py`) is provided to demonstrate how to work with the tools extension.

Run it with:

```bash
python3 add_tools_example.py
```

This will display available tools, categorize them, and ask if you want to add them to PAW.

## Development

### Adding Custom Tools

You can add your own custom tools by modifying the `tools` list in `extensive_kali_tools.py` or by creating a JSON file with your tools and importing it.

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

## Troubleshooting

- If you encounter import errors, make sure the PAW modules are in your Python path
- If tools don't appear in PAW after adding them, check the PAW log for any errors
- For permission issues, ensure you have write access to the PAW configuration directory 