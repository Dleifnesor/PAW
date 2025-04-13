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
sudo ./install.sh
```

The installation script will:
- Install PAW system-wide for all users
- Set up Ollama and download the required LLM model
- Create command-line tools `paw` and `add-paw-tool`
- Install documentation

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

See `examples.md` for more detailed examples, or view the installed documentation at `/usr/local/share/doc/paw/examples.md`.

## Extending PAW

### Adding Custom Tools

You can add custom tools to PAW's registry using the `add-paw-tool` command:

```bash
sudo add-paw-tool add --name "my-tool" \
    --category "custom" \
    --description "My custom tool description" \
    --usage "my-tool [options]" \
    --examples "my-tool -h" "my-tool --option value"
```

To list all custom tools:

```bash
add-paw-tool list
```

### Creating Custom Command Modules

PAW supports custom command modules for more complex functionality:

1. Create your Python script in `/usr/local/share/paw/custom_commands/`
2. Make it executable: `sudo chmod +x /usr/local/share/paw/custom_commands/your_script.py`
3. Register it with PAW using `add-paw-tool`

See the included `recon_suite.py` for a complete example or refer to the documentation at `/usr/local/share/doc/paw/custom_commands_guide.md`.

## System Files and Directories

- Commands: `/usr/local/bin/paw` and `/usr/local/bin/add-paw-tool`
- Main files: `/usr/local/share/paw/`
- Configuration: `/etc/paw/config.ini`
- Logs: `/var/log/paw/`
- Documentation: `/usr/local/share/doc/paw/`

## Requirements

- Kali Linux
- 8GB+ RAM (recommended for running the LLM)
- Internet connection (for initial setup)
- Root/sudo access (for installation)

## License

MIT 