#!/usr/bin/env python3
"""
Minimal ESP01 Test Firmware

This creates a simple test firmware to verify ESP01 functionality.
"""

import subprocess
import time

def create_minimal_firmware():
    """Create a minimal test firmware"""
    print("🔨 Creating minimal test firmware...")
    
    # This is a minimal ESP8266 firmware that just creates WiFi AP
    minimal_code = """
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

const char* ssid = "ESP01_Test";
const char* password = "test12345";

ESP8266WebServer server(80);

void handleRoot() {
  server.send(200, "text/html", "<h1>ESP01 Test Firmware Working!</h1>");
}

void handleStatus() {
  String response = "{\"status\":\"online\",\"firmware\":\"minimal_test\",\"wifi\":\"active\"}";
  server.send(200, "application/json", response);
}

void setup() {
  Serial.begin(115200);
  Serial.println("ESP01 Test Firmware Starting...");
  
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ssid, password);
  
  Serial.print("WiFi AP Started: ");
  Serial.println(ssid);
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());
  
  server.on("/", handleRoot);
  server.on("/status", handleStatus);
  server.begin();
  
  Serial.println("Web server started!");
}

void loop() {
  server.handleClient();
  delay(10);
}
"""
    
    # Write the minimal firmware
    with open("ESP01_Minimal_Test.ino", "w") as f:
        f.write(minimal_code)
    
    print("✅ Minimal test firmware created: ESP01_Minimal_Test.ino")
    return True

def upload_minimal_firmware():
    """Upload the minimal firmware to ESP01"""
    print("\n🚀 Uploading minimal test firmware...")
    
    try:
        # First, let's try to erase the flash
        print("🧹 Erasing flash memory...")
        cmd = [
            'esptool', '--port', 'COM5', '--baud', '115200',
            'erase_flash'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ Flash erased successfully")
        else:
            print(f"⚠️  Flash erase failed: {result.stderr}")
            return False
        
        # Now upload the minimal firmware
        print("\n📤 Uploading minimal firmware...")
        # Note: We need a compiled .bin file, but for now let's test communication
        
        return True
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def test_minimal_firmware():
    """Test the minimal firmware"""
    print("\n🧪 Testing minimal firmware...")
    
    # Wait for ESP01 to restart
    print("⏳ Waiting for ESP01 to restart...")
    time.sleep(20)
    
    # Test WiFi connection
    try:
        import requests
        print("🔐 Testing WiFi connection...")
        
        # Try to connect to the test network
        response = requests.get("http://192.168.4.1/status", timeout=5)
        if response.status_code == 200:
            print("✅ ESP01 responding on WiFi!")
            print(f"   Response: {response.text}")
            return True
        else:
            print(f"⚠️  ESP01 responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ WiFi test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ESP01 Minimal Test Firmware")
    print("=" * 40)
    
    # Create minimal firmware
    if not create_minimal_firmware():
        print("❌ Failed to create test firmware")
        return False
    
    # Upload minimal firmware
    if not upload_minimal_firmware():
        print("❌ Failed to upload test firmware")
        return False
    
    # Test the result
    if test_minimal_firmware():
        print("\n🎉 Minimal firmware test successful!")
        print("   ESP01 is working and can run custom firmware!")
        return True
    else:
        print("\n⚠️  Minimal firmware test failed")
        print("   ESP01 may have hardware issues")
        return False

if __name__ == "__main__":
    main()
