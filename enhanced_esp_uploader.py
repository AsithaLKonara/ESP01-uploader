#!/usr/bin/env python3
"""
Enhanced ESP-01 Uploader with Hash Verification
Provides secure OTA uploads with SHA256 hash verification
"""

import os
import requests
import time
import threading
import hashlib
import json
from typing import Optional, Callable, Dict, Any
from pathlib import Path

class EnhancedESPUploader:
    """
    Enhanced ESP-01 Uploader with hash verification
    Supports both HTTP file upload and OTA firmware updates
    """
    
    def __init__(self):
        self.upload_lock = threading.Lock()
        self.current_upload = None
        self.upload_status = {
            'status': 'idle',
            'progress': 0,
            'bytes_sent': 0,
            'total_bytes': 0,
            'error': None,
            'verification': 'pending'
        }
        
        # ESP-01 endpoints
        self.esp_base_url = "http://192.168.4.1"
        self.upload_url = f"{self.esp_base_url}/upload"
        self.hash_url = f"{self.esp_base_url}/firmware-hash"
        self.status_url = f"{self.esp_base_url}/status"
        self.system_url = f"{self.esp_base_url}/system-info"
        
        self.timeout = 30.0
        
    def upload_file(self, file_path: str, wifi_manager,
                   stream_to_ram: bool = False, verify: bool = True,
                   progress_callback: Optional[Callable] = None) -> bool:
        """
        Upload file to ESP-01 with hash verification
        
        Args:
            file_path: Path to file (.bin, .hex, .dat, .lms, etc.)
            wifi_manager: WiFiManager instance for connection
            stream_to_ram: Not used in HTTP upload
            verify: Whether to verify upload with hash comparison
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: True if upload successful and verified, False otherwise
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
                
            # Calculate local file hash
            local_hash = self._calculate_file_hash(file_path)
            print(f"Local file hash (SHA256): {local_hash}")
            
            # Perform HTTP upload
            success = self._perform_http_upload(file_path, progress_callback)
            
            if success and verify:
                # Verify upload with hash comparison
                verification_success = self._verify_upload_with_hash(file_path, local_hash)
                if verification_success:
                    self._update_status('completed', verification='verified')
                    print("✅ Upload verified with hash comparison!")
                else:
                    self._update_status('completed', verification='failed')
                    print("⚠️  Upload completed but verification failed!")
                    success = False
            else:
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
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating file hash: {e}")
            return ""
    
    def _check_esp_connectivity(self) -> bool:
        """Check if ESP-01 is reachable"""
        try:
            response = requests.get(self.esp_base_url, timeout=5)
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
    
    def _verify_upload_with_hash(self, file_path: str, local_hash: str) -> bool:
        """Verify upload by comparing local and ESP-01 file hashes"""
        try:
            print("Verifying upload with hash comparison...")
            
            # Wait a moment for ESP-01 to process the upload
            time.sleep(1)
            
            # Get ESP-01 firmware hash
            esp_hash_data = self._get_esp_firmware_hash()
            if not esp_hash_data:
                print("⚠️  Could not retrieve ESP-01 firmware hash")
                return False
            
            esp_hash = esp_hash_data.get('hash', '')
            esp_file = esp_hash_data.get('file', '')
            esp_size = esp_hash_data.get('size', 0)
            
            print(f"ESP-01 reports:")
            print(f"  File: {esp_file}")
            print(f"  Size: {esp_size} bytes")
            print(f"  Hash: {esp_hash}")
            
            # Compare hashes
            if esp_hash and local_hash:
                if esp_hash.lower() == local_hash.lower():
                    print("✅ Hash verification successful!")
                    return True
                else:
                    print("❌ Hash verification failed!")
                    print(f"  Local:  {local_hash}")
                    print(f"  ESP-01: {esp_hash}")
                    return False
            else:
                print("⚠️  Hash verification inconclusive (missing hash data)")
                return False
                
        except Exception as e:
            print(f"Hash verification failed: {e}")
            return False
    
    def _get_esp_firmware_hash(self) -> Optional[Dict[str, Any]]:
        """Get firmware hash from ESP-01"""
        try:
            response = requests.get(self.hash_url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get firmware hash: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting firmware hash: {e}")
            return None
    
    def get_esp_status(self) -> Optional[Dict[str, Any]]:
        """Get ESP-01 status information"""
        try:
            response = requests.get(self.status_url, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception:
            return None
    
    def get_system_info(self) -> Optional[Dict[str, Any]]:
        """Get ESP-01 system information"""
        try:
            response = requests.get(self.system_url, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception:
            return None
    
    def _update_status(self, status: str, progress: int = 0, 
                      bytes_sent: int = 0, total_bytes: int = 0, 
                      error: Optional[str] = None, verification: str = 'pending'):
        """Update upload status"""
        with self.upload_lock:
            self.upload_status.update({
                'status': status,
                'progress': progress,
                'bytes_sent': bytes_sent,
                'total_bytes': total_bytes,
                'error': error,
                'verification': verification
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
            response = requests.get(self.esp_base_url, timeout=5)
            
            if response.status_code == 200:
                content = response.text
                
                capabilities = {
                    'status': 'connected',
                    'interface_type': 'enhanced_http_upload',
                    'upload_endpoint': '/upload',
                    'hash_endpoint': '/firmware-hash',
                    'status_endpoint': '/status',
                    'supports_files': True,
                    'supports_hash_verification': True,
                    'page_content': content[:500],  # First 500 chars
                    'has_upload_form': 'upload' in content.lower()
                }
                
                return capabilities
            else:
                return {'status': 'error', 'http_code': response.status_code}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def verify_existing_upload(self, file_path: str) -> bool:
        """Verify an existing upload without re-uploading"""
        try:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False
            
            local_hash = self._calculate_file_hash(file_path)
            print(f"Local file hash: {local_hash}")
            
            esp_hash_data = self._get_esp_firmware_hash()
            if not esp_hash_data:
                print("Could not get ESP-01 hash data")
                return False
            
            esp_hash = esp_hash_data.get('hash', '')
            if not esp_hash:
                print("No hash data from ESP-01")
                return False
            
            if esp_hash.lower() == local_hash.lower():
                print("✅ Existing upload verified successfully!")
                return True
            else:
                print("❌ Existing upload verification failed!")
                return False
                
        except Exception as e:
            print(f"Verification error: {e}")
            return False
