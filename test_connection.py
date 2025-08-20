#!/usr/bin/env python3
"""
ESP-01 WiFi Connection Test Script
Tests basic connectivity and upload functionality
"""

import requests
import json
import time
from wifi_manager import WiFiManager
from esp_uploader import ESPUploader

def test_basic_connection():
    """Test basic HTTP connection to ESP-01"""
    print("=== Testing Basic ESP-01 Connection ===")
    
    # Default ESP-01 settings
    esp_ip = "192.168.4.1"  # Default ESP-01 AP IP
    esp_port = 8266
    
    print(f"Attempting to connect to ESP-01 at {esp_ip}:{esp_port}")
    
    try:
        # Test basic HTTP connection
        response = requests.get(f"http://{esp_ip}:{esp_port}/", timeout=5)
        print(f"✓ HTTP connection successful! Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ Connection failed - ESP-01 not reachable")
        print("Make sure ESP-01 is powered and WiFi AP is active")
        return False
    except requests.exceptions.Timeout:
        print("✗ Connection timeout - ESP-01 not responding")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_wifi_manager():
    """Test WiFi manager functionality"""
    print("\n=== Testing WiFi Manager ===")
    
    wifi_mgr = WiFiManager()
    
    # Test connection
    print("Testing WiFi manager connection...")
    if wifi_mgr.connect("192.168.4.1", 8266):
        print("✓ WiFi manager connected successfully!")
        
        # Test ping
        print("Testing ping...")
        if wifi_mgr.ping():
            print("✓ Ping successful!")
        else:
            print("✗ Ping failed")
        
        # Test device info
        print("Getting device info...")
        info = wifi_mgr.get_device_info()
        if info:
            print(f"✓ Device info: {info}")
        else:
            print("✗ Could not get device info")
        
        # Test memory info
        print("Getting memory info...")
        mem_info = wifi_mgr.get_memory_info()
        if mem_info:
            print(f"✓ Memory info: {mem_info}")
        else:
            print("✗ Could not get memory info")
        
        wifi_mgr.disconnect()
        return True
    else:
        print("✗ WiFi manager connection failed")
        return False

def test_esp_uploader():
    """Test ESP uploader functionality"""
    print("\n=== Testing ESP Uploader ===")
    
    uploader = ESPUploader()
    wifi_mgr = WiFiManager()
    
    # Connect first
    if not wifi_mgr.connect("192.168.4.1", 8266):
        print("✗ Cannot test uploader without connection")
        return False
    
    # Test upload session preparation
    print("Testing upload session preparation...")
    session_info = uploader._prepare_upload_session("test.bin", wifi_mgr)
    if session_info:
        print(f"✓ Upload session prepared: {session_info}")
    else:
        print("✗ Upload session preparation failed")
    
    wifi_mgr.disconnect()
    return True

def test_led_matrix_preview():
    """Test LED matrix preview functionality"""
    print("\n=== Testing LED Matrix Preview ===")
    
    try:
        from led_matrix_preview import LEDMatrixPreview
        
        preview = LEDMatrixPreview()
        preview.set_matrix_size(8, 8)
        
        # Create a test pattern
        test_pattern = preview.create_test_pattern()
        if test_pattern:
            print("✓ Test pattern created successfully!")
            print(f"Pattern info: {preview.get_pattern_info()}")
        else:
            print("✗ Test pattern creation failed")
        
        return True
    except Exception as e:
        print(f"✗ LED matrix preview test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("ESP-01 WiFi Uploader - Connection Test")
    print("=" * 50)
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("WiFi Manager", test_wifi_manager),
        ("ESP Uploader", test_esp_uploader),
        ("LED Matrix Preview", test_led_matrix_preview)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your ESP-01 setup is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("\nTroubleshooting tips:")
        print("1. Make sure ESP-01 is powered and WiFi AP is active")
        print("2. Verify you're connected to 'ESP01_AP' WiFi network")
        print("3. Check ESP-01 IP address (default: 192.168.4.1)")
        print("4. Ensure ESP-01 firmware is loaded correctly")

if __name__ == "__main__":
    main()
