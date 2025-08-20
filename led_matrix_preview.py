#!/usr/bin/env python3
"""
LED Matrix Preview Module
Provides virtual LED matrix emulation and LED Matrix Studio pattern visualization
"""

import tkinter as tk
from tkinter import ttk, Canvas
import json
import time
import threading
from typing import Optional, List, Tuple, Dict, Any
from PIL import Image, ImageTk
import numpy as np

class LEDMatrixPreview:
    """LED Matrix preview and pattern visualization"""
    
    def __init__(self):
        self.matrix_size = (8, 8)  # Default 8x8 matrix
        self.led_size = 20  # LED size in pixels
        self.led_spacing = 2  # Spacing between LEDs
        self.led_color_on = "#00FF00"  # Green when ON
        self.led_color_off = "#333333"  # Dark gray when OFF
        self.led_color_border = "#666666"  # LED border color
        
        # Pattern data
        self.pattern_data = None
        self.current_frame = 0
        self.total_frames = 0
        self.frame_delay = 100  # milliseconds
        self.is_playing = False
        self.playback_thread = None
        
        # Matrix canvas
        self.canvas = None
        self.led_widgets = []
        
        # Pattern types
        self.supported_formats = ['.lms', '.json', '.txt', '.csv']
        
    def set_matrix_size(self, size_str: str):
        """Set matrix size from string (e.g., '8x8', '16x16')"""
        try:
            width, height = map(int, size_str.split('x'))
            self.matrix_size = (width, height)
            self._create_matrix()
        except ValueError:
            print(f"Invalid matrix size format: {size_str}")
            
    def _create_matrix(self):
        """Create the LED matrix display"""
        if not self.canvas:
            return
            
        # Clear existing LEDs
        for widget in self.led_widgets:
            widget.destroy()
        self.led_widgets.clear()
        
        # Calculate canvas size
        canvas_width = self.matrix_size[0] * (self.led_size + self.led_spacing) + self.led_spacing
        canvas_height = self.matrix_size[1] * (self.led_size + self.led_spacing) + self.led_spacing
        
        self.canvas.config(width=canvas_width, height=canvas_height)
        
        # Create LED widgets
        for y in range(self.matrix_size[1]):
            row = []
            for x in range(self.matrix_size[0]):
                # Calculate LED position
                led_x = x * (self.led_size + self.led_spacing) + self.led_spacing
                led_y = y * (self.led_size + self.led_spacing) + self.led_spacing
                
                # Create LED circle
                led = self.canvas.create_oval(
                    led_x, led_y,
                    led_x + self.led_size, led_y + self.led_size,
                    fill=self.led_color_off,
                    outline=self.led_color_border,
                    width=1,
                    tags=f"led_{x}_{y}"
                )
                
                # Bind click events for manual testing
                self.canvas.tag_bind(f"led_{x}_{y}", "<Button-1>", 
                                   lambda e, x=x, y=y: self._toggle_led(x, y))
                
                row.append(led)
            self.led_widgets.append(row)
            
    def _toggle_led(self, x: int, y: int):
        """Toggle LED state on click"""
        if 0 <= y < len(self.led_widgets) and 0 <= x < len(self.led_widgets[0]):
            current_fill = self.canvas.itemcget(self.led_widgets[y][x], "fill")
            new_fill = self.led_color_on if current_fill == self.led_color_off else self.led_color_off
            self.canvas.itemconfig(self.led_widgets[y][x], fill=new_fill)
            
    def set_canvas(self, canvas: Canvas):
        """Set the canvas for LED matrix display"""
        self.canvas = canvas
        self._create_matrix()
        
    def load_pattern(self, file_path: str) -> bool:
        """
        Load LED Matrix Studio pattern file
        
        Args:
            file_path: Path to the pattern file
            
        Returns:
            bool: True if pattern loaded successfully
        """
        try:
            file_ext = file_path.lower().split('.')[-1]
            
            if file_ext == 'lms':
                return self._load_lms_pattern(file_path)
            elif file_ext == 'json':
                return self._load_json_pattern(file_path)
            elif file_ext in ['txt', 'csv']:
                return self._load_text_pattern(file_path)
            else:
                print(f"Unsupported file format: {file_ext}")
                return False
                
        except Exception as e:
            print(f"Error loading pattern: {e}")
            return False
            
    def _load_lms_pattern(self, file_path: str) -> bool:
        """Load LED Matrix Studio (.lms) pattern file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Parse LMS format (simplified - adjust based on actual format)
            # This is a basic parser - you may need to adjust based on your LMS file structure
            lines = content.strip().split('\n')
            
            pattern_data = []
            current_frame = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if line.startswith('FRAME'):
                    if current_frame:
                        pattern_data.append(current_frame)
                    current_frame = []
                elif line.startswith('END'):
                    break
                else:
                    # Parse LED data (assuming binary or hex format)
                    try:
                        led_row = []
                        for char in line:
                            if char in '01':
                                led_row.append(int(char))
                            elif char in '0123456789ABCDEFabcdef':
                                # Convert hex to binary
                                val = int(char, 16)
                                for i in range(4):
                                    led_row.append((val >> (3-i)) & 1)
                        if led_row:
                            current_frame.append(led_row)
                    except:
                        continue
                        
            if current_frame:
                pattern_data.append(current_frame)
                
            if pattern_data:
                self.pattern_data = pattern_data
                self.total_frames = len(pattern_data)
                self.current_frame = 0
                self._display_frame(0)
                return True
                
            return False
            
        except Exception as e:
            print(f"Error parsing LMS file: {e}")
            return False
            
    def _load_json_pattern(self, file_path: str) -> bool:
        """Load JSON pattern file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Extract pattern data from JSON
            if 'frames' in data:
                pattern_data = data['frames']
            elif 'pattern' in data:
                pattern_data = data['pattern']
            else:
                print("Invalid JSON format: no frames or pattern found")
                return False
                
            # Validate and convert pattern data
            validated_pattern = []
            for frame in pattern_data:
                if isinstance(frame, list) and len(frame) <= self.matrix_size[1]:
                    # Pad or truncate to match matrix size
                    validated_frame = []
                    for row in frame:
                        if isinstance(row, list):
                            # Ensure row has correct width
                            row_data = row[:self.matrix_size[0]]
                            while len(row_data) < self.matrix_size[0]:
                                row_data.append(0)
                            validated_frame.append(row_data)
                        else:
                            # Single row - convert to 2D
                            row_data = [int(bit) for bit in str(row)]
                            row_data = row_data[:self.matrix_size[0]]
                            while len(row_data) < self.matrix_size[0]:
                                row_data.append(0)
                            validated_frame.append(row_data)
                            
                    # Pad height if needed
                    while len(validated_frame) < self.matrix_size[1]:
                        validated_frame.append([0] * self.matrix_size[0])
                        
                    validated_pattern.append(validated_frame)
                    
            if validated_pattern:
                self.pattern_data = validated_pattern
                self.total_frames = len(validated_pattern)
                self.current_frame = 0
                self._display_frame(0)
                return True
                
            return False
            
        except Exception as e:
            print(f"Error parsing JSON file: {e}")
            return False
            
    def _load_text_pattern(self, file_path: str) -> bool:
        """Load text/CSV pattern file"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            pattern_data = []
            current_frame = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if line.startswith('FRAME') or line.startswith('---'):
                    if current_frame:
                        pattern_data.append(current_frame)
                    current_frame = []
                elif line.startswith('END'):
                    break
                else:
                    # Parse line as comma-separated or space-separated values
                    values = line.replace(',', ' ').split()
                    led_row = []
                    
                    for val in values:
                        try:
                            if val in '01':
                                led_row.append(int(val))
                            elif val.isdigit():
                                led_row.append(int(val) % 2)  # Convert to binary
                            else:
                                led_row.append(0)
                        except:
                            led_row.append(0)
                            
                    if led_row:
                        # Pad or truncate to matrix width
                        led_row = led_row[:self.matrix_size[0]]
                        while len(led_row) < self.matrix_size[0]:
                            led_row.append(0)
                        current_frame.append(led_row)
                        
            if current_frame:
                pattern_data.append(current_frame)
                
            if pattern_data:
                # Pad height if needed
                for frame in pattern_data:
                    while len(frame) < self.matrix_size[1]:
                        frame.append([0] * self.matrix_size[0])
                        
                self.pattern_data = pattern_data
                self.total_frames = len(pattern_data)
                self.current_frame = 0
                self._display_frame(0)
                return True
                
            return False
            
        except Exception as e:
            print(f"Error parsing text file: {e}")
            return False
            
    def _display_frame(self, frame_index: int):
        """Display a specific frame on the LED matrix"""
        if not self.pattern_data or frame_index >= len(self.pattern_data):
            return
            
        frame = self.pattern_data[frame_index]
        
        for y, row in enumerate(frame):
            if y >= len(self.led_widgets):
                break
            for x, led_state in enumerate(row):
                if x >= len(self.led_widgets[y]):
                    break
                    
                # Update LED color based on state
                color = self.led_color_on if led_state else self.led_color_off
                self.canvas.itemconfig(self.led_widgets[y][x], fill=color)
                
    def play_pattern(self, speed: float = 1.0):
        """Start pattern playback"""
        if not self.pattern_data or self.is_playing:
            return
            
        self.is_playing = True
        self.frame_delay = int(100 / speed)  # Convert speed to delay
        
        # Start playback in separate thread
        self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.playback_thread.start()
        
    def _playback_loop(self):
        """Pattern playback loop"""
        while self.is_playing:
            # Display current frame
            self._display_frame(self.current_frame)
            
            # Wait for frame delay
            time.sleep(self.frame_delay / 1000.0)
            
            # Move to next frame
            self.current_frame = (self.current_frame + 1) % self.total_frames
            
    def stop_pattern(self):
        """Stop pattern playback"""
        self.is_playing = False
        if self.playback_thread:
            self.playback_thread.join(timeout=1.0)
            self.playback_thread = None
            
    def pause_pattern(self):
        """Pause pattern playback"""
        self.is_playing = False
        
    def resume_pattern(self):
        """Resume pattern playback"""
        if self.pattern_data and not self.is_playing:
            self.play_pattern()
            
    def next_frame(self):
        """Go to next frame"""
        if self.pattern_data:
            self.current_frame = (self.current_frame + 1) % self.total_frames
            self._display_frame(self.current_frame)
            
    def previous_frame(self):
        """Go to previous frame"""
        if self.pattern_data:
            self.current_frame = (self.current_frame - 1) % self.total_frames
            self._display_frame(self.current_frame)
            
    def go_to_frame(self, frame_index: int):
        """Go to specific frame"""
        if self.pattern_data and 0 <= frame_index < len(self.pattern_data):
            self.current_frame = frame_index
            self._display_frame(frame_index)
            
    def set_speed(self, speed: float):
        """Set playback speed (0.1 to 5.0)"""
        self.frame_delay = int(100 / max(0.1, min(5.0, speed)))
        
    def clear_matrix(self):
        """Clear all LEDs (turn off)"""
        for row in self.led_widgets:
            for led in row:
                self.canvas.itemconfig(led, fill=self.led_color_off)
                
    def set_led_color(self, color_on: str, color_off: str = None, color_border: str = None):
        """Set LED colors"""
        self.led_color_on = color_on
        if color_off:
            self.led_color_off = color_off
        if color_border:
            self.led_color_border = color_border
            
        # Update current display
        if self.pattern_data:
            self._display_frame(self.current_frame)
            
    def get_pattern_info(self) -> Dict[str, Any]:
        """Get information about the loaded pattern"""
        if not self.pattern_data:
            return {'loaded': False}
            
        return {
            'loaded': True,
            'total_frames': self.total_frames,
            'current_frame': self.current_frame,
            'matrix_size': self.matrix_size,
            'frame_delay': self.frame_delay,
            'is_playing': self.is_playing
        }
        
    def export_pattern(self, file_path: str, format: str = 'json') -> bool:
        """Export pattern to different format"""
        if not self.pattern_data:
            return False
            
        try:
            if format == 'json':
                with open(file_path, 'w') as f:
                    json.dump({
                        'matrix_size': self.matrix_size,
                        'total_frames': self.total_frames,
                        'frames': self.pattern_data
                    }, f, indent=2)
                    
            elif format == 'txt':
                with open(file_path, 'w') as f:
                    f.write(f"# LED Matrix Pattern Export\n")
                    f.write(f"# Matrix Size: {self.matrix_size[0]}x{self.matrix_size[1]}\n")
                    f.write(f"# Total Frames: {self.total_frames}\n\n")
                    
                    for i, frame in enumerate(self.pattern_data):
                        f.write(f"FRAME {i}\n")
                        for row in frame:
                            f.write(' '.join(map(str, row)) + '\n')
                        f.write('\n')
                    f.write("END\n")
                    
            else:
                print(f"Unsupported export format: {format}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Export error: {e}")
            return False
            
    def create_test_pattern(self, pattern_type: str = 'blink'):
        """Create a test pattern for demonstration"""
        if pattern_type == 'blink':
            # Simple blink pattern
            frame1 = [[1] * self.matrix_size[0] for _ in range(self.matrix_size[1])]
            frame2 = [[0] * self.matrix_size[0] for _ in range(self.matrix_size[1])]
            self.pattern_data = [frame1, frame2]
            
        elif pattern_type == 'scan':
            # Scanning pattern
            self.pattern_data = []
            for i in range(self.matrix_size[0]):
                frame = [[0] * self.matrix_size[0] for _ in range(self.matrix_size[1])]
                for y in range(self.matrix_size[1]):
                    frame[y][i] = 1
                self.pattern_data.append(frame)
                
        elif pattern_type == 'random':
            # Random pattern
            import random
            self.pattern_data = []
            for _ in range(10):
                frame = []
                for _ in range(self.matrix_size[1]):
                    row = [random.choice([0, 1]) for _ in range(self.matrix_size[0])]
                    frame.append(row)
                self.pattern_data.append(frame)
                
        if self.pattern_data:
            self.total_frames = len(self.pattern_data)
            self.current_frame = 0
            self._display_frame(0)
            return True
            
        return False
