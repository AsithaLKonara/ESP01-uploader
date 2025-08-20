#!/usr/bin/env python3
"""
WiFi Manager Module
Handles TCP/IP connections to ESP-01 modules over WiFi
"""

import socket
import json
import time
import threading
from typing import Optional, Dict, Any
import requests

class WiFiManager:
    """Manages WiFi connections to ESP-01 modules"""
    
    def __init__(self):
        self.connection = None
        self.connected = False
        self.ip_address = None
        self.port = None
        self.timeout = 10.0
        self.retry_count = 3
        self.retry_delay = 1.0
        
        # Connection lock for thread safety
        self.connection_lock = threading.Lock()
        
    def connect(self, ip_address: str, port: int) -> bool:
        """
        Connect to ESP-01 module over WiFi
        
        Args:
            ip_address: IP address of the ESP-01
            port: Port number for connection
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        with self.connection_lock:
            try:
                # Close existing connection
                self.disconnect()
                
                # Test connection with HTTP request first
                if self._test_http_connection(ip_address, port):
                    self.ip_address = ip_address
                    self.port = port
                    self.connected = True
                    return True
                    
                # Fallback to direct socket connection
                if self._test_socket_connection(ip_address, port):
                    self.ip_address = ip_address
                    self.port = port
                    self.connected = True
                    return True
                    
                return False
                
            except Exception as e:
                print(f"Connection error: {e}")
                return False
                
    def _test_http_connection(self, ip_address: str, port: int) -> bool:
        """Test HTTP connection to ESP-01"""
        try:
            url = f"http://{ip_address}:{port}/"
            response = requests.get(url, timeout=self.timeout)
            return response.status_code == 200
        except:
            return False
            
    def _test_socket_connection(self, ip_address: str, port: int) -> bool:
        """Test direct socket connection to ESP-01"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip_address, port))
            sock.close()
            return result == 0
        except:
            return False
            
    def disconnect(self):
        """Disconnect from ESP-01 module"""
        with self.connection_lock:
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
                
            self.connected = False
            self.ip_address = None
            self.port = None
            
    def is_connected(self) -> bool:
        """Check if connected to ESP-01"""
        return self.connected
        
    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send command to ESP-01 module
        
        Args:
            command: Command dictionary to send
            
        Returns:
            Dict: Response from ESP-01
        """
        if not self.is_connected():
            return {'success': False, 'error': 'Not connected'}
            
        with self.connection_lock:
            try:
                # Try HTTP POST first
                response = self._send_http_command(command)
                if response:
                    return response
                    
                # Fallback to socket connection
                return self._send_socket_command(command)
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
                
    def _send_http_command(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send command via HTTP POST"""
        try:
            url = f"http://{self.ip_address}:{self.port}/command"
            response = requests.post(
                url,
                json=command,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except:
            return None
            
    def _send_socket_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command via direct socket connection"""
        try:
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip_address, self.port))
            
            # Send command
            command_json = json.dumps(command) + '\n'
            sock.send(command_json.encode('utf-8'))
            
            # Receive response
            response_data = b''
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response_data += chunk
                if b'\n' in response_data:
                    break
                    
            sock.close()
            
            # Parse response
            try:
                response = json.loads(response_data.decode('utf-8').strip())
                return response
            except json.JSONDecodeError:
                return {'success': False, 'error': 'Invalid response format'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def send_file_chunk(self, chunk_data: bytes, chunk_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send file chunk to ESP-01
        
        Args:
            chunk_data: Binary chunk data
            chunk_info: Chunk information dictionary
            
        Returns:
            Dict: Response from ESP-01
        """
        if not self.is_connected():
            return {'success': False, 'error': 'Not connected'}
            
        with self.connection_lock:
            try:
                # Try HTTP POST with file data
                response = self._send_http_file_chunk(chunk_data, chunk_info)
                if response:
                    return response
                    
                # Fallback to socket
                return self._send_socket_file_chunk(chunk_data, chunk_info)
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
                
    def _send_http_file_chunk(self, chunk_data: bytes, chunk_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send file chunk via HTTP POST"""
        try:
            url = f"http://{self.ip_address}:{self.port}/upload"
            
            # Prepare multipart form data
            files = {'chunk': ('chunk.bin', chunk_data, 'application/octet-stream')}
            data = {'info': json.dumps(chunk_info)}
            
            response = requests.post(url, files=files, data=data, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except:
            return None
            
    def _send_socket_file_chunk(self, chunk_data: bytes, chunk_info: Dict[str, Any]) -> Dict[str, Any]:
        """Send file chunk via socket connection"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip_address, self.port))
            
            # Send chunk info first
            info_json = json.dumps(chunk_info) + '\n'
            sock.send(info_json.encode('utf-8'))
            
            # Wait for acknowledgment
            ack = sock.recv(1024)
            if not ack or b'OK' not in ack:
                sock.close()
                return {'success': False, 'error': 'No acknowledgment received'}
                
            # Send chunk data
            sock.send(chunk_data)
            
            # Receive response
            response_data = b''
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response_data += chunk
                if b'\n' in response_data:
                    break
                    
            sock.close()
            
            try:
                response = json.loads(response_data.decode('utf-8').strip())
                return response
            except json.JSONDecodeError:
                return {'success': False, 'error': 'Invalid response format'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def ping(self) -> bool:
        """Ping ESP-01 to check connection status"""
        if not self.is_connected():
            return False
            
        try:
            response = self.send_command({'command': 'ping'})
            return response.get('success', False)
        except:
            return False
            
    def get_device_info(self) -> Dict[str, Any]:
        """Get device information from ESP-01"""
        if not self.is_connected():
            return {'success': False, 'error': 'Not connected'}
            
        try:
            response = self.send_command({'command': 'get_info'})
            return response
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information from ESP-01"""
        if not self.is_connected():
            return {'success': False, 'error': 'Not connected'}
            
        try:
            response = self.send_command({'command': 'get_memory_info'})
            return response
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def reset_device(self) -> bool:
        """Reset ESP-01 device"""
        if not self.is_connected():
            return False
            
        try:
            response = self.send_command({'command': 'reset'})
            if response.get('success'):
                # Disconnect after reset
                self.disconnect()
                return True
            return False
        except:
            return False
            
    def set_timeout(self, timeout: float):
        """Set connection timeout"""
        self.timeout = timeout
        
    def set_retry_settings(self, count: int, delay: float):
        """Set retry settings"""
        self.retry_count = count
        self.retry_delay = delay
        
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        return {
            'connected': self.connected,
            'ip_address': self.ip_address,
            'port': self.port,
            'timeout': self.timeout,
            'ping': self.ping() if self.connected else False
        }
