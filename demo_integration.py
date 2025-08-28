#!/usr/bin/env python3
"""
Demo Integration Script for LED Matrix Studio + ESP01

This script demonstrates how to integrate the LED Matrix Studio parser
with your existing ESP01 uploader system.
"""

import os
import sys
import json
import time
from integrate_with_ledmatrixstudio import process_led_matrix_file


def demo_basic_integration():
    """Demonstrate basic integration"""
    print("🎯 LED Matrix Studio + ESP01 Integration Demo")
    print("=" * 50)
    
    # Test file
    test_file = "heart_pattern.leds"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"📁 Processing file: {test_file}")
    
    # Process the LED Matrix Studio file
    result = process_led_matrix_file(test_file, "binary", "demo_output")
    
    if result["success"]:
        print("✅ File processed successfully!")
        print(f"   - Total frames: {result['total_frames']}")
        print(f"   - Matrix size: {result['matrix_width']}x{result['matrix_height']}")
        print(f"   - Matrix mode: {result['matrix_mode']}")
        print(f"   - Output format: {result['output_format']}")
        print(f"   - Output files: {len(result['output_files'])}")
        
        # Show frame details
        for frame in result["frame_details"]:
            print(f"   - Frame {frame['frame_number']}: {frame['width']}x{frame['height']} ({frame['data_size_bytes']} bytes)")
        
        return True
    else:
        print(f"❌ Processing failed: {result['error']}")
        return False


def demo_frame_upload_simulation():
    """Simulate frame-by-frame upload to ESP01"""
    print("\n🚀 Simulating Frame Upload to ESP01")
    print("=" * 40)
    
    # Process file
    result = process_led_matrix_file("heart_pattern.leds", "binary", "upload_demo")
    
    if not result["success"]:
        print("❌ Cannot simulate upload - file processing failed")
        return False
    
    print(f"📤 Simulating upload of {result['total_frames']} frames...")
    
    # Simulate uploading each frame
    for i, frame_info in enumerate(result["frame_details"]):
        print(f"   📡 Uploading frame {i+1}/{result['total_frames']}...")
        print(f"      Size: {frame_info['data_size_bytes']} bytes")
        print(f"      Dimensions: {frame_info['width']}x{frame_info['height']}")
        
        # Simulate upload delay
        time.sleep(0.5)
        
        print(f"      ✅ Frame {i+1} uploaded successfully")
    
    print(f"\n🎉 All {result['total_frames']} frames uploaded successfully!")
    return True


def demo_multiple_formats():
    """Demonstrate different export formats"""
    print("\n🎨 Testing Different Export Formats")
    print("=" * 35)
    
    formats = ["mono", "binary", "rgb", "rgb3pp"]
    test_file = "heart_pattern.leds"
    
    for format_type in formats:
        print(f"\n🔄 Testing {format_type.upper()} format...")
        
        try:
            result = process_led_matrix_file(test_file, format_type, f"format_test_{format_type}")
            
            if result["success"]:
                print(f"   ✅ {format_type.upper()} format successful")
                print(f"   📊 Frame size: {result['frame_details'][0]['data_size_bytes']} bytes")
            else:
                print(f"   ❌ {format_type.upper()} format failed: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ {format_type.upper()} format error: {e}")


def demo_integration_with_existing_uploader():
    """Show how to integrate with existing ESP01 uploader"""
    print("\n🔌 Integration with Existing ESP01 Uploader")
    print("=" * 50)
    
    print("""
Here's how to integrate this parser with your existing ESP01 uploader:

1. **Import the parser:**
   ```python
   from integrate_with_ledmatrixstudio import process_led_matrix_file
   ```

2. **Process LED Matrix Studio files:**
   ```python
   result = process_led_matrix_file('animation.LedAnim', 'binary', 'frames')
   if result['success']:
       print(f"Processed {result['total_frames']} frames")
   ```

3. **Upload frames to ESP01:**
   ```python
   for frame_file in result['output_files']:
       # Your existing ESP01 upload logic here
       upload_to_esp01(frame_file)
   ```

4. **Stream frames for smooth display:**
   ```python
   # Use the enhanced uploader for streaming
   from esp01_led_uploader import ESP01LEDUploader
   
   uploader = ESP01LEDUploader()
   uploader.load_led_matrix_file('animation.LedAnim')
   uploader.start_streaming(loop=True)
   ```
    """)


def main():
    """Main demo function"""
    print("🎯 LED Matrix Studio + ESP01 Integration Demo")
    print("=" * 60)
    
    # Run demos
    if demo_basic_integration():
        demo_frame_upload_simulation()
        demo_multiple_formats()
        demo_integration_with_existing_uploader()
        
        print("\n🎉 Demo completed successfully!")
        print("\n📁 Generated files:")
        
        # List generated directories
        for item in os.listdir("."):
            if item.startswith(("demo_", "format_test_", "upload_")):
                if os.path.isdir(item):
                    print(f"   📂 {item}/")
                    try:
                        files = os.listdir(item)
                        for file in files:
                            print(f"      📄 {file}")
                    except:
                        pass
    else:
        print("❌ Demo failed - check the errors above")


if __name__ == "__main__":
    main()
