# PAW - Prompt Assistant for Wireless

PAW is a terminal-based assistant that provides guidance and commands for wireless network penetration testing tasks. It is designed as an educational tool to help users learn about wireless security tools and techniques.

## Features

- **Natural Language Interface**: Ask questions about wireless hacking techniques and get relevant information
- **Context-Aware Responses**: PAW provides context from its knowledge base based on keywords in your queries
- **Command Execution**: Directly execute wireless security tool commands
- **Suggest Mode**: Get suggested commands without executing them
- **Tab Completion**: Command and keyword completion using the Tab key
- **Command History**: Use up/down arrow keys to navigate through command history

## Installation

### Prerequisites

PAW is designed for Kali Linux, which already includes the necessary wireless security tools. It can also be used on other Linux distributions with the appropriate tools installed.

### Required Python Packages

```
pip install rich
```

### Clone the Repository

```bash
git clone https://github.com/yourusername/paw.git
cd paw
```

## Usage

### Interactive Mode

```bash
python paw.py
```

### Suggest Mode (Safe Mode)

Suggest mode provides command suggestions without executing them, which is useful for learning or creating scripts.

```bash
python paw.py -s
```

### One-time Query

```bash
python paw.py "How to enable monitor mode?"
```

### One-time Query in Suggest Mode

```bash
python paw.py -s "How to crack a WPA password?"
```

## Examples

Here are some example queries you can try:

- "How do I enable monitor mode on my wireless card?"
- "How to scan for wireless networks?"
- "How to capture a WPA handshake?"
- "How to crack a wifi password?"
- "How to deauthenticate a client?"
- "Show me nmap options for scanning ports"
- "How do I change my MAC address?"

## Module Structure

PAW consists of several Python modules:

- **paw.py**: Main script and command-line interface
- **context_lib.py**: Provides context information based on user queries
- **prompts_lib.py**: Contains dictionaries of information about wireless security tools
- **tool_executor.py**: Executes commands and parses user input
- **interface_manager.py**: Manages wireless interfaces
- **autocomplete.py**: Provides command completion functionality
- **banner.py**: Displays the PAW banner

## Testing Scripts

- **test_suggest.py**: Tests the suggest mode with various queries
- **test_tools.py**: Tests the context library functionality 
- **test_context.py**: Tests context retrieval based on user prompts

## Security Considerations

PAW is designed for educational purposes only. Always ensure that you have permission to use these tools on any networks you test. Unauthorized penetration testing is illegal and unethical.

## Development

This project is under active development. Feel free to contribute by submitting pull requests or opening issues on GitHub.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

PAW is intended for educational purposes only. The authors are not responsible for any misuse of the information or tools provided by this software. Always use security tools ethically and with proper authorization. 