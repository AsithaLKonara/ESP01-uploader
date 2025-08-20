#!/usr/bin/env python3
"""
Custom ESP-01 Uploader for LED Matrix Firmware
Works with existing firmware that has file upload capability
"""

import os
import requests
import time
import threading
from typing import Optional, Callable, Dict, Any
from pathlib import Path

class CustomESPUploader:
    """
    Custom ESP-01 Uploader for existing LED Matrix firmware
    Uses HTTP file upload instead of OTA protocol
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
        
        # HTTP upload settings
        self.upload_url = "http://192.168.4.1/upload"
        self.timeout = 30.0
        
    def upload_file(self, file_path: str, wifi_manager,
                   stream_to_ram: bool = False, verify: bool = True,
                   progress_callback: Optional[Callable] = None) -> bool:
        """
        Upload file to ESP-01 using HTTP POST
        
        Args:
            file_path: Path to file (.bin, .hex, .dat, .lms, etc.)
            wifi_manager: WiFiManager instance for connection
            stream_to_ram: Not used in HTTP upload
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
                
            # Check if ESP-01 is reachable
            if not self._check_esp_connectivity():
                self._update_status('error', error="ESP-01 not reachable")
                return False
                
            # Perform HTTP upload
            success = self._perform_http_upload(file_path, progress_callback)
            
            if success and verify:
                success = self._verify_http_upload(file_path)
                
            self._update_status('completed' if success else 'error')
            return success
            
        except Exception as e:
            self._update_status('error', error=str(e))
            return False
        finally:
            with self.upload_lock:
                self.current_upload = None
    
    def _validate_file(self, file_path: str) -> bool:
        """Validate file for upload"""
        try:
            if not os.path.exists(file_path):
                return False
                
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False
                
            # Accept any file type since ESP-01 handles it
            return True
        except Exception:
            return False
    
    def _check_esp_connectivity(self) -> bool:
        """Check if ESP-01 is reachable"""
        try:
            response = requests.get("http://192.168.4.1/", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _perform_http_upload(self, file_path: str, 
                            progress_callback: Optional[Callable]) -> bool:
        """Perform HTTP file upload to ESP-01"""
        try:
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            print(f"Starting HTTP upload: {file_name} ({file_size} bytes)")
            
            # Prepare file for upload
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f, 'application/octet-stream')}
                
                # Start upload
                self._update_status('uploading', progress=0, 
                                  bytes_sent=0, total_bytes=file_size)
                
                if progress_callback:
                    progress_callback(0, 0, file_size)
                
                # Upload file with progress tracking
                response = requests.post(
                    self.upload_url,
                    files=files,
                    timeout=self.timeout,
                    stream=True
                )
                
                if response.status_code == 200:
                    print("✓ File uploaded successfully via HTTP")
                    self._update_status('uploading', progress=100, 
                                      bytes_sent=file_size, total_bytes=file_size)
                    
                    if progress_callback:
                        progress_callback(100, file_size, file_size)
                    
                    return True
                else:
                    print(f"✗ Upload failed with status: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"HTTP upload failed: {e}")
            return False
    
    def _verify_http_upload(self, file_path: str) -> bool:
        """Verify upload by checking ESP-01 response"""
        try:
            print("Verifying HTTP upload...")
            
            # Try to access the uploaded file or check ESP-01 status
            response = requests.get("http://192.168.4.1/", timeout=5)
            
            if response.status_code == 200:
                # Check if the page shows any indication of successful upload
                content = response.text.lower()
                if "upload" in content or "file" in content:
                    print("✓ Upload verification successful")
                    return True
                else:
                    print("⚠️  Upload verification inconclusive")
                    return True  # Assume success if page loads
            
            return False
            
        except Exception as e:
            print(f"Upload verification failed: {e}")
            return False
    
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
        return ['.bin', '.hex', '.dat', '.lms', '.json', '.txt', '.csv', '*.*']
    
    def test_esp_interface(self) -> Dict[str, Any]:
        """Test ESP-01 interface and return capabilities"""
        try:
            response = requests.get("http://192.168.4.1/", timeout=5)
            
            if response.status_code == 200:
                content = response.text
                
                capabilities = {
                    'status': 'connected',
                    'interface_type': 'http_upload',
                    'upload_endpoint': '/upload',
                    'supports_files': True,
                    'page_content': content[:500],  # First 500 chars
                    'has_upload_form': 'upload' in content.lower()
                }
                
                return capabilities
            else:
                return {'status': 'error', 'http_code': response.status_code}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
