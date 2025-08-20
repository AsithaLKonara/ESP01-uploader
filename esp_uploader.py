#!/usr/bin/env python3
"""
ESP-01 WiFi Uploader using OTA Protocol
Implements the ArduinoOTA protocol for WiFi firmware uploads
"""

import os
import hashlib
import time
import socket
import struct
import threading
from typing import Optional, Callable, Dict, Any
from pathlib import Path

class ESPUploader:
    """
    ESP-01 WiFi Uploader using OTA (Over-The-Air) protocol
    Implements the ArduinoOTA protocol for WiFi firmware uploads
    """
    
    def __init__(self):
        self.upload_lock = threading.Lock()
        self.current_upload = None
        self.upload_status = {
            'status': 'idle',
            'progress': 0,
            'bytes_sent': 0,
            'total_bytes': 0,
            'error': None
        }
        
        # OTA Protocol constants
        self.OTA_HEADER_SIZE = 16
        self.OTA_BLOCK_SIZE = 1024
        self.OTA_PORT = 8266
        
    def upload_file(self, file_path: str, wifi_manager,
                   stream_to_ram: bool = False, verify: bool = True,
                   progress_callback: Optional[Callable] = None) -> bool:
        """
        Upload firmware file to ESP-01 using OTA protocol
        
        Args:
            file_path: Path to firmware file (.bin, .hex, .dat)
            wifi_manager: WiFiManager instance for connection
            stream_to_ram: Not used in OTA (always streams to flash)
            verify: Whether to verify upload after completion
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        with self.upload_lock:
            if self.current_upload:
                print("Upload already in progress")
                return False
                
            self.current_upload = {
                'file_path': file_path,
                'start_time': time.time(),
                'status': 'preparing'
            }
            
        try:
            # Validate file
            if not self._validate_file(file_path):
                self._update_status('error', error="Invalid file")
                return False
                
            # Prepare upload session
            session_info = self._prepare_ota_session(file_path, wifi_manager)
            if not session_info:
                self._update_status('error', error="Failed to prepare OTA session")
                return False
                
            # Perform OTA upload
            success = self._perform_ota_upload(file_path, wifi_manager, session_info, progress_callback)
            
            if success and verify:
                success = self._verify_ota_upload(file_path, wifi_manager)
                
            self._update_status('completed' if success else 'error')
            return success
            
        except Exception as e:
            self._update_status('error', error=str(e))
            return False
        finally:
            with self.upload_lock:
                self.current_upload = None
    
    def _validate_file(self, file_path: str) -> bool:
        """Validate firmware file"""
        try:
            if not os.path.exists(file_path):
                return False
                
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False
                
            # Check file extension
            ext = Path(file_path).suffix.lower()
            if ext not in ['.bin', '.hex', '.dat']:
                return False
                
            return True
        except Exception:
            return False
    
    def _prepare_ota_session(self, file_path: str, wifi_manager) -> Optional[Dict[str, Any]]:
        """Prepare OTA upload session"""
        try:
            file_size = os.path.getsize(file_path)
            file_hash = self._calculate_file_hash(file_path)
            
            session_info = {
                'file_path': file_path,
                'file_size': file_size,
                'file_hash': file_hash,
                'block_size': self.OTA_BLOCK_SIZE,
                'total_blocks': (file_size + self.OTA_BLOCK_SIZE - 1) // self.OTA_BLOCK_SIZE,
                'start_time': time.time()
            }
            
            print(f"OTA Session prepared: {file_size} bytes, {session_info['total_blocks']} blocks")
            return session_info
            
        except Exception as e:
            print(f"Failed to prepare OTA session: {e}")
            return None
    
    def _perform_ota_upload(self, file_path: str, wifi_manager, 
                           session_info: Dict[str, Any], 
                           progress_callback: Optional[Callable]) -> bool:
        """Perform the actual OTA upload using ArduinoOTA protocol"""
        try:
            # Connect to ESP-01 OTA service
            if not wifi_manager.is_connected():
                print("WiFi not connected")
                return False
            
            # Create TCP connection for OTA
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30.0)
            
            esp_ip = wifi_manager.ip_address
            esp_port = self.OTA_PORT
            
            print(f"Connecting to ESP-01 OTA service at {esp_ip}:{esp_port}")
            sock.connect((esp_ip, esp_port))
            
            # Send OTA header
            if not self._send_ota_header(sock, session_info):
                sock.close()
                return False
            
            # Stream firmware in blocks
            success = self._stream_firmware_blocks(sock, file_path, session_info, progress_callback)
            
            sock.close()
            return success
            
        except Exception as e:
            print(f"OTA upload failed: {e}")
            return False
    
    def _send_ota_header(self, sock: socket.socket, session_info: Dict[str, Any]) -> bool:
        """Send OTA protocol header"""
        try:
            # OTA header format: [command][size][md5][block_size][block_count]
            command = 0x01  # Flash command
            size = session_info['file_size']
            md5 = session_info['file_hash'].encode('utf-8')
            block_size = session_info['block_size']
            block_count = session_info['total_blocks']
            
            # Pad MD5 to 32 bytes
            md5_padded = md5.ljust(32, b'\x00')
            
            # Create header
            header = struct.pack('<II32sII', command, size, md5_padded, block_size, block_count)
            
            print(f"Sending OTA header: {len(header)} bytes")
            sock.send(header)
            
            # Wait for acknowledgment
            ack = sock.recv(1)
            if not ack or ack[0] != 0x06:  # ACK byte
                print("No ACK received from ESP-01")
                return False
                
            print("OTA header acknowledged")
            return True
            
        except Exception as e:
            print(f"Failed to send OTA header: {e}")
            return False
    
    def _stream_firmware_blocks(self, sock: socket.socket, file_path: str,
                               session_info: Dict[str, Any],
                               progress_callback: Optional[Callable]) -> bool:
        """Stream firmware data in blocks"""
        try:
            total_blocks = session_info['total_blocks']
            block_size = session_info['block_size']
            
            with open(file_path, 'rb') as f:
                for block_num in range(total_blocks):
                    # Read block data
                    block_data = f.read(block_size)
                    if not block_data:
                        break
                    
                    # Pad last block if needed
                    if len(block_data) < block_size:
                        block_data = block_data.ljust(block_size, b'\xFF')
                    
                    # Send block header: [block_num][block_size]
                    block_header = struct.pack('<II', block_num, len(block_data))
                    sock.send(block_header)
                    
                    # Send block data
                    sock.send(block_data)
                    
                    # Wait for block ACK
                    ack = sock.recv(1)
                    if not ack or ack[0] != 0x06:
                        print(f"Block {block_num} not acknowledged")
                        return False
                    
                    # Update progress
                    bytes_sent = (block_num + 1) * block_size
                    progress = min(100, (bytes_sent * 100) // session_info['file_size'])
                    
                    self._update_status('uploading', 
                                      progress=progress,
                                      bytes_sent=bytes_sent,
                                      total_bytes=session_info['file_size'])
                    
                    if progress_callback:
                        progress_callback(progress, bytes_sent, session_info['file_size'])
                    
                    print(f"Block {block_num + 1}/{total_blocks} uploaded ({progress}%)")
            
            print("All firmware blocks uploaded successfully")
            return True
            
        except Exception as e:
            print(f"Failed to stream firmware blocks: {e}")
            return False
    
    def _verify_ota_upload(self, file_path: str, wifi_manager) -> bool:
        """Verify OTA upload by checking file hash"""
        try:
            print("Verifying OTA upload...")
            
            # Get uploaded file hash from ESP-01
            response = wifi_manager.send_command({
                'command': 'get_uploaded_hash',
                'file_path': os.path.basename(file_path)
            })
            
            if not response or 'hash' not in response:
                print("Could not get uploaded file hash")
                return False
            
            uploaded_hash = response['hash']
            local_hash = self._calculate_file_hash(file_path)
            
            if uploaded_hash == local_hash:
                print("✓ Upload verification successful")
                return True
            else:
                print(f"✗ Upload verification failed")
                print(f"Local hash: {local_hash}")
                print(f"Uploaded hash: {uploaded_hash}")
                return False
                
        except Exception as e:
            print(f"Upload verification failed: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _update_status(self, status: str, progress: int = 0, 
                      bytes_sent: int = 0, total_bytes: int = 0, 
                      error: Optional[str] = None):
        """Update upload status"""
        with self.upload_lock:
            self.upload_status.update({
                'status': status,
                'progress': progress,
                'bytes_sent': bytes_sent,
                'total_bytes': total_bytes,
                'error': error
            })
    
    def get_upload_status(self) -> Dict[str, Any]:
        """Get current upload status"""
        with self.upload_lock:
            return self.upload_status.copy()
    
    def cancel_upload(self) -> bool:
        """Cancel current upload"""
        with self.upload_lock:
            if self.current_upload:
                self.current_upload['status'] = 'cancelled'
                self._update_status('cancelled')
                return True
            return False
    
    def get_supported_formats(self) -> list:
        """Get supported file formats"""
        return ['.bin', '.hex', '.dat']
    
    def get_upload_history(self) -> list:
        """Get upload history (placeholder)"""
        return []
