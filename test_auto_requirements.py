#!/usr/bin/env python3
"""
Test Auto-Requirements ESP-01 Uploader
Demonstrates automatic requirements checking and installation
"""

from smart_esp_uploader_with_requirements import SmartESPUploaderWithRequirements
import os
import time

def log_message(message: str):
    """Log message with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_auto_requirements():
    """Test the auto-requirements functionality"""
    print("=== Testing Auto-Requirements ESP-01 Uploader ===")
    
    # Create uploader instance
    uploader = SmartESPUploaderWithRequirements()
    
    # Set log callback for detailed logging
    uploader.set_log_callback(log_message)
    
    # Test 1: Requirements Check and Installation
    print("\n1. Testing Auto-Requirements Management...")
    requirements_success = uploader.check_and_install_requirements()
    
    if requirements_success:
        print("✅ Requirements management successful!")
        
        # Get requirements report
        requirements_report = uploader.get_requirements_report()
        print(f"📊 Requirements Report:")
        print(f"  Total Required: {requirements_report['total_required']}")
        print(f"  Available: {len(requirements_report['available'])}")
        print(f"  Missing: {len(requirements_report['missing'])}")
        print(f"  All Available: {requirements_report['all_available']}")
        
        if requirements_report['install_log']:
            print(f"  Install Log:")
            for log_entry in requirements_report['install_log']:
                print(f"    {log_entry}")
    else:
        print("❌ Requirements management failed!")
        return False
    
    # Test 2: ESP Interface Detection
    print("\n2. Testing ESP-01 Interface Detection...")
    capabilities = uploader.test_esp_interface()
    
    if capabilities['status'] == 'connected':
        print("✅ ESP-01 interface detected")
        print(f"  Interface Type: {capabilities['interface_type']}")
        print(f"  Upload Endpoint: {capabilities['upload_endpoint']}")
        print(f"  Supports Auto-Requirements: {capabilities['supports_auto_requirements']}")
        print(f"  Has Upload Form: {capabilities['has_upload_form']}")
    else:
        print(f"❌ ESP-01 interface error: {capabilities}")
        return False
    
    # Test 3: Create Test File
    print("\n3. Creating Test File...")
    test_file = "test_auto_requirements.bin"
    test_data = b"AUTO_REQUIREMENTS_TEST_DATA_" + b"X" * 2000  # 2KB test data
    
    try:
        with open(test_file, "wb") as f:
            f.write(test_data)
        print(f"✅ Test file created: {test_file} ({len(test_data)} bytes)")
    except Exception as e:
        print(f"❌ Failed to create test file: {e}")
        return False
    
    # Test 4: Test Upload with Auto-Requirements
    print("\n4. Testing Upload with Auto-Requirements...")
    
    def progress_callback(progress, bytes_sent, total_bytes):
        if progress % 25 == 0:  # Log every 25%
            log_message(f"Progress: {progress}% ({bytes_sent}/{total_bytes} bytes)")
    
    try:
        # Mock WiFi manager (not needed for HTTP uploads)
        class MockWiFiManager:
            def is_connected(self):
                return True
        
        wifi_mgr = MockWiFiManager()
        
        # Attempt upload with auto-requirements
        success = uploader.upload_file(
            test_file, 
            wifi_mgr,
            stream_to_ram=False,
            verify=True,  # Enable verification
            progress_callback=progress_callback
        )
        
        if success:
            print("✅ Upload with auto-requirements successful!")
            
            # Get final status
            final_status = uploader.get_upload_status()
            print(f"  Final Status: {final_status['status']}")
            print(f"  Verification: {final_status['verification']}")
            print(f"  Requirements Status: {final_status['requirements_status']}")
            print(f"  Local Hash: {final_status['local_hash'][:32]}...")
            
            # Test verification of existing upload
            print("\n5. Testing Verification of Existing Upload...")
            verify_success = uploader.verify_existing_upload(test_file)
            
            if verify_success:
                print("✅ Existing upload verification successful!")
            else:
                print("❌ Existing upload verification failed!")
            
        else:
            print("❌ Upload test failed!")
            
        return success
        
    except Exception as e:
        print(f"❌ Upload test error: {e}")
        return False
    
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"  Cleaned up test file: {test_file}")

def test_requirements_only():
    """Test requirements management without upload"""
    print("\n=== Testing Requirements Management Only ===")
    
    uploader = SmartESPUploaderWithRequirements()
    uploader.set_log_callback(log_message)
    
    # Test requirements check
    print("Testing requirements check...")
    requirements_success = uploader.check_and_install_requirements()
    
    if requirements_success:
        print("✅ Requirements check successful!")
        
        # Get detailed report
        report = uploader.get_requirements_report()
        print(f"📋 Requirements Status:")
        print(f"  All Available: {report['all_available']}")
        print(f"  Available Packages: {', '.join(report['available'])}")
        
        if report['missing']:
            print(f"  Missing Packages: {', '.join(report['missing'])}")
        else:
            print("  Missing Packages: None")
            
        return True
    else:
        print("❌ Requirements check failed!")
        return False

def test_upload_history():
    """Test upload history functionality"""
    print("\n=== Testing Upload History ===")
    
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
    print("\n6. Exporting Comprehensive Report...")
    report_file = uploader.export_upload_report()
    if report_file:
        print(f"✅ Comprehensive report exported to: {report_file}")
        
        # Show report contents
        try:
            with open(report_file, 'r') as f:
                import json
                report_data = json.load(f)
                print(f"📄 Report contains:")
                print(f"  Upload History: {len(report_data.get('upload_history', {}))} entries")
                print(f"  Requirements: {len(report_data.get('requirements_report', {}).get('available', []))} packages")
                print(f"  ESP Interface: {report_data.get('esp_interface', {}).get('status', 'unknown')}")
        except Exception as e:
            print(f"⚠️  Could not read report: {e}")

def main():
    """Run all tests"""
    print("Auto-Requirements ESP-01 Uploader Test")
    print("=" * 60)
    
    # Test 1: Requirements management only
    requirements_success = test_requirements_only()
    
    # Test 2: Full uploader functionality
    uploader_success = test_auto_requirements()
    
    # Test 3: Upload history and reporting
    test_upload_history()
    
    # Summary
    print("\n" + "=" * 60)
    print("AUTO-REQUIREMENTS TEST RESULTS")
    print("=" * 60)
    
    if requirements_success:
        print("🎉 Requirements management test PASSED!")
        print("✅ Automatic package checking and installation working!")
    else:
        print("⚠️  Requirements management test FAILED")
    
    if uploader_success:
        print("🎉 Auto-requirements uploader test PASSED!")
        print("Your ESP-01 now has enterprise-grade features!")
        print("\nFeatures available:")
        print("✅ Automatic requirements checking and installation")
        print("✅ HTTP file upload with progress tracking")
        print("✅ Smart verification using local hash")
        print("✅ Upload history tracking and management")
        print("✅ Comprehensive logging and reporting")
        print("✅ File integrity verification")
        print("\nNote: This works with your existing ESP-01 firmware!")
    else:
        print("⚠️  Auto-requirements uploader test FAILED")
        print("Check the error messages above for details")
    
    print("\nNext steps:")
    print("1. Use the auto-requirements uploader in your main application")
    print("2. Enjoy automatic dependency management")
    print("3. Monitor detailed upload logs and progress")
    print("4. Generate comprehensive upload reports")
    print("5. Verify uploads with hash integrity checking")

if __name__ == "__main__":
    main()
