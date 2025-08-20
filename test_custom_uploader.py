#!/usr/bin/env python3
"""
Test Custom ESP-01 Uploader
Tests the HTTP-based uploader for existing LED Matrix firmware
"""

from custom_esp_uploader import CustomESPUploader
import os

def test_custom_uploader():
    """Test the custom ESP uploader"""
    print("=== Testing Custom ESP-01 Uploader ===")
    
    # Create uploader instance
    uploader = CustomESPUploader()
    
    # Test 1: ESP Interface Detection
    print("\n1. Testing ESP-01 Interface Detection...")
    capabilities = uploader.test_esp_interface()
    
    if capabilities['status'] == 'connected':
        print("✓ ESP-01 interface detected")
        print(f"  Interface Type: {capabilities['interface_type']}")
        print(f"  Upload Endpoint: {capabilities['upload_endpoint']}")
        print(f"  Has Upload Form: {capabilities['has_upload_form']}")
        print(f"  Page Content Preview: {capabilities['page_content'][:100]}...")
    else:
        print(f"✗ ESP-01 interface error: {capabilities}")
        return False
    
    # Test 2: Create Test File
    print("\n2. Creating Test File...")
    test_file = "test_upload.bin"
    test_data = b"ESP01_TEST_DATA_" + b"X" * 1000  # 1KB test data
    
    try:
        with open(test_file, "wb") as f:
            f.write(test_data)
        print(f"✓ Test file created: {test_file} ({len(test_data)} bytes)")
    except Exception as e:
        print(f"✗ Failed to create test file: {e}")
        return False
    
    # Test 3: Test Upload
    print("\n3. Testing File Upload...")
    
    def progress_callback(progress, bytes_sent, total_bytes):
        print(f"  Progress: {progress}% ({bytes_sent}/{total_bytes} bytes)")
    
    try:
        # Mock WiFi manager (not needed for HTTP uploads)
        class MockWiFiManager:
            def is_connected(self):
                return True
        
        wifi_mgr = MockWiFiManager()
        
        # Attempt upload
        success = uploader.upload_file(
            test_file, 
            wifi_mgr,
            stream_to_ram=False,
            verify=True,
            progress_callback=progress_callback
        )
        
        if success:
            print("✓ File upload test successful!")
        else:
            print("✗ File upload test failed")
            
        return success
        
    except Exception as e:
        print(f"✗ Upload test error: {e}")
        return False
    
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"  Cleaned up test file: {test_file}")

def test_esp_upload_endpoint():
    """Test the ESP-01 upload endpoint directly"""
    print("\n=== Testing ESP-01 Upload Endpoint ===")
    
    import requests
    
    esp_ip = "192.168.4.1"
    upload_url = f"http://{esp_ip}/upload"
    
    # Test 1: Check if upload endpoint exists
    print("1. Checking upload endpoint...")
    try:
        response = requests.get(upload_url, timeout=5)
        print(f"  Upload endpoint response: {response.status_code}")
        
        if response.status_code == 405:  # Method Not Allowed (expected for GET)
            print("  ✓ Upload endpoint exists (GET not allowed)")
        elif response.status_code == 200:
            print("  ✓ Upload endpoint accessible")
        else:
            print(f"  ⚠️  Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"  ✗ Upload endpoint test failed: {e}")
    
    # Test 2: Test POST to upload endpoint
    print("2. Testing POST to upload endpoint...")
    
    # Create small test file
    test_file = "test_post.bin"
    test_data = b"POST_TEST_DATA"
    
    try:
        with open(test_file, "wb") as f:
            f.write(test_data)
        
        # Try POST request
        with open(test_file, "rb") as f:
            files = {'file': ('test_post.bin', f, 'application/octet-stream')}
            
            response = requests.post(upload_url, files=files, timeout=10)
            
            print(f"  POST response: {response.status_code}")
            if response.status_code == 200:
                print("  ✓ POST upload successful")
                print(f"  Response content: {response.text[:200]}...")
            else:
                print(f"  ✗ POST upload failed: {response.status_code}")
                print(f"  Response: {response.text[:200]}...")
                
    except Exception as e:
        print(f"  ✗ POST test failed: {e}")
        
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

def main():
    """Run all tests"""
    print("Custom ESP-01 Uploader Test")
    print("=" * 50)
    
    # Test 1: Custom uploader functionality
    uploader_success = test_custom_uploader()
    
    # Test 2: Direct ESP-01 endpoint testing
    test_esp_upload_endpoint()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    
    if uploader_success:
        print("🎉 Custom uploader test PASSED!")
        print("Your ESP-01 is ready for HTTP file uploads")
        print("\nNext steps:")
        print("1. Use the main application with custom uploader")
        print("2. Or use the custom uploader directly in Python")
    else:
        print("⚠️  Custom uploader test FAILED")
        print("Check the error messages above for details")
    
    print("\nNote: This uploader works with your existing ESP-01 firmware")
    print("No need to upload new firmware via USB!")

if __name__ == "__main__":
    main()
