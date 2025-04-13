# PAW Custom Commands

This directory contains custom command modules for PAW that extend its functionality beyond basic command execution.

## Available Custom Commands

### recon_suite.py

A comprehensive reconnaissance suite for gathering information about domains.

Usage:
```bash
recon-suite -d example.com -o output_directory
```

Features:
- WHOIS lookups
- DNS enumeration
- Subdomain discovery
- Web server header analysis
- Email harvesting
- Comprehensive reporting

## Creating Your Own Custom Commands

You can create your own custom command modules by following these steps:

1. Create a Python script in `/usr/local/share/paw/custom_commands/`
2. Make it executable with `sudo chmod +x /usr/local/share/paw/custom_commands/your_script.py`
3. Register it with PAW using:

```bash
sudo add-paw-tool add --name "your-tool-name" \
    --category "your_category" \
    --description "Description of your tool" \
    --usage "your-tool-name [options]" \
    --examples "your-tool-name -h" "your-tool-name --option value"
```

### Template for Custom Commands

Here's a basic template you can use for creating your own custom commands:

```python
#!/usr/bin/env python3

"""
Custom PAW module: Your Tool Name
This module provides [description of functionality].

To register this module with PAW, run:
sudo add-paw-tool add --name "your-tool-name" --category "category" \
    --description "Description of your tool" \
    --usage "your-tool-name [options]" \
    --examples "your-tool-name -h" "your-tool-name --option value"
"""

import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Your tool description")
    parser.add_argument("-o", "--option", help="Description of this option")
    # Add more arguments as needed
    
    args = parser.parse_args()
    
    # Your tool's functionality goes here
    print("[*] Running your custom command...")
    
    # Example of executing a command
    os.system("echo 'Custom command executed!'")
    
    print("[+] Custom command completed!")

if __name__ == "__main__":
    main()
```

## Integration with PAW

Once registered, your custom commands can be invoked directly from PAW using natural language:

```
PAW> run a comprehensive reconnaissance on example.com
```

PAW will identify your custom tool as the most appropriate option and execute it with the right parameters.

## Tips for Custom Command Development

1. Always include helpful documentation with usage examples
2. Handle errors gracefully and provide clear error messages
3. Use standard output formats that PAW can parse (JSON recommended)
4. Follow the Unix philosophy: make each tool do one thing well
5. Provide a way to run the tool with verbose output for debugging 