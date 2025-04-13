#!/usr/bin/env python3

def display_ascii_art():
    """Display the Victorian-style ASCII art for PAW."""
    
    # ANSI color codes
    BLUE = '\033[1;34m'
    CYAN = '\033[1;36m'
    GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    PURPLE = '\033[1;35m'
    RED = '\033[1;31m'
    NC = '\033[0m'  # No Color
    
    # Victorian-style ASCII art
    art = f"""{PURPLE}
    .-~~~-.              ▄▄▄▄▄▄▄      ▄▄▄▄▄           ▄▄      ▄▄ 
  .'       `.          ▐█      █▌   ▄█     █▄        ████  ████ 
 :            :        ▐█      █▌  ██       ██       █▌  ██  ▐█▌
 :            :        ▐█▀▀▀▀▀▀█▌  ██       ██      ██    ██  ██
 :            :        ▐█      █▌  ██       ██      ████████████
 :            :        ▐█      █▌  ██       ██      ██        ██
 :            :        ▐█      █▌   █▀     ▀█       ██        ██
 :            ;        ▐█      █▌    ▀█████▀        ██        ██
  `._      _.'         
    `-.  .-'          {GREEN}┌────────────────────────────────────────────┐{NC}
      |  |            {GREEN}│{BLUE}       Prompt Assisted Workflow               {GREEN}│{NC}
      |  |            {GREEN}│{YELLOW}            Kali Linux Edition                {GREEN}│{NC}
      |  |            {GREEN}└────────────────────────────────────────────┘{NC}
      |  |
    .-'  '-.          {CYAN}A natural language interface to Kali Linux tools{NC}
    `-.__.-'
    """
    
    print(art)

if __name__ == "__main__":
    display_ascii_art() 