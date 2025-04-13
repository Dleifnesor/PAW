# PAW (Prompt Assisted Workflow)

PAW is a natural language-powered automation layer for Kali Linux, turning your terminal into an AI assistant that can understand and execute complex cybersecurity tasks through plain English commands.

## Features

- Natural language interface to Kali Linux tools
- Intelligent task decomposition and tool selection
- Automated command chaining and execution
- Beautiful Victorian-style ASCII art interface
- Powered by Ollama and MartinRizzo/Ayla-Light-v2:12b-q4_K_M

## Installation

```bash
git clone https://github.com/yourusername/PAW.git
cd PAW
chmod +x install.sh
./install.sh
```

The installation script will set up Ollama and download the required LLM model.

## Usage

Simply type `paw` in your terminal to start:

```bash
paw
```

Or directly issue a command:

```bash
paw "scan the local network for vulnerable services"
```

## Examples

- `paw "find all open ports on 192.168.1.0/24 and identify services"`
- `paw "perform passive reconnaissance on example.com"`
- `paw "check if this system has any known vulnerabilities"`
- `paw "create a wordlist from the contents of this website"`

See `examples.md` for more detailed examples.

## Extending PAW

### Adding Custom Tools

You can add custom tools to PAW's registry using the `add_custom_tool.py` script:

```bash
python3 add_custom_tool.py add --name "my-tool" \
    --category "custom" \
    --description "My custom tool description" \
    --usage "my-tool [options]" \
    --examples "my-tool -h" "my-tool --option value"
```

To list all custom tools:

```bash
python3 add_custom_tool.py list
```

### Creating Custom Command Modules

PAW supports custom command modules for more complex functionality. Check out the example in the `custom_commands` directory:

1. Create your Python script in the `custom_commands` directory
2. Make it executable: `chmod +x custom_commands/your_script.py`
3. Register it with PAW using `add_custom_tool.py`

See the included `recon_suite.py` for a complete example.

## Requirements

- Kali Linux
- 8GB+ RAM (recommended for running the LLM)
- Internet connection (for initial setup)

## License

MIT 