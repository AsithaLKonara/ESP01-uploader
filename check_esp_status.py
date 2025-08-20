#!/usr/bin/env python3
"""
Check ESP-01 Status and Available Endpoints
See what's actually running on your ESP-01
"""

import requests
import socket

def check_esp_endpoints():
    """Check what endpoints are available on ESP-01"""
    print("=== Checking ESP-01 Available Endpoints ===")
    
    esp_ip = "192.168.4.1"
    base_url = f"http://{esp_ip}"
    
    # Common endpoints to test
    endpoints = [
        "/",           # Root page
        "/status",     # Status API
        "/info",       # Device info
        "/memory",     # Memory info
        "/ping",       # Ping endpoint
        "/ota",        # OTA endpoint
        "/update",     # Update endpoint
        "/firmware",   # Firmware endpoint
    ]
    
    print(f"Testing endpoints on {base_url}:")
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=3)
            print(f"  {endpoint}: {response.status_code} - {response.reason}")
            
            # If it's the root page and it works, show some content
            if endpoint == "/" and response.status_code == 200:
                content = response.text[:200]  # First 200 chars
                print(f"    Content preview: {content}...")
                
        except Exception as e:
            print(f"  {endpoint}: ERROR - {e}")

def check_esp_ports():
    """Check which ports are open on ESP-01"""
    print("\n=== Checking ESP-01 Open Ports ===")
    
    esp_ip = "192.168.4.1"
    common_ports = [80, 8266, 8080, 8888, 23, 22]
    
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            result = sock.connect_ex((esp_ip, port))
            if result == 0:
                print(f"  Port {port}: OPEN")
            else:
                print(f"  Port {port}: CLOSED")
            sock.close()
        except Exception as e:
            print(f"  Port {port}: ERROR - {e}")

def check_esp_web_interface():
    """Try to access the ESP-01 web interface"""
    print("\n=== Checking ESP-01 Web Interface ===")
    
    esp_ip = "192.168.4.1"
    
    try:
        # Try to get the root page
        response = requests.get(f"http://{esp_ip}/", timeout=5)
        
        if response.status_code == 200:
            print("✓ Root page accessible")
            
            # Check if it looks like our OTA firmware
            content = response.text.lower()
            if "esp" in content or "ota" in content or "wifi" in content:
                print("✓ Content appears to be ESP-related")
            else:
                print("⚠️  Content doesn't appear to be ESP-related")
                
            # Show first few lines
            lines = response.text.split('\n')[:5]
            print("First few lines:")
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"  {i+1}: {line.strip()}")
                    
        else:
            print(f"✗ Root page returned: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Could not access web interface: {e}")

def main():
    print("ESP-01 Status Check")
    print("=" * 50)
    
    check_esp_endpoints()
    check_esp_ports()
    check_esp_web_interface()
    
    print("\n" + "=" * 50)
    print("ANALYSIS:")
    print("If you see HTTP 200 responses, your ESP-01 is running")
    print("If OTA port 8266 is closed, you need to upload the OTA firmware")
    print("If you get 404 errors, the ESP-01 doesn't have the expected endpoints")
    print("\nNEXT STEPS:")
    print("1. Upload the OTA firmware via USB first")
    print("2. Then try WiFi OTA updates")

if __name__ == "__main__":
    main()
