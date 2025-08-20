#!/usr/bin/env python3
"""
ESP-01 OTA Connection Test
Tests the ArduinoOTA protocol connection for WiFi firmware uploads
"""

import socket
import struct
import time
import hashlib
import os

def test_ota_connection():
    """Test OTA connection to ESP-01"""
    print("=== Testing ESP-01 OTA Connection ===")
    
    # ESP-01 OTA settings
    esp_ip = "192.168.4.1"  # ESP-01 AP IP
    ota_port = 8266          # ArduinoOTA port
    
    print(f"Attempting to connect to ESP-01 OTA service at {esp_ip}:{ota_port}")
    
    try:
        # Create TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        
        # Connect to ESP-01
        print("Connecting to OTA service...")
        sock.connect((esp_ip, ota_port))
        print("✓ Connected to ESP-01 OTA service!")
        
        # Test basic OTA handshake
        print("Testing OTA handshake...")
        
        # Send a simple ping command
        ping_data = struct.pack('<I', 0x00)  # Ping command
        sock.send(ping_data)
        
        # Wait for response
        response = sock.recv(1)
        if response:
            print(f"✓ Received response: {response.hex()}")
        else:
            print("⚠️  No response received")
        
        sock.close()
        return True
        
    except socket.timeout:
        print("✗ Connection timeout - ESP-01 not responding")
        return False
    except ConnectionRefusedError:
        print("✗ Connection refused - OTA service not running")
        print("Make sure ESP-01 has ArduinoOTA firmware loaded")
        return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

def test_http_status():
    """Test HTTP status endpoint"""
    print("\n=== Testing HTTP Status ===")
    
    try:
        import requests
        
        esp_ip = "192.168.4.1"
        response = requests.get(f"http://{esp_ip}/status", timeout=5)
        
        if response.status_code == 200:
            print("✓ HTTP status endpoint working")
            try:
                data = response.json()
                print(f"Device: {data.get('device', 'Unknown')}")
                print(f"Uptime: {data.get('uptime', 0)}s")
                print(f"Free Memory: {data.get('free_heap', 0)} bytes")
                print(f"WiFi Clients: {data.get('wifi_connected', 0)}")
                print(f"OTA Port: {data.get('ota_port', 0)}")
                return True
            except:
                print("⚠️  Could not parse JSON response")
                return False
        else:
            print(f"✗ HTTP status failed: {response.status_code}")
            return False
            
    except ImportError:
        print("⚠️  Requests library not available")
        return False
    except Exception as e:
        print(f"✗ HTTP test failed: {e}")
        return False

def test_ota_protocol():
    """Test OTA protocol with a small test file"""
    print("\n=== Testing OTA Protocol ===")
    
    # Create a small test file
    test_file = "test_firmware.bin"
    test_data = b"ESP01_TEST_FIRMWARE_" + b"X" * 1000  # 1KB test data
    
    try:
        with open(test_file, "wb") as f:
            f.write(test_data)
        
        print(f"Created test file: {test_file} ({len(test_data)} bytes)")
        
        # Test OTA header
        esp_ip = "192.168.4.1"
        ota_port = 8266
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15.0)
        
        print("Connecting for OTA test...")
        sock.connect((esp_ip, ota_port))
        
        # Calculate file hash
        file_hash = hashlib.md5(test_data).hexdigest()
        
        # Send OTA header: [command][size][md5][block_size][block_count]
        command = 0x01  # Flash command
        size = len(test_data)
        md5 = file_hash.encode('utf-8')
        block_size = 1024
        block_count = 1
        
        # Pad MD5 to 32 bytes
        md5_padded = md5.ljust(32, b'\x00')
        
        # Create header
        header = struct.pack('<II32sII', command, size, md5_padded, block_size, block_count)
        
        print(f"Sending OTA header: {len(header)} bytes")
        sock.send(header)
        
        # Wait for acknowledgment
        ack = sock.recv(1)
        if ack and ack[0] == 0x06:  # ACK byte
            print("✓ OTA header acknowledged - protocol working!")
            
            # Send test block
            block_header = struct.pack('<II', 0, len(test_data))
            sock.send(block_header)
            sock.send(test_data)
            
            # Wait for block ACK
            block_ack = sock.recv(1)
            if block_ack and block_ack[0] == 0x06:
                print("✓ Test block acknowledged - OTA protocol fully functional!")
                success = True
            else:
                print("⚠️  Block acknowledgment failed")
                success = False
        else:
            print("✗ OTA header not acknowledged")
            success = False
        
        sock.close()
        
        # Clean up test file
        os.remove(test_file)
        
        return success
        
    except Exception as e:
        print(f"✗ OTA protocol test failed: {e}")
        # Clean up test file if it exists
        if os.path.exists(test_file):
            os.remove(test_file)
        return False

def main():
    """Run all OTA tests"""
    print("ESP-01 OTA Connection Test")
    print("=" * 50)
    
    tests = [
        ("OTA Connection", test_ota_connection),
        ("HTTP Status", test_http_status),
        ("OTA Protocol", test_ota_protocol)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("OTA TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All OTA tests passed! Your ESP-01 is ready for WiFi firmware uploads.")
        print("\nNext steps:")
        print("1. Use the main application to upload firmware files")
        print("2. Or use Arduino IDE with 'Upload via Network' option")
        print("3. Or use espota.py command line tool")
    else:
        print("⚠️  Some OTA tests failed. Check the output above for details.")
        print("\nTroubleshooting tips:")
        print("1. Make sure ESP-01 has the ArduinoOTA firmware loaded")
        print("2. Verify you're connected to 'ESP01_AP' WiFi network")
        print("3. Check ESP-01 IP address (default: 192.168.4.1)")
        print("4. Ensure ESP-01 is powered and responding")

if __name__ == "__main__":
    main()
