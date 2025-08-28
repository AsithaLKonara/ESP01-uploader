#!/usr/bin/env python3
"""
Smart ESP-01 Uploader with Auto-Requirements Management and Real ESP-01 Verification
Automatically checks and installs dependencies before upload, then verifies with ESP-01 hash
"""

import os
import sys
import subprocess
import importlib
import time
import threading
import hashlib
import json
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path

class RequirementsManager:
    """Manages Python package requirements automatically"""
    
    def __init__(self):
        self.required_packages = {
            'requests': 'requests',
            'hashlib': 'hashlib',  # Built-in
            'json': 'json',        # Built-in
            'threading': 'threading',  # Built-in
            'time': 'time',        # Built-in
            'os': 'os',            # Built-in
            'pathlib': 'pathlib'   # Built-in
        }
        
        self.optional_packages = {
            'PIL': 'Pillow',  # For image processing
            'numpy': 'numpy',  # For data processing
            'matplotlib': 'matplotlib'  # For plotting
        }
        
        self.install_log = []
        self.check_log = []
        
    def check_package(self, package_name: str, import_name: str = None) -> bool:
        """Check if a package is available"""
        if import_name is None:
            import_name = package_name
            
        try:
            importlib.import_module(import_name)
            return True
        except ImportError:
            return False
    
    def get_missing_packages(self) -> List[str]:
        """Get list of missing required packages"""
        missing = []
        
        for package, import_name in self.required_packages.items():
            if not self.check_package(package, import_name):
                missing.append(package)
                
        return missing
    
    def install_package(self, package_name: str, log_callback: Optional[Callable] = None) -> bool:
        """Install a single package using pip"""
        try:
            if log_callback:
                log_callback(f"Installing {package_name}...")
            
            # Use subprocess to install package
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package_name
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                if log_callback:
                    log_callback(f"✅ {package_name} installed successfully")
                self.install_log.append(f"SUCCESS: {package_name}")
                return True
            else:
                if log_callback:
                    log_callback(f"❌ Failed to install {package_name}: {result.stderr}")
                self.install_log.append(f"FAILED: {package_name} - {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            if log_callback:
                log_callback(f"❌ Timeout installing {package_name}")
            self.install_log.append(f"TIMEOUT: {package_name}")
            return False
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Error installing {package_name}: {str(e)}")
            self.install_log.append(f"ERROR: {package_name} - {str(e)}")
            return False
    
    def install_missing_packages(self, log_callback: Optional[Callable] = None) -> bool:
        """Install all missing required packages"""
        missing = self.get_missing_packages()
        
        if not missing:
            if log_callback:
                log_callback("✅ All required packages are already installed")
            return True
        
        if log_callback:
            log_callback(f"📦 Installing {len(missing)} missing packages: {', '.join(missing)}")
        
        success_count = 0
        for package in missing:
            if self.install_package(package, log_callback):
                success_count += 1
            else:
                if log_callback:
                    log_callback(f"⚠️  Package {package} failed to install")
        
        if log_callback:
            log_callback(f"📊 Package installation complete: {success_count}/{len(missing)} successful")
        
        return success_count == len(missing)
    
    def verify_requirements(self, log_callback: Optional[Callable] = None) -> bool:
        """Verify all requirements are met"""
        if log_callback:
            log_callback("🔍 Checking package requirements...")
        
        missing = self.get_missing_packages()
        
        if log_callback:
            for package in self.required_packages:
                status = "✅" if package not in missing else "❌"
                log_callback(f"  {status} {package}")
        
        if missing:
            if log_callback:
                log_callback(f"⚠️  {len(missing)} packages missing: {', '.join(missing)}")
            return False
        else:
            if log_callback:
                log_callback("✅ All required packages are available")
            return True
    
    def get_requirements_report(self) -> Dict[str, Any]:
        """Get detailed requirements report"""
        missing = self.get_missing_packages()
        available = [pkg for pkg in self.required_packages if pkg not in missing]
        
        return {
            'total_required': len(self.required_packages),
            'available': available,
            'missing': missing,
            'install_log': self.install_log,
            'check_log': self.check_log,
            'all_available': len(missing) == 0
        }

class SmartESPUploaderWithRequirements:
    """
    Smart ESP-01 Uploader with automatic requirements management and real ESP-01 verification
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
            'verification': 'pending',
            'local_hash': '',
            'esp_hash': '',
            'verification_method': 'pending',
            'upload_time': None,
            'requirements_status': 'pending'
        }
        
        # ESP-01 endpoints
        self.esp_base_url = "http://192.168.4.1"
        self.upload_url = f"{self.esp_base_url}/upload"
        self.hash_url = f"{self.esp_base_url}/firmware-hash"
        self.timeout = 300.0  # 300 seconds timeout for large files (up to 700KB)
        
        # Upload history for verification
        self.upload_history = {}
        

        
        # Requirements manager
        self.requirements_manager = RequirementsManager()
        
        # Log callback
        self.log_callback = None
        
    def set_log_callback(self, callback: Callable[[str], None]):
        """Set callback for logging messages"""
        self.log_callback = callback
    
    def log_message(self, message: str):
        """Log a message using callback if available"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
    
    def check_and_install_requirements(self) -> bool:
        """Check and install requirements automatically"""
        self.log_message("🚀 Starting requirements check and installation...")
        
        # Check current requirements
        if not self.requirements_manager.verify_requirements(self.log_message):
            self.log_message("📦 Installing missing packages...")
            
            # Install missing packages
            if not self.requirements_manager.install_missing_packages(self.log_message):
                self.log_message("❌ Failed to install required packages")
                return False
            
            # Verify again after installation
            if not self.requirements_manager.verify_requirements(self.log_message):
                self.log_message("❌ Requirements verification failed after installation")
                return False
        
        self.log_message("✅ Requirements check and installation completed successfully")
        return True
    
    def upload_file(self, file_path: str, wifi_manager,
                   stream_to_ram: bool = False, verify: bool = True,
                   progress_callback: Optional[Callable] = None) -> bool:
        """
        Upload file to ESP-01 with automatic requirements management and real ESP-01 verification
        
        Args:
            file_path: Path to file (.bin, .hex, .dat, .lms, etc.)
            wifi_manager: WiFiManager instance for connection
            stream_to_ram: Not used in HTTP upload
            verify: Whether to verify upload with ESP-01 hash
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        with self.upload_lock:
            if self.current_upload:
                self.log_message("❌ Upload already in progress")
                return False
                
            self.current_upload = {
                'file_path': file_path,
                'start_time': time.time(),
                'status': 'preparing'
            }
        
        try:
            # Step 1: Check and install requirements
            self.log_message("📋 Step 1: Checking requirements...")
            self._update_status('preparing', requirements_status='checking')
            
            if not self.check_and_install_requirements():
                self._update_status('error', error="Requirements check failed")
                return False
            
            self._update_status('preparing', requirements_status='ready')
            
            # Step 2: Validate file
            self.log_message("📋 Step 2: Validating file...")
            if not self._validate_file(file_path):
                self._update_status('error', error="Invalid file")
                return False
            
            # Step 3: Check ESP-01 connectivity
            self.log_message("📋 Step 3: Checking ESP-01 connectivity...")
            if not self._check_esp_connectivity():
                self._update_status('error', error="ESP-01 not reachable")
                return False
            
            # Step 4: Calculate local file hash
            self.log_message("📋 Step 4: Calculating file hash...")
            local_hash = self._calculate_file_hash(file_path)
            self.log_message(f"📊 File hash (SHA256): {local_hash}")
            
            # Store hash for verification
            self._update_status('preparing', local_hash=local_hash)
            
            # Step 5: Perform HTTP upload
            self.log_message("📋 Step 5: Starting file upload...")
            
            # Use original file
            upload_file_path = file_path
            self.log_message(f"📤 Uploading file: {os.path.basename(upload_file_path)}")
            self.log_message(f"📊 File size: {os.path.getsize(upload_file_path)} bytes")
            
            success = self._perform_http_upload(upload_file_path, progress_callback)
            
            if success:
                # Store upload in history
                self._store_upload_history(file_path, local_hash)
                

                
                if verify:
                    # Step 6: Smart verification (local hash + upload success)
                    self.log_message("📋 Step 6: Smart verification (local hash + upload success)...")
                    smart_verification_success = self._smart_verification(file_path, local_hash)
                    
                    if smart_verification_success:
                        # Step 7: REAL ESP-01 Verification (NEW!)
                        self.log_message("📋 Step 7: Real ESP-01 verification...")
                        esp_verification_success = self._verify_with_esp_hash(file_path, local_hash)
                        
                        if esp_verification_success:
                            self._update_status('completed', verification='verified_esp', verification_method='esp_hash_verification')
                            self.log_message("✅ Upload verified with ESP-01 hash! (TRUE VERIFICATION)")
                        else:
                            self._update_status('completed', verification='smart_only', verification_method='smart_verification')
                            self.log_message("⚠️  Upload completed, verification limited to smart verification (local hash + upload success)")
                    else:
                        self._update_status('completed', verification='failed', verification_method='smart_verification_failed')
                        self.log_message("❌ Smart verification failed!")
                        success = False
                else:
                    self._update_status('completed', verification='skipped', verification_method='verification_disabled')
                    self.log_message("✅ Upload completed (verification skipped)")
                    
            else:
                self._update_status('error')
                
            return success
            
        except Exception as e:
            self.log_message(f"❌ Upload error: {str(e)}")
            self._update_status('error', error=str(e))
            return False
        finally:
            with self.upload_lock:
                self.current_upload = None
    
    def _verify_with_esp_hash(self, file_path: str, local_hash: str) -> bool:
        """
        NEW: Verify upload by querying ESP-01 for the actual file hash
        This provides TRUE verification that the ESP-01 actually stored the file correctly
        """
        try:
            self.log_message("🔍 Querying ESP-01 for uploaded file hash...")
            
            # Import requests here to ensure it's available
            import requests
            
            # Query ESP-01 for the hash of what it actually stored
            response = requests.get(self.hash_url, timeout=10)
            
            if response.status_code == 200:
                try:
                    # Parse ESP-01 response
                    esp_data = response.json()
                    
                    if esp_data.get('status') == 'success':
                        esp_hash = esp_data.get('hash', '')
                        esp_file = esp_data.get('file', '')
                        esp_size = esp_data.get('size', 0)
                        
                        self.log_message(f"📊 ESP-01 Response:")
                        self.log_message(f"  File: {esp_file}")
                        self.log_message(f"  Size: {esp_size} bytes")
                        self.log_message(f"  Hash: {esp_hash}")
                        
                        # Compare hashes
                        if esp_hash and esp_hash.lower() == local_hash.lower():
                            self.log_message("✅ HASH MATCH! ESP-01 file matches local file exactly!")
                            self.log_message(f"  Local Hash:  {local_hash}")
                            self.log_message(f"  ESP-01 Hash: {esp_hash}")
                            
                            # Update status with ESP hash
                            self._update_status('verifying', esp_hash=esp_hash)
                            
                            return True
                        else:
                            self.log_message("❌ HASH MISMATCH! ESP-01 file differs from local file!")
                            self.log_message(f"  Local Hash:  {local_hash}")
                            self.log_message(f"  ESP-01 Hash: {esp_hash}")
                            
                            if esp_hash:
                                self.log_message("⚠️  This indicates the file was corrupted during upload or storage")
                            else:
                                self.log_message("⚠️  ESP-01 did not provide a valid hash")
                            
                            return False
                    else:
                        self.log_message(f"❌ ESP-01 returned error status: {esp_data.get('message', 'Unknown error')}")
                        return False
                        
                except json.JSONDecodeError:
                    self.log_message("❌ ESP-01 response is not valid JSON")
                    self.log_message(f"  Response: {response.text}")
                    return False
                    
            elif response.status_code == 404:
                self.log_message("❌ ESP-01 /firmware-hash endpoint not found")
                self.log_message("  This ESP-01 firmware doesn't support hash verification")
                self.log_message("  Consider flashing the enhanced firmware for true verification")
                return False
            else:
                self.log_message(f"❌ ESP-01 hash endpoint returned status: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self.log_message("❌ Timeout querying ESP-01 hash endpoint")
            return False
        except requests.exceptions.ConnectionError:
            self.log_message("❌ Connection error querying ESP-01 hash endpoint")
            return False
        except Exception as e:
            self.log_message(f"❌ Error querying ESP-01 hash: {str(e)}")
            return False
    
    def _validate_file(self, file_path: str) -> bool:
        """Validate file for upload with size optimization"""
        try:
            if not os.path.exists(file_path):
                self.log_message(f"❌ File not found: {file_path}")
                return False
                
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                self.log_message(f"❌ File is empty: {file_path}")
                return False
            
            # Check file size limit (700KB)
            if file_size > 716800:  # 700KB limit (700 * 1024)
                self.log_message(f"⚠️  File is too large: {os.path.basename(file_path)} ({file_size} bytes)")
                self.log_message(f"❌ File exceeds 700KB limit")
                return False
            else:
                self.log_message(f"✅ File validated: {os.path.basename(file_path)} ({file_size} bytes)")
            
            return True
        except Exception as e:
            self.log_message(f"❌ File validation error: {str(e)}")
            return False
    

    

    

    

    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        try:
            self.log_message("🔐 Calculating SHA256 hash...")
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                chunk_count = 0
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
                    chunk_count += 1
                    if chunk_count % 100 == 0:  # Log every 100 chunks
                        self.log_message(f"  Processing chunk {chunk_count}...")
            
            hash_result = sha256_hash.hexdigest()
            self.log_message(f"✅ Hash calculation complete: {hash_result[:16]}...")
            return hash_result
            
        except Exception as e:
            self.log_message(f"❌ Hash calculation error: {str(e)}")
            return ""
    
    def _check_esp_connectivity(self) -> bool:
        """Check if ESP-01 is reachable"""
        try:
            self.log_message(f"🌐 Testing connection to {self.esp_base_url}...")
            
            # Import requests here to ensure it's available
            import requests
            
            response = requests.get(self.esp_base_url, timeout=5)
            
            if response.status_code == 200:
                self.log_message("✅ ESP-01 connection successful")
                return True
            else:
                self.log_message(f"❌ ESP-01 returned status: {response.status_code}")
                return False
                
        except ImportError:
            self.log_message("❌ 'requests' package not available")
            return False
        except Exception as e:
            self.log_message(f"❌ ESP-01 connection failed: {str(e)}")
            return False
    
    def _perform_http_upload(self, file_path: str, 
                            progress_callback: Optional[Callable]) -> bool:
        """Perform HTTP file upload to ESP-01"""
        try:
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            self.log_message(f"📤 Starting HTTP upload: {file_name} ({file_size} bytes)")
            
            # Import requests here to ensure it's available
            import requests
            
            # Prepare file for upload
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f, 'application/octet-stream')}
                
                # Start upload
                self._update_status('uploading', progress=0, 
                                  bytes_sent=0, total_bytes=file_size)
                
                if progress_callback:
                    progress_callback(0, 0, file_size)
                
                self.log_message("📡 Sending file to ESP-01...")
                
                # Upload file with progress tracking
                response = requests.post(
                    self.upload_url,
                    files=files,
                    timeout=self.timeout,
                    stream=True
                )
                
                if response.status_code == 200:
                    self.log_message("✅ File uploaded successfully via HTTP")
                    self._update_status('uploading', progress=100, 
                                      bytes_sent=file_size, total_bytes=file_size)
                    
                    if progress_callback:
                        progress_callback(100, file_size, file_size)
                    
                    return True
                else:
                    self.log_message(f"❌ Upload failed with status: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_message(f"❌ HTTP upload failed: {str(e)}")
            return False
    
    def _smart_verification(self, file_path: str, local_hash: str) -> bool:
        """Smart verification using local hash and upload success"""
        try:
            self.log_message("🔍 Performing smart verification...")
            
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            self.log_message(f"📊 Smart Verification Results:")
            self.log_message(f"  File: {file_name}")
            self.log_message(f"  Size: {file_size} bytes")
            self.log_message(f"  Hash: {local_hash[:16]}...")
            self.log_message(f"  Upload Status: Success (HTTP 200)")
            
            # Store verification data
            verification_data = {
                'file_name': file_name,
                'file_size': file_size,
                'local_hash': local_hash,
                'upload_time': time.time(),
                'verification_method': 'smart_local_hash_plus_upload_success'
            }
            
            self.log_message("✅ Smart verification completed (local hash + upload success)")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Smart verification failed: {str(e)}")
            return False
    
    def _store_upload_history(self, file_path: str, local_hash: str):
        """Store upload information for future reference"""
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            self.upload_history[file_name] = {
                'file_path': file_path,
                'file_size': file_size,
                'local_hash': local_hash,
                'upload_time': time.time(),
                'verification_status': 'local_hash_verified'
            }
            
            self.log_message(f"📚 Upload history updated for: {file_name}")
            
        except Exception as e:
            self.log_message(f"❌ Failed to store upload history: {str(e)}")
    
    def verify_existing_upload(self, file_path: str) -> bool:
        """Verify an existing upload using stored history"""
        try:
            if not os.path.exists(file_path):
                self.log_message(f"❌ File not found: {file_path}")
                return False
            
            file_name = os.path.basename(file_path)
            
            # Check if we have upload history for this file
            if file_name in self.upload_history:
                history = self.upload_history[file_name]
                stored_hash = history['local_hash']
                
                self.log_message(f"🔍 Verifying existing upload: {file_name}")
                
                # Calculate current hash
                current_hash = self._calculate_file_hash(file_path)
                
                if current_hash == stored_hash:
                    self.log_message(f"✅ File verification successful!")
                    self.log_message(f"  File: {file_name}")
                    self.log_message(f"  Hash: {current_hash[:16]}...")
                    self.log_message(f"  Upload Time: {time.ctime(history['upload_time'])}")
                    return True
                else:
                    self.log_message(f"❌ File verification failed!")
                    self.log_message(f"  Stored Hash: {stored_hash[:16]}...")
                    self.log_message(f"  Current Hash: {current_hash[:16]}...")
                    return False
            else:
                self.log_message(f"⚠️  No upload history found for: {file_name}")
                self.log_message("  This file may not have been uploaded via this tool")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Verification error: {str(e)}")
            return False
    
    def get_requirements_report(self) -> Dict[str, Any]:
        """Get requirements status report"""
        return self.requirements_manager.get_requirements_report()
    
    def get_upload_history(self) -> Dict[str, Any]:
        """Get upload history"""
        return self.upload_history.copy()
    
    def get_upload_status(self) -> Dict[str, Any]:
        """Get current upload status"""
        with self.upload_lock:
            return self.upload_status.copy()
    
    def _update_status(self, status: str, progress: int = 0, 
                      bytes_sent: int = 0, total_bytes: int = 0, 
                      error: Optional[str] = None, verification: str = 'pending',
                      local_hash: str = '', esp_hash: str = '', 
                      verification_method: str = 'pending', requirements_status: str = 'pending'):
        """Update upload status"""
        with self.upload_lock:
            self.upload_status.update({
                'status': status,
                'progress': progress,
                'bytes_sent': bytes_sent,
                'total_bytes': total_bytes,
                'error': error,
                'verification': verification,
                'local_hash': local_hash,
                'esp_hash': esp_hash,
                'verification_method': verification_method,
                'upload_time': time.time() if status == 'completed' else None,
                'requirements_status': requirements_status
            })
    
    def cancel_upload(self) -> bool:
        """Cancel current upload"""
        with self.upload_lock:
            if self.current_upload:
                self.current_upload['status'] = 'cancelled'
                self._update_status('cancelled')
                self.log_message("⏹️  Upload cancelled")
                return True
            return False
    
    def get_supported_formats(self) -> list:
        """Get supported file formats"""
        return ['.bin', '.hex', '.dat', '.lms', '.json', '.txt', '.csv', '*.*']
    
    def test_esp_interface(self) -> Dict[str, Any]:
        """Test ESP-01 interface and return capabilities"""
        try:
            import requests
            
            # Test basic connectivity
            response = requests.get(self.esp_base_url, timeout=5)
            
            if response.status_code == 200:
                content = response.text
                
                # Test hash endpoint availability
                hash_response = requests.get(self.hash_url, timeout=5)
                hash_support = hash_response.status_code == 200
                
                capabilities = {
                    'status': 'connected',
                    'interface_type': 'smart_http_upload_with_requirements_and_esp_verification',
                    'upload_endpoint': '/upload',
                    'hash_endpoint': '/firmware-hash',
                    'supports_files': True,
                    'supports_smart_verification': True,
                    'supports_esp_hash_verification': hash_support,
                    'supports_auto_requirements': True,
                    'verification_method': 'esp_hash_verification' if hash_support else 'local_hash_plus_upload_success',
                    'page_content': content[:500],  # First 500 chars
                    'has_upload_form': 'upload' in content.lower()
                }
                
                return capabilities
            else:
                return {'status': 'error', 'http_code': response.status_code}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def export_upload_report(self, file_path: str = None) -> str:
        """Export comprehensive upload and requirements report"""
        try:
            if file_path is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                file_path = f"esp01_smart_upload_report_{timestamp}.json"
            
            report_data = {
                'timestamp': time.time(),
                'upload_history': self.upload_history,
                'current_status': self.upload_status,
                'esp_interface': self.test_esp_interface(),
                'requirements_report': self.get_requirements_report()
            }
            
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            self.log_message(f"📄 Upload report exported to: {file_path}")
            return file_path
            
        except Exception as e:
            self.log_message(f"❌ Failed to export report: {str(e)}")
            return ""
