#!/usr/bin/env python3
# PAW - Prompt Assistant for Wireless
# A terminal-based tool to provide guidance for wireless penetration testing tasks
# Created for educational purposes only

import os
import sys
import argparse
import subprocess
import time
import random
import re
import signal
import platform
from typing import List, Dict, Optional, Tuple, Any
import traceback

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.prompt import Prompt, Confirm
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Import PAW modules
try:
    from context_lib import get_context_for_prompt
    from interface_manager import InterfaceManager
    from prompts_lib import AIRCRACK_PROMPTS, NETWORK_PROMPTS
    from tool_executor import execute_tool_command, parse_tool_command
    from db_manager import NetworkDatabase
    from banner import print_banner
except ImportError as e:
    print(f"Error: Could not import PAW modules. {e}")
    print("Make sure you're running from the PAW directory.")
    sys.exit(1)

# Global variables
console = Console() if RICH_AVAILABLE else None
interface_manager = InterfaceManager()
db = NetworkDatabase()
last_command_output = None
use_context = True

# Signal handler for graceful exit
def signal_handler(sig, frame):
    """Handle Ctrl+C and other exit signals"""
    print("\n\nExiting PAW. Cleaning up...")
    # Ensure monitor mode is disabled before exit
    try:
        interface_manager.disable_all_monitor_modes()
    except Exception as e:
        print(f"Warning during cleanup: {e}")
    print("Goodbye!")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

def display_output(output: str, title: str = "Output") -> None:
    """Display command output in a rich panel or plain text"""
    global last_command_output
    # Save output for context in future commands
    last_command_output = output
    
    if RICH_AVAILABLE:
        console.print(Panel(output, title=title, border_style="blue", padding=(1, 2)))
    else:
        print(f"--- {title} ---")
        print(output)
        print("-" * (len(title) + 6))
    
    # Ask user if they want to use this output as context for next command
    prompt_for_context_preference()

def prompt_for_context_preference():
    """Ask user if they want to use previous output as context for next command"""
    global use_context
    
    if RICH_AVAILABLE:
        console.print("[bold]For the next command:[/bold]")
        console.print("[cyan]1.[/cyan] Use this output as context")
        console.print("[cyan]2.[/cyan] Start fresh (ignore previous output)")
        choice = Prompt.ask("Choose an option", choices=["1", "2"], default="1")
        use_context = (choice == "1")
    else:
        print("\nFor the next command:")
        print("1. Use this output as context")
        print("2. Start fresh (ignore previous output)")
        choice = input("Choose an option [1/2] (default: 1): ").strip()
        use_context = (choice != "2")
    
    if use_context:
        if RICH_AVAILABLE:
            console.print("[green]Next command will use previous output as context[/green]")
        else:
            print("Next command will use previous output as context")
    else:
        if RICH_AVAILABLE:
            console.print("[yellow]Next command will start fresh (no context from previous output)[/yellow]")
        else:
            print("Next command will start fresh (no context from previous output)")

def handle_macchanger_command(args: List[str]) -> None:
    """Handle MAC address changing commands with macchanger"""
    parser = argparse.ArgumentParser(prog="macchanger", 
                                    description="Change MAC address using macchanger")
    parser.add_argument("interface", help="Network interface to modify")
    parser.add_argument("-r", "--random", action="store_true", 
                       help="Set fully random MAC address")
    parser.add_argument("-p", "--permanent", action="store_true", 
                       help="Reset to original hardware MAC address")
    parser.add_argument("-a", "--same-kind", action="store_true", 
                       help="Set random vendor MAC of same device type")
    parser.add_argument("-A", "--random-vendor", action="store_true", 
                       help="Set random vendor MAC address")
    parser.add_argument("-m", "--mac", 
                       help="Set specific MAC address (format: XX:XX:XX:XX:XX:XX)")
    parser.add_argument("-s", "--show", action="store_true", 
                       help="Show current MAC address")
    parser.add_argument("-l", "--list", action="store_true", 
                       help="List known vendors")
    
    try:
        # Parse arguments - using args[1:] to skip the 'macchanger' command itself
        if len(args) > 1:
            options = parser.parse_args(args[1:])
        else:
            parser.print_help()
            return
            
        interface = options.interface
        
        # Check if macchanger is installed
        if not is_tool_available("macchanger"):
            display_output("macchanger is not installed. Install with: sudo apt-get install macchanger", "Error")
            return
            
        # Show current MAC
        if options.show:
            cmd = ["macchanger", "-s", interface]
            result = execute_command(cmd)
            display_output(result, f"Current MAC for {interface}")
            return
            
        # List vendors
        if options.list:
            cmd = ["macchanger", "-l"]
            result = execute_command(cmd)
            display_output(result, "MAC Vendors List (truncated)")
            return
            
        # For all other operations, we need to take down the interface first
        if not (options.show or options.list):
            # Check if we have permission to modify interfaces
            if os.geteuid() != 0:
                display_output("You need root privileges to change MAC addresses", "Error")
                return
                
            # Take down the interface
            down_cmd = ["ifconfig", interface, "down"]
            execute_command(down_cmd)
            
            # Determine which macchanger option to use
            mac_cmd = ["macchanger"]
            
            if options.permanent:
                mac_cmd.append("-p")
            elif options.random:
                mac_cmd.append("-r")
            elif options.same_kind:
                mac_cmd.append("-a")
            elif options.random_vendor:
                mac_cmd.append("-A")
            elif options.mac:
                mac_cmd.extend(["-m", options.mac])
            else:
                # Default to random if no option specified
                mac_cmd.append("-r")
                
            mac_cmd.append(interface)
            result = execute_command(mac_cmd)
            
            # Bring the interface back up
            up_cmd = ["ifconfig", interface, "up"]
            execute_command(up_cmd)
            
            display_output(result, f"MAC Address Change for {interface}")
            
    except Exception as e:
        display_output(f"Error: {str(e)}", "MAC Changer Error")
        traceback.print_exc()

def is_tool_available(tool_name: str) -> bool:
    """Check if a command-line tool is available"""
    try:
        devnull = open(os.devnull, 'w')
        subprocess.Popen([tool_name, "--help"], stdout=devnull, stderr=devnull).communicate()
        return True
    except OSError:
        return False

def execute_command(command: List[str]) -> str:
    """Execute a shell command and return the output"""
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0 and result.stderr:
            return f"Error: {result.stderr}"
        return result.stdout or result.stderr or "Command executed successfully."
    except Exception as e:
        return f"Failed to execute command: {str(e)}"

def interactive_mode() -> None:
    """Run PAW in interactive mode"""
    print_banner()
    
    if RICH_AVAILABLE:
        console.print("[bold green]Welcome to PAW - Prompt Assistant for Wireless[/bold green]")
        console.print("[italic]Type [bold]help[/bold] for assistance or [bold]exit[/bold] to quit.[/italic]\n")
    else:
        print("Welcome to PAW - Prompt Assistant for Wireless")
        print("Type 'help' for assistance or 'exit' to quit.\n")
    
    try:
        # Check if running with admin/root privileges
        if os.geteuid() != 0:
            if RICH_AVAILABLE:
                console.print("[bold yellow]Warning: PAW is not running with root privileges.[/bold yellow]")
                console.print("[yellow]Some functions like changing interface modes will not work.[/yellow]\n")
            else:
                print("Warning: PAW is not running with root privileges.")
                print("Some functions like changing interface modes will not work.\n")
    except AttributeError:
        # Windows doesn't have geteuid
        if platform.system() == "Windows":
            if RICH_AVAILABLE:
                console.print("[bold yellow]Warning: Running on Windows. Some Linux-specific features are not available.[/bold yellow]\n")
            else:
                print("Warning: Running on Windows. Some Linux-specific features are not available.\n")
    
    while True:
        try:
            if RICH_AVAILABLE:
                user_input = Prompt.ask("[bold blue]PAW[/bold blue]")
            else:
                user_input = input("PAW> ")
            
            user_input = user_input.strip()
            
            # Exit command
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Exiting PAW. Cleaning up...")
                # Ensure monitor mode is disabled before exit
                interface_manager.disable_all_monitor_modes()
                print("Goodbye!")
                sys.exit(0)
            
            # Empty input
            if not user_input:
                continue
            
            # Help command
            if user_input.lower() == 'help':
                show_help()
                continue
                
            # Process commands with context if enabled
            context_to_use = last_command_output if use_context and last_command_output else None
            
            # Process commands
            if user_input.lower().startswith('aircrack'):
                args = user_input.split()
                handle_aircrack_command(args, context_to_use)
            elif user_input.lower().startswith('interface'):
                args = user_input.split()
                handle_interface_command(args)
            elif user_input.lower().startswith('scan'):
                args = user_input.split()
                handle_scan_command(args)
            elif user_input.lower().startswith('capture'):
                args = user_input.split()
                handle_capture_command(args)
            elif user_input.lower().startswith('attack'):
                args = user_input.split()
                handle_attack_command(args)
            elif user_input.lower().startswith('db'):
                args = user_input.split()
                handle_database_command(args)
            elif user_input.lower().startswith('macchanger'):
                args = user_input.split()
                handle_macchanger_command(args)
            else:
                # Try to get context for the prompt
                context = get_context_for_prompt(user_input, context_to_use)
                if context:
                    display_output(context, "Tool Context")
                else:
                    display_output("Unknown command or no relevant context found. Type 'help' for assistance.", "Info")
        
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[bold red]Error: {str(e)}[/bold red]")
            else:
                print(f"Error: {str(e)}")
            traceback.print_exc()

def show_help() -> None:
    """Show help information for PAW"""
    if RICH_AVAILABLE:
        help_table = Table(title="PAW Commands", box=box.ROUNDED)
        help_table.add_column("Command", style="cyan")
        help_table.add_column("Description", style="green")
        
        # Add command rows
        help_table.add_row("help", "Show this help message")
        help_table.add_row("exit, quit, q", "Exit PAW")
        help_table.add_row("interface list", "List available network interfaces")
        help_table.add_row("interface monitor [interface]", "Enable monitor mode on interface")
        help_table.add_row("interface managed [interface]", "Set interface to managed mode")
        help_table.add_row("scan networks [interface]", "Scan for wireless networks")
        help_table.add_row("capture start [interface] [bssid] [channel]", "Start capturing packets")
        help_table.add_row("capture stop", "Stop packet capture")
        help_table.add_row("attack deauth [interface] [bssid] [client] [count]", "Send deauth packets")
        help_table.add_row("db list", "List saved networks in database")
        help_table.add_row("db export [filename]", "Export database to CSV")
        help_table.add_row("macchanger [options] [interface]", "Change MAC address")
        help_table.add_row("[natural language]", "Ask about wireless hacking tasks")
        
        console.print(help_table)
    else:
        print("PAW Commands:")
        print("  help                                 - Show this help message")
        print("  exit, quit, q                        - Exit PAW")
        print("  interface list                       - List available network interfaces")
        print("  interface monitor [interface]        - Enable monitor mode on interface")
        print("  interface managed [interface]        - Set interface to managed mode")
        print("  scan networks [interface]            - Scan for wireless networks")
        print("  capture start [i] [bssid] [channel]  - Start capturing packets")
        print("  capture stop                         - Stop packet capture")
        print("  attack deauth [i] [bssid] [client]   - Send deauth packets")
        print("  db list                              - List saved networks in database")
        print("  db export [filename]                 - Export database to CSV")
        print("  macchanger [options] [interface]     - Change MAC address")
        print("  [natural language]                   - Ask about wireless hacking tasks")

def handle_interface_command(args: List[str]) -> None:
    """Handle commands related to network interfaces"""
    if len(args) < 2:
        display_output("Missing subcommand. Use 'interface list', 'interface monitor <iface>', or 'interface managed <iface>'", "Error")
        return
    
    subcommand = args[1].lower()
    
    if subcommand == "list":
        interfaces = interface_manager.get_wireless_interfaces()
        
        if RICH_AVAILABLE:
            table = Table(title="Wireless Interfaces")
            table.add_column("Interface", style="cyan")
            table.add_column("MAC Address", style="green")
            table.add_column("Mode", style="yellow")
            
            for iface in interfaces:
                table.add_row(
                    iface["name"],
                    iface.get("mac_address", "Unknown"),
                    iface.get("mode", "Unknown")
                )
            
            console.print(table)
        else:
            print("Wireless Interfaces:")
            for iface in interfaces:
                print(f"  {iface['name']} - MAC: {iface.get('mac_address', 'Unknown')} - Mode: {iface.get('mode', 'Unknown')}")
    
    elif subcommand == "monitor":
        if len(args) < 3:
            display_output("Missing interface name. Use 'interface monitor <interface>'", "Error")
            return
        
        interface_name = args[2]
        result = interface_manager.enable_monitor_mode(interface_name)
        display_output(result, "Monitor Mode")
    
    elif subcommand == "managed":
        if len(args) < 3:
            display_output("Missing interface name. Use 'interface managed <interface>'", "Error")
            return
        
        interface_name = args[2]
        result = interface_manager.set_managed_mode(interface_name)
        display_output(result, "Managed Mode")
    
    else:
        display_output(f"Unknown subcommand: {subcommand}", "Error")

def handle_aircrack_command(args: List[str], context: Optional[str] = None) -> None:
    """Handle aircrack-ng suite commands with optional context from previous command"""
    # For now, just get context from prompts_lib
    combined_input = " ".join(args)
    if context:
        command_context = f"{combined_input}\n\nPrevious output:\n{context}"
    else:
        command_context = combined_input
        
    context_info = get_context_for_prompt(command_context)
    if context_info:
        display_output(context_info, "Aircrack-ng Context")
    else:
        # Execute the actual aircrack command
        cmd, explanation = parse_tool_command(combined_input)
        if cmd:
            if RICH_AVAILABLE and explanation:
                console.print(f"[italic]{explanation}[/italic]")
            output = execute_tool_command(cmd)
            display_output(output, "Command Output")
        else:
            display_output("Could not parse aircrack command", "Error")

def handle_scan_command(args: List[str]) -> None:
    """Handle network scanning commands"""
    if len(args) < 2:
        display_output("Missing subcommand. Use 'scan networks <interface>'", "Error")
        return
    
    subcommand = args[1].lower()
    
    if subcommand == "networks":
        if len(args) < 3:
            display_output("Missing interface name. Use 'scan networks <interface>'", "Error")
            return
        
        interface_name = args[2]
        
        # Check if interface is in monitor mode
        interfaces = interface_manager.get_wireless_interfaces()
        is_monitor = False
        for iface in interfaces:
            if iface["name"] == interface_name and iface.get("mode") == "monitor":
                is_monitor = True
                break
        
        if not is_monitor:
            if RICH_AVAILABLE:
                console.print(f"[yellow]Interface {interface_name} is not in monitor mode.[/yellow]")
                put_in_monitor = Confirm.ask("Do you want to put it in monitor mode now?")
                if put_in_monitor:
                    result = interface_manager.enable_monitor_mode(interface_name)
                    console.print(result)
                else:
                    return
            else:
                print(f"Interface {interface_name} is not in monitor mode.")
                put_in_monitor = input("Do you want to put it in monitor mode now? (y/n) ").lower() == 'y'
                if put_in_monitor:
                    result = interface_manager.enable_monitor_mode(interface_name)
                    print(result)
                else:
                    return
        
        # Use airodump-ng to scan for networks
        display_output(f"Starting network scan with {interface_name}...\nPress Ctrl+C to stop the scan.", "Scan")
        
        try:
            cmd = ["airodump-ng", interface_name]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            if RICH_AVAILABLE:
                console.print("[bold]Press Ctrl+C to stop scanning[/bold]")
            else:
                print("Press Ctrl+C to stop scanning")
                
            # Let airodump-ng run until user interrupts
            process.wait()
        except KeyboardInterrupt:
            process.terminate()
            display_output("Scan interrupted by user", "Scan Stopped")
        except Exception as e:
            display_output(f"Error during scan: {str(e)}", "Error")
    else:
        display_output(f"Unknown scan subcommand: {subcommand}", "Error")

def handle_capture_command(args: List[str]) -> None:
    """Handle packet capture commands"""
    if len(args) < 2:
        display_output("Missing subcommand. Use 'capture start <interface> <bssid> <channel>' or 'capture stop'", "Error")
        return
    
    subcommand = args[1].lower()
    
    if subcommand == "start":
        # Check arguments
        if len(args) < 5:
            display_output("Missing parameters. Use 'capture start <interface> <bssid> <channel>'", "Error")
            return
        
        interface_name = args[2]
        bssid = args[3]
        channel = args[4]
        
        output_file = f"paw_capture_{bssid.replace(':', '')}"
        
        # Ensure interface is in monitor mode
        interfaces = interface_manager.get_wireless_interfaces()
        is_monitor = False
        for iface in interfaces:
            if iface["name"] == interface_name and iface.get("mode") == "monitor":
                is_monitor = True
                break
        
        if not is_monitor:
            if RICH_AVAILABLE:
                console.print(f"[yellow]Interface {interface_name} is not in monitor mode.[/yellow]")
                put_in_monitor = Confirm.ask("Do you want to put it in monitor mode now?")
                if put_in_monitor:
                    result = interface_manager.enable_monitor_mode(interface_name)
                    console.print(result)
                else:
                    return
            else:
                print(f"Interface {interface_name} is not in monitor mode.")
                put_in_monitor = input("Do you want to put it in monitor mode now? (y/n) ").lower() == 'y'
                if put_in_monitor:
                    result = interface_manager.enable_monitor_mode(interface_name)
                    print(result)
                else:
                    return
        
        # Start capture
        try:
            cmd = [
                "airodump-ng", 
                "-c", channel,
                "--bssid", bssid,
                "-w", output_file,
                interface_name
            ]
            
            if RICH_AVAILABLE:
                console.print(f"[green]Starting capture on {interface_name} for BSSID {bssid} on channel {channel}[/green]")
                console.print(f"[green]Output will be saved to {output_file}[/green]")
                console.print("[bold]Press Ctrl+C to stop capture[/bold]")
            else:
                print(f"Starting capture on {interface_name} for BSSID {bssid} on channel {channel}")
                print(f"Output will be saved to {output_file}")
                print("Press Ctrl+C to stop capture")
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            # Store process for stop command
            interface_manager.set_active_capture(process, output_file)
            
            # Let airodump-ng run until user interrupts
            process.wait()
        except KeyboardInterrupt:
            process.terminate()
            display_output("Capture interrupted by user", "Capture Stopped")
        except Exception as e:
            display_output(f"Error during capture: {str(e)}", "Error")
    
    elif subcommand == "stop":
        # Stop the active capture
        if interface_manager.active_capture:
            interface_manager.active_capture.terminate()
            display_output(f"Capture stopped. Output saved to {interface_manager.capture_file}", "Capture Stopped")
            interface_manager.active_capture = None
            interface_manager.capture_file = None
        else:
            display_output("No active capture to stop", "Error")
    
    else:
        display_output(f"Unknown capture subcommand: {subcommand}", "Error")

def handle_attack_command(args: List[str]) -> None:
    """Handle attack commands"""
    if len(args) < 2:
        display_output("Missing attack type. Use 'attack deauth <interface> <bssid> <client> [count]'", "Error")
        return
    
    attack_type = args[1].lower()
    
    if attack_type == "deauth":
        # Check arguments
        if len(args) < 5:
            display_output("Missing parameters. Use 'attack deauth <interface> <bssid> <client> [count]'", "Error")
            return
        
        interface_name = args[2]
        bssid = args[3]
        client = args[4]
        count = args[5] if len(args) > 5 else "0"  # 0 means continuous
        
        # Ensure interface is in monitor mode
        interfaces = interface_manager.get_wireless_interfaces()
        is_monitor = False
        for iface in interfaces:
            if iface["name"] == interface_name and iface.get("mode") == "monitor":
                is_monitor = True
                break
        
        if not is_monitor:
            if RICH_AVAILABLE:
                console.print(f"[yellow]Interface {interface_name} is not in monitor mode.[/yellow]")
                put_in_monitor = Confirm.ask("Do you want to put it in monitor mode now?")
                if put_in_monitor:
                    result = interface_manager.enable_monitor_mode(interface_name)
                    console.print(result)
                else:
                    return
            else:
                print(f"Interface {interface_name} is not in monitor mode.")
                put_in_monitor = input("Do you want to put it in monitor mode now? (y/n) ").lower() == 'y'
                if put_in_monitor:
                    result = interface_manager.enable_monitor_mode(interface_name)
                    print(result)
                else:
                    return
        
        # Execute deauth attack
        try:
            if client.lower() == "broadcast":
                client = "FF:FF:FF:FF:FF:FF"
            
            cmd = [
                "aireplay-ng",
                "-0", count,
                "-a", bssid,
                "-c", client,
                interface_name
            ]
            
            if RICH_AVAILABLE:
                if count == "0":
                    console.print(f"[bold red]Starting continuous deauthentication attack from {interface_name}[/bold red]")
                else:
                    console.print(f"[bold red]Sending {count} deauthentication packets from {interface_name}[/bold red]")
                console.print(f"[red]Target AP: {bssid}, Client: {client}[/red]")
                console.print("[bold]Press Ctrl+C to stop the attack[/bold]")
            else:
                if count == "0":
                    print(f"Starting continuous deauthentication attack from {interface_name}")
                else:
                    print(f"Sending {count} deauthentication packets from {interface_name}")
                print(f"Target AP: {bssid}, Client: {client}")
                print("Press Ctrl+C to stop the attack")
            
            subprocess.run(cmd)
            
        except KeyboardInterrupt:
            display_output("Attack interrupted by user", "Attack Stopped")
        except Exception as e:
            display_output(f"Error during attack: {str(e)}", "Error")
    
    else:
        display_output(f"Unknown attack type: {attack_type}", "Error")

def handle_database_command(args: List[str]) -> None:
    """Handle database commands"""
    if len(args) < 2:
        display_output("Missing subcommand. Use 'db list' or 'db export <filename>'", "Error")
        return
    
    subcommand = args[1].lower()
    
    if subcommand == "list":
        # List networks in database
        networks = db.get_all_networks()
        
        if not networks:
            display_output("No networks in database", "Database")
            return
        
        if RICH_AVAILABLE:
            table = Table(title="Saved Networks")
            table.add_column("BSSID", style="cyan")
            table.add_column("ESSID", style="green")
            table.add_column("Channel", style="yellow")
            table.add_column("Encryption", style="magenta")
            table.add_column("First Seen", style="blue")
            
            for network in networks:
                table.add_row(
                    network.get("bssid", "Unknown"),
                    network.get("essid", "Unknown"),
                    str(network.get("channel", "?")),
                    network.get("encryption", "Unknown"),
                    network.get("first_seen", "Unknown")
                )
            
            console.print(table)
        else:
            print("Saved Networks:")
            for network in networks:
                print(f"  {network.get('bssid', 'Unknown')} - {network.get('essid', 'Unknown')} - CH:{network.get('channel', '?')} - {network.get('encryption', 'Unknown')}")
    
    elif subcommand == "export":
        # Export database to CSV
        if len(args) < 3:
            display_output("Missing filename. Use 'db export <filename>'", "Error")
            return
        
        filename = args[2]
        result = db.export_to_csv(filename)
        display_output(result, "Database Export")
    
    else:
        display_output(f"Unknown database subcommand: {subcommand}", "Error")

def main():
    parser = argparse.ArgumentParser(description="PAW - Prompt Assistant for Wireless")
    parser.add_argument("--version", action="version", version="PAW v0.1")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    # Add other arguments as needed
    
    args = parser.parse_args()
    
    # Run in interactive mode by default or if specified
    if args.interactive or len(sys.argv) == 1:
        interactive_mode()
    
if __name__ == "__main__":
    main() 