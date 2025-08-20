#!/usr/bin/env python3
"""
Simple ESP-01 Ping Test
Quick test to see if ESP-01 is reachable
"""

import socket
import requests
import time

def test_basic_connectivity():
    """Test basic network connectivity to ESP-01"""
    print("=== ESP-01 Basic Connectivity Test ===")
    
    esp_ip = "192.168.4.1"
    
    # Test 1: Basic ping (TCP connection test)
    print(f"1. Testing TCP connection to {esp_ip}:80 (HTTP)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((esp_ip, 80))
        print("   ✓ HTTP port (80) is reachable")
        sock.close()
    except Exception as e:
        print(f"   ✗ HTTP port (80) failed: {e}")
    
    # Test 2: OTA port test
    print(f"2. Testing TCP connection to {esp_ip}:8266 (OTA)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((esp_ip, 8266))
        print("   ✓ OTA port (8266) is reachable")
        sock.close()
    except Exception as e:
        print(f"   ✗ OTA port (8266) failed: {e}")
    
    # Test 3: HTTP status page
    print(f"3. Testing HTTP status page...")
    try:
        response = requests.get(f"http://{esp_ip}/status", timeout=5)
        if response.status_code == 200:
            print("   ✓ HTTP status page working")
            try:
                data = response.json()
                print(f"   Device: {data.get('device', 'Unknown')}")
                print(f"   OTA Port: {data.get('ota_port', 'Unknown')}")
            except:
                print("   ⚠️  Could not parse JSON response")
        else:
            print(f"   ✗ HTTP status failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ HTTP test failed: {e}")
    
    # Test 4: Network interface check
    print("4. Checking your network configuration...")
    try:
        import subprocess
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
        if '192.168.4' in result.stdout:
            print("   ✓ Found 192.168.4.x network interface")
        else:
            print("   ⚠️  No 192.168.4.x network interface found")
            print("   This might mean you're not connected to ESP01_AP WiFi")
    except Exception as e:
        print(f"   ⚠️  Could not check network interfaces: {e}")

def main():
    print("ESP-01 Connectivity Test")
    print("=" * 40)
    
    test_basic_connectivity()
    
    print("\n" + "=" * 40)
    print("TROUBLESHOOTING TIPS:")
    print("1. Make sure ESP-01 is powered ON")
    print("2. Connect to WiFi network: ESP01_AP (password: 12345678)")
    print("3. Check if ESP-01 has the OTA firmware loaded")
    print("4. Verify ESP-01 IP address is 192.168.4.1")
    print("5. Try moving closer to the ESP-01 if WiFi signal is weak")

if __name__ == "__main__":
    main()
