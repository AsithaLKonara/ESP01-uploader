#!/usr/bin/env python3
"""
Test Smart ESP-01 Uploader
Demonstrates smart verification with existing firmware
"""

from smart_esp_uploader import SmartESPUploader
import os

def test_smart_uploader():
    """Test the smart ESP uploader"""
    print("=== Testing Smart ESP-01 Uploader ===")
    
    # Create uploader instance
    uploader = SmartESPUploader()
    
    # Test 1: ESP Interface Detection
    print("\n1. Testing ESP-01 Interface Detection...")
    capabilities = uploader.test_esp_interface()
    
    if capabilities['status'] == 'connected':
        print("✓ ESP-01 interface detected")
        print(f"  Interface Type: {capabilities['interface_type']}")
        print(f"  Upload Endpoint: {capabilities['upload_endpoint']}")
        print(f"  Supports Smart Verification: {capabilities['supports_smart_verification']}")
        print(f"  Verification Method: {capabilities['verification_method']}")
        print(f"  Has Upload Form: {capabilities['has_upload_form']}")
    else:
        print(f"✗ ESP-01 interface error: {capabilities}")
        return False
    
    # Test 2: Create Test File
    print("\n2. Creating Test File...")
    test_file = "test_smart_upload.bin"
    test_data = b"SMART_TEST_DATA_" + b"X" * 1500  # 1.5KB test data
    
    try:
        with open(test_file, "wb") as f:
            f.write(test_data)
        print(f"✓ Test file created: {test_file} ({len(test_data)} bytes)")
    except Exception as e:
        print(f"✗ Failed to create test file: {e}")
        return False
    
    # Test 3: Test Smart Upload with Verification
    print("\n3. Testing Smart Upload with Verification...")
    
    def progress_callback(progress, bytes_sent, total_bytes):
        print(f"  Progress: {progress}% ({bytes_sent}/{total_bytes} bytes)")
    
    try:
        # Mock WiFi manager (not needed for HTTP uploads)
        class MockWiFiManager:
            def is_connected(self):
                return True
        
        wifi_mgr = MockWiFiManager()
        
        # Attempt upload with smart verification
        success = uploader.upload_file(
            test_file, 
            wifi_mgr,
            stream_to_ram=False,
            verify=True,  # Enable smart verification
            progress_callback=progress_callback
        )
        
        if success:
            print("✓ Smart upload with verification successful!")
            
            # Get final status
            final_status = uploader.get_upload_status()
            print(f"  Final Status: {final_status['status']}")
            print(f"  Verification: {final_status['verification']}")
            print(f"  Local Hash: {final_status['local_hash'][:32]}...")
            
            # Test verification of existing upload
            print("\n4. Testing Verification of Existing Upload...")
            verify_success = uploader.verify_existing_upload(test_file)
            
            if verify_success:
                print("✅ Existing upload verification successful!")
            else:
                print("❌ Existing upload verification failed!")
            
        else:
            print("✗ Smart upload test failed")
            
        return success
        
    except Exception as e:
        print(f"✗ Smart upload test error: {e}")
        return False
    
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"  Cleaned up test file: {test_file}")

def test_upload_history():
    """Test upload history functionality"""
    print("\n=== Testing Upload History ===")
    
    uploader = SmartESPUploader()
    
    # Get upload history
    history = uploader.get_upload_history()
    if history:
        print("✓ Upload History Found:")
        for filename, details in history.items():
            print(f"  File: {filename}")
            print(f"    Size: {details['file_size']} bytes")
            print(f"    Hash: {details['local_hash'][:32]}...")
            print(f"    Upload Time: {details['upload_time']}")
            print(f"    Status: {details['verification_status']}")
    else:
        print("⚠️  No upload history found")
    
    # Export upload report
    print("\n5. Exporting Upload Report...")
    report_file = uploader.export_upload_report()
    if report_file:
        print(f"✓ Upload report exported to: {report_file}")

def main():
    """Run all tests"""
    print("Smart ESP-01 Uploader Test")
    print("=" * 50)
    
    # Test 1: Smart uploader functionality
    uploader_success = test_smart_uploader()
    
    # Test 2: Upload history
    test_upload_history()
    
    # Summary
    print("\n" + "=" * 50)
    print("SMART TEST RESULTS")
    print("=" * 50)
    
    if uploader_success:
        print("🎉 Smart uploader test PASSED!")
        print("Your ESP-01 now has enhanced features through Python!")
        print("\nFeatures available:")
        print("✅ HTTP file upload with progress tracking")
        print("✅ Smart verification using local hash")
        print("✅ Upload history tracking")
        print("✅ File integrity verification")
        print("✅ Upload report generation")
        print("\nNote: This works with your existing ESP-01 firmware!")
    else:
        print("⚠️  Smart uploader test FAILED")
        print("Check the error messages above for details")
    
    print("\nNext steps:")
    print("1. Use the smart uploader in your main application")
    print("2. Enable smart verification for secure uploads")
    print("3. Track upload history and verify files")
    print("4. Generate upload reports for documentation")

if __name__ == "__main__":
    main()
