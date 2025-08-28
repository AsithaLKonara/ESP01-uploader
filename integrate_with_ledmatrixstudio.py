#!/usr/bin/env python3
"""
Simple Integration Script for LED Matrix Studio + ESP01

This script provides a simple interface that can be called from your existing
ESP01 uploader to handle LED Matrix Studio files.
"""

import os
import sys
import json
from led_matrix_parser import LEDMatrixParser, ExportFormat


def process_led_matrix_file(file_path: str, output_format: str = "binary", output_dir: str = None):
    """
    Process a LED Matrix Studio file and prepare it for ESP01 upload
    
    Args:
        file_path: Path to .leds or .LedAnim file
        output_format: Output format (mono, binary, rgb, rgb3pp)
        output_dir: Output directory for frame files
    
    Returns:
        dict: Processing results and file information
    """
    try:
        # Create parser
        parser = LEDMatrixParser()
        
        # Parse file
        frames = parser.parse_file(file_path)
        
        if not frames:
            return {
                "success": False,
                "error": "No frames found in file"
            }
        
        # Determine output format
        format_map = {
            "mono": ExportFormat.MONO,
            "binary": ExportFormat.BINARY,
            "rgb": ExportFormat.RGB,
            "rgb3pp": ExportFormat.RGB3PP
        }
        
        export_format = format_map.get(output_format.lower(), ExportFormat.BINARY)
        
        # Export frames
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        output_files = parser.export_frames_for_esp01(export_format, output_dir)
        
        # Get frame information
        frame_info = parser.get_frame_info()
        
        # Prepare result
        result = {
            "success": True,
            "file_path": file_path,
            "total_frames": len(frames),
            "matrix_width": frame_info["matrix_width"],
            "matrix_height": frame_info["matrix_height"],
            "matrix_mode": frame_info["matrix_mode"],
            "output_format": output_format,
            "output_files": output_files,
            "frame_details": frame_info["frame_details"]
        }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Command-line interface"""
    if len(sys.argv) < 2:
        print("Usage: python integrate_with_ledmatrixstudio.py <file_path> [format] [output_dir]")
        print("\nFormats: mono, binary, rgb, rgb3pp")
        print("Example: python integrate_with_ledmatrixstudio.py animation.LedAnim binary esp01_frames")
        return
    
    file_path = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "binary"
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Process file
    result = process_led_matrix_file(file_path, output_format, output_dir)
    
    # Output result as JSON (for easy parsing by other tools)
    print(json.dumps(result, indent=2))
    
    if result["success"]:
        print(f"\n✅ Successfully processed {result['total_frames']} frames")
        print(f"📁 Output files: {len(result['output_files'])}")
        if output_dir:
            print(f"📂 Output directory: {output_dir}")
    else:
        print(f"\n❌ Processing failed: {result['error']}")


if __name__ == "__main__":
    main()
