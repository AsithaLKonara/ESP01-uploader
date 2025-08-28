#!/usr/bin/env python3
"""
Comprehensive ESP-01 Diagnostic Script
Provides detailed error analysis and troubleshooting information
"""

import requests
import json
import time
import sys
import os
from urllib.parse import urlparse

class ESP01ComprehensiveDiagnostic:
    def __init__(self, host="192.168.4.1"):
        self.host = host
        self.base_url = f"http://{host}"
        self.session = requests.Session()
        self.session.timeout = 10
        self.diagnostic_results = {}
        
    def log(self, message, level="INFO"):
        """Log message with timestamp and level"""
        timestamp = time.strftime("%H:%M:%S")
        level_icon = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🔍"
        }.get(level, "ℹ️")
        
        print(f"[{timestamp}] {level_icon} {message}")
        
    def test_basic_connectivity(self):
        """Test basic network connectivity to ESP-01"""
        self.log("Testing basic connectivity...", "INFO")
        
        try:
            # Test 1: Basic HTTP connection
            response = self.session.get(f"{self.base_url}/", timeout=5)
            self.log(f"HTTP Status: {response.status_code}", "INFO")
            
            if response.status_code == 200:
                self.log("✅ Basic HTTP connection successful", "SUCCESS")
                
                # Check if it's the enhanced firmware
                if "Enhanced LED Matrix Uploader" in response.text:
                    self.log("✅ Enhanced firmware detected", "SUCCESS")
                    self.diagnostic_results['firmware_type'] = 'enhanced'
                else:
                    self.log("⚠️  Old firmware detected - may not support uploads", "WARNING")
                    self.diagnostic_results['firmware_type'] = 'old'
                    
                self.diagnostic_results['basic_connectivity'] = True
                return True
            else:
                self.log(f"❌ HTTP Error: {response.status_code}", "ERROR")
                self.diagnostic_results['basic_connectivity'] = False
                self.diagnostic_results['http_error'] = response.status_code
                return False
                
        except requests.exceptions.ConnectTimeout:
            self.log("❌ Connection timeout - ESP-01 may be unreachable", "ERROR")
            self.diagnostic_results['basic_connectivity'] = False
            self.diagnostic_results['error_type'] = 'connection_timeout'
            return False
            
        except requests.exceptions.ConnectionError as e:
            self.log(f"❌ Connection error: {e}", "ERROR")
            self.diagnostic_results['basic_connectivity'] = False
            self.diagnostic_results['error_type'] = 'connection_error'
            self.diagnostic_results['error_details'] = str(e)
            return False
            
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}", "ERROR")
            self.diagnostic_results['basic_connectivity'] = False
            self.diagnostic_results['error_type'] = 'unexpected_error'
            self.diagnostic_results['error_details'] = str(e)
            return False
    
    def test_endpoint_availability(self):
        """Test availability of key endpoints"""
        self.log("Testing endpoint availability...", "INFO")
        
        endpoints_to_test = [
            "/upload",
            "/ping", 
            "/health",
            "/led-control",
            "/system-info",
            "/fs-info"
        ]
        
        endpoint_results = {}
        
        for endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                status = response.status_code
                
                if status == 200:
                    self.log(f"✅ {endpoint}: Available (200)", "SUCCESS")
                    endpoint_results[endpoint] = {"status": "available", "code": 200}
                elif status == 404:
                    self.log(f"❌ {endpoint}: Not Found (404)", "ERROR")
                    endpoint_results[endpoint] = {"status": "not_found", "code": 404}
                elif status == 405:
                    self.log(f"⚠️  {endpoint}: Method Not Allowed (405)", "WARNING")
                    endpoint_results[endpoint] = {"status": "method_not_allowed", "code": 405}
                else:
                    self.log(f"⚠️  {endpoint}: Unexpected status {status}", "WARNING")
                    endpoint_results[endpoint] = {"status": "unexpected", "code": status}
                    
            except Exception as e:
                self.log(f"❌ {endpoint}: Error - {e}", "ERROR")
                endpoint_results[endpoint] = {"status": "error", "error": str(e)}
        
        self.diagnostic_results['endpoints'] = endpoint_results
        return endpoint_results
    
    def test_upload_endpoint_specifically(self):
        """Test the upload endpoint specifically for POST method"""
        self.log("Testing upload endpoint specifically...", "INFO")
        
        try:
            # Test POST method on upload endpoint
            response = self.session.post(f"{self.base_url}/upload", timeout=5)
            self.log(f"Upload endpoint POST response: {response.status_code}", "INFO")
            
            if response.status_code == 200:
                self.log("✅ Upload endpoint accepts POST requests", "SUCCESS")
                self.diagnostic_results['upload_post_working'] = True
                return True
            elif response.status_code == 404:
                self.log("❌ Upload endpoint returns 404 - endpoint not implemented", "ERROR")
                self.diagnostic_results['upload_post_working'] = False
                self.diagnostic_results['upload_error'] = 'endpoint_not_found'
                return False
            elif response.status_code == 405:
                self.log("❌ Upload endpoint returns 405 - POST method not allowed", "ERROR")
                self.diagnostic_results['upload_post_working'] = False
                self.diagnostic_results['upload_error'] = 'method_not_allowed'
                return False
            else:
                self.log(f"⚠️  Upload endpoint returns unexpected status: {response.status_code}", "WARNING")
                self.diagnostic_results['upload_post_working'] = False
                self.diagnostic_results['upload_error'] = f'unexpected_status_{response.status_code}'
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing upload endpoint: {e}", "ERROR")
            self.diagnostic_results['upload_post_working'] = False
            self.diagnostic_results['upload_error'] = 'test_error'
            self.diagnostic_results['upload_error_details'] = str(e)
            return False
    
    def test_file_upload_simulation(self):
        """Simulate a file upload to identify exact failure point"""
        self.log("Simulating file upload to identify failure point...", "INFO")
        
        # Create a small test file
        test_file_content = b"TEST_UPLOAD_CONTENT_" + b"X" * 100  # 120 bytes
        test_filename = "test_upload.bin"
        
        try:
            with open(test_filename, "wb") as f:
                f.write(test_file_content)
            
            self.log(f"✅ Test file created: {test_filename} ({len(test_file_content)} bytes)", "SUCCESS")
            
            # Attempt upload
            with open(test_filename, "rb") as f:
                files = {'file': (test_filename, f, 'application/octet-stream')}
                data = {'action': 'upload'}
                
                self.log("📤 Attempting file upload...", "INFO")
                response = self.session.post(f"{self.base_url}/upload", files=files, data=data, timeout=30)
                
                self.log(f"📡 Upload response: {response.status_code}", "INFO")
                
                if response.status_code == 200:
                    self.log("✅ File upload successful!", "SUCCESS")
                    self.diagnostic_results['file_upload_test'] = True
                    self.diagnostic_results['upload_response'] = response.text
                    return True
                else:
                    self.log(f"❌ File upload failed with status: {response.status_code}", "ERROR")
                    self.log(f"Response content: {response.text[:200]}...", "ERROR")
                    self.diagnostic_results['file_upload_test'] = False
                    self.diagnostic_results['upload_failure_status'] = response.status_code
                    self.diagnostic_results['upload_failure_response'] = response.text
                    return False
                    
        except Exception as e:
            self.log(f"❌ File upload simulation error: {e}", "ERROR")
            self.diagnostic_results['file_upload_test'] = False
            self.diagnostic_results['upload_simulation_error'] = str(e)
            return False
        finally:
            # Clean up test file
            if os.path.exists(test_filename):
                os.remove(test_filename)
                self.log("🧹 Test file cleaned up", "INFO")
    
    def analyze_firmware_capabilities(self):
        """Analyze what the current firmware can and cannot do"""
        self.log("Analyzing firmware capabilities...", "INFO")
        
        capabilities = {
            'supports_file_upload': False,
            'supports_led_control': False,
            'supports_system_monitoring': False,
            'supports_wifi_config': False,
            'firmware_version': 'unknown'
        }
        
        # Check endpoints from previous test
        if 'endpoints' in self.diagnostic_results:
            endpoints = self.diagnostic_results['endpoints']
            
            if endpoints.get('/upload', {}).get('status') == 'available':
                capabilities['supports_file_upload'] = True
                
            if endpoints.get('/led-control', {}).get('status') == 'available':
                capabilities['supports_led_control'] = True
                
            if endpoints.get('/system-info', {}).get('status') == 'available':
                capabilities['supports_system_monitoring'] = True
                
            if endpoints.get('/wifi-config', {}).get('status') == 'available':
                capabilities['supports_wifi_config'] = True
        
        # Check firmware type
        if self.diagnostic_results.get('firmware_type') == 'enhanced':
            capabilities['firmware_version'] = 'enhanced_v1.0'
        else:
            capabilities['firmware_version'] = 'basic_wifi_manager'
        
        self.diagnostic_results['capabilities'] = capabilities
        return capabilities
    
    def generate_troubleshooting_report(self):
        """Generate comprehensive troubleshooting report"""
        self.log("Generating troubleshooting report...", "INFO")
        
        print("\n" + "="*80)
        print("🔍 COMPREHENSIVE ESP-01 DIAGNOSTIC REPORT")
        print("="*80)
        
        # Basic connectivity status
        print(f"\n📡 CONNECTIVITY STATUS:")
        if self.diagnostic_results.get('basic_connectivity'):
            print("   ✅ ESP-01 is reachable")
            print(f"   🌐 IP Address: {self.host}")
        else:
            print("   ❌ ESP-01 is NOT reachable")
            error_type = self.diagnostic_results.get('error_type', 'unknown')
            print(f"   🚨 Error Type: {error_type}")
            if 'error_details' in self.diagnostic_results:
                print(f"   📝 Error Details: {self.diagnostic_results['error_details']}")
        
        # Firmware analysis
        print(f"\n💾 FIRMWARE ANALYSIS:")
        firmware_type = self.diagnostic_results.get('firmware_type', 'unknown')
        print(f"   🔧 Firmware Type: {firmware_type}")
        
        if firmware_type == 'enhanced':
            print("   ✅ Enhanced firmware detected - should support all features")
        else:
            print("   ⚠️  Basic firmware detected - limited functionality")
            print("   🚨 RECOMMENDATION: Upload enhanced firmware")
        
        # Endpoint analysis
        print(f"\n🔗 ENDPOINT ANALYSIS:")
        if 'endpoints' in self.diagnostic_results:
            endpoints = self.diagnostic_results['endpoints']
            for endpoint, status in endpoints.items():
                if status['status'] == 'available':
                    print(f"   ✅ {endpoint}: Available")
                elif status['status'] == 'not_found':
                    print(f"   ❌ {endpoint}: Not Found (404)")
                else:
                    print(f"   ⚠️  {endpoint}: {status['status']} (Code: {status.get('code', 'N/A')})")
        
        # Upload capability analysis
        print(f"\n📤 UPLOAD CAPABILITY ANALYSIS:")
        if self.diagnostic_results.get('upload_post_working'):
            print("   ✅ Upload endpoint accepts POST requests")
        else:
            print("   ❌ Upload endpoint has issues")
            upload_error = self.diagnostic_results.get('upload_error', 'unknown')
            print(f"   🚨 Upload Error: {upload_error}")
        
        if self.diagnostic_results.get('file_upload_test'):
            print("   ✅ File upload test successful")
        else:
            print("   ❌ File upload test failed")
            failure_status = self.diagnostic_results.get('upload_failure_status', 'unknown')
            print(f"   🚨 Failure Status: {failure_status}")
        
        # Root cause analysis
        print(f"\n🎯 ROOT CAUSE ANALYSIS:")
        if not self.diagnostic_results.get('basic_connectivity'):
            print("   🚨 PRIMARY ISSUE: ESP-01 is not reachable")
            print("   💡 SOLUTION: Check WiFi connection and ESP-01 power")
            
        elif self.diagnostic_results.get('firmware_type') == 'old':
            print("   🚨 PRIMARY ISSUE: Old firmware doesn't support uploads")
            print("   💡 SOLUTION: Upload enhanced firmware using uploader")
            
        elif not self.diagnostic_results.get('upload_post_working'):
            print("   🚨 PRIMARY ISSUE: Upload endpoint not properly implemented")
            print("   💡 SOLUTION: Re-upload firmware or check firmware code")
            
        elif not self.diagnostic_results.get('file_upload_test'):
            print("   🚨 PRIMARY ISSUE: File upload process failing")
            print("   💡 SOLUTION: Check ESP-01 memory and file system")
            
        else:
            print("   ✅ No major issues detected")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if self.diagnostic_results.get('firmware_type') == 'old':
            print("   1. 🚀 UPLOAD ENHANCED FIRMWARE")
            print("      - Use QUICK_START.bat to launch uploader")
            print("      - Select ESP01_Flash.ino firmware")
            print("      - Choose correct COM port")
            print("      - Click Upload")
            print("   2. 🔄 Wait for ESP-01 to restart")
            print("   3. 📱 Connect to 'MatrixUploader' WiFi")
            print("   4. 🧪 Run TEST_ESP01.bat to verify")
            
        elif not self.diagnostic_results.get('basic_connectivity'):
            print("   1. 🔌 Check ESP-01 power and USB connection")
            print("   2. 📶 Look for 'MatrixUploader' WiFi network")
            print("   3. 🔄 Reset ESP-01 if needed")
            
        else:
            print("   1. 🧪 Run TEST_ESP01.bat to verify functionality")
            print("   2. 📤 Test file upload via web interface")
            print("   3. 🎮 Test LED control functions")
        
        print(f"\n📊 DIAGNOSTIC DATA:")
        print(f"   Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   ESP-01 IP: {self.host}")
        print(f"   Firmware: {self.diagnostic_results.get('firmware_type', 'unknown')}")
        print(f"   Upload Working: {self.diagnostic_results.get('file_upload_test', False)}")
        
        print("\n" + "="*80)
    
    def run_comprehensive_diagnostic(self):
        """Run all diagnostic tests"""
        self.log("Starting comprehensive ESP-01 diagnostic...", "INFO")
        
        # Test 1: Basic connectivity
        if not self.test_basic_connectivity():
            self.log("❌ Basic connectivity failed - stopping diagnostic", "ERROR")
            self.generate_troubleshooting_report()
            return False
        
        # Test 2: Endpoint availability
        self.test_endpoint_availability()
        
        # Test 3: Upload endpoint specifically
        self.test_upload_endpoint_specifically()
        
        # Test 4: File upload simulation
        self.test_file_upload_simulation()
        
        # Test 5: Analyze capabilities
        self.analyze_firmware_capabilities()
        
        # Generate report
        self.generate_troubleshooting_report()
        
        return True

def main():
    """Main function"""
    print("🔍 ESP-01 Comprehensive Diagnostic Tool")
    print("This tool will identify exactly why your uploads are failing")
    print()
    
    host = "192.168.4.1"
    
    print("⚠️  IMPORTANT: Make sure you're connected to 'MatrixUploader' WiFi network")
    print("   (No password required)")
    print()
    
    input("Press Enter when connected to ESP-01 WiFi...")
    
    # Create diagnostic instance
    diagnostic = ESP01ComprehensiveDiagnostic(host)
    
    # Run comprehensive diagnostic
    success = diagnostic.run_comprehensive_diagnostic()
    
    if success:
        print("\n✅ Diagnostic completed successfully!")
        print("Check the report above for detailed analysis and solutions.")
    else:
        print("\n❌ Diagnostic encountered critical errors.")
        print("Check the report above for troubleshooting steps.")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
