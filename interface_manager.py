#!/usr/bin/env python3
# PAW Interface Manager
# Handles wireless interface management functions

import os
import subprocess
import re
from typing import List, Dict, Optional, Any

class InterfaceManager:
    """Class to manage wireless network interfaces"""
    
    def __init__(self):
        """Initialize the interface manager"""
        self.active_capture = None
        self.capture_file = None
    
    def get_wireless_interfaces(self) -> List[Dict[str, str]]:
        """
        Get a list of wireless interfaces on the system
        
        Returns:
            List of dictionaries with interface information
        """
        interfaces = []
        
        try:
            # Try using iw dev first (Linux)
            result = subprocess.run(["iw", "dev"], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse iw dev output
                current_interface = None
                for line in result.stdout.splitlines():
                    line = line.strip()
                    
                    if "Interface" in line:
                        if current_interface:
                            interfaces.append(current_interface)
                        
                        interface_name = line.split("Interface", 1)[1].strip()
                        current_interface = {"name": interface_name, "mode": "managed"}
                    
                    if current_interface and "type" in line:
                        mode = line.split("type", 1)[1].strip()
                        current_interface["mode"] = mode
                
                # Add the last interface if exists
                if current_interface:
                    interfaces.append(current_interface)
                
                # Get MAC addresses for each interface
                for interface in interfaces:
                    mac = self._get_mac_address(interface["name"])
                    if mac:
                        interface["mac_address"] = mac
            
            # If iw dev fails or returns no interfaces, try ip link (more generic)
            if not interfaces and os.name != "nt":  # Not on Windows
                result = subprocess.run(["ip", "link"], capture_output=True, text=True)
                
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if ": " in line and "<" in line and ">" in line:
                            parts = line.split(": ", 1)
                            if len(parts) > 1 and "lo" not in parts[1]:  # Skip loopback
                                interface_name = parts[1].split(":", 1)[0]
                                # Check if it's wireless (wlan, mon, etc.)
                                if any(keyword in interface_name for keyword in ["wlan", "mon", "wifi", "wl", "ath"]):
                                    interface = {"name": interface_name, "mode": "unknown"}
                                    mac = self._get_mac_address(interface_name)
                                    if mac:
                                        interface["mac_address"] = mac
                                    interfaces.append(interface)
            
            # On Windows, try netsh (or other Windows-specific methods)
            if not interfaces and os.name == "nt":
                result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True)
                
                if result.returncode == 0:
                    current_interface = None
                    for line in result.stdout.splitlines():
                        line = line.strip()
                        
                        if "Name" in line and ":" in line:
                            if current_interface:
                                interfaces.append(current_interface)
                            
                            interface_name = line.split(":", 1)[1].strip()
                            current_interface = {"name": interface_name, "mode": "managed"}
                        
                        if current_interface and "Physical address" in line and ":" in line:
                            mac = line.split(":", 1)[1].strip()
                            current_interface["mac_address"] = mac
                    
                    # Add the last interface if exists
                    if current_interface:
                        interfaces.append(current_interface)
            
        except Exception as e:
            print(f"Error getting wireless interfaces: {e}")
        
        return interfaces
    
    def _get_mac_address(self, interface_name: str) -> Optional[str]:
        """Get MAC address for a given interface"""
        try:
            # Try using ip link command (Linux)
            result = subprocess.run(["ip", "link", "show", interface_name], capture_output=True, text=True)
            
            if result.returncode == 0:
                mac_match = re.search(r'link/ether\s+([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})', result.stdout)
                if mac_match:
                    return mac_match.group(1).upper()
            
            # Fallback to ifconfig for systems that have it
            result = subprocess.run(["ifconfig", interface_name], capture_output=True, text=True)
            
            if result.returncode == 0:
                mac_match = re.search(r'(?:ether|HWaddr)\s+([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})', result.stdout)
                if mac_match:
                    return mac_match.group(1).upper()
            
        except Exception as e:
            print(f"Error getting MAC address: {e}")
        
        return None
    
    def enable_monitor_mode(self, interface_name: str) -> str:
        """
        Enable monitor mode on a wireless interface
        
        Args:
            interface_name: Name of the interface to put in monitor mode
            
        Returns:
            Status message
        """
        try:
            # Check if airmon-ng is available
            airmon_check = subprocess.run(["which", "airmon-ng"], capture_output=True, text=True)
            if airmon_check.returncode != 0:
                return "Error: airmon-ng not found. Make sure it's installed."
            
            # Kill potential interfering processes
            kill_cmd = subprocess.run(["airmon-ng", "check", "kill"], capture_output=True, text=True)
            
            # Start monitor mode
            result = subprocess.run(["airmon-ng", "start", interface_name], capture_output=True, text=True)
            
            # Try to find the monitor interface name from the output
            monitor_interface = None
            if "monitor mode enabled" in result.stdout:
                # Modern airmon-ng often adds 'mon' to the interface name
                monitor_interface = f"{interface_name}mon"
            else:
                # Try to parse the output to find the actual name
                match = re.search(r'monitor mode (?:enabled|vif) on\s+([^\s\)]+)', result.stdout)
                if match:
                    monitor_interface = match.group(1)
            
            if monitor_interface:
                return f"Monitor mode enabled on {interface_name}. New interface: {monitor_interface}"
            else:
                # If we can't determine the new interface name, just return success
                return f"Monitor mode enabled on {interface_name}. Check 'iwconfig' to see the new interface name."
                
        except Exception as e:
            return f"Error enabling monitor mode: {e}"
    
    def set_managed_mode(self, interface_name: str) -> str:
        """
        Set an interface to managed mode
        
        Args:
            interface_name: Name of the interface to put in managed mode
            
        Returns:
            Status message
        """
        try:
            # Check if airmon-ng is available
            airmon_check = subprocess.run(["which", "airmon-ng"], capture_output=True, text=True)
            if airmon_check.returncode != 0:
                return "Error: airmon-ng not found. Make sure it's installed."
            
            # Stop monitor mode
            result = subprocess.run(["airmon-ng", "stop", interface_name], capture_output=True, text=True)
            
            # Try to find the managed interface name from the output
            managed_interface = None
            match = re.search(r'(?:mode disabled on|switched to managed mode)\s+([^\s\)]+)', result.stdout)
            if match:
                managed_interface = match.group(1)
                
            # If monitor mode is stopped but we don't know the new interface name
            if not managed_interface and "monitor mode disabled" in result.stdout:
                # Remove 'mon' from the interface name if it exists
                if interface_name.endswith("mon"):
                    managed_interface = interface_name[:-3]
                else:
                    managed_interface = interface_name
            
            if managed_interface:
                return f"Managed mode set on {interface_name}. New interface: {managed_interface}"
            else:
                # If we can't determine the new interface name, just return success
                return f"Managed mode set. Check 'iwconfig' to see the new interface name."
                
        except Exception as e:
            return f"Error setting managed mode: {e}"
    
    def set_active_capture(self, process, filename: str) -> None:
        """Store information about an active capture process"""
        self.active_capture = process
        self.capture_file = filename
    
    def disable_all_monitor_modes(self) -> None:
        """Disable monitor mode on all interfaces"""
        try:
            interfaces = self.get_wireless_interfaces()
            for interface in interfaces:
                if interface.get("mode") == "monitor":
                    self.set_managed_mode(interface["name"])
                    
            # Also kill any active capture process
            if self.active_capture:
                self.active_capture.terminate()
                self.active_capture = None
                self.capture_file = None
                
        except Exception as e:
            print(f"Error disabling monitor modes: {e}")

if __name__ == "__main__":
    # Test the interface manager
    manager = InterfaceManager()
    interfaces = manager.get_wireless_interfaces()
    
    print("Detected wireless interfaces:")
    for interface in interfaces:
        print(f"  {interface['name']} - MAC: {interface.get('mac_address', 'Unknown')} - Mode: {interface.get('mode', 'Unknown')}") 