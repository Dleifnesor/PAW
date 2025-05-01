# OA - Ollama Assistant
![image](https://github.com/user-attachments/assets/b5770a66-d15e-4f19-a2a6-9dbb64568368)

OA (Ollama Assistant) is a command-line tool for Kali Linux that uses AI to generate and execute commands based on natural language prompts. The tool leverages Ollama, a local AI model runner, with the CodeLlama model to understand and generate Linux commands.

## Features

- Generate commands from natural language prompts
- Edit generated commands before execution
- Save frequently used commands for later use
- Explain what commands do in detail
- Command history with readline support
- Switch between different Ollama models

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Dleifnesor/PAW/tree/OA.git
   cd PAW
   ```

2. Run the installation script (requires root privileges):
   ```bash
   sudo bash install.sh
   ```

This will:
- Install Ollama if not already installed
- Download the CodeLlama model
- Install required Python dependencies
- Create the OA command for system-wide access

Note: The installation process might take some time, especially downloading the AI model.

## Usage
![image](https://github.com/user-attachments/assets/68c8f532-a55c-4df6-b032-c77e9c152668)

Start the tool by typing:

```bash
OA
```

### Basic Usage

1. Type your request in natural language:
   ```
   OA> find all PDF files in the current directory and subdirectories
   ```

2. OA will generate a command:
   ```
   Generated command: find . -type f -name "*.pdf"
   ```

3. You can:
   - Type `y` to execute the command
   - Type `n` to reject the command
   - Type `e` to edit the command before execution

### Special Commands

OA supports several special commands:

- `!help` - Show help information
- `!exit` - Exit OA
- `!save [name]` - Save the last command with optional name
- `!list` - List all saved commands
- `!load [number]` - Load and execute a saved command
- `!clear` - Clear the screen
- `!model [name]` - Change the Ollama model (default: codellama)
- `!explain [cmd]` - Explain what a command does

## Requirements

- Kali Linux
- Python 3.x
- Internet connection for the initial model download

## Troubleshooting

If you encounter issues with Ollama connectivity, check if the Ollama service is running:

```bash
systemctl status ollama
```

If it's not running, start it with:

```bash
systemctl start ollama
```
