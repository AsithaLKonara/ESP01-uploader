#!/usr/bin/env python3
"""
Test script for WS2812_Uploader ESP-01 connection
Tests the correct WiFi network: WS2812_Uploader (no password)
"""

import requests
import time
import subprocess
import sys

def check_wifi_connection():
    """Check if connected to WS2812_Uploader network"""
    print("🔍 Checking WiFi connection...")
    
    try:
        # Check network interfaces (Windows)
        result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                              capture_output=True, text=True, timeout=10)
        
        if 'WS2812_Uploader' in result.stdout:
            print("✅ Connected to WS2812_Uploader network")
            return True
        else:
            print("❌ Not connected to WS2812_Uploader network")
            print("   Please connect to 'WS2812_Uploader' WiFi (no password)")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not check WiFi: {e}")
        return False

def test_esp01_connection():
    """Test ESP-01 connection at 192.168.4.1"""
    print("\n🌐 Testing ESP-01 connection...")
    
    # Test ping endpoint first
    try:
        print("   Testing /ping endpoint...")
        response = requests.get('http://192.168.4.1/ping', timeout=5)
        if response.status_code == 200 and response.text == 'pong':
            print("   ✅ /ping endpoint working")
        else:
            print(f"   ⚠️  /ping returned: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ /ping failed: {e}")
    
    # Test main page
    try:
        print("   Testing main page...")
        response = requests.get('http://192.168.4.1/', timeout=10)
        if response.status_code == 200:
            print("   ✅ Main page loaded successfully")
            if 'WS2812 LED Strip Uploader' in response.text:
                print("   ✅ Correct firmware detected")
            else:
                print("   ⚠️  Unexpected content on main page")
        else:
            print(f"   ❌ Main page failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Main page failed: {e}")
    
    # Test status endpoint
    try:
        print("   Testing /status endpoint...")
        response = requests.get('http://192.168.4.1/status', timeout=5)
        if response.status_code == 200:
            print("   ✅ /status endpoint working")
            print(f"   📊 Response: {response.text[:100]}...")
        else:
            print(f"   ❌ /status failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ /status failed: {e}")

def main():
    print("🎨 WS2812 ESP-01 Connection Test")
    print("=" * 40)
    
    # Check WiFi connection
    if not check_wifi_connection():
        print("\n📋 To connect to ESP-01:")
        print("1. Look for 'WS2812_Uploader' WiFi network")
        print("2. Connect to it (no password required)")
        print("3. Wait for connection to establish")
        print("4. Run this test again")
        return
    
    # Test ESP-01 connection
    test_esp01_connection()
    
    print("\n🎯 Next steps:")
    print("1. If all tests pass, you can use the main uploader")
    print("2. If tests fail, check ESP-01 power and firmware")
    print("3. Try uploading the firmware again if needed")

if __name__ == "__main__":
    main()
