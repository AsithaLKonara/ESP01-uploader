#!/usr/bin/env python3
"""
ESP-01 Status Test Script
Tests if the new firmware is working properly with enhanced error reporting
"""

import requests
import time
import sys
import json

def test_esp01_status(host="192.168.4.1"):
    """Test ESP-01 status and endpoints with enhanced error reporting"""
    
    print(f"🔍 Testing ESP-01 at {host}")
    print("=" * 50)
    
    test_results = {}
    
    # Test 1: Basic connectivity
    print("\n📡 Test 1: Basic Connectivity")
    try:
        response = requests.get(f"http://{host}/", timeout=5)
        if response.status_code == 200:
            if "Enhanced LED Matrix Uploader" in response.text:
                print("✅ Enhanced firmware detected!")
                print("✅ Web interface working")
                test_results['basic_connectivity'] = {'status': 'success', 'firmware': 'enhanced'}
            else:
                print("⚠️  Web interface working but firmware may be old")
                print("   This could explain why uploads are failing!")
                test_results['basic_connectivity'] = {'status': 'warning', 'firmware': 'old'}
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   This indicates a server-side issue")
            test_results['basic_connectivity'] = {'status': 'error', 'code': response.status_code}
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Error Type: {type(e).__name__}")
        if "ConnectTimeout" in str(e):
            print("   💡 SOLUTION: Check if ESP-01 is powered on and WiFi is working")
        elif "ConnectionError" in str(e):
            print("   💡 SOLUTION: Make sure you're connected to 'MatrixUploader' WiFi")
        test_results['basic_connectivity'] = {'status': 'error', 'error': str(e), 'type': type(e).__name__}
        return False
    
    # Test 2: Ping endpoint
    print("\n🏓 Test 2: Ping Endpoint")
    try:
        response = requests.get(f"http://{host}/ping", timeout=5)
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Ping successful")
                print(f"   Status: {data.get('status', 'N/A')}")
                print(f"   Free Heap: {data.get('free_heap', 'N/A')} bytes")
                print(f"   Uptime: {data.get('uptime', 'N/A')} seconds")
                test_results['ping'] = {'status': 'success', 'data': data}
            except json.JSONDecodeError:
                print(f"⚠️  Ping responded but not valid JSON")
                print(f"   Response: {response.text[:100]}...")
                test_results['ping'] = {'status': 'warning', 'response': response.text}
        else:
            print(f"❌ Ping failed: {response.status_code}")
            if response.status_code == 404:
                print("   💡 ISSUE: /ping endpoint not found - old firmware detected")
                print("   💡 SOLUTION: Upload enhanced firmware")
            test_results['ping'] = {'status': 'error', 'code': response.status_code}
    except Exception as e:
        print(f"❌ Ping error: {e}")
        test_results['ping'] = {'status': 'error', 'error': str(e)}
    
    # Test 3: Health endpoint
    print("\n💚 Test 3: Health Endpoint")
    try:
        response = requests.get(f"http://{host}/health", timeout=5)
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Health check successful")
                print(f"   Status: {data.get('status', 'N/A')}")
                print(f"   Free Heap: {data.get('free_heap', 'N/A')} bytes")
                print(f"   FS Free: {data.get('fs_free', 'N/A')} bytes")
                test_results['health'] = {'status': 'success', 'data': data}
            except json.JSONDecodeError:
                print(f"⚠️  Health responded but not valid JSON")
                print(f"   Response: {response.text[:100]}...")
                test_results['health'] = {'status': 'warning', 'response': response.text}
        else:
            print(f"❌ Health check failed: {response.status_code}")
            if response.status_code == 404:
                print("   💡 ISSUE: /health endpoint not found - old firmware detected")
                print("   💡 SOLUTION: Upload enhanced firmware")
            test_results['health'] = {'status': 'error', 'code': response.status_code}
    except Exception as e:
        print(f"❌ Health check error: {e}")
        test_results['health'] = {'status': 'error', 'error': str(e)}
    
    # Test 4: LED Control endpoint
    print("\n🎮 Test 4: LED Control Endpoint")
    try:
        response = requests.get(f"http://{host}/led-control?action=status", timeout=5)
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ LED control working")
                print(f"   Playing: {data.get('playing', 'N/A')}")
                print(f"   Current Frame: {data.get('current_frame', 'N/A')}")
                print(f"   Frame Delay: {data.get('frame_delay_ms', 'N/A')} ms")
                test_results['led_control'] = {'status': 'success', 'data': data}
            except json.JSONDecodeError:
                print(f"⚠️  LED control responded but not valid JSON")
                print(f"   Response: {response.text[:100]}...")
                test_results['led_control'] = {'status': 'warning', 'response': response.text}
        else:
            print(f"❌ LED control failed: {response.status_code}")
            if response.status_code == 404:
                print("   💡 ISSUE: /led-control endpoint not found - old firmware detected")
                print("   💡 SOLUTION: Upload enhanced firmware")
            test_results['led_control'] = {'status': 'error', 'code': response.status_code}
    except Exception as e:
        print(f"❌ LED control error: {e}")
        test_results['led_control'] = {'status': 'error', 'error': str(e)}
    
    # Test 5: System Info endpoint
    print("\n📊 Test 5: System Info Endpoint")
    try:
        response = requests.get(f"http://{host}/system-info", timeout=5)
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ System info working")
                print(f"   Status: {data.get('status', 'N/A')}")
                print(f"   Free Heap: {data.get('free_heap', 'N/A')} bytes")
                print(f"   Flash Size: {data.get('flash_size', 'N/A')} bytes")
                test_results['system_info'] = {'status': 'success', 'data': data}
            except json.JSONDecodeError:
                print(f"⚠️  System info responded but not valid JSON")
                print(f"   Response: {response.text[:100]}...")
                test_results['system_info'] = {'status': 'warning', 'response': response.text}
        else:
            print(f"❌ System info failed: {response.status_code}")
            if response.status_code == 404:
                print("   💡 ISSUE: /system-info endpoint not found - old firmware detected")
                print("   💡 SOLUTION: Upload enhanced firmware")
            test_results['system_info'] = {'status': 'error', 'code': response.status_code}
    except Exception as e:
        print(f"❌ System info error: {e}")
        test_results['system_info'] = {'status': 'error', 'error': str(e)}
    
    # Test 6: Upload endpoint (critical for your issue)
    print("\n📤 Test 6: Upload Endpoint (CRITICAL)")
    try:
        response = requests.get(f"http://{host}/upload", timeout=5)
        if response.status_code == 200:
            print(f"✅ Upload endpoint accessible")
            test_results['upload_endpoint'] = {'status': 'success', 'code': 200}
        elif response.status_code == 404:
            print(f"❌ Upload endpoint NOT FOUND (404)")
            print("   🚨 THIS IS YOUR MAIN PROBLEM!")
            print("   💡 ROOT CAUSE: Old firmware doesn't have /upload endpoint")
            print("   💡 SOLUTION: Upload enhanced firmware using QUICK_START.bat")
            test_results['upload_endpoint'] = {'status': 'critical_error', 'code': 404}
        else:
            print(f"⚠️  Upload endpoint status: {response.status_code}")
            test_results['upload_endpoint'] = {'status': 'warning', 'code': response.status_code}
    except Exception as e:
        print(f"❌ Upload endpoint error: {e}")
        test_results['upload_endpoint'] = {'status': 'error', 'error': str(e)}
    
    print("\n" + "=" * 50)
    print("🎉 ESP-01 Status Test Complete!")
    
    # Generate summary and recommendations
    generate_test_summary(test_results)
    
    return True

def generate_test_summary(test_results):
    """Generate a summary of test results with specific recommendations"""
    print("\n📋 TEST SUMMARY & RECOMMENDATIONS:")
    print("=" * 50)
    
    # Count results
    success_count = sum(1 for test in test_results.values() if test.get('status') == 'success')
    warning_count = sum(1 for test in test_results.values() if test.get('status') == 'warning')
    error_count = sum(1 for test in test_results.values() if test.get('status') in ['error', 'critical_error'])
    
    print(f"✅ Successful: {success_count}")
    print(f"⚠️  Warnings: {warning_count}")
    print(f"❌ Errors: {error_count}")
    
    # Check for critical issues
    if test_results.get('upload_endpoint', {}).get('status') == 'critical_error':
        print("\n🚨 CRITICAL ISSUE DETECTED:")
        print("   The /upload endpoint is missing (404 error)")
        print("   This explains why your file uploads are failing!")
        print("\n💡 IMMEDIATE SOLUTION REQUIRED:")
        print("   1. 🚀 Run QUICK_START.bat to launch firmware uploader")
        print("   2. 📁 Select ESP01_Flash.ino firmware")
        print("   3. 🔌 Choose your ESP-01 COM port")
        print("   4. ⬆️  Click Upload")
        print("   5. 🔄 Wait for ESP-01 to restart")
        print("   6. 📱 Connect to 'MatrixUploader' WiFi")
        print("   7. 🧪 Run this test again to verify")
        
    elif test_results.get('basic_connectivity', {}).get('firmware') == 'old':
        print("\n⚠️  OLD FIRMWARE DETECTED:")
        print("   Your ESP-01 is running basic firmware")
        print("   This limits functionality and may cause upload issues")
        print("\n💡 RECOMMENDATION:")
        print("   Upload enhanced firmware for full functionality")
        
    elif error_count > 0:
        print("\n⚠️  SOME ISSUES DETECTED:")
        print("   Some endpoints are not working properly")
        print("   This may affect functionality")
        
    else:
        print("\n✅ ALL TESTS PASSED:")
        print("   Your ESP-01 is working perfectly!")
        print("   All endpoints are functional")
    
    print("\n📊 DETAILED RESULTS:")
    for test_name, result in test_results.items():
        status = result.get('status', 'unknown')
        if status == 'success':
            print(f"   ✅ {test_name}: Working")
        elif status == 'warning':
            print(f"   ⚠️  {test_name}: Warning")
        elif status == 'error':
            print(f"   ❌ {test_name}: Error")
        elif status == 'critical_error':
            print(f"   🚨 {test_name}: CRITICAL ERROR")
    
    print("\n🔧 NEXT STEPS:")
    if test_results.get('upload_endpoint', {}).get('status') == 'critical_error':
        print("   1. 🚀 Upload enhanced firmware (QUICK_START.bat)")
        print("   2. 🔄 Restart ESP-01")
        print("   3. 🧪 Re-run this test")
    else:
        print("   1. 🧪 Test file upload via web interface")
        print("   2. 🎮 Try LED control functions")
        print("   3. 📊 Monitor system health")

def main():
    """Main function"""
    print("ESP-01 Enhanced Status Test Script")
    print("This script tests if your ESP-01 is working properly")
    print("with detailed error reporting and specific solutions")
    print()
    
    # Check if ESP-01 is accessible
    host = "192.168.4.1"
    
    print("⚠️  IMPORTANT: Make sure you're connected to 'MatrixUploader' WiFi network")
    print("   (No password required)")
    print()
    
    input("Press Enter when connected to ESP-01 WiFi...")
    
    # Test the ESP-01
    success = test_esp01_status(host)
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("Check the summary above for detailed analysis and solutions.")
    else:
        print("\n❌ Some tests failed.")
        print("Check the summary above for troubleshooting steps.")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
