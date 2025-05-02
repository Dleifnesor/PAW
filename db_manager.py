#!/usr/bin/env python3
# PAW Database Manager
# Handles storage and retrieval of captured network information

import os
import csv
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any

class NetworkDatabase:
    """Class to manage storage of wireless networks and related information"""
    
    def __init__(self, db_path: str = "paw_networks.db"):
        """Initialize the database connection"""
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self._initialize_db()
        
    def _initialize_db(self):
        """Create the database and tables if they don't exist"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            
            # Create networks table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS networks (
                id INTEGER PRIMARY KEY,
                bssid TEXT UNIQUE,
                essid TEXT,
                channel INTEGER,
                encryption TEXT,
                signal_strength INTEGER,
                first_seen TEXT,
                last_seen TEXT,
                latitude REAL,
                longitude REAL,
                notes TEXT
            )
            ''')
            
            # Create clients table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY,
                mac_address TEXT UNIQUE,
                network_id INTEGER,
                first_seen TEXT,
                last_seen TEXT,
                probed_essids TEXT,
                FOREIGN KEY (network_id) REFERENCES networks (id)
            )
            ''')
            
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
            
    def add_network(self, network_data: Dict[str, Any]) -> bool:
        """
        Add or update a network in the database
        
        Args:
            network_data: Dictionary containing network information
                Required keys: bssid
                Optional keys: essid, channel, encryption, signal_strength, 
                               latitude, longitude, notes
                
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if BSSID is provided
            if 'bssid' not in network_data:
                return False
                
            # Prepare current timestamp
            now = datetime.now().isoformat()
            
            # Check if network exists
            self.cursor.execute(
                "SELECT id, first_seen FROM networks WHERE bssid = ?", 
                (network_data['bssid'],)
            )
            result = self.cursor.fetchone()
            
            if result:
                # Network exists, update it
                network_id, first_seen = result
                
                # Prepare update statement
                update_fields = []
                params = []
                
                for key, value in network_data.items():
                    if key != 'bssid' and value is not None:
                        update_fields.append(f"{key} = ?")
                        params.append(value)
                
                # Always update last_seen
                update_fields.append("last_seen = ?")
                params.append(now)
                
                # Add bssid as the last parameter for WHERE clause
                params.append(network_data['bssid'])
                
                # Execute update
                self.cursor.execute(
                    f"UPDATE networks SET {', '.join(update_fields)} WHERE bssid = ?",
                    params
                )
                
                return True
            else:
                # New network, insert it
                keys = ['bssid']
                values = [network_data['bssid']]
                placeholders = ['?']
                
                for key, value in network_data.items():
                    if key != 'bssid' and value is not None:
                        keys.append(key)
                        values.append(value)
                        placeholders.append('?')
                
                # Add timestamps
                keys.extend(['first_seen', 'last_seen'])
                values.extend([now, now])
                placeholders.extend(['?', '?'])
                
                # Execute insert
                self.cursor.execute(
                    f"INSERT INTO networks ({', '.join(keys)}) VALUES ({', '.join(placeholders)})",
                    values
                )
                
                self.connection.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"Error adding network: {e}")
            return False
    
    def add_client(self, client_data: Dict[str, Any]) -> bool:
        """
        Add or update a client in the database
        
        Args:
            client_data: Dictionary containing client information
                Required keys: mac_address
                Optional keys: network_id, probed_essids
                
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if MAC address is provided
            if 'mac_address' not in client_data:
                return False
                
            # Prepare current timestamp
            now = datetime.now().isoformat()
            
            # Check if client exists
            self.cursor.execute(
                "SELECT id, first_seen FROM clients WHERE mac_address = ?", 
                (client_data['mac_address'],)
            )
            result = self.cursor.fetchone()
            
            if result:
                # Client exists, update it
                client_id, first_seen = result
                
                # Prepare update statement
                update_fields = []
                params = []
                
                for key, value in client_data.items():
                    if key != 'mac_address' and value is not None:
                        update_fields.append(f"{key} = ?")
                        params.append(value)
                
                # Always update last_seen
                update_fields.append("last_seen = ?")
                params.append(now)
                
                # Add mac_address as the last parameter for WHERE clause
                params.append(client_data['mac_address'])
                
                # Execute update
                self.cursor.execute(
                    f"UPDATE clients SET {', '.join(update_fields)} WHERE mac_address = ?",
                    params
                )
                
                self.connection.commit()
                return True
            else:
                # New client, insert it
                keys = ['mac_address']
                values = [client_data['mac_address']]
                placeholders = ['?']
                
                for key, value in client_data.items():
                    if key != 'mac_address' and value is not None:
                        keys.append(key)
                        values.append(value)
                        placeholders.append('?')
                
                # Add timestamps
                keys.extend(['first_seen', 'last_seen'])
                values.extend([now, now])
                placeholders.extend(['?', '?'])
                
                # Execute insert
                self.cursor.execute(
                    f"INSERT INTO clients ({', '.join(keys)}) VALUES ({', '.join(placeholders)})",
                    values
                )
                
                self.connection.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"Error adding client: {e}")
            return False
    
    def get_network(self, bssid: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific network"""
        try:
            self.cursor.execute(
                "SELECT * FROM networks WHERE bssid = ?", 
                (bssid,)
            )
            result = self.cursor.fetchone()
            
            if result:
                # Convert to dictionary
                columns = [col[0] for col in self.cursor.description]
                return dict(zip(columns, result))
            else:
                return None
                
        except sqlite3.Error as e:
            print(f"Error getting network: {e}")
            return None
    
    def get_all_networks(self) -> List[Dict[str, Any]]:
        """Get all networks from the database"""
        try:
            self.cursor.execute("SELECT * FROM networks ORDER BY last_seen DESC")
            results = self.cursor.fetchall()
            
            # Convert to list of dictionaries
            columns = [col[0] for col in self.cursor.description]
            return [dict(zip(columns, row)) for row in results]
                
        except sqlite3.Error as e:
            print(f"Error getting networks: {e}")
            return []
    
    def get_clients_for_network(self, network_id: int) -> List[Dict[str, Any]]:
        """Get all clients associated with a specific network"""
        try:
            self.cursor.execute(
                "SELECT * FROM clients WHERE network_id = ? ORDER BY last_seen DESC", 
                (network_id,)
            )
            results = self.cursor.fetchall()
            
            # Convert to list of dictionaries
            columns = [col[0] for col in self.cursor.description]
            return [dict(zip(columns, row)) for row in results]
                
        except sqlite3.Error as e:
            print(f"Error getting clients: {e}")
            return []
    
    def export_to_csv(self, filename: str) -> str:
        """
        Export the database to a CSV file
        
        Args:
            filename: Name of the CSV file to create
            
        Returns:
            Status message
        """
        try:
            # Ensure the filename has .csv extension
            if not filename.lower().endswith('.csv'):
                filename += '.csv'
                
            networks = self.get_all_networks()
            
            if not networks:
                return "No networks to export"
                
            with open(filename, 'w', newline='') as csvfile:
                # Get all field names from the first network
                fieldnames = networks[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for network in networks:
                    writer.writerow(network)
                    
            return f"Exported {len(networks)} networks to {filename}"
                
        except Exception as e:
            return f"Error exporting to CSV: {e}"
    
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            
    def __del__(self):
        """Destructor to ensure database is closed"""
        self.close()

if __name__ == "__main__":
    # Test the database manager
    db = NetworkDatabase()
    
    # Add a test network
    test_network = {
        'bssid': '00:11:22:33:44:55',
        'essid': 'Test Network',
        'channel': 6,
        'encryption': 'WPA2',
        'signal_strength': -65
    }
    
    if db.add_network(test_network):
        print("Added test network")
    
    # Add a test client
    test_client = {
        'mac_address': 'AA:BB:CC:DD:EE:FF',
        'network_id': 1,
        'probed_essids': 'Test Network,Another Network'
    }
    
    if db.add_client(test_client):
        print("Added test client")
    
    # Get and print networks
    networks = db.get_all_networks()
    print(f"Found {len(networks)} networks:")
    for network in networks:
        print(f"  {network['bssid']} - {network['essid']}")
    
    # Export to CSV
    result = db.export_to_csv('test_export.csv')
    print(result)
    
    # Close the database
    db.close() 