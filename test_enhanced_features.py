#!/usr/bin/env python3
"""
test_enhanced_features.py
Test script for the enhanced ESP-01 LED Matrix features:
- HMAC-SHA1 token generation and verification
- Metadata uploads with per-chunk delays
- Enhanced LED control
- Performance monitoring

Usage:
  python test_enhanced_features.py --host 192.168.4.1 --token-secret change_this_secret
"""

import argparse
import requests
import time
import hmac
import hashlib
import json

class ESP01EnhancedTester:
    def __init__(self, host, token_secret):
        self.host = host
        self.token_secret = token_secret
        self.base_url = f"http://{host}"
        
    def make_token(self, ttl_seconds=90):
        """Generate HMAC-SHA1 token for uploads"""
        ts = str(int(time.time()))
        digest = hmac.new(self.token_secret.encode('utf-8'), ts.encode('utf-8'), hashlib.sha1).hexdigest()
        return f"{digest}:{ts}"
    
    def test_connection(self):
        """Test basic connection to ESP-01"""
        try:
            response = requests.get(f"{self.base_url}/ping", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Connection successful - Free heap: {data['free_heap']} bytes")
                return True
            else:
                print(f"❌ Connection failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def test_health(self):
        """Test health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check - Status: {data['status']}")
                print(f"   Free heap: {data['free_heap']} bytes")
                print(f"   Uptime: {data['uptime']} seconds")
                return True
            else:
                print(f"❌ Health check failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_performance(self):
        """Test performance monitoring"""
        try:
            response = requests.get(f"{self.base_url}/performance", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Performance monitoring:")
                print(f"   Free heap: {data['free_heap']} bytes")
                print(f"   Max alloc heap: {data['max_alloc_heap']} bytes")
                print(f"   Heap fragmentation: {data['heap_fragmentation']}%")
                print(f"   CPU frequency: {data['cpu_freq']} MHz")
                return True
            else:
                print(f"❌ Performance check failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Performance check error: {e}")
            return False
    
    def test_led_control(self):
        """Test LED matrix control functions"""
        token = self.make_token()
        headers = {'X-Upload-Token': token}
        
        # Test LED status
        try:
            response = requests.get(f"{self.base_url}/led-control?action=status", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ LED Control - Status: {data['status']}")
                print(f"   Playing: {data['playing']}")
                print(f"   Paused: {data['paused']}")
                print(f"   Current frame: {data['current_frame']}")
                print(f"   Total frames: {data['total_frames']}")
                print(f"   Frame delay: {data['frame_delay_ms']} ms")
                return True
            else:
                print(f"❌ LED control failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ LED control error: {e}")
            return False
    
    def test_metadata_upload(self):
        """Test metadata upload with per-chunk delays"""
        token = self.make_token()
        headers = {'X-Upload-Token': token}
        
        # Sample metadata with per-chunk delays
        metadata = {
            "frame_delay_ms": 150,
            "total_frames": 10,
            "per_chunk_delays": [100, 200, 150, 300, 100, 250, 150, 200, 100, 300]
        }
        
        try:
            data = {'metadata': json.dumps(metadata)}
            response = requests.post(f"{self.base_url}/upload-metadata", headers=headers, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Metadata upload successful: {result['message']}")
                print(f"   Frame delay: {metadata['frame_delay_ms']} ms")
                print(f"   Total frames: {metadata['total_frames']}")
                print(f"   Per-chunk delays: {metadata['per_chunk_delays']}")
                return True
            else:
                print(f"❌ Metadata upload failed - Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Metadata upload error: {e}")
            return False
    
    def test_led_playback(self):
        """Test LED playback control"""
        token = self.make_token()
        headers = {'X-Upload-Token': token}
        
        # Test play command
        try:
            response = requests.get(f"{self.base_url}/led-control?action=play", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ LED Play command: {data['message']}")
                
                # Wait a moment then check status
                time.sleep(1)
                status_response = requests.get(f"{self.base_url}/led-control?action=status", headers=headers, timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   Status after play: Playing={status_data['playing']}, Frame={status_data['current_frame']}")
                
                # Test pause
                pause_response = requests.get(f"{self.base_url}/led-control?action=pause", headers=headers, timeout=5)
                if pause_response.status_code == 200:
                    pause_data = pause_response.json()
                    print(f"✅ LED Pause command: {pause_data['message']}")
                
                # Test stop
                stop_response = requests.get(f"{self.base_url}/led-control?action=stop", headers=headers, timeout=5)
                if stop_response.status_code == 200:
                    stop_data = stop_response.json()
                    print(f"✅ LED Stop command: {stop_data['message']}")
                
                return True
            else:
                print(f"❌ LED playback test failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ LED playback test error: {e}")
            return False
    
    def test_frame_delay_setting(self):
        """Test frame delay setting"""
        token = self.make_token()
        headers = {'X-Upload-Token': token}
        
        test_delays = [50, 200, 500, 1000]
        
        for delay in test_delays:
            try:
                response = requests.get(f"{self.base_url}/led-control?action=set_delay&delay_ms={delay}", headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Frame delay set to {delay} ms: {data['message']}")
                else:
                    print(f"❌ Failed to set frame delay to {delay} ms - Status: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Frame delay setting error: {e}")
                return False
        
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Enhanced ESP-01 LED Matrix Tests")
        print("=" * 50)
        
        tests = [
            ("Connection Test", self.test_connection),
            ("Health Check", self.test_health),
            ("Performance Monitoring", self.test_performance),
            ("LED Control", self.test_led_control),
            ("Metadata Upload", self.test_metadata_upload),
            ("LED Playback", self.test_led_playback),
            ("Frame Delay Setting", self.test_frame_delay_setting),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            print("-" * 30)
            
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                print(f"❌ {test_name} ERROR: {e}")
            
            time.sleep(1)  # Brief pause between tests
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Enhanced features are working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        
        return passed == total

def main():
    parser = argparse.ArgumentParser(description='Test Enhanced ESP-01 LED Matrix Features')
    parser.add_argument('--host', required=True, help='ESP-01 IP address (e.g., 192.168.4.1)')
    parser.add_argument('--token-secret', required=True, help='Token secret for authentication')
    
    args = parser.parse_args()
    
    tester = ESP01EnhancedTester(args.host, args.token_secret)
    success = tester.run_all_tests()
    
    exit(0 if success else 1)

if __name__ == '__main__':
    main()
