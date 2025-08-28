#!/usr/bin/env python3
"""
ESP-01 Diagnostic Tool
Checks storage, memory, and file system status
"""

import requests
import json
import time

def diagnose_esp01(ip="192.168.4.1", port=80):
    """Diagnose ESP-01 status and storage"""
    base_url = f"http://{ip}:{port}"
    
    print("🔍 ESP-01 Diagnostic Tool")
    print("=" * 50)
    
    try:
        # Check system status
        print("\n📊 System Status:")
        response = requests.get(f"{base_url}/system-info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  Status: {data.get('status', 'Unknown')}")
            print(f"  Free Heap: {data.get('free_heap', 0)} bytes")
            print(f"  Flash Size: {data.get('flash_size', 0)} bytes")
            print(f"  Last Upload: {data.get('last_upload', 'None')}")
        else:
            print(f"  ❌ Failed to get system info: {response.status_code}")
            
        # Check file system
        print("\n💾 File System Status:")
        response = requests.get(f"{base_url}/fs-info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  Total Space: {data.get('total_bytes', 0)} bytes")
            print(f"  Used Space: {data.get('used_bytes', 0)} bytes")
            print(f"  Free Space: {data.get('free_bytes', 0)} bytes")
            print(f"  Files: {data.get('file_count', 0)}")
        else:
            print(f"  ❌ Failed to get FS info: {response.status_code}")
            
        # Check uploaded file
        print("\n📁 Uploaded File Status:")
        response = requests.get(f"{base_url}/firmware-hash", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  File: {data.get('file', 'None')}")
            print(f"  Size: {data.get('size', 0)} bytes")
            print(f"  Hash: {data.get('hash', 'None')}")
            
            if data.get('size', 0) == 0:
                print("  ⚠️  WARNING: File size is 0 bytes!")
                print("  💡 This indicates storage failure or file corruption")
        else:
            print(f"  ❌ Failed to get file info: {response.status_code}")
            
        # Check if ESP-01 is accessible
        print("\n🌐 Connectivity Test:")
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("  ✅ ESP-01 is accessible")
            if "Enhanced LED Matrix Uploader" in response.text:
                print("  ✅ Enhanced firmware detected")
            else:
                print("  ⚠️  Basic firmware detected (limited features)")
        else:
            print(f"  ❌ ESP-01 not accessible: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Connection failed: {e}")
        print("  💡 Make sure ESP-01 is powered and WiFi is connected")
        
    print("\n" + "=" * 50)
    print("💡 Recommendations:")
    print("  1. If file size is 0: ESP-01 storage is full or corrupted")
    print("  2. If free heap < 32KB: ESP-01 is low on memory")
    print("  3. Use LED Matrix Studio ESP01 optimization to reduce file size")
    print("  4. Consider reflashing ESP-01 firmware if issues persist")

if __name__ == "__main__":
    print("ESP-01 Diagnostic Tool")
    print("Make sure your ESP-01 is powered and WiFi is connected to 'MatrixUploader'")
    
    ip = input("Enter ESP-01 IP (default: 192.168.4.1): ").strip()
    if not ip:
        ip = "192.168.4.1"
        
    diagnose_esp01(ip)
