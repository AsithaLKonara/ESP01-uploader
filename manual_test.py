#!/usr/bin/env python3
"""
Manual ESP01 Test Script

Run this to test your ESP01 enhanced firmware manually.
"""

import requests
import time

def test_esp01():
    """Test ESP01 enhanced firmware"""
    print("🧪 Testing ESP01 Enhanced Firmware")
    print("=" * 40)
    
    # Test 1: Basic connection
    print("\n1️⃣ Testing basic connection...")
    try:
        response = requests.get("http://192.168.4.1/status", timeout=5)
        if response.status_code == 200:
            print("✅ ESP01 responding!")
            data = response.json()
            print(f"   Uptime: {data.get('uptime')} ms")
            print(f"   Free Heap: {data.get('free_heap')} bytes")
            print(f"   Playing: {data.get('playing')}")
        else:
            print(f"❌ ESP01 responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Test 2: Web interface
    print("\n2️⃣ Testing web interface...")
    try:
        response = requests.get("http://192.168.4.1/", timeout=5)
        if response.status_code == 200:
            print("✅ Web interface accessible!")
            if "ESP Matrix Uploader" in response.text:
                print("   ✅ Correct title found")
            if "upload_token_2025" in response.text:
                print("   ✅ Upload token visible")
        else:
            print(f"❌ Web interface failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web interface test failed: {e}")
        return False
    
    # Test 3: WiFi credentials
    print("\n3️⃣ Testing WiFi credentials...")
    try:
        response = requests.get("http://192.168.4.1/", timeout=5)
        if response.status_code == 200:
            if "MatrixUploader_ESP01" in response.text:
                print("✅ WiFi SSID visible: MatrixUploader_ESP01")
            else:
                print("❌ WiFi SSID not found")
            
            if "MatrixSecure2024!" in response.text:
                print("✅ WiFi password visible: MatrixSecure2024!")
            else:
                print("❌ WiFi password not found")
        else:
            print(f"❌ Could not access web interface: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ WiFi credentials test failed: {e}")
        return False
    
    # Test 4: Upload endpoints
    print("\n4️⃣ Testing upload endpoints...")
    try:
        # Test upload endpoint
        response = requests.get("http://192.168.4.1/upload?token=upload_token_2025", timeout=5)
        if response.status_code == 405:  # Method not allowed for GET
            print("✅ Upload endpoint accessible (GET not allowed as expected)")
        else:
            print(f"⚠️  Upload endpoint: HTTP {response.status_code}")
        
        # Test chunked upload endpoint
        response = requests.get("http://192.168.4.1/upload-chunked?token=upload_token_2025", timeout=5)
        if response.status_code == 405:  # Method not allowed for GET
            print("✅ Chunked upload endpoint accessible (GET not allowed as expected)")
        else:
            print(f"⚠️  Chunked upload endpoint: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Upload endpoints test failed: {e}")
        return False
    
    # Test 5: Playback endpoints
    print("\n5️⃣ Testing playback endpoints...")
    try:
        # Test play endpoint
        response = requests.get("http://192.168.4.1/play", timeout=5)
        if response.status_code == 400:  # Missing file parameter
            print("✅ Play endpoint accessible (file parameter required)")
        else:
            print(f"⚠️  Play endpoint: HTTP {response.status_code}")
        
        # Test stop endpoint
        response = requests.get("http://192.168.4.1/stop", timeout=5)
        if response.status_code == 200:
            print("✅ Stop endpoint accessible")
        else:
            print(f"⚠️  Stop endpoint: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Playback endpoints test failed: {e}")
        return False
    
    print("\n🎉 All tests completed!")
    print("Your ESP01 enhanced firmware is working!")
    return True

if __name__ == "__main__":
    test_esp01()
