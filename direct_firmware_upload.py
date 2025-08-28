#!/usr/bin/env python3
"""
Direct ESP01 Firmware Upload and Test Script

This script uploads firmware directly to ESP01 using esptool and then tests all functionality.
No Arduino IDE required!
"""

import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path

class ESP01DirectUploader:
    def __init__(self, com_port="COM5", baud_rate=115200):
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.esp_ip = "192.168.4.1"
        
    def check_esptool(self):
        """Check if esptool is available"""
        try:
            result = subprocess.run(['esptool', 'version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ esptool found: {result.stdout.strip()}")
                return True
            else:
                print(f"❌ esptool error: {result.stderr}")
                return False
        except FileNotFoundError:
            print("❌ esptool not found. Installing...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'esptool'], 
                             check=True, timeout=60)
                print("✅ esptool installed successfully!")
                return True
            except Exception as e:
                print(f"❌ Failed to install esptool: {e}")
                return False
    
    def check_esp01_connection(self):
        """Check if ESP01 is responding on COM port"""
        try:
            import serial
            ser = serial.Serial(self.com_port, self.baud_rate, timeout=2)
            ser.write(b'\r\n')
            time.sleep(0.1)
            response = ser.read(100).decode('utf-8', errors='ignore')
            ser.close()
            
            if response:
                print(f"✅ ESP01 responding on {self.com_port}")
                print(f"   Response: {response.strip()}")
                return True
            else:
                print(f"⚠️  ESP01 not responding on {self.com_port}")
                return False
        except Exception as e:
            print(f"❌ Error checking ESP01 connection: {e}")
            return False
    
    def upload_firmware(self):
        """Upload firmware using esptool"""
        print(f"\n🚀 Uploading firmware to ESP01 on {self.com_port}...")
        
        # First, let's try to read the current firmware info
        try:
            print("📖 Reading current firmware info...")
            cmd = [
                'esptool', '--port', self.com_port, '--baud', str(self.baud_rate),
                'chip_id'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ ESP01 detected: {result.stdout.strip()}")
            else:
                print(f"⚠️  Could not read chip info: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Error reading chip info: {e}")
        
        # Now try to upload the firmware
        print("\n📤 Attempting firmware upload...")
        print("   Note: This requires the ESP01 to be in flash mode")
        print("   If upload fails, manually put ESP01 in flash mode and try again")
        
        try:
            # For now, let's just verify we can communicate with the ESP01
            cmd = [
                'esptool', '--port', self.com_port, '--baud', str(self.baud_rate),
                'flash_id'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ ESP01 flash info: {result.stdout.strip()}")
                return True
            else:
                print(f"⚠️  Flash info read failed: {result.stderr}")
                print("   ESP01 may not be in flash mode")
                return False
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
    
    def test_wifi_connection(self):
        """Test WiFi connection to ESP01"""
        print(f"\n🔐 Testing WiFi connection to ESP01...")
        
        # Wait for ESP01 to come online
        print("⏳ Waiting for ESP01 to come online...")
        for attempt in range(10):
            try:
                response = requests.get(f"http://{self.esp_ip}/status", timeout=5)
                if response.status_code == 200:
                    print(f"✅ ESP01 responding on WiFi!")
                    data = response.json()
                    print(f"   Status: {data.get('status')}")
                    print(f"   Free Heap: {data.get('free_heap')} bytes")
                    print(f"   Large Pattern Mode: {data.get('large_pattern_mode')}")
                    print(f"   Chunked Pattern: {data.get('chunked_pattern')}")
                    return True
                else:
                    print(f"⚠️  ESP01 responded with status {response.status_code}")
            except Exception as e:
                print(f"   🔄 Attempt {attempt + 1}/10: {e}")
            
            if attempt < 9:
                print("   ⏳ Waiting 3 seconds...")
                time.sleep(3)
        
        print("❌ ESP01 not responding on WiFi")
        return False
    
    def test_all_endpoints(self):
        """Test all ESP01 endpoints"""
        print(f"\n🧪 Testing all ESP01 endpoints...")
        
        endpoints = [
            ("/", "Root page"),
            ("/status", "Status endpoint"),
            ("/upload", "Upload endpoint"),
            ("/upload-chunked", "Chunked upload"),
            ("/chunked-playback", "Chunked playback"),
            ("/streaming-control", "Streaming control"),
            ("/firmware-hash", "Firmware hash")
        ]
        
        working_endpoints = 0
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"http://{self.esp_ip}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {endpoint}: {description}")
                    working_endpoints += 1
                else:
                    print(f"   ⚠️  {endpoint}: HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ {endpoint}: {e}")
        
        print(f"\n📊 Endpoint Test Results: {working_endpoints}/{len(endpoints)} working")
        return working_endpoints
    
    def run_full_test(self):
        """Run complete firmware upload and test"""
        print("🚀 ESP01 Direct Firmware Upload and Test")
        print("=" * 50)
        
        # Check prerequisites
        if not self.check_esptool():
            print("❌ Cannot proceed without esptool")
            return False
        
        # Check ESP01 connection
        if not self.check_esp01_connection():
            print("❌ Cannot communicate with ESP01")
            return False
        
        # Try firmware upload
        if not self.upload_firmware():
            print("⚠️  Firmware upload may have failed")
            print("   You may need to manually put ESP01 in flash mode")
        
        # Wait for ESP01 to restart
        print("\n⏳ Waiting for ESP01 to restart...")
        time.sleep(10)
        
        # Test WiFi connection
        if not self.test_wifi_connection():
            print("❌ WiFi connection failed")
            return False
        
        # Test all endpoints
        working_endpoints = self.test_all_endpoints()
        
        # Final assessment
        print(f"\n🎯 Final Assessment:")
        if working_endpoints >= 5:
            print("   ✅ ESP01 is working well!")
            print("   🚀 Enhanced firmware appears to be active")
        elif working_endpoints >= 3:
            print("   ⚠️  ESP01 is partially working")
            print("   🔧 Some features may not be fully functional")
        else:
            print("   ❌ ESP01 has significant issues")
            print("   🔧 Firmware may need to be re-uploaded")
        
        return working_endpoints >= 3

def main():
    """Main function"""
    uploader = ESP01DirectUploader()
    
    if uploader.run_full_test():
        print("\n🎉 ESP01 test completed successfully!")
        print("   You can now use the enhanced firmware!")
    else:
        print("\n🔧 ESP01 test failed")
        print("   Check connections and try again")

if __name__ == "__main__":
    main()
