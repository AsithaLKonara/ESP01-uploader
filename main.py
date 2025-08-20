#!/usr/bin/env python3
"""
J Tech Pixel LED ESP01 Uploader
Professional ESP-01 WiFi firmware uploader with LED Matrix support
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import os
from pathlib import Path

# Import our custom modules
from smart_esp_uploader_with_requirements import SmartESPUploaderWithRequirements
from led_matrix_preview import LEDMatrixPreview
from file_manager import FileManager
from wifi_manager import WiFiManager

class JTechPixelLEDUploader:
    """Main application class for J Tech Pixel LED ESP01 Uploader"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J Tech Pixel LED ESP01 Uploader")
        
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
        
        # Initialize components
        self.esp_uploader = SmartESPUploaderWithRequirements()
        self.led_matrix_preview = LEDMatrixPreview()
        self.file_manager = FileManager()
        self.wifi_manager = WiFiManager()
        
        # Set log callback for the uploader
        self.esp_uploader.set_log_callback(self.log_message)
        
        # Variables
        self.selected_file = tk.StringVar()
        self.ip_var = tk.StringVar(value="192.168.4.1")
        self.port_var = tk.StringVar(value="80")
        self.upload_progress = tk.IntVar()
        
        # Setup UI
        self.setup_ui()
        
        # Load configuration
        self.load_config()
        
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
        
        title_label = ttk.Label(title_frame, text="J Tech Pixel LED ESP01 Uploader", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="Professional ESP-01 WiFi Firmware Uploader with LED Matrix Support",
                                 font=("Arial", 10))
        subtitle_label.pack()
        
        # Connection settings
        connection_frame = ttk.LabelFrame(main_frame, text="ESP-01 Connection Settings", padding="10")
        connection_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Label(connection_frame, text="IP Address:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(connection_frame, textvariable=self.ip_var, width=15).grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(connection_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Entry(connection_frame, textvariable=self.port_var, width=8).grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        
        ttk.Button(connection_frame, text="Connect", command=self.connect_to_esp).grid(row=0, column=4, padx=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(connection_frame, text="Not Connected", foreground="red")
        self.status_label.grid(row=1, column=0, columnspan=5, pady=(5, 0), sticky=tk.W)
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Label(file_frame, text="Selected File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(file_frame, textvariable=self.selected_file, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(file_frame, text="Browse", command=self.browse_file).grid(row=0, column=2)
        
        file_frame.columnconfigure(1, weight=1)
        
        # Upload options
        options_frame = ttk.Frame(file_frame)
        options_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))
        
        self.verify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Verify Upload", variable=self.verify_var).pack(side=tk.LEFT, padx=(0, 20))
        
        self.stream_to_ram_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Stream to RAM", variable=self.stream_to_ram_var).pack(side=tk.LEFT)
        
        # Upload button
        ttk.Button(file_frame, text="Upload File", command=self.upload_file, 
                  style="Accent.TButton").grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        # Progress bar
        progress_frame = ttk.Frame(file_frame)
        progress_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))
        
        ttk.Label(progress_frame, text="Progress:").pack(side=tk.LEFT, padx=(0, 5))
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.upload_progress, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side=tk.LEFT)
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Log tab
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Upload Log")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # LED Matrix Preview tab
        preview_frame = ttk.Frame(notebook)
        notebook.add(preview_frame, text="LED Matrix Preview")
        
        # Add LED matrix preview components here
        ttk.Label(preview_frame, text="LED Matrix Preview - Coming Soon", font=("Arial", 12)).pack(pady=50)
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        
        # Add settings components here
        ttk.Label(settings_frame, text="Settings - Coming Soon", font=("Arial", 12)).pack(pady=50)
        
        # About tab
        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="About")
        
        about_text = """
J Tech Pixel LED ESP01 Uploader
Version 1.0.0

Professional ESP-01 WiFi firmware uploader with LED Matrix support.

Features:
• Automatic requirements management
• WiFi file upload to ESP-01
• SHA256 hash verification
• LED Matrix pattern preview
• Upload history tracking
• Comprehensive logging

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
            
    def connect_to_esp(self):
        """Connect to ESP-01 module"""
        ip = self.ip_var.get()
        
        self.log_message(f"Testing connection to ESP-01 at {ip}")
        self.status_label.config(text="Testing...", foreground="orange")
        
        # Run connection test in separate thread
        def connect_thread():
            try:
                # Test HTTP connectivity to ESP-01
                import requests
                response = requests.get(f"http://{ip}/", timeout=5)
                
                if response.status_code == 200:
                    self.root.after(0, self.connection_success)
                else:
                    self.root.after(0, self.connection_failed, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.root.after(0, self.connection_failed, str(e))
        
        threading.Thread(target=connect_thread, daemon=True).start()
        
    def connection_success(self):
        """Handle successful connection"""
        self.status_label.config(text="Connected to ESP-01", foreground="green")
        self.log_message("Successfully connected to ESP-01")
        
    def connection_failed(self, error):
        """Handle connection failure"""
        self.status_label.config(text="Connection Failed", foreground="red")
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
        
        # For HTTP uploads, we don't need WiFi connection check
        # The custom uploader handles connectivity internally
        
        # Get upload options
        verify = self.verify_var.get()
        stream_to_ram = self.stream_to_ram_var.get()
        
        self.log_message(f"Starting upload: {os.path.basename(file_path)}")
        
        # Run upload in separate thread
        def upload_thread():
            try:
                # Create mock WiFi manager (not needed for HTTP uploads)
                class MockWiFiManager:
                    def is_connected(self):
                        return True
                
                wifi_mgr = MockWiFiManager()
                
                # Perform upload
                success = self.esp_uploader.upload_file(
                    file_path,
                    wifi_mgr,
                    stream_to_ram=stream_to_ram,
                    verify=verify,
                    progress_callback=self.update_progress
                )
                
                if success:
                    self.root.after(0, self.upload_success)
                else:
                    self.root.after(0, self.upload_failed)
                    
            except Exception as e:
                self.root.after(0, self.upload_error, str(e))
        
        threading.Thread(target=upload_thread, daemon=True).start()
        
    def update_progress(self, progress, bytes_sent, total_bytes):
        """Update upload progress"""
        self.root.after(0, self._update_progress_ui, progress, bytes_sent, total_bytes)
        
    def _update_progress_ui(self, progress, bytes_sent, total_bytes):
        """Update progress UI in main thread"""
        self.upload_progress.set(progress)
        self.progress_label.config(text=f"{progress}% ({bytes_sent}/{total_bytes} bytes)")
        
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
        
    def load_config(self):
        """Load application configuration"""
        try:
            config = self.file_manager.load_config()
            if config:
                self.ip_var.set(config.get('esp_ip', '192.168.4.1'))
                self.port_var.set(config.get('esp_port', '80'))
                self.log_message("Configuration loaded")
        except Exception as e:
            self.log_message(f"Could not load configuration: {e}")
            
    def save_config(self):
        """Save application configuration"""
        try:
            config = {
                'esp_ip': self.ip_var.get(),
                'esp_port': self.port_var.get()
            }
            self.file_manager.save_config(config)
            self.log_message("Configuration saved")
        except Exception as e:
            self.log_message(f"Could not save configuration: {e}")
            
    def run(self):
        """Run the application"""
        # Save configuration on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start the main loop
        self.root.mainloop()
        
    def on_closing(self):
        """Handle application closing"""
        self.save_config()
        self.root.destroy()

def main():
    """Main entry point"""
    app = JTechPixelLEDUploader()
    app.run()

if __name__ == "__main__":
    main()
