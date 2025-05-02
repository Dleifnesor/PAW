#!/usr/bin/env python3
# Interface Manager for PAW
# Handles wireless interface management tasks

import subprocess
import re
import os
import time
import platform
from typing import List, Dict, Optional, Any

class InterfaceManager:
    """Class to manage wireless interfaces"""
    
    def __init__(self):
        """Initialize the interface manager"""
        self.active_capture = None
        self.capture_file = None
    
    def get_wireless_interfaces(self) -> List[Dict[str, str]]:
        """Get a list of wireless interfaces"""
        interfaces = []
        
        try:
            # Handle different OS platforms
            if platform.system() == "Linux":
                # Use iw dev on Linux
                output = subprocess.check_output(["iw", "dev"], universal_newlines=True)
                
                # Parse iw dev output
                current_interface = None
                current_info = {}
                
                for line in output.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Interface line
                    if "Interface" in line:
                        # Save previous interface if exists
                        if current_interface and current_info:
                            # Get MAC address for the interface
                            try:
                                mac_output = subprocess.check_output(["macchanger", "-s", current_interface], 
                                                                    universal_newlines=True, stderr=subprocess.DEVNULL)
                                mac_match = re.search(r"Current MAC:\s+([0-9A-F:]{17})", mac_output)
                                if mac_match:
                                    current_info["mac_address"] = mac_match.group(1)
                                
                                # Check if this is permanent or changed MAC
                                perm_match = re.search(r"Permanent MAC:\s+([0-9A-F:]{17})", mac_output)
                                if perm_match and perm_match.group(1) != current_info.get("mac_address"):
                                    current_info["mac_changed"] = True
                                    current_info["permanent_mac"] = perm_match.group(1)
                                else:
                                    current_info["mac_changed"] = False
                                    
                            except (subprocess.SubprocessError, FileNotFoundError):
                                # If macchanger not available, try using ifconfig
                                try:
                                    ifconfig_output = subprocess.check_output(["ifconfig", current_interface], 
                                                                           universal_newlines=True, stderr=subprocess.DEVNULL)
                                    mac_match = re.search(r"ether\s+([0-9a-f:]{17})", ifconfig_output, re.IGNORECASE)
                                    if mac_match:
                                        current_info["mac_address"] = mac_match.group(1)
                                except (subprocess.SubprocessError, FileNotFoundError):
                                    current_info["mac_address"] = "Unknown"
                                    
                            interfaces.append(current_info)
                        
                        # Start a new interface
                        current_interface = line.split()[-1]
                        current_info = {"name": current_interface}
                    
                    # Type line (managed, monitor, etc.)
                    elif "type" in line and current_interface:
                        type_match = re.search(r"type\s+(\w+)", line)
                        if type_match:
                            current_info["mode"] = type_match.group(1)
                
                # Add the last interface
                if current_interface and current_info:
                    # Get MAC address for the interface
                    try:
                        mac_output = subprocess.check_output(["macchanger", "-s", current_interface], 
                                                           universal_newlines=True, stderr=subprocess.DEVNULL)
                        mac_match = re.search(r"Current MAC:\s+([0-9A-F:]{17})", mac_output)
                        if mac_match:
                            current_info["mac_address"] = mac_match.group(1)
                            
                        # Check if this is permanent or changed MAC
                        perm_match = re.search(r"Permanent MAC:\s+([0-9A-F:]{17})", mac_output)
                        if perm_match and perm_match.group(1) != current_info.get("mac_address"):
                            current_info["mac_changed"] = True
                            current_info["permanent_mac"] = perm_match.group(1)
                        else:
                            current_info["mac_changed"] = False
                            
                    except (subprocess.SubprocessError, FileNotFoundError):
                        # If macchanger not available, try using ifconfig
                        try:
                            ifconfig_output = subprocess.check_output(["ifconfig", current_interface], 
                                                                  universal_newlines=True, stderr=subprocess.DEVNULL)
                            mac_match = re.search(r"ether\s+([0-9a-f:]{17})", ifconfig_output, re.IGNORECASE)
                            if mac_match:
                                current_info["mac_address"] = mac_match.group(1)
                        except (subprocess.SubprocessError, FileNotFoundError):
                            current_info["mac_address"] = "Unknown"
                            
                    interfaces.append(current_info)
            
            elif platform.system() == "Windows":
                # Use netsh on Windows
                output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], universal_newlines=True)
                
                # Parse netsh output
                current_interface = None
                current_info = {}
                
                for line in output.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                        
                    if "Name" in line and ":" in line:
                        # Save previous interface if exists
                        if current_interface and current_info:
                            interfaces.append(current_info)
                        
                        # Start a new interface
                        current_interface = line.split(":", 1)[1].strip()
                        current_info = {"name": current_interface, "mode": "managed"}  # Windows interfaces are always in managed mode
                    
                    elif "Physical address" in line and ":" in line and current_interface:
                        mac = line.split(":", 1)[1].strip()
                        current_info["mac_address"] = mac
                
                # Add the last interface
                if current_interface and current_info:
                    interfaces.append(current_info)
            
            else:
                # For other platforms, provide a limited implementation
                # This is a very basic fallback that won't work well
                output = subprocess.check_output(["ifconfig"], universal_newlines=True)
                for line in output.splitlines():
                    if "wlan" in line or "eth" in line or "en" in line:
                        interface_name = line.split(":")[0].strip()
                        interfaces.append({"name": interface_name, "mode": "unknown", "mac_address": "Unknown"})
        
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Warning: Couldn't get wireless interfaces: {e}")
            # Provide a minimal fallback
            if platform.system() == "Linux":
                try:
                    # Try to get interfaces from /proc
                    with open("/proc/net/dev") as f:
                        for line in f:
                            if ":" in line and ("wlan" in line or "eth" in line or "mon" in line):
                                interface_name = line.split(":")[0].strip()
                                interfaces.append({"name": interface_name, "mode": "unknown", "mac_address": "Unknown"})
                except Exception:
                    pass
        
        return interfaces
    
    def enable_monitor_mode(self, interface_name: str) -> str:
        """Enable monitor mode on an interface"""
        if platform.system() != "Linux":
            return f"Monitor mode is only supported on Linux, not on {platform.system()}"
        
        try:
            # Check if airmon-ng is available
            airmon_available = False
            try:
                subprocess.check_call(["which", "airmon-ng"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                airmon_available = True
            except subprocess.SubprocessError:
                pass
            
            if airmon_available:
                # Kill processes that might interfere with monitor mode
                subprocess.run(["airmon-ng", "check", "kill"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Enable monitor mode
                subprocess.run(["airmon-ng", "start", interface_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Determine the new interface name (usually interface_name + "mon")
                time.sleep(1)  # Give it a moment to change
                interfaces = self.get_wireless_interfaces()
                for interface in interfaces:
                    if interface_name in interface["name"] and "mon" in interface["name"]:
                        return f"Monitor mode enabled on {interface['name']} (MAC: {interface.get('mac_address', 'Unknown')})"
                
                # If we can't find the mon interface, assume it's the same name
                return f"Monitor mode may be enabled on {interface_name}, but couldn't confirm"
            else:
                # Alternative method using iw
                try:
                    # Set interface down
                    subprocess.run(["ifconfig", interface_name, "down"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Set monitor mode
                    subprocess.run(["iw", "dev", interface_name, "set", "monitor", "none"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Set interface up
                    subprocess.run(["ifconfig", interface_name, "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    return f"Monitor mode enabled on {interface_name} (using iw method)"
                except subprocess.SubprocessError:
                    return f"Failed to enable monitor mode on {interface_name} using iw method"
        
        except subprocess.SubprocessError as e:
            return f"Error enabling monitor mode: {e}"
    
    def set_managed_mode(self, interface_name: str) -> str:
        """Set an interface to managed mode"""
        if platform.system() != "Linux":
            return f"Setting managed mode is only supported on Linux, not on {platform.system()}"
        
        try:
            # Check if airmon-ng is available
            airmon_available = False
            try:
                subprocess.check_call(["which", "airmon-ng"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                airmon_available = True
            except subprocess.SubprocessError:
                pass
            
            if airmon_available and "mon" in interface_name:
                # Stop monitor mode with airmon-ng
                subprocess.run(["airmon-ng", "stop", interface_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Determine the new interface name (usually interface_name without "mon")
                time.sleep(1)  # Give it a moment to change
                interfaces = self.get_wireless_interfaces()
                base_name = interface_name.replace("mon", "")
                for interface in interfaces:
                    if base_name in interface["name"] and "mon" not in interface["name"]:
                        # Start network manager if it was killed
                        subprocess.run(["service", "NetworkManager", "start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return f"Managed mode enabled on {interface['name']} (MAC: {interface.get('mac_address', 'Unknown')})"
                
                # If we can't find the managed interface, assume it's the base name
                # Start network manager if it was killed
                subprocess.run(["service", "NetworkManager", "start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Managed mode may be enabled on {base_name}, but couldn't confirm"
            else:
                # Alternative method using iw
                try:
                    # Set interface down
                    subprocess.run(["ifconfig", interface_name, "down"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Set managed mode
                    subprocess.run(["iw", "dev", interface_name, "set", "type", "managed"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Set interface up
                    subprocess.run(["ifconfig", interface_name, "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Restart network manager
                    subprocess.run(["service", "NetworkManager", "start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    return f"Managed mode enabled on {interface_name} (using iw method)"
                except subprocess.SubprocessError:
                    return f"Failed to enable managed mode on {interface_name} using iw method"
        
        except subprocess.SubprocessError as e:
            return f"Error setting managed mode: {e}"
    
    def set_active_capture(self, process, output_file):
        """Store the active capture process and filename"""
        self.active_capture = process
        self.capture_file = output_file
    
    def disable_all_monitor_modes(self):
        """Disable monitor mode on all interfaces"""
        if platform.system() != "Linux":
            return
        
        try:
            # First, kill any active captures
            if self.active_capture:
                self.active_capture.terminate()
                self.active_capture = None
            
            # Get all interfaces
            interfaces = self.get_wireless_interfaces()
            
            # Check if airmon-ng is available
            airmon_available = False
            try:
                subprocess.check_call(["which", "airmon-ng"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                airmon_available = True
            except subprocess.SubprocessError:
                pass
            
            # Disable monitor mode on all monitor interfaces
            for interface in interfaces:
                if interface.get("mode") == "monitor":
                    if airmon_available:
                        subprocess.run(["airmon-ng", "stop", interface["name"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        # Fallback to iw method
                        try:
                            subprocess.run(["ifconfig", interface["name"], "down"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            subprocess.run(["iw", "dev", interface["name"], "set", "type", "managed"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            subprocess.run(["ifconfig", interface["name"], "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except subprocess.SubprocessError:
                            pass
            
            # Start network manager if it was killed
            subprocess.run(["service", "NetworkManager", "start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        except Exception as e:
            print(f"Warning during monitor mode cleanup: {e}")
    
    def change_mac_address(self, interface_name: str, new_mac: Optional[str] = None, random: bool = False,
                          same_vendor: bool = False, random_vendor: bool = False, permanent: bool = False) -> str:
        """Change the MAC address of an interface using macchanger"""
        if platform.system() != "Linux":
            return f"Changing MAC address is only supported on Linux, not on {platform.system()}"
        
        try:
            # Check if macchanger is available
            try:
                subprocess.check_call(["which", "macchanger"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.SubprocessError:
                return "macchanger is not installed. Install with: sudo apt-get install macchanger"
            
            # Take down the interface
            subprocess.run(["ifconfig", interface_name, "down"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Determine which macchanger option to use
            if permanent:
                result = subprocess.run(["macchanger", "-p", interface_name], capture_output=True, text=True)
                mac_type = "permanent (original)"
            elif new_mac:
                result = subprocess.run(["macchanger", "-m", new_mac, interface_name], capture_output=True, text=True)
                mac_type = f"specific ({new_mac})"
            elif same_vendor:
                result = subprocess.run(["macchanger", "-a", interface_name], capture_output=True, text=True)
                mac_type = "same vendor random"
            elif random_vendor:
                result = subprocess.run(["macchanger", "-A", interface_name], capture_output=True, text=True)
                mac_type = "random vendor"
            elif random:
                result = subprocess.run(["macchanger", "-r", interface_name], capture_output=True, text=True)
                mac_type = "fully random"
            else:
                # Default to random
                result = subprocess.run(["macchanger", "-r", interface_name], capture_output=True, text=True)
                mac_type = "fully random"
            
            # Bring the interface back up
            subprocess.run(["ifconfig", interface_name, "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Extract new MAC from macchanger output
            new_mac_match = re.search(r"New MAC:\s+([0-9A-F:]{17})", result.stdout)
            if new_mac_match:
                new_mac_value = new_mac_match.group(1)
                return f"MAC address of {interface_name} changed to {new_mac_value} ({mac_type})"
            else:
                return f"MAC address change failed or couldn't confirm new MAC"
        
        except subprocess.SubprocessError as e:
            return f"Error changing MAC address: {e}"
        finally:
            # Make sure the interface is up even if something failed
            try:
                subprocess.run(["ifconfig", interface_name, "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
    
    def get_interface_mac(self, interface_name: str) -> Dict[str, str]:
        """Get current and permanent MAC addresses for an interface"""
        result = {
            "current_mac": "Unknown",
            "permanent_mac": "Unknown",
            "is_changed": False
        }
        
        if platform.system() != "Linux":
            return result
        
        try:
            # Try with macchanger first
            try:
                mac_output = subprocess.check_output(["macchanger", "-s", interface_name], 
                                                   universal_newlines=True, stderr=subprocess.DEVNULL)
                
                current_match = re.search(r"Current MAC:\s+([0-9A-F:]{17})", mac_output)
                if current_match:
                    result["current_mac"] = current_match.group(1)
                
                perm_match = re.search(r"Permanent MAC:\s+([0-9A-F:]{17})", mac_output)
                if perm_match:
                    result["permanent_mac"] = perm_match.group(1)
                    result["is_changed"] = (result["current_mac"] != result["permanent_mac"])
            except (subprocess.SubprocessError, FileNotFoundError):
                # Fall back to ifconfig
                try:
                    ifconfig_output = subprocess.check_output(["ifconfig", interface_name], 
                                                           universal_newlines=True, stderr=subprocess.DEVNULL)
                    mac_match = re.search(r"ether\s+([0-9a-f:]{17})", ifconfig_output, re.IGNORECASE)
                    if mac_match:
                        result["current_mac"] = mac_match.group(1)
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass
        except Exception as e:
            print(f"Error getting MAC address: {e}")
        
        return result 