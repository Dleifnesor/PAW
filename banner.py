#!/usr/bin/env python3
# PAW Banner Module
# Display ASCII art banner for PAW

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# ASCII art banner
PAW_BANNER = r"""
 ____   _____      __
|  _ \ / _ \ \    / /
| |_) | (_) \ \  / / 
|  __/ \___/ \ \/ /  
|_|          \__/   
"""

PAW_BANNER_ALT = r"""
 _______  _______  _______
|       ||   _   ||       |
|    _  ||  |_|  ||  _____|
|   |_| ||       || |_____ 
|    ___||       ||_____  |
|   |    |   _   | _____| |
|___|    |__| |__||_______|
"""

PAW_SUBTITLE = "Prompt Assistant for Wireless"
PAW_VERSION = "v0.1"
PAW_AUTHOR = "Created for educational purposes only"

def print_banner():
    """Print the PAW banner"""
    if RICH_AVAILABLE:
        console = Console()
        
        # Create a stylized banner using rich
        console.print("")
        console.print(PAW_BANNER, style="bold cyan", highlight=False)
        console.print(f"[bold cyan]{PAW_SUBTITLE}[/bold cyan] [dim]{PAW_VERSION}[/dim]")
        console.print(f"[dim italic]{PAW_AUTHOR}[/dim italic]")
        console.print("")
    else:
        # Fallback to plain text
        print("")
        print(PAW_BANNER)
        print(f"{PAW_SUBTITLE} {PAW_VERSION}")
        print(f"{PAW_AUTHOR}")
        print("")

def print_exit_message():
    """Print exit message"""
    if RICH_AVAILABLE:
        console = Console()
        console.print("\n[bold cyan]Thanks for using PAW![/bold cyan]")
        console.print("[dim italic]Stay safe and ethical in your wireless testing.[/dim italic]\n")
    else:
        print("\nThanks for using PAW!")
        print("Stay safe and ethical in your wireless testing.\n")

if __name__ == "__main__":
    # Test the banner
    print_banner()
    print_exit_message() 