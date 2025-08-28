#!/usr/bin/env python3
"""
LED Matrix Studio File Parser for ESP01 Integration

This script can parse LED Matrix Studio files (.leds, .LedAnim) and extract
frames for uploading to ESP01 devices. It provides the core functionality
needed for ESP01 integration without requiring the full C++ build.
"""

import os
import struct
import json
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum


class MatrixMode(Enum):
    """Matrix operation modes"""
    MONO = 0
    BI = 1
    RGB = 2
    RGB3PP = 3


class ExportFormat(Enum):
    """Export format types"""
    MONO = 0
    BINARY = 1
    RGB = 2
    RGB3PP = 3


@dataclass
class MatrixFrame:
    """Represents a single matrix frame"""
    width: int
    height: int
    mode: MatrixMode
    data: List[List[int]]  # 2D array of pixel values
    frame_number: int = 0
    
    def to_bytes(self, format_type: ExportFormat) -> bytes:
        """Convert frame to bytes for transmission"""
        if format_type == ExportFormat.MONO:
            return self._to_mono_bytes()
        elif format_type == ExportFormat.BINARY:
            return self._to_binary_bytes()
        elif format_type == ExportFormat.RGB:
            return self._to_rgb_bytes()
        elif format_type == ExportFormat.RGB3PP:
            return self._to_rgb3pp_bytes()
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _to_mono_bytes(self) -> bytes:
        """Convert to monochrome format (1 bit per pixel)"""
        result = bytearray()
        for row in self.data:
            byte = 0
            bit_count = 0
            for pixel in row:
                byte |= (1 if pixel > 0 else 0) << bit_count
                bit_count += 1
                if bit_count == 8:
                    result.append(byte)
                    byte = 0
                    bit_count = 0
            # Handle remaining bits in the last byte
            if bit_count > 0:
                result.append(byte)
        return bytes(result)
    
    def _to_binary_bytes(self) -> bytes:
        """Convert to binary format (8 bits per pixel)"""
        result = bytearray()
        for row in self.data:
            for pixel in row:
                result.append(min(255, max(0, pixel)))
        return bytes(result)
    
    def _to_rgb_bytes(self) -> bytes:
        """Convert to RGB format (24 bits per pixel)"""
        result = bytearray()
        for row in self.data:
            for pixel in row:
                # Convert pixel value to RGB (assuming grayscale for now)
                r = g = b = min(255, max(0, pixel))
                result.extend([r, g, b])
        return bytes(result)
    
    def _to_rgb3pp_bytes(self) -> bytes:
        """Convert to RGB 3-bit per pixel format"""
        result = bytearray()
        for row in self.data:
            for pixel in row:
                # Convert to 3-bit RGB (0-7 range)
                value = min(7, max(0, pixel // 36))  # Scale 0-255 to 0-7
                result.append(value)
        return bytes(result)


class LEDMatrixParser:
    """Parser for LED Matrix Studio files"""
    
    def __init__(self):
        self.frames: List[MatrixFrame] = []
        self.matrix_width = 16
        self.matrix_height = 16
        self.matrix_mode = MatrixMode.MONO
    
    def parse_file(self, file_path: str) -> List[MatrixFrame]:
        """Parse a LED Matrix Studio file and return frames"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.leds':
            return self._parse_leds_file(file_path)
        elif file_ext == '.ledanim':
            return self._parse_ledanim_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _parse_leds_file(self, file_path: str) -> List[MatrixFrame]:
        """Parse .leds file (single frame)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the LEDS file format
            # This is a simplified parser - you may need to adjust based on actual format
            lines = content.strip().split('\n')
            
            # Extract matrix dimensions and data
            matrix_data = []
            for line in lines:
                if line.startswith('{') or line.startswith('}'):
                    continue
                if ':' in line:
                    key, value = line.split(':', 1)
                    if key.strip().lower() == 'width':
                        self.matrix_width = int(value.strip())
                    elif key.strip().lower() == 'height':
                        self.matrix_height = int(value.strip())
                    elif key.strip().lower() == 'mode':
                        mode_val = int(value.strip())
                        self.matrix_mode = MatrixMode(mode_val)
                else:
                    # Assume this is pixel data
                    row_data = []
                    for char in line.strip():
                        if char == '0':
                            row_data.append(0)
                        elif char == '1':
                            row_data.append(1)
                        else:
                            row_data.append(0)  # Default to off
                    
                    if row_data:
                        matrix_data.append(row_data)
            
            # Create frame
            if matrix_data:
                frame = MatrixFrame(
                    width=self.matrix_width,
                    height=self.matrix_height,
                    mode=self.matrix_mode,
                    data=matrix_data,
                    frame_number=0
                )
                self.frames = [frame]
                return self.frames
            
        except Exception as e:
            print(f"Error parsing LEDS file: {e}")
        
        # Return empty frame if parsing fails
        return self._create_empty_frame()
    
    def _parse_ledanim_file(self, file_path: str) -> List[MatrixFrame]:
        """Parse .LedAnim file (multiple frames)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the LedAnim file format
            # This is a simplified parser - you may need to adjust based on actual format
            lines = content.strip().split('\n')
            
            frames = []
            current_frame_data = []
            frame_number = 0
            
            for line in lines:
                if line.startswith('{Frame'):
                    # Start of new frame
                    if current_frame_data:
                        frame = self._create_frame_from_data(current_frame_data, frame_number)
                        frames.append(frame)
                        frame_number += 1
                        current_frame_data = []
                elif line.startswith('}'):
                    # End of frame
                    if current_frame_data:
                        frame = self._create_frame_from_data(current_frame_data, frame_number)
                        frames.append(frame)
                        frame_number += 1
                        current_frame_data = []
                else:
                    # Pixel data line
                    row_data = []
                    for char in line.strip():
                        if char == '0':
                            row_data.append(0)
                        elif char == '1':
                            row_data.append(1)
                        else:
                            row_data.append(0)  # Default to off
                    
                    if row_data:
                        current_frame_data.append(row_data)
            
            # Handle last frame
            if current_frame_data:
                frame = self._create_frame_from_data(current_frame_data, frame_number)
                frames.append(frame)
            
            self.frames = frames
            return frames
            
        except Exception as e:
            print(f"Error parsing LedAnim file: {e}")
        
        # Return empty frame if parsing fails
        return self._create_empty_frame()
    
    def _create_frame_from_data(self, matrix_data: List[List[int]], frame_number: int) -> MatrixFrame:
        """Create a MatrixFrame from parsed data"""
        return MatrixFrame(
            width=len(matrix_data[0]) if matrix_data else 16,
            height=len(matrix_data) if matrix_data else 16,
            mode=self.matrix_mode,
            data=matrix_data,
            frame_number=frame_number
        )
    
    def _create_empty_frame(self) -> List[MatrixFrame]:
        """Create an empty frame for fallback"""
        empty_data = [[0 for _ in range(self.matrix_width)] for _ in range(self.matrix_height)]
        frame = MatrixFrame(
            width=self.matrix_width,
            height=self.matrix_height,
            mode=self.matrix_mode,
            data=empty_data,
            frame_number=0
        )
        return [frame]
    
    def export_frames_for_esp01(self, format_type: ExportFormat, output_dir: str = None) -> List[str]:
        """Export frames in ESP01-compatible format"""
        if not self.frames:
            raise ValueError("No frames to export. Parse a file first.")
        
        output_files = []
        
        for i, frame in enumerate(self.frames):
            # Convert frame to bytes
            frame_bytes = frame.to_bytes(format_type)
            
            # Create output filename
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                filename = os.path.join(output_dir, f"frame_{i:03d}.bin")
            else:
                filename = f"frame_{i:03d}.bin"
            
            # Write frame data
            with open(filename, 'wb') as f:
                f.write(frame_bytes)
            
            output_files.append(filename)
        
        return output_files
    
    def get_frame_info(self) -> Dict[str, Any]:
        """Get information about the parsed frames"""
        if not self.frames:
            return {"error": "No frames parsed"}
        
        return {
            "total_frames": len(self.frames),
            "matrix_width": self.matrix_width,
            "matrix_height": self.matrix_height,
            "matrix_mode": self.matrix_mode.name,
            "frame_details": [
                {
                    "frame_number": frame.frame_number,
                    "width": frame.width,
                    "height": frame.height,
                    "data_size_bytes": len(frame.to_bytes(ExportFormat.BINARY))
                }
                for frame in self.frames
            ]
        }


def main():
    """Main function for testing"""
    parser = LEDMatrixParser()
    
    # Example usage
    print("LED Matrix Studio Parser for ESP01 Integration")
    print("=" * 50)
    
    # Test with a sample file if provided
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            frames = parser.parse_file(file_path)
            print(f"Successfully parsed {len(frames)} frames")
            
            # Show frame info
            info = parser.get_frame_info()
            print(json.dumps(info, indent=2))
            
            # Export frames for ESP01
            output_files = parser.export_frames_for_esp01(ExportFormat.BINARY, "esp01_frames")
            print(f"Exported {len(output_files)} frames to ESP01 format")
            
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python led_matrix_parser.py <file_path>")
        print("Supported formats: .leds, .LedAnim")


if __name__ == "__main__":
    main()
