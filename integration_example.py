#!/usr/bin/env python3
"""
Practical Integration Example for LED Matrix Studio + ESP01

This example shows exactly how to integrate the LED Matrix Studio parser
with your existing ESP01 uploader system.
"""

import os
import sys
import time
from integrate_with_ledmatrixstudio import process_led_matrix_file


class ESP01Uploader:
    """Example ESP01 uploader class - replace with your actual uploader"""
    
    def __init__(self, ip_address="192.168.4.1", port=80):
        self.ip_address = ip_address
        self.port = port
        self.is_connected = False
    
    def connect(self):
        """Connect to ESP01"""
        print(f"🔌 Connecting to ESP01 at {self.ip_address}:{self.port}...")
        # Your actual connection logic here
        self.is_connected = True
        print("✅ Connected to ESP01")
        return True
    
    def upload_frame(self, frame_file_path):
        """Upload a single frame to ESP01"""
        if not self.is_connected:
            print("❌ Not connected to ESP01")
            return False
        
        print(f"📤 Uploading frame: {os.path.basename(frame_file_path)}")
        
        # Read frame data
        try:
            with open(frame_file_path, 'rb') as f:
                frame_data = f.read()
            
            print(f"   📊 Frame size: {len(frame_data)} bytes")
            
            # Your actual ESP01 upload logic here
            # For example:
            # success = self._send_to_esp01(frame_data)
            
            # Simulate upload
            time.sleep(0.1)  # Simulate upload time
            success = True
            
            if success:
                print("   ✅ Frame uploaded successfully")
                return True
            else:
                print("   ❌ Frame upload failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Error reading frame: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from ESP01"""
        if self.is_connected:
            print("🔌 Disconnecting from ESP01...")
            self.is_connected = False
            print("✅ Disconnected from ESP01")


def integrate_led_matrix_studio_with_esp01():
    """Main integration function"""
    print("🎯 LED Matrix Studio + ESP01 Integration Example")
    print("=" * 55)
    
    # 1. Initialize ESP01 uploader
    print("\n1️⃣ Initializing ESP01 uploader...")
    uploader = ESP01Uploader(ip_address="192.168.4.1", port=80)
    
    # 2. Connect to ESP01
    print("\n2️⃣ Connecting to ESP01...")
    if not uploader.connect():
        print("❌ Failed to connect to ESP01")
        return False
    
    # 3. Process LED Matrix Studio file
    print("\n3️⃣ Processing LED Matrix Studio file...")
    led_file = "heart_pattern.leds"
    
    if not os.path.exists(led_file):
        print(f"❌ LED Matrix Studio file not found: {led_file}")
        uploader.disconnect()
        return False
    
    # Process the file and extract frames
    result = process_led_matrix_file(led_file, "binary", "integration_frames")
    
    if not result["success"]:
        print(f"❌ Failed to process file: {result['error']}")
        uploader.disconnect()
        return False
    
    print(f"✅ File processed successfully!")
    print(f"   📊 Total frames: {result['total_frames']}")
    print(f"   📐 Matrix size: {result['matrix_width']}x{result['matrix_height']}")
    print(f"   🎨 Matrix mode: {result['matrix_mode']}")
    
    # 4. Upload frames to ESP01
    print(f"\n4️⃣ Uploading {result['total_frames']} frames to ESP01...")
    
    successful_uploads = 0
    for i, frame_file in enumerate(result['output_files']):
        print(f"\n   📡 Frame {i+1}/{result['total_frames']}:")
        
        if uploader.upload_frame(frame_file):
            successful_uploads += 1
        else:
            print(f"   ⚠️  Frame {i+1} upload failed, continuing...")
        
        # Add delay between frames for smooth display
        if i < result['total_frames'] - 1:
            time.sleep(0.2)  # 200ms delay between frames
    
    # 5. Summary
    print(f"\n5️⃣ Upload Summary:")
    print(f"   📤 Total frames: {result['total_frames']}")
    print(f"   ✅ Successful uploads: {successful_uploads}")
    print(f"   ❌ Failed uploads: {result['total_frames'] - successful_uploads}")
    
    if successful_uploads == result['total_frames']:
        print("   🎉 All frames uploaded successfully!")
    else:
        print("   ⚠️  Some frames failed to upload")
    
    # 6. Cleanup
    print("\n6️⃣ Cleaning up...")
    uploader.disconnect()
    
    return successful_uploads == result['total_frames']


def show_usage_examples():
    """Show various usage examples"""
    print("\n📖 Usage Examples")
    print("=" * 20)
    
    print("""
🔧 **Basic Integration:**
```python
from integrate_with_ledmatrixstudio import process_led_matrix_file

# Process a single frame file
result = process_led_matrix_file('pattern.leds', 'binary', 'frames')
if result['success']:
    print(f"Processed {result['total_frames']} frames")
```

🚀 **Streaming Integration:**
```python
from esp01_led_uploader import ESP01LEDUploader

uploader = ESP01LEDUploader()
uploader.load_led_matrix_file('animation.LedAnim')
uploader.start_streaming(loop=True)  # Loop animation
```

📊 **Multiple Formats:**
```python
formats = ['mono', 'binary', 'rgb', 'rgb3pp']
for format_type in formats:
    result = process_led_matrix_file('pattern.leds', format_type, f'frames_{format_type}')
    print(f"{format_type}: {result['frame_details'][0]['data_size_bytes']} bytes")
```

🔄 **Batch Processing:**
```python
import os
for file in os.listdir('.'):
    if file.endswith(('.leds', '.LedAnim')):
        result = process_led_matrix_file(file, 'binary', f'frames_{file}')
        print(f"{file}: {result['total_frames']} frames")
```
    """)


def main():
    """Main function"""
    print("🎯 LED Matrix Studio + ESP01 Integration Example")
    print("=" * 60)
    
    # Run the integration example
    success = integrate_led_matrix_studio_with_esp01()
    
    if success:
        print("\n🎉 Integration completed successfully!")
        print("✅ You can now use this system with your ESP01!")
    else:
        print("\n❌ Integration failed - check the errors above")
    
    # Show usage examples
    show_usage_examples()
    
    print("\n📁 Generated files:")
    if os.path.exists("integration_frames"):
        files = os.listdir("integration_frames")
        for file in files:
            print(f"   📄 integration_frames/{file}")


if __name__ == "__main__":
    main()
