#!/usr/bin/env python3
"""
Test Enhanced ESP-01 Uploader with Hash Verification
Demonstrates secure OTA uploads with SHA256 verification
"""

from enhanced_esp_uploader import EnhancedESPUploader
import os
import hashlib

def test_enhanced_uploader():
    """Test the enhanced ESP uploader with hash verification"""
    print("=== Testing Enhanced ESP-01 Uploader with Hash Verification ===")
    
    # Create uploader instance
    uploader = EnhancedESPUploader()
    
    # Test 1: ESP Interface Detection
    print("\n1. Testing ESP-01 Interface Detection...")
    capabilities = uploader.test_esp_interface()
    
    if capabilities['status'] == 'connected':
        print("✓ ESP-01 interface detected")
        print(f"  Interface Type: {capabilities['interface_type']}")
        print(f"  Upload Endpoint: {capabilities['upload_endpoint']}")
        print(f"  Hash Endpoint: {capabilities['hash_endpoint']}")
        print(f"  Supports Hash Verification: {capabilities['supports_hash_verification']}")
        print(f"  Has Upload Form: {capabilities['has_upload_form']}")
    else:
        print(f"✗ ESP-01 interface error: {capabilities}")
        return False
    
    # Test 2: Get ESP-01 Status
    print("\n2. Getting ESP-01 Status...")
    status = uploader.get_esp_status()
    if status:
        print("✓ ESP-01 Status:")
        print(f"  Device: {status.get('device', 'Unknown')}")
        print(f"  OTA Port: {status.get('ota_port', 'Unknown')}")
        print(f"  Last Upload: {status.get('last_upload', 'None')}")
        print(f"  Firmware Hash: {status.get('firmware_hash', 'None')[:32]}...")
    else:
        print("⚠️  Could not get ESP-01 status")
    
    # Test 3: Get System Info
    print("\n3. Getting ESP-01 System Info...")
    system_info = uploader.get_system_info()
    if system_info:
        print("✓ System Info:")
        print(f"  Chip ID: {system_info.get('chip_id', 'Unknown')}")
        print(f"  Flash Size: {system_info.get('flash_size', 0) / 1024:.1f} KB")
        print(f"  Free Heap: {system_info.get('free_heap', 0)} bytes")
        print(f"  OTA Port: {system_info.get('ota_port', 'Unknown')}")
    else:
        print("⚠️  Could not get system info")
    
    # Test 4: Create Test File
    print("\n4. Creating Test File...")
    test_file = "test_enhanced_upload.bin"
    test_data = b"ENHANCED_TEST_DATA_" + b"X" * 2000  # 2KB test data
    
    try:
        with open(test_file, "wb") as f:
            f.write(test_data)
        print(f"✓ Test file created: {test_file} ({len(test_data)} bytes)")
        
        # Calculate expected hash
        expected_hash = hashlib.sha256(test_data).hexdigest()
        print(f"  Expected SHA256: {expected_hash}")
        
    except Exception as e:
        print(f"✗ Failed to create test file: {e}")
        return False
    
    # Test 5: Test Enhanced Upload with Verification
    print("\n5. Testing Enhanced Upload with Hash Verification...")
    
    def progress_callback(progress, bytes_sent, total_bytes):
        print(f"  Progress: {progress}% ({bytes_sent}/{total_bytes} bytes)")
    
    try:
        # Mock WiFi manager (not needed for HTTP uploads)
        class MockWiFiManager:
            def is_connected(self):
                return True
        
        wifi_mgr = MockWiFiManager()
        
        # Attempt upload with verification
        success = uploader.upload_file(
            test_file, 
            wifi_mgr,
            stream_to_ram=False,
            verify=True,  # Enable hash verification
            progress_callback=progress_callback
        )
        
        if success:
            print("✓ Enhanced upload with verification successful!")
            
            # Get final status
            final_status = uploader.get_upload_status()
            print(f"  Final Status: {final_status['status']}")
            print(f"  Verification: {final_status['verification']}")
            
        else:
            print("✗ Enhanced upload test failed")
            
        return success
        
    except Exception as e:
        print(f"✗ Enhanced upload test error: {e}")
        return False
    
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"  Cleaned up test file: {test_file}")

def test_hash_verification_only():
    """Test hash verification without uploading"""
    print("\n=== Testing Hash Verification Only ===")
    
    uploader = EnhancedESPUploader()
    
    # Test with your existing file
    existing_file = "C:/Users/asith/Documents/MicroControllerUploaderPython/SampleFirmware/alternating_cols_8x8.bin"
    
    if os.path.exists(existing_file):
        print(f"Testing verification of existing file: {existing_file}")
        
        success = uploader.verify_existing_upload(existing_file)
        if success:
            print("✅ Existing upload verification successful!")
        else:
            print("❌ Existing upload verification failed!")
            
        return success
    else:
        print(f"File not found: {existing_file}")
        return False

def test_esp_endpoints():
    """Test individual ESP-01 endpoints"""
    print("\n=== Testing ESP-01 Endpoints ===")
    
    import requests
    
    esp_ip = "192.168.4.1"
    
    # Test endpoints
    endpoints = [
        ("/", "Root Page"),
        ("/firmware-hash", "Firmware Hash"),
        ("/status", "Status"),
        ("/system-info", "System Info"),
        ("/memory", "Memory Info")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://{esp_ip}{endpoint}", timeout=5)
            print(f"  {description}: {response.status_code}")
            
            if response.status_code == 200:
                if endpoint == "/firmware-hash":
                    try:
                        data = response.json()
                        print(f"    Hash: {data.get('hash', 'None')[:32]}...")
                        print(f"    File: {data.get('file', 'None')}")
                    except:
                        print("    Could not parse JSON response")
                elif endpoint == "/status":
                    try:
                        data = response.json()
                        print(f"    Device: {data.get('device', 'Unknown')}")
                        print(f"    OTA Port: {data.get('ota_port', 'Unknown')}")
                    except:
                        print("    Could not parse JSON response")
                        
        except Exception as e:
            print(f"  {description}: ERROR - {e}")

def main():
    """Run all tests"""
    print("Enhanced ESP-01 Uploader with Hash Verification Test")
    print("=" * 70)
    
    # Test 1: Enhanced uploader functionality
    uploader_success = test_enhanced_uploader()
    
    # Test 2: Hash verification only
    verification_success = test_hash_verification_only()
    
    # Test 3: Individual endpoints
    test_esp_endpoints()
    
    # Summary
    print("\n" + "=" * 70)
    print("ENHANCED TEST RESULTS")
    print("=" * 70)
    
    if uploader_success:
        print("🎉 Enhanced uploader test PASSED!")
        print("Your ESP-01 now supports secure hash verification!")
        print("\nFeatures available:")
        print("✅ HTTP file upload with progress tracking")
        print("✅ SHA256 hash verification")
        print("✅ ESP-01 status monitoring")
        print("✅ System information retrieval")
        print("✅ Firmware hash comparison")
    else:
        print("⚠️  Enhanced uploader test FAILED")
        print("Check the error messages above for details")
    
    if verification_success:
        print("✅ Hash verification test PASSED!")
        print("Your existing uploads can be verified!")
    else:
        print("⚠️  Hash verification test FAILED")
    
    print("\nNext steps:")
    print("1. Use the enhanced uploader in your main application")
    print("2. Enable hash verification for secure uploads")
    print("3. Monitor ESP-01 status and system info")
    print("4. Verify existing uploads without re-uploading")

if __name__ == "__main__":
    main()
