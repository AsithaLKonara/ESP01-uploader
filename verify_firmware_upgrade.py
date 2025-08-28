#!/usr/bin/env python3
"""
ESP01 Firmware Upgrade Verification Script

This script verifies that the ESP01 firmware has been successfully upgraded
to support large pattern handling features.
"""

import requests
import time
import json

def verify_firmware_upgrade(ip_address="192.168.4.1", max_retries=10):
    """Verify that the ESP01 firmware has been upgraded"""
    print("🔍 Verifying ESP01 Firmware Upgrade...")
    print("=" * 50)
    print("🔐 New WiFi Credentials:")
    print("   SSID: MatrixUploader_ESP01")
    print("   Password: MatrixSecure2024!")
    print("   IP: 192.168.4.1")
    print("=" * 50)
    
    base_url = f"http://{ip_address}"
    
    # Wait for ESP01 to restart and come back online
    print("⏳ Waiting for ESP01 to restart after firmware upload...")
    print("   (This may take 10-30 seconds)")
    
    for attempt in range(max_retries):
        try:
            print(f"   🔄 Attempt {attempt + 1}/{max_retries}...")
            
            # Try to connect to ESP01
            response = requests.get(f"{base_url}/status", timeout=5)
            
            if response.status_code == 200:
                print("   ✅ ESP01 is responding!")
                
                # Parse the response
                try:
                    data = response.json()
                    print(f"   📊 Status: {data.get('status', 'Unknown')}")
                    print(f"   💾 Free Heap: {data.get('free_heap', 0):,} bytes")
                    
                    # Check for new large pattern features
                    large_pattern_mode = data.get('large_pattern_mode', False)
                    chunked_pattern = data.get('chunked_pattern', False)
                    supports_hash_verification = data.get('supports_hash_verification', False)
                    
                    print(f"\n🔧 Large Pattern Features:")
                    print(f"   Large Pattern Mode: {'✅ Yes' if large_pattern_mode else '❌ No'}")
                    print(f"   Chunked Pattern Support: {'✅ Yes' if chunked_pattern else '❌ No'}")
                    print(f"   Hash Verification: {'✅ Yes' if supports_hash_verification else '❌ No'}")
                    
                    # Check if upgrade was successful
                    if large_pattern_mode and chunked_pattern:
                        print(f"\n🎉 FIRMWARE UPGRADE SUCCESSFUL!")
                        print(f"   ESP01 now supports large pattern handling!")
                        print(f"   You can now upload patterns >32KB with chunking!")
                        return True
                    else:
                        print(f"\n⚠️  Firmware upgrade may not be complete")
                        print(f"   Large pattern features not detected")
                        print(f"   Please check the upload process")
                        return False
                        
                except json.JSONDecodeError:
                    print("   ❌ ESP01 response is not valid JSON")
                    print(f"   Response: {response.text}")
                    return False
                    
            else:
                print(f"   ⚠️  ESP01 responded with status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection failed: {e}")
        
        # Wait before next attempt
        if attempt < max_retries - 1:
            print(f"   ⏳ Waiting 3 seconds before next attempt...")
            time.sleep(3)
    
    print(f"\n❌ ESP01 did not come back online after {max_retries} attempts")
    print(f"   Please check:")
    print(f"   1. ESP01 is powered and connected")
    print(f"   2. Firmware upload completed successfully")
    print(f"   3. ESP01 is broadcasting WiFi network")
    return False

def test_large_pattern_endpoints(ip_address="192.168.4.1"):
    """Test the new large pattern endpoints"""
    print(f"\n🧪 Testing Large Pattern Endpoints...")
    print("=" * 50)
    
    base_url = f"http://{ip_address}"
    endpoints = [
        "/upload-chunked",
        "/chunked-playback", 
        "/streaming-control"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {endpoint}: Working")
            else:
                print(f"   ⚠️  {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: {e}")
    
    print(f"\n📋 Endpoint Test Complete")

def main():
    """Main verification function"""
    print("🚀 ESP01 Firmware Upgrade Verification")
    print("=" * 50)
    
    # Verify the upgrade
    if verify_firmware_upgrade():
        # Test the new endpoints
        test_large_pattern_endpoints()
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Run the large pattern uploader: python large_pattern_uploader.py")
        print(f"   2. Test with a large pattern file")
        print(f"   3. Verify chunked upload and playback")
        
    else:
        print(f"\n🔧 Troubleshooting:")
        print(f"   1. Check Arduino IDE for upload errors")
        print(f"   2. Verify ESP01 board settings")
        print(f"   3. Try uploading firmware again")
        print(f"   4. Check USB connection and power")

if __name__ == "__main__":
    main()
