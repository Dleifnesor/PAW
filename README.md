# PAW (Prompt Assisted Workflow)

PAW is a natural language-powered automation layer for Kali Linux, turning your terminal into an AI assistant that can understand and execute complex cybersecurity tasks through plain English commands.

## Features

- Natural language interface to Kali Linux tools
- Intelligent task decomposition and tool selection
- Automated command chaining and execution
- Beautiful Victorian-style ASCII art interface
- Powered by Ollama and qwen2.5-coder:7b

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
- Create command-line tools `PAW` and `add-paw-tool`
- Install documentation

## Usage

Simply type `PAW` in your terminal to start:

```bash
PAW
```

Or directly issue a command:

```bash
PAW "scan the local network for vulnerable services"
```

### Additional Command-line Options

- `--timeout SECONDS`: Set custom timeout for LLM requests (default is 180 seconds)
  ```
  PAW --timeout 300 "install and configure OpenVAS"
  ```

- `--version`: Display version information

## Examples

- `PAW "find all open ports on 192.168.1.0/24 and identify services"`
- `PAW "perform passive reconnaissance on example.com"`
- `PAW "check if this system has any known vulnerabilities"`
- `PAW "create a wordlist from the contents of this website"`

See `examples.md` for more detailed examples, or view the installed documentation at `/usr/local/share/doc/paw/examples.md`.

## Configuration

You can configure PAW using the interactive configuration tool:

```bash
sudo paw-config
```

This tool allows you to:
- Change the LLM model
- Adjust timeout settings
- Toggle command explanation and logging
- Change log directory
- Update Ollama host URL

Alternatively, you can manually edit the configuration file:

```bash
sudo nano /etc/paw/config.ini
```

Key settings include:
- `model`: The Ollama model to use
- `ollama_host`: The URL of your Ollama server
- `explain_commands`: Whether to explain commands before execution
- `log_commands`: Whether to log commands and output
- `log_directory`: Where to store logs
- `llm_timeout`: Timeout in seconds for LLM requests (default: 180.0)

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

- Commands: `/usr/local/bin/PAW`, `/usr/local/bin/add-paw-tool`, and `/usr/local/bin/paw-config`
- Main files: `/usr/local/share/paw/`
- Configuration: `/etc/paw/config.ini`
- Logs: `/var/log/paw/`
- Documentation: `/usr/local/share/doc/paw/`

## Troubleshooting

- **LLM Request Timeout**: If you encounter timeout errors when making complex requests, try increasing the timeout setting using `paw-config` or use the `--timeout` command-line option.
  ```
  PAW --timeout 300 "your complex query"
  ```

- **Ollama Model Issues**: Ensure Ollama is running and properly configured. You can manage your models and update the active model using `paw-config`.

## Requirements

- Kali Linux
- 8GB+ RAM (recommended for running the LLM)
- Internet connection (for initial setup)
- Root/sudo access (for installation)

## License

MIT 