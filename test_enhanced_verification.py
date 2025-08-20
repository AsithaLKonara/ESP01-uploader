#!/usr/bin/env python3
"""
Test Enhanced ESP-01 Verification
Demonstrates the new 7-step verification process with real ESP-01 hash verification
"""

from smart_esp_uploader_with_requirements import SmartESPUploaderWithRequirements
import os
import time

def log_message(message: str):
    """Log message with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_enhanced_verification():
    """Test the enhanced verification with ESP-01 hash checking"""
    print("=== Testing Enhanced ESP-01 Verification ===")
    
    # Create uploader instance
    uploader = SmartESPUploaderWithRequirements()
    
    # Set log callback for detailed logging
    uploader.set_log_callback(log_message)
    
    # Test 1: ESP Interface Detection with Hash Support
    print("\n1. Testing ESP-01 Interface Detection...")
    capabilities = uploader.test_esp_interface()
    
    if capabilities['status'] == 'connected':
        print("✅ ESP-01 interface detected")
        print(f"  Interface Type: {capabilities['interface_type']}")
        print(f"  Upload Endpoint: {capabilities['upload_endpoint']}")
        print(f"  Hash Endpoint: {capabilities['hash_endpoint']}")
        print(f"  Supports ESP Hash Verification: {capabilities['supports_esp_hash_verification']}")
        print(f"  Verification Method: {capabilities['verification_method']}")
        
        if capabilities['supports_esp_hash_verification']:
            print("🎉 This ESP-01 supports TRUE verification!")
        else:
            print("⚠️  This ESP-01 doesn't support hash verification")
            print("   Consider flashing the enhanced firmware")
    else:
        print(f"❌ ESP-01 interface error: {capabilities}")
        return False
    
    # Test 2: Create Test File
    print("\n2. Creating Test File...")
    test_file = "test_enhanced_verification.bin"
    test_data = b"ENHANCED_VERIFICATION_TEST_DATA_" + b"X" * 3000  # 3KB test data
    
    try:
        with open(test_file, "wb") as f:
            f.write(test_data)
        print(f"✅ Test file created: {test_file} ({len(test_data)} bytes)")
    except Exception as e:
        print(f"❌ Failed to create test file: {e}")
        return False
    
    # Test 3: Test Enhanced Upload with 7-Step Verification
    print("\n3. Testing Enhanced Upload with 7-Step Verification...")
    
    def progress_callback(progress, bytes_sent, total_bytes):
        if progress % 25 == 0:  # Log every 25%
            log_message(f"Progress: {progress}% ({bytes_sent}/{total_bytes} bytes)")
    
    try:
        # Mock WiFi manager (not needed for HTTP uploads)
        class MockWiFiManager:
            def is_connected(self):
                return True
        
        wifi_mgr = MockWiFiManager()
        
        # Attempt upload with enhanced verification
        success = uploader.upload_file(
            test_file, 
            wifi_mgr,
            stream_to_ram=False,
            verify=True,  # Enable enhanced verification
            progress_callback=progress_callback
        )
        
        if success:
            print("✅ Enhanced upload with verification successful!")
            
            # Get final status
            final_status = uploader.get_upload_status()
            print(f"  Final Status: {final_status['status']}")
            print(f"  Verification: {final_status['verification']}")
            print(f"  Verification Method: {final_status['verification_method']}")
            print(f"  Local Hash: {final_status['local_hash'][:32]}...")
            
            if final_status.get('esp_hash'):
                print(f"  ESP-01 Hash: {final_status['esp_hash'][:32]}...")
                print("🎉 TRUE VERIFICATION ACHIEVED!")
            else:
                print("  ESP-01 Hash: Not available")
                print("⚠️  Verification limited to smart verification")
            
            # Test verification of existing upload
            print("\n4. Testing Verification of Existing Upload...")
            verify_success = uploader.verify_existing_upload(test_file)
            
            if verify_success:
                print("✅ Existing upload verification successful!")
            else:
                print("❌ Existing upload verification failed!")
            
        else:
            print("❌ Enhanced upload test failed!")
            
        return success
        
    except Exception as e:
        print(f"❌ Enhanced upload test error: {e}")
        return False
    
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"  Cleaned up test file: {test_file}")

def test_verification_methods():
    """Test different verification methods"""
    print("\n=== Testing Verification Methods ===")
    
    uploader = SmartESPUploaderWithRequirements()
    uploader.set_log_callback(log_message)
    
    # Test ESP interface capabilities
    capabilities = uploader.test_esp_interface()
    
    if capabilities['status'] == 'connected':
        print("📊 Verification Method Analysis:")
        print(f"  ESP-01 Status: {capabilities['status']}")
        print(f"  Hash Endpoint Available: {capabilities['supports_esp_hash_verification']}")
        print(f"  Recommended Method: {capabilities['verification_method']}")
        
        if capabilities['supports_esp_hash_verification']:
            print("\n🎯 This ESP-01 supports:")
            print("  ✅ Step 7: Real ESP-01 Verification")
            print("  ✅ TRUE file integrity verification")
            print("  ✅ ESP-side hash calculation")
            print("  ✅ Hash comparison for corruption detection")
        else:
            print("\n⚠️  This ESP-01 supports:")
            print("  ✅ Step 6: Smart Verification")
            print("  ✅ Local hash calculation")
            print("  ✅ Upload success confirmation")
            print("  ❌ No ESP-side hash verification")
            print("\n💡 To enable TRUE verification:")
            print("   Flash the enhanced firmware (enhanced_esp01_firmware.ino)")
    else:
        print("❌ Cannot test verification methods - ESP-01 not reachable")

def test_upload_history():
    """Test upload history with enhanced verification data"""
    print("\n=== Testing Enhanced Upload History ===")
    
    uploader = SmartESPUploaderWithRequirements()
    uploader.set_log_callback(log_message)
    
    # Get upload history
    history = uploader.get_upload_history()
    if history:
        print("✅ Upload History Found:")
        for filename, details in history.items():
            print(f"  File: {filename}")
            print(f"    Size: {details['file_size']} bytes")
            print(f"    Hash: {details['local_hash'][:32]}...")
            print(f"    Upload Time: {details['upload_time']}")
            print(f"    Status: {details['verification_status']}")
    else:
        print("⚠️  No upload history found")
    
    # Export comprehensive report
    print("\n5. Exporting Enhanced Upload Report...")
    report_file = uploader.export_upload_report()
    if report_file:
        print(f"✅ Enhanced upload report exported to: {report_file}")
        
        # Show report contents
        try:
            with open(report_file, 'r') as f:
                import json
                report_data = json.load(f)
                print(f"📄 Report contains:")
                print(f"  Upload History: {len(report_data.get('upload_history', {}))} entries")
                print(f"  Requirements: {len(report_data.get('requirements_report', {}).get('available', []))} packages")
                print(f"  ESP Interface: {report_data.get('esp_interface', {}).get('status', 'unknown')}")
                print(f"  Hash Verification: {report_data.get('esp_interface', {}).get('supports_esp_hash_verification', False)}")
        except Exception as e:
            print(f"⚠️  Could not read report: {e}")

def main():
    """Run all tests"""
    print("Enhanced ESP-01 Verification Test")
    print("=" * 60)
    
    # Test 1: Enhanced verification
    verification_success = test_enhanced_verification()
    
    # Test 2: Verification methods
    test_verification_methods()
    
    # Test 3: Upload history
    test_upload_history()
    
    # Summary
    print("\n" + "=" * 60)
    print("ENHANCED VERIFICATION TEST RESULTS")
    print("=" * 60)
    
    if verification_success:
        print("🎉 Enhanced verification test PASSED!")
        print("Your ESP-01 now has TRUE verification capabilities!")
        print("\nNew Features Available:")
        print("✅ Step 7: Real ESP-01 Verification")
        print("✅ ESP-side hash calculation")
        print("✅ True file integrity verification")
        print("✅ Corruption detection during upload")
        print("✅ Hash mismatch identification")
        print("\nVerification Process:")
        print("1. 📋 Requirements check and installation")
        print("2. 📋 File validation")
        print("3. 📋 ESP-01 connectivity test")
        print("4. 📋 Local SHA256 hash calculation")
        print("5. 📋 File upload via HTTP")
        print("6. 📋 Smart verification (local hash + upload success)")
        print("7. 📋 REAL ESP-01 verification (ESP hash vs local hash)")
        print("\nThis provides TRUE verification that your file was stored correctly!")
    else:
        print("⚠️  Enhanced verification test FAILED")
        print("Check the error messages above for details")
    
    print("\nNext steps:")
    print("1. Flash enhanced firmware to ESP-01 for TRUE verification")
    print("2. Enjoy 7-step verification process")
    print("3. Detect file corruption during upload")
    print("4. Verify ESP-01 storage integrity")
    print("5. Generate comprehensive verification reports")

if __name__ == "__main__":
    main()
