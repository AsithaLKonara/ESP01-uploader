#!/usr/bin/env python3
"""
J Tech Pixel LED ESP01 Uploader - Enhanced Version
Professional ESP-01 WiFi firmware uploader with LED Matrix support
Updated for Enhanced Firmware with Large Pattern Support
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import requests
import json
import time
import os
import sys
from pathlib import Path

class JTechPixelLEDUploader:
    """Main application class for J Tech Pixel LED ESP01 Uploader"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J Tech Pixel LED ESP01 Uploader - Enhanced")
        
        # Set application icon
        try:
            icon_path = "LEDMatrixStudio_Icon.ico"
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        # Configure window
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Variables
        self.selected_file = tk.StringVar()
        self.ip_var = tk.StringVar(value="192.168.4.1")
        self.port_var = tk.StringVar(value="80")
        self.upload_progress = tk.IntVar()
        self.upload_token = tk.StringVar(value="upload_token_2025")
        self.connection_status = "Not Connected"
        
        # Setup UI
        self.setup_ui()
        
        # Test connection on startup
        self.test_connection()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title and branding
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky=(tk.W, tk.E))
        
        title_label = ttk.Label(title_frame, text="J Tech Pixel LED ESP01 Uploader - Enhanced", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="Enhanced ESP-01 WiFi Firmware with Large Pattern Support",
                                  font=("Arial", 10))
        subtitle_label.pack()
        
        # Connection settings
        connection_frame = ttk.LabelFrame(main_frame, text="ESP-01 Connection Settings", padding="10")
        connection_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Label(connection_frame, text="IP Address:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(connection_frame, textvariable=self.ip_var, width=15).grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(connection_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Entry(connection_frame, textvariable=self.ip_var, width=8).grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(connection_frame, text="Token:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        ttk.Entry(connection_frame, textvariable=self.upload_token, width=20).grid(row=0, column=5, sticky=tk.W, padx=(0, 10))
        
        ttk.Button(connection_frame, text="Test Connection", command=self.test_connection).grid(row=0, column=6, padx=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(connection_frame, text="Not Connected", foreground="red")
        self.status_label.grid(row=1, column=0, columnspan=7, pady=(5, 0), sticky=tk.W)
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="File Selection & Upload", padding="10")
        file_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Label(file_frame, text="Selected File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(file_frame, textvariable=self.selected_file, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(file_frame, text="Browse", command=self.browse_file).grid(row=0, column=2)
        
        file_frame.columnconfigure(1, weight=1)
        
        # Upload options
        options_frame = ttk.Frame(file_frame)
        options_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))
        
        self.verify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Verify Upload", variable=self.verify_var).pack(side=tk.LEFT)
        
        self.chunked_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Chunked Upload (Large Files)", variable=self.chunked_var).pack(side=tk.LEFT, padx=(20, 0))
        
        # Upload buttons
        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="Upload File", command=self.upload_file, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Upload Chunked", command=self.upload_chunked).pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress bar
        progress_frame = ttk.Frame(file_frame)
        progress_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))
        
        ttk.Label(progress_frame, text="Progress:").pack(side=tk.LEFT, padx=(0, 5))
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.upload_progress, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side=tk.LEFT)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Pattern Control", padding="10")
        control_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Pattern playback controls
        playback_frame = ttk.Frame(control_frame)
        playback_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Label(playback_frame, text="Pattern File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.pattern_file_var = tk.StringVar()
        ttk.Entry(playback_frame, textvariable=self.pattern_file_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Button(playback_frame, text="Play", command=self.play_pattern).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(playback_frame, text="Stop", command=self.stop_pattern).grid(row=0, column=3)
        
        # Metadata frame
        metadata_frame = ttk.Frame(control_frame)
        metadata_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(metadata_frame, text="Frames:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.frames_var = tk.StringVar(value="100")
        ttk.Entry(metadata_frame, textvariable=self.frames_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(metadata_frame, text="Delay (ms):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.delay_var = tk.StringVar(value="50")
        ttk.Entry(metadata_frame, textvariable=self.delay_var, width=10).grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        
        ttk.Button(metadata_frame, text="Set Metadata", command=self.set_metadata).grid(row=0, column=4, padx=(10, 0))
        
        control_frame.columnconfigure(0, weight=1)
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Log tab
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Upload Log")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status tab
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="ESP01 Status")
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=15, width=80)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Test tab
        test_frame = ttk.Frame(notebook)
        notebook.add(test_frame, text="Firmware Test")
        
        test_buttons_frame = ttk.Frame(test_frame)
        test_buttons_frame.pack(pady=20)
        
        ttk.Button(test_buttons_frame, text="Test Connection", command=self.test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_buttons_frame, text="Test All Endpoints", command=self.test_endpoints).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_buttons_frame, text="Show Status", command=self.show_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_buttons_frame, text="Open Web Interface", command=self.open_web_interface).pack(side=tk.LEFT, padx=5)
        
        # About tab
        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="About")
        
        about_text = """
J Tech Pixel LED ESP01 Uploader - Enhanced Version
Version 2.0.0

Enhanced ESP-01 WiFi firmware with LED Matrix support.

New Features:
• Large pattern support (up to 200KB)
• Chunked uploads for huge files
• Enhanced WiFi security
• FastLED integration
• Web interface control
• Token-based security

© 2025 J Tech Solutions
        """
        
        about_label = ttk.Label(about_frame, text=about_text, justify=tk.LEFT, font=("Arial", 10))
        about_label.pack(pady=20)
    
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Update log in main thread
        self.root.after(0, self._update_log, log_entry)
    
    def _update_log(self, message):
        """Update log text widget (called in main thread)"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
    
    def update_status_display(self, message):
        """Update status display in main thread"""
        self.root.after(0, self._update_status_display, message)
    
    def _update_status_display(self, message):
        """Update status text widget (called in main thread)"""
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, message)
    
    def browse_file(self):
        """Browse for file to upload"""
        file_types = [
            ("All supported files", "*.bin;*.hex;*.dat;*.lms;*.json;*.txt;*.csv"),
            ("Binary files", "*.bin"),
            ("Intel HEX files", "*.hex"),
            ("Data files", "*.dat"),
            ("LED Matrix Studio files", "*.lms"),
            ("JSON files", "*.json"),
            ("Text files", "*.txt"),
            ("CSV files", "*.csv"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select file to upload",
            filetypes=file_types
        )
        
        if filename:
            self.selected_file.set(filename)
            self.log_message(f"Selected file: {filename}")
            
            # Auto-fill pattern file name for playback
            self.pattern_file_var.set(os.path.basename(filename))
    
    def test_connection(self):
        """Test connection to ESP-01 module"""
        ip = self.ip_var.get()
        
        self.log_message(f"Testing connection to ESP-01 at {ip}")
        self.status_label.config(text="Testing...", foreground="orange")
        
        # Run connection test in separate thread
        def connect_thread():
            try:
                response = requests.get(f"http://{ip}/status", timeout=5)
                if response.status_code == 200:
                    self.root.after(0, self.connection_success)
                    self.log_message("Successfully connected to ESP-01")
                else:
                    self.root.after(0, self.connection_failed, f"HTTP {response.status_code}")
            except Exception as e:
                self.root.after(0, self.connection_failed, str(e))
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def connection_success(self):
        """Handle successful connection"""
        self.status_label.config(text="Connected to ESP-01", foreground="green")
        self.connection_status = "Connected"
        self.log_message("Successfully connected to ESP-01")
    
    def connection_failed(self, error):
        """Handle connection failure"""
        self.status_label.config(text="Connection Failed", foreground="red")
        self.connection_status = "Failed"
        self.log_message(f"Connection failed: {error}")
    
    def upload_file(self):
        """Upload selected file to ESP-01"""
        file_path = self.selected_file.get()
        
        if not file_path:
            messagebox.showerror("Error", "Please select a file to upload")
            return
            
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "Selected file does not exist")
            return
        
        if self.connection_status != "Connected":
            messagebox.showerror("Error", "Please connect to ESP-01 first")
            return
        
        self.log_message(f"Starting upload: {os.path.basename(file_path)}")
        
        # Run upload in separate thread
        def upload_thread():
            try:
                success = self._perform_upload(file_path, chunked=False)
                if success:
                    self.root.after(0, self.upload_success)
                else:
                    self.root.after(0, self.upload_failed)
            except Exception as e:
                self.root.after(0, self.upload_error, str(e))
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def upload_chunked(self):
        """Upload selected file using chunked method"""
        file_path = self.selected_file.get()
        
        if not file_path:
            messagebox.showerror("Error", "Please select a file to upload")
            return
            
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "Selected file does not exist")
            return
        
        if self.connection_status != "Connected":
            messagebox.showerror("Error", "Please connect to ESP-01 first")
            return
        
        self.log_message(f"Starting chunked upload: {os.path.basename(file_path)}")
        
        # Run upload in separate thread
        def upload_thread():
            try:
                success = self._perform_upload(file_path, chunked=True)
                if success:
                    self.root.after(0, self.upload_success)
                else:
                    self.root.after(0, self.upload_failed)
            except Exception as e:
                self.root.after(0, self.upload_error, str(e))
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def _perform_upload(self, file_path, chunked=False):
        """Perform the actual upload"""
        try:
            file_size = os.path.getsize(file_path)
            self.log_message(f"File size: {file_size} bytes")
            
            with open(file_path, 'rb') as f:
                if chunked:
                    # Chunked upload
                    chunk_name = f"chunk_{int(time.time())}.bin"
                    files = {'file': (chunk_name, f, 'application/octet-stream')}
                    data = {'chunk_name': chunk_name, 'token': self.upload_token.get()}
                    url = f"http://{self.ip_var.get()}/upload-chunked?token={self.upload_token.get()}"
                else:
                    # Regular upload
                    files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                    data = {'token': self.upload_token.get()}
                    url = f"http://{self.ip_var.get()}/upload?token={self.upload_token.get()}"
                
                # Simulate progress
                for i in range(0, 101, 10):
                    self.root.after(0, self._update_progress, i)
                    time.sleep(0.1)
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    self.log_message("Upload completed successfully!")
                    return True
                else:
                    self.log_message(f"Upload failed: HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_message(f"Upload error: {e}")
            return False
    
    def play_pattern(self):
        """Start playing a pattern"""
        filename = self.pattern_file_var.get()
        
        if not filename:
            messagebox.showerror("Error", "Please enter a pattern filename")
            return
        
        self.log_message(f"Starting playback: {filename}")
        
        # Run in separate thread
        def play_thread():
            try:
                response = requests.get(f"http://{self.ip_var.get()}/play?file={filename}", timeout=5)
                if response.status_code == 200:
                    self.log_message("Playback started successfully!")
                else:
                    self.log_message(f"Playback failed: HTTP {response.status_code}")
            except Exception as e:
                self.log_message(f"Playback error: {e}")
        
        threading.Thread(target=play_thread, daemon=True).start()
    
    def stop_pattern(self):
        """Stop current playback"""
        self.log_message("Stopping playback...")
        
        # Run in separate thread
        def stop_thread():
            try:
                response = requests.get(f"http://{self.ip_var.get()}/stop", timeout=5)
                if response.status_code == 200:
                    self.log_message("Playback stopped successfully!")
                else:
                    self.log_message(f"Stop failed: HTTP {response.status_code}")
            except Exception as e:
                self.log_message(f"Stop error: {e}")
        
        threading.Thread(target=stop_thread, daemon=True).start()
    
    def set_metadata(self):
        """Set metadata for a pattern file"""
        filename = self.pattern_file_var.get()
        frames = self.frames_var.get()
        delay = self.delay_var.get()
        
        if not all([filename, frames, delay]):
            messagebox.showerror("Error", "Please fill in all metadata fields")
            return
        
        try:
            frames_int = int(frames)
            delay_int = int(delay)
        except ValueError:
            messagebox.showerror("Error", "Frames and delay must be numbers")
            return
        
        self.log_message(f"Setting metadata: {filename}, {frames_int} frames, {delay_int}ms delay")
        
        # Run in separate thread
        def metadata_thread():
            try:
                metadata = {
                    "file": filename,
                    "frames": frames_int,
                    "delay": delay_int
                }
                
                response = requests.post(
                    f"http://{self.ip_var.get()}/set-metadata?token={self.upload_token.get()}",
                    json=metadata,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_message("Metadata set successfully!")
                else:
                    self.log_message(f"Metadata set failed: HTTP {response.status_code}")
            except Exception as e:
                self.log_message(f"Metadata set error: {e}")
        
        threading.Thread(target=metadata_thread, daemon=True).start()
    
    def test_endpoints(self):
        """Test all ESP01 endpoints"""
        self.log_message("Testing all endpoints...")
        
        # Run in separate thread
        def test_thread():
            try:
                ip = self.ip_var.get()
                endpoints = [
                    ("/", "Root page", 200),
                    ("/status", "Status endpoint", 200),
                    ("/upload", "Upload endpoint", 405),
                    ("/upload-chunked", "Chunked upload", 405),
                    ("/set-metadata", "Metadata endpoint", 405),
                    ("/play", "Play endpoint", 400),
                    ("/stop", "Stop endpoint", 200)
                ]
                
                results = []
                for endpoint, description, expected_status in endpoints:
                    try:
                        response = requests.get(f"http://{ip}{endpoint}", timeout=5)
                        if response.status_code == expected_status:
                            results.append(f"✅ {endpoint}: {description}")
                        else:
                            results.append(f"⚠️  {endpoint}: HTTP {response.status_code} (expected {expected_status})")
                    except Exception as e:
                        results.append(f"❌ {endpoint}: {e}")
                
                self.update_status_display("Endpoint Test Results:\n\n" + "\n".join(results))
                self.log_message("Endpoint testing completed")
                
            except Exception as e:
                self.log_message(f"Endpoint testing error: {e}")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def show_status(self):
        """Show current ESP01 status"""
        self.log_message("Fetching ESP01 status...")
        
        # Run in separate thread
        def status_thread():
            try:
                response = requests.get(f"http://{self.ip_var.get()}/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    status_text = f"ESP01 Status:\n\n"
                    status_text += f"Uptime: {data.get('uptime')} ms\n"
                    status_text += f"Free Heap: {data.get('free_heap')} bytes\n"
                    status_text += f"Playing: {data.get('playing')}\n"
                    status_text += f"Current File: {data.get('current_file', 'None')}"
                    
                    self.update_status_display(status_text)
                    self.log_message("Status updated")
                else:
                    self.log_message(f"Status request failed: HTTP {response.status_code}")
            except Exception as e:
                self.log_message(f"Status check error: {e}")
        
        threading.Thread(target=status_thread, daemon=True).start()
    
    def open_web_interface(self):
        """Open web interface in default browser"""
        import webbrowser
        url = f"http://{self.ip_var.get()}/"
        self.log_message(f"Opening web interface: {url}")
        webbrowser.open(url)
    
    def _update_progress(self, progress):
        """Update progress bar"""
        self.upload_progress.set(progress)
        self.progress_label.config(text=f"{progress}%")
    
    def upload_success(self):
        """Handle successful upload"""
        self.log_message("File uploaded successfully!")
        messagebox.showinfo("Success", "File uploaded successfully!")
        self.upload_progress.set(0)
        self.progress_label.config(text="0%")
    
    def upload_failed(self):
        """Handle upload failure"""
        self.log_message("Upload failed")
        messagebox.showerror("Error", "Upload failed")
        self.upload_progress.set(0)
        self.progress_label.config(text="0%")
    
    def upload_error(self, error):
        """Handle upload error"""
        self.log_message(f"Upload error: {error}")
        messagebox.showerror("Error", f"Upload error: {error}")
        self.upload_progress.set(0)
        self.progress_label.config(text="0%")
    
    def run(self):
        """Run the application"""
        # Start the main loop
        self.root.mainloop()

def main():
    """Main entry point"""
    # Create and run the application
    app = JTechPixelLEDUploader()
    app.run()

if __name__ == "__main__":
    main()
