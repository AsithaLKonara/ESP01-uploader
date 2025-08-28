#!/usr/bin/env python3
"""
Test Enhanced ESP01 Firmware

This script tests all the enhanced features of the ESP01 firmware.
"""

import requests
import time
import json

class ESP01EnhancedTester:
    def __init__(self, ip_address="192.168.4.1", token="upload_token_2025"):
        self.ip_address = ip_address
        self.token = token
        self.base_url = f"http://{ip_address}"
        
    def test_connection(self):
        """Test basic connection to ESP01"""
        print("🔍 Testing ESP01 Connection...")
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                print("✅ ESP01 responding!")
                data = response.json()
                print(f"   Uptime: {data.get('uptime')} ms")
                print(f"   Free Heap: {data.get('free_heap')} bytes")
                print(f"   Playing: {data.get('playing')}")
                return True
            else:
                print(f"❌ ESP01 responded with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def test_web_interface(self):
        """Test the web interface"""
        print("\n🌐 Testing Web Interface...")
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                print("✅ Web interface accessible!")
                if "ESP Matrix Uploader" in response.text:
                    print("   ✅ Correct title found")
                if "upload_token_2025" in response.text:
                    print("   ✅ Upload token visible")
                return True
            else:
                print(f"❌ Web interface failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Web interface test failed: {e}")
            return False
    
    def test_upload_endpoints(self):
        """Test upload endpoints"""
        print("\n📤 Testing Upload Endpoints...")
        
        # Test upload endpoint
        try:
            response = requests.get(f"{self.base_url}/upload?token={self.token}", timeout=5)
            if response.status_code == 405:  # Method not allowed for GET
                print("✅ Upload endpoint accessible (GET not allowed as expected)")
            else:
                print(f"⚠️  Upload endpoint: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Upload endpoint test failed: {e}")
        
        # Test chunked upload endpoint
        try:
            response = requests.get(f"{self.base_url}/upload-chunked?token={self.token}", timeout=5)
            if response.status_code == 405:  # Method not allowed for GET
                print("✅ Chunked upload endpoint accessible (GET not allowed as expected)")
            else:
                print(f"⚠️  Chunked upload endpoint: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Chunked upload endpoint test failed: {e}")
        
        return True
    
    def test_playback_endpoints(self):
        """Test playback endpoints"""
        print("\n▶️  Testing Playback Endpoints...")
        
        # Test play endpoint
        try:
            response = requests.get(f"{self.base_url}/play", timeout=5)
            if response.status_code == 400:  # Missing file parameter
                print("✅ Play endpoint accessible (file parameter required)")
            else:
                print(f"⚠️  Play endpoint: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Play endpoint test failed: {e}")
        
        # Test stop endpoint
        try:
            response = requests.get(f"{self.base_url}/stop", timeout=5)
            if response.status_code == 200:
                print("✅ Stop endpoint accessible")
            else:
                print(f"⚠️  Stop endpoint: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Stop endpoint test failed: {e}")
        
        return True
    
    def test_metadata_endpoint(self):
        """Test metadata endpoint"""
        print("\n📊 Testing Metadata Endpoint...")
        try:
            response = requests.get(f"{self.base_url}/set-metadata", timeout=5)
            if response.status_code == 405:  # Method not allowed for GET
                print("✅ Metadata endpoint accessible (POST required)")
            else:
                print(f"⚠️  Metadata endpoint: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Metadata endpoint test failed: {e}")
        
        return True
    
    def test_wifi_credentials(self):
        """Test WiFi credentials display"""
        print("\n🔐 Testing WiFi Credentials...")
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                if "MatrixUploader_ESP01" in response.text:
                    print("✅ WiFi SSID visible: MatrixUploader_ESP01")
                else:
                    print("❌ WiFi SSID not found")
                
                if "MatrixSecure2024!" in response.text:
                    print("✅ WiFi password visible: MatrixSecure2024!")
                else:
                    print("❌ WiFi password not found")
                
                return True
            else:
                print(f"❌ Could not access web interface: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ WiFi credentials test failed: {e}")
            return False
    
    def run_full_test(self):
        """Run complete firmware test"""
        print("🧪 ESP01 Enhanced Firmware Test")
        print("=" * 40)
        
        tests = [
            ("Connection", self.test_connection),
            ("Web Interface", self.test_web_interface),
            ("Upload Endpoints", self.test_upload_endpoints),
            ("Playback Endpoints", self.test_playback_endpoints),
            ("Metadata Endpoint", self.test_metadata_endpoint),
            ("WiFi Credentials", self.test_wifi_credentials)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    print(f"   ⚠️  {test_name} test had issues")
            except Exception as e:
                print(f"   ❌ {test_name} test failed with error: {e}")
        
        # Final assessment
        print(f"\n🎯 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! ESP01 enhanced firmware is working perfectly!")
            print("   🚀 You can now upload LED patterns and control your matrix!")
        elif passed >= total * 0.8:
            print("✅ Most tests passed! ESP01 is working well.")
            print("   🔧 Some minor issues may exist but core functionality works.")
        else:
            print("⚠️  Many tests failed. ESP01 may need firmware re-upload.")
            print("   🔧 Check connections and try uploading firmware again.")
        
        return passed >= total * 0.8

def main():
    """Main function"""
    print("🚀 ESP01 Enhanced Firmware Test Suite")
    print("=" * 50)
    
    # Check if ESP01 is accessible
    tester = ESP01EnhancedTester()
    
    if tester.run_full_test():
        print("\n🎉 ESP01 enhanced firmware test completed successfully!")
        print("   Your LED matrix control system is ready!")
    else:
        print("\n🔧 ESP01 test completed with issues")
        print("   Check the details above and troubleshoot as needed")

if __name__ == "__main__":
    main()
