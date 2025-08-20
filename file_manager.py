#!/usr/bin/env python3
"""
File Manager Module
Handles file operations, configuration management, and file format detection
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import configparser
import time

class FileManager:
    """Manages file operations and configuration"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.expanduser("~"), ".esp01_uploader")
            
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "config.ini"
        self.history_file = self.config_dir / "upload_history.json"
        self.log_file = self.config_dir / "upload_log.txt"
        
        # Supported file types
        self.supported_formats = {
            '.bin': 'Binary firmware file',
            '.hex': 'Intel HEX file',
            '.dat': 'Data file',
            '.lms': 'LED Matrix Studio pattern',
            '.json': 'JSON pattern file',
            '.txt': 'Text pattern file',
            '.csv': 'CSV pattern file'
        }
        
        # Initialize configuration
        self._load_config()
        
    def _load_config(self):
        """Load configuration from file"""
        self.config = configparser.ConfigParser()
        
        if self.config_file.exists():
            self.config.read(self.config_file)
        else:
            self._create_default_config()
            
    def _create_default_config(self):
        """Create default configuration"""
        self.config['DEFAULT'] = {
            'default_ip': '192.168.4.1',
            'default_port': '8266',
            'default_stream': 'true',
            'default_verify': 'true',
            'chunk_size': '1024',
            'timeout': '10.0',
            'retry_count': '3',
            'retry_delay': '1.0'
        }
        
        self.config['LED_MATRIX'] = {
            'default_size': '8x8',
            'led_size': '20',
            'led_spacing': '2',
            'led_color_on': '#00FF00',
            'led_color_off': '#333333',
            'led_color_border': '#666666'
        }
        
        self.config['UPLOAD'] = {
            'auto_verify': 'true',
            'stream_to_ram': 'true',
            'backup_files': 'true',
            'log_uploads': 'true'
        }
        
        self._save_config()
        
    def _save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
            
    def get_config(self, section: str = 'DEFAULT', key: str = None) -> Any:
        """Get configuration value"""
        if key is None:
            return dict(self.config[section]) if section in self.config else {}
            
        if section in self.config and key in self.config[section]:
            value = self.config[section][key]
            
            # Convert string values to appropriate types
            if value.lower() in ['true', 'false']:
                return value.lower() == 'true'
            elif value.isdigit():
                return int(value)
            elif value.replace('.', '').isdigit():
                return float(value)
            else:
                return value
                
        return None
        
    def set_config(self, section: str, key: str, value: Any):
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
            
        self.config[section][key] = str(value)
        self._save_config()
        
    def save_config(self, config_data: Dict[str, Any]):
        """Save configuration data"""
        for section, items in config_data.items():
            if section not in self.config:
                self.config[section] = {}
            for key, value in items.items():
                self.config[section][key] = str(value)
                
        self._save_config()
        
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict containing file information
        """
        if not os.path.exists(file_path):
            return {'error': 'File not found'}
            
        file_path = Path(file_path)
        file_stat = file_path.stat()
        
        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        
        # Detect file type
        file_type = self._detect_file_type(file_path)
        
        info = {
            'name': file_path.name,
            'path': str(file_path),
            'size': file_stat.st_size,
            'size_human': self._format_file_size(file_stat.st_size),
            'extension': file_path.suffix.lower(),
            'file_type': file_type,
            'hash': file_hash,
            'modified': file_stat.st_mtime,
            'created': file_stat.st_ctime,
            'is_readable': os.access(file_path, os.R_OK),
            'is_writable': os.access(file_path, os.W_OK)
        }
        
        return info
        
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except:
            return ""
            
    def _detect_file_type(self, file_path: Path) -> str:
        """Detect file type based on extension and content"""
        ext = file_path.suffix.lower()
        
        if ext in self.supported_formats:
            return self.supported_formats[ext]
            
        # Try to detect by content for unknown extensions
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)
                
            # Check for common file signatures
            if header.startswith(b'\x7fELF'):
                return 'ELF executable'
            elif header.startswith(b'MZ'):
                return 'Windows executable'
            elif header.startswith(b'\x89PNG'):
                return 'PNG image'
            elif header.startswith(b'GIF8'):
                return 'GIF image'
            elif header.startswith(b'\xff\xd8\xff'):
                return 'JPEG image'
            else:
                return 'Unknown binary file'
                
        except:
            return 'Unknown file type'
            
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0B"
            
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
            
        return f"{size_bytes:.1f}{size_names[i]}"
        
    def validate_file(self, file_path: str, expected_type: str = None) -> Tuple[bool, str]:
        """
        Validate file for upload
        
        Args:
            file_path: Path to the file
            expected_type: Expected file type (optional)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, "File not found"
            
        file_path = Path(file_path)
        
        # Check file size
        file_size = file_path.stat().st_size
        max_size = 1024 * 1024 * 10  # 10MB limit
        
        if file_size > max_size:
            return False, f"File too large ({self._format_file_size(file_size)}). Maximum size: 10MB"
            
        # Check file extension
        ext = file_path.suffix.lower()
        if ext not in self.supported_formats:
            return False, f"Unsupported file type: {ext}"
            
        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            return False, "File is not readable"
            
        # Type-specific validation
        if expected_type and ext != expected_type:
            return False, f"Expected {expected_type} file, got {ext}"
            
        return True, "File is valid"
        
    def backup_file(self, file_path: str, backup_dir: str = None) -> str:
        """
        Create a backup of the file
        
        Args:
            file_path: Path to the file to backup
            backup_dir: Backup directory (optional)
            
        Returns:
            Path to backup file
        """
        if backup_dir is None:
            backup_dir = self.config_dir / "backups"
            
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(exist_ok=True)
        
        file_path = Path(file_path)
        timestamp = int(time.time())
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = backup_dir / backup_name
        
        try:
            shutil.copy2(file_path, backup_path)
            return str(backup_path)
        except Exception as e:
            print(f"Backup failed: {e}")
            return ""
            
    def log_upload(self, file_path: str, success: bool, details: Dict[str, Any] = None):
        """Log upload attempt"""
        if not self.get_config('UPLOAD', 'log_uploads'):
            return
            
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        file_name = os.path.basename(file_path)
        
        log_entry = {
            'timestamp': timestamp,
            'file': file_name,
            'success': success,
            'details': details or {}
        }
        
        # Save to history file
        history = self._load_history()
        history.append(log_entry)
        self._save_history(history)
        
        # Append to log file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                status = "SUCCESS" if success else "FAILED"
                f.write(f"[{timestamp}] {status}: {file_name}\n")
                if details:
                    for key, value in details.items():
                        f.write(f"  {key}: {value}\n")
                f.write("\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}")
            
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load upload history"""
        if not self.history_file.exists():
            return []
            
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
            
    def _save_history(self, history: List[Dict[str, Any]]):
        """Save upload history"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")
            
    def get_upload_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent upload history"""
        history = self._load_history()
        return history[-limit:] if limit > 0 else history
        
    def clear_history(self):
        """Clear upload history"""
        if self.history_file.exists():
            self.history_file.unlink()
            
    def get_recent_files(self, directory: str = None, limit: int = 10) -> List[str]:
        """Get list of recently modified files"""
        if directory is None:
            directory = os.path.expanduser("~")
            
        try:
            files = []
            for item in Path(directory).iterdir():
                if item.is_file() and item.suffix.lower() in self.supported_formats:
                    files.append((item.stat().st_mtime, str(item)))
                    
            # Sort by modification time (newest first)
            files.sort(reverse=True)
            
            return [path for _, path in files[:limit]]
            
        except Exception as e:
            print(f"Failed to get recent files: {e}")
            return []
            
    def create_sample_files(self, output_dir: str):
        """Create sample files for testing"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Sample binary file
        sample_bin = output_dir / "sample.bin"
        with open(sample_bin, 'wb') as f:
            f.write(b'\x00' * 1024)  # 1KB of zeros
            
        # Sample HEX file
        sample_hex = output_dir / "sample.hex"
        with open(sample_hex, 'w') as f:
            f.write(":020000040000FA\n")  # Extended linear address
            f.write(":100000000102030405060708090A0B0C0D0E0F10\n")  # Data record
            f.write(":00000001FF\n")  # End of file
            
        # Sample JSON pattern
        sample_json = output_dir / "sample_pattern.json"
        pattern_data = {
            "matrix_size": [8, 8],
            "total_frames": 4,
            "frames": [
                [[1, 0, 1, 0, 1, 0, 1, 0] for _ in range(8)],
                [[0, 1, 0, 1, 0, 1, 0, 1] for _ in range(8)],
                [[1, 1, 0, 0, 1, 1, 0, 0] for _ in range(8)],
                [[0, 0, 1, 1, 0, 0, 1, 1] for _ in range(8)]
            ]
        }
        with open(sample_json, 'w') as f:
            json.dump(pattern_data, f, indent=2)
            
        # Sample text pattern
        sample_txt = output_dir / "sample_pattern.txt"
        with open(sample_txt, 'w') as f:
            f.write("# Sample LED Matrix Pattern\n")
            f.write("# Matrix Size: 8x8\n\n")
            f.write("FRAME 0\n")
            for _ in range(8):
                f.write("1 0 1 0 1 0 1 0\n")
            f.write("\nFRAME 1\n")
            for _ in range(8):
                f.write("0 1 0 1 0 1 0 1\n")
            f.write("\nEND\n")
            
        return [str(f) for f in [sample_bin, sample_hex, sample_json, sample_txt]]
        
    def cleanup_temp_files(self, temp_dir: str = None):
        """Clean up temporary files"""
        if temp_dir is None:
            temp_dir = self.config_dir / "temp"
            
        temp_dir = Path(temp_dir)
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                print(f"Failed to cleanup temp files: {e}")
                
    def get_disk_space(self, path: str = None) -> Dict[str, Any]:
        """Get available disk space"""
        if path is None:
            path = os.path.expanduser("~")
            
        try:
            stat = os.statvfs(path)
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            used = total - free
            
            return {
                'total': total,
                'used': used,
                'free': free,
                'total_human': self._format_file_size(total),
                'used_human': self._format_file_size(used),
                'free_human': self._format_file_size(free),
                'usage_percent': (used / total) * 100 if total > 0 else 0
            }
        except Exception as e:
            return {'error': str(e)}
