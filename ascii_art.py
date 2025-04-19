#!/usr/bin/env python3

def display_ascii_art():
    """Display PAW ASCII art with color"""
    try:
        from rich.console import Console
        from rich.text import Text
        console = Console()
        
        # Simplified ASCII art using more compatible characters
        ascii_art = """
  ____  ___    __
 |  _ \\| \\ \\  / /
 | |_) | |\\ \\/ / 
 |  __/| | \\  /  
 |_|   |_|  \\/   
                 
        """
        
        # Create colored text
        text = Text(ascii_art, style="bold cyan")
        console.print(text)
        
    except ImportError:
        # Fallback to simple ANSI colors
        print("\033[1;36m")  # Bold cyan
        print("""
  ____  ___    __
 |  _ \\| \\ \\  / /
 | |_) | |\\ \\/ / 
 |  __/| | \\  /  
 |_|   |_|  \\/   
                 
        """)
        print("\033[0m")  # Reset color

if __name__ == "__main__":
    display_ascii_art() 