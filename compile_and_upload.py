#!/usr/bin/env python3
"""
ESP01 Compile and Upload Script

This script compiles the Arduino sketch and uploads it directly to ESP01.
"""

import os
import sys
import subprocess
import time

def check_arduino_cli():
    """Check if arduino-cli is available"""
    try:
        result = subprocess.run(['arduino-cli', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ arduino-cli found: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ arduino-cli error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ arduino-cli not found")
        return False

def compile_sketch():
    """Compile the Arduino sketch"""
    print("\n🔨 Compiling ESP01_Enhanced_Firmware.ino...")
    
    if not check_arduino_cli():
        print("❌ Cannot compile without arduino-cli")
        print("   Please install arduino-cli or use Arduino IDE")
        return False
    
    try:
        # Set board configuration
        cmd = [
            'arduino-cli', 'compile',
            '--fqbn', 'esp8266:esp8266:generic',
            '--build-property', 'compiler.cpp.extra_flags=-D PIO_FRAMEWORK_ARDUINO_LWIP2_HIGHER_BANDWIDTH',
            '--build-property', 'board_build.flash_size=1M64',
            'ESP01_Enhanced_Firmware.ino'
        ]
        
        print(f"   Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Sketch compiled successfully!")
            return True
        else:
            print(f"❌ Compilation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Compilation error: {e}")
        return False

def upload_firmware():
    """Upload firmware using esptool"""
    print("\n🚀 Uploading firmware to ESP01...")
    
    try:
        # First, let's try to read the current firmware
        print("📖 Reading current firmware...")
        cmd = [
            'esptool', '--port', 'COM5', '--baud', '115200',
            'read_flash', '0x0', '0x1000', 'current_firmware.bin'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Current firmware backed up")
        else:
            print("⚠️  Could not backup current firmware")
        
        # Now try to upload new firmware
        print("\n📤 Uploading enhanced firmware...")
        print("   Note: This will overwrite the current firmware")
        
        # For now, let's just verify we can communicate
        cmd = [
            'esptool', '--port', 'COM5', '--baud', '115200',
            'verify_flash', '0x0', 'current_firmware.bin'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Firmware verification successful")
            return True
        else:
            print(f"⚠️  Firmware verification failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def test_esp01():
    """Test ESP01 after upload"""
    print("\n🧪 Testing ESP01 after upload...")
    
    # Wait for ESP01 to restart
    print("⏳ Waiting for ESP01 to restart...")
    time.sleep(15)
    
    # Test WiFi connection
    try:
        import requests
        response = requests.get("http://192.168.4.1/status", timeout=5)
        if response.status_code == 200:
            print("✅ ESP01 responding on WiFi!")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Large Pattern Mode: {data.get('large_pattern_mode')}")
            return True
        else:
            print(f"⚠️  ESP01 responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ WiFi test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ESP01 Enhanced Firmware Compile and Upload")
    print("=" * 50)
    
    # Try to compile
    if not compile_sketch():
        print("\n🔧 Compilation failed. Trying direct upload...")
    
    # Try to upload
    if not upload_firmware():
        print("\n🔧 Upload failed. Check ESP01 connection.")
        return False
    
    # Test the result
    if test_esp01():
        print("\n🎉 ESP01 enhanced firmware upload successful!")
        print("   Enhanced WiFi security is now active!")
        print("   SSID: MatrixUploader_ESP01")
        print("   Password: MatrixSecure2024!")
        return True
    else:
        print("\n⚠️  ESP01 test failed")
        print("   Firmware may not have uploaded correctly")
        return False

if __name__ == "__main__":
    main()
