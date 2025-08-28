#!/usr/bin/env python3
"""
ESP01 LED Matrix Uploader with LED Matrix Studio Integration

This enhanced uploader can:
1. Parse LED Matrix Studio files (.leds, .LedAnim)
2. Split animations into individual frames
3. Upload frames to ESP01 one by one for smooth display
4. Handle different export formats (Mono, Binary, RGB)
5. Provide streaming upload without overwhelming ESP01 memory
"""

import os
import sys
import time
import json
import threading
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Import our LED Matrix parser
from led_matrix_parser import LEDMatrixParser, MatrixFrame, ExportFormat, MatrixMode


class UploadMode(Enum):
    """Upload operation modes"""
    SINGLE_FRAME = "single"
    STREAM_FRAMES = "stream"
    LOOP_ANIMATION = "loop"


@dataclass
class ESP01Settings:
    """ESP01 connection settings"""
    ip_address: str = "192.168.4.1"
    port: int = 80
    upload_endpoint: str = "/upload"
    frame_delay_ms: int = 100  # Delay between frames
    timeout_seconds: int = 5
    max_retries: int = 3


class ESP01LEDUploader:
    """Enhanced ESP01 uploader for LED Matrix Studio files"""
    
    def __init__(self, settings: ESP01Settings = None):
        self.settings = settings or ESP01Settings()
        self.parser = LEDMatrixParser()
        self.current_animation = None
        self.is_streaming = False
        self.stream_thread = None
        
    def load_led_matrix_file(self, file_path: str) -> bool:
        """Load and parse a LED Matrix Studio file"""
        try:
            print(f"Loading LED Matrix Studio file: {file_path}")
            frames = self.parser.parse_file(file_path)
            
            if frames:
                self.current_animation = {
                    'file_path': file_path,
                    'frames': frames,
                    'total_frames': len(frames),
                    'current_frame': 0
                }
                
                info = self.parser.get_frame_info()
                print(f"Successfully loaded animation:")
                print(f"  - Total frames: {info['total_frames']}")
                print(f"  - Matrix size: {info['matrix_width']}x{info['matrix_height']}")
                print(f"  - Matrix mode: {info['matrix_mode']}")
                
                return True
            else:
                print("No frames found in file")
                return False
                
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def upload_single_frame(self, frame_index: int = 0, format_type: ExportFormat = ExportFormat.BINARY) -> bool:
        """Upload a single frame to ESP01"""
        if not self.current_animation:
            print("No animation loaded. Load a file first.")
            return False
        
        if frame_index >= len(self.current_animation['frames']):
            print(f"Frame index {frame_index} out of range")
            return False
        
        frame = self.current_animation['frames'][frame_index]
        print(f"Uploading frame {frame_index + 1}/{self.current_animation['total_frames']}")
        
        try:
            # Convert frame to bytes
            frame_bytes = frame.to_bytes(format_type)
            
            # Upload to ESP01
            success = self._upload_frame_data(frame_bytes, frame_index)
            
            if success:
                print(f"Frame {frame_index + 1} uploaded successfully")
                self.current_animation['current_frame'] = frame_index
                return True
            else:
                print(f"Failed to upload frame {frame_index + 1}")
                return False
                
        except Exception as e:
            print(f"Error uploading frame: {e}")
            return False
    
    def start_streaming(self, format_type: ExportFormat = ExportFormat.BINARY, loop: bool = False) -> bool:
        """Start streaming frames to ESP01"""
        if not self.current_animation:
            print("No animation loaded. Load a file first.")
            return False
        
        if self.is_streaming:
            print("Already streaming. Stop current stream first.")
            return False
        
        self.is_streaming = True
        self.stream_thread = threading.Thread(
            target=self._stream_frames,
            args=(format_type, loop)
        )
        self.stream_thread.daemon = True
        self.stream_thread.start()
        
        print(f"Started streaming {self.current_animation['total_frames']} frames")
        if loop:
            print("Loop mode enabled")
        return True
    
    def stop_streaming(self):
        """Stop the current stream"""
        self.is_streaming = False
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2)
        print("Streaming stopped")
    
    def _stream_frames(self, format_type: ExportFormat, loop: bool):
        """Internal method for streaming frames"""
        try:
            while self.is_streaming:
                frames = self.current_animation['frames']
                total_frames = len(frames)
                
                for frame_index in range(total_frames):
                    if not self.is_streaming:
                        break
                    
                    # Upload frame
                    success = self.upload_single_frame(frame_index, format_type)
                    
                    if not success:
                        print(f"Streaming failed at frame {frame_index + 1}")
                        break
                    
                    # Wait before next frame (unless it's the last frame and we're not looping)
                    if frame_index < total_frames - 1 or loop:
                        time.sleep(self.settings.frame_delay_ms / 1000.0)
                
                # If not looping, break after one complete cycle
                if not loop:
                    break
                
                print("Animation loop completed, restarting...")
                
        except Exception as e:
            print(f"Streaming error: {e}")
        finally:
            self.is_streaming = False
    
    def _upload_frame_data(self, frame_data: bytes, frame_index: int) -> bool:
        """Upload frame data to ESP01 via HTTP"""
        try:
            import requests
            
            # Prepare upload data
            upload_data = {
                'frame_index': frame_index,
                'frame_data': frame_data.hex(),  # Convert bytes to hex string
                'frame_size': len(frame_data),
                'timestamp': int(time.time())
            }
            
            # Upload to ESP01
            url = f"http://{self.settings.ip_address}:{self.settings.port}{self.settings.upload_endpoint}"
            
            response = requests.post(
                url,
                json=upload_data,
                timeout=self.settings.timeout_seconds
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return True
                else:
                    print(f"ESP01 returned error: {result.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"HTTP error: {response.status_code}")
                return False
                
        except ImportError:
            print("requests library not available. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Upload error: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current uploader status"""
        status = {
            'is_streaming': self.is_streaming,
            'has_animation': self.current_animation is not None
        }
        
        if self.current_animation:
            status.update({
                'file_path': self.current_animation['file_path'],
                'total_frames': self.current_animation['total_frames'],
                'current_frame': self.current_animation['current_frame'],
                'frames_remaining': self.current_animation['total_frames'] - self.current_animation['current_frame'] - 1
            })
        
        return status
    
    def export_frames_locally(self, format_type: ExportFormat = ExportFormat.BINARY, output_dir: str = "esp01_frames") -> List[str]:
        """Export frames to local files for manual upload"""
        if not self.current_animation:
            print("No animation loaded. Load a file first.")
            return []
        
        try:
            output_files = self.parser.export_frames_for_esp01(format_type, output_dir)
            print(f"Exported {len(output_files)} frames to {output_dir}/")
            return output_files
        except Exception as e:
            print(f"Export error: {e}")
            return []


def main():
    """Main function for command-line usage"""
    print("ESP01 LED Matrix Uploader with LED Matrix Studio Integration")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python esp01_led_uploader.py <file_path> [options]")
        print("\nOptions:")
        print("  --stream          Stream frames continuously")
        print("  --loop            Loop animation (use with --stream)")
        print("  --format FORMAT   Export format (mono, binary, rgb, rgb3pp)")
        print("  --ip IP           ESP01 IP address (default: 192.168.4.1)")
        print("  --port PORT       ESP01 port (default: 80)")
        print("  --delay MS        Frame delay in milliseconds (default: 100)")
        print("  --export-only     Export frames locally without uploading")
        print("\nExamples:")
        print("  python esp01_led_uploader.py animation.LedAnim --stream --loop")
        print("  python esp01_led_uploader.py pattern.leds --format binary --export-only")
        return
    
    file_path = sys.argv[1]
    
    # Parse options
    options = {
        'stream': '--stream' in sys.argv,
        'loop': '--loop' in sys.argv,
        'export_only': '--export-only' in sys.argv,
        'format': 'binary'  # default
    }
    
    # Parse format
    if '--format' in sys.argv:
        try:
            format_index = sys.argv.index('--format')
            if format_index + 1 < len(sys.argv):
                format_str = sys.argv[format_index + 1].lower()
                format_map = {
                    'mono': ExportFormat.MONO,
                    'binary': ExportFormat.BINARY,
                    'rgb': ExportFormat.RGB,
                    'rgb3pp': ExportFormat.RGB3PP
                }
                if format_str in format_map:
                    options['format'] = format_map[format_str]
        except:
            pass
    
    # Parse ESP01 settings
    settings = ESP01Settings()
    if '--ip' in sys.argv:
        try:
            ip_index = sys.argv.index('--ip')
            if ip_index + 1 < len(sys.argv):
                settings.ip_address = sys.argv[ip_index + 1]
        except:
            pass
    
    if '--port' in sys.argv:
        try:
            port_index = sys.argv.index('--port')
            if port_index + 1 < len(sys.argv):
                settings.port = int(sys.argv[port_index + 1])
        except:
            pass
    
    if '--delay' in sys.argv:
        try:
            delay_index = sys.argv.index('--delay')
            if delay_index + 1 < len(sys.argv):
                settings.frame_delay_ms = int(sys.argv[delay_index + 1])
        except:
            pass
    
    # Create uploader and load file
    uploader = ESP01LEDUploader(settings)
    
    if not uploader.load_led_matrix_file(file_path):
        print("Failed to load file. Exiting.")
        return
    
    # Handle export-only mode
    if options['export_only']:
        print("Exporting frames locally...")
        output_files = uploader.export_frames_locally(options['format'])
        print(f"Exported {len(output_files)} frames")
        return
    
    # Handle streaming mode
    if options['stream']:
        print("Starting frame stream...")
        if uploader.start_streaming(options['format'], options['loop']):
            try:
                # Keep main thread alive while streaming
                while uploader.is_streaming:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nStopping stream...")
                uploader.stop_streaming()
    else:
        # Single frame upload mode
        print("Uploading single frame...")
        if uploader.upload_single_frame(0, options['format']):
            print("Frame uploaded successfully")
        else:
            print("Frame upload failed")


if __name__ == "__main__":
    main()
