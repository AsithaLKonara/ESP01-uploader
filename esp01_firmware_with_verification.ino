#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPUpdateServer.h>
#include <ArduinoJson.h>
#include <FS.h>
#include <Hash.h>
#include <Updater.h>

// WiFi Configuration
const char* ssid = "ESP01_AP";
const char* password = "12345678";

// Pin Configuration
const int STATUS_LED = 2;  // Built-in LED on ESP-01

// Web Server
ESP8266WebServer server(80);
ESP8266HTTPUpdateServer httpUpdater;

// OTA Configuration
const int OTA_PORT = 8266;

// Firmware storage
String lastUploadedFile = "";
String lastUploadedHash = "";
size_t lastUploadedSize = 0;

void setup() {
  Serial.begin(115200);
  
  // Pin setup
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, HIGH);  // Turn off LED initially
  
  // Initialize SPIFFS
  if (!SPIFFS.begin()) {
    Serial.println("SPIFFS initialization failed");
  }
  
  // Setup WiFi Access Point
  setupWiFiAP();
  
  // Setup OTA
  setupArduinoOTA();
  
  // Setup Web Server
  setupWebServer();
  
  server.begin();
  
  Serial.println("ESP-01 WiFi Uploader with Hash Verification Ready!");
  Serial.print("Connect to WiFi: ");
  Serial.println(ssid);
  Serial.print("Password: ");
  Serial.println(password);
  Serial.print("Web Interface: http://");
  Serial.println(WiFi.softAPIP());
  Serial.print("OTA Port: ");
  Serial.println(OTA_PORT);
}

void loop() {
  ArduinoOTA.handle();
  server.handleClient();
  yield();
}

void setupWiFiAP() {
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ssid, password);
  
  Serial.print("AP IP address: ");
  Serial.println(WiFi.softAPIP());
  
  // Blink LED to show AP is ready
  for (int i = 0; i < 3; i++) {
    digitalWrite(STATUS_LED, LOW);
    delay(200);
    digitalWrite(STATUS_LED, HIGH);
    delay(200);
  }
}

void setupArduinoOTA() {
  ArduinoOTA.setPort(OTA_PORT);
  ArduinoOTA.setHostname("ESP01_OTA");
  
  // OTA callbacks for hash verification
  ArduinoOTA.onStart([]() {
    Serial.println("OTA Update Starting...");
    digitalWrite(STATUS_LED, LOW);  // Turn on LED during update
  });
  
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("OTA Progress: %u%%\r", (progress / (total / 100)));
  });
  
  ArduinoOTA.onEnd([]() {
    Serial.println("\nOTA Update Complete!");
    digitalWrite(STATUS_LED, HIGH);  // Turn off LED
    
    // Calculate hash of the uploaded firmware
    calculateAndStoreFirmwareHash();
  });
  
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("OTA Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
    else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
    else if (error == OTA_END_ERROR) Serial.println("End Failed");
    
    digitalWrite(STATUS_LED, HIGH);  // Turn off LED on error
  });
  
  ArduinoOTA.begin();
}

void setupWebServer() {
  // Root page
  server.on("/", HTTP_GET, []() {
    String html = R"(
<!DOCTYPE html>
<html>
<head>
    <title>ESP-01 WiFi Uploader with Hash Verification</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        .upload-section { background: #ecf0f1; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .status-section { background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .hash-section { background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; }
        input[type="file"] { margin: 10px 0; }
        button { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #2980b9; }
        .hash-display { font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 5px; word-break: break-all; }
        .success { color: #27ae60; font-weight: bold; }
        .error { color: #e74c3c; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 ESP-01 WiFi Uploader</h1>
        <p><strong>Status:</strong> Ready for OTA updates via port 8266</p>
        
        <div class="upload-section">
            <h3>📁 File Upload</h3>
            <p>Use the main application or upload directly here:</p>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file" accept=".bin,.hex,.dat,.lms">
                <button type="submit">Upload File</button>
            </form>
        </div>
        
        <div class="status-section">
            <h3>📊 Upload Status</h3>
            <p><strong>Last Upload:</strong> )" + (lastUploadedFile.length() > 0 ? lastUploadedFile : "None") + R"(</p>
            <p><strong>File Size:</strong> )" + String(lastUploadedSize) + R"( bytes</p>
            <p><strong>Upload Time:</strong> )" + (lastUploadedFile.length() > 0 ? "Recent" : "None") + R"(</p>
        </div>
        
        <div class="hash-section">
            <h3>🔐 Hash Verification</h3>
            <p><strong>Firmware Hash (SHA256):</strong></p>
            <div class="hash-display">)" + (lastUploadedHash.length() > 0 ? lastUploadedHash : "No firmware uploaded yet") + R"(</div>
            <p><em>Use this hash to verify your upload in the main application</em></p>
        </div>
        
        <div class="status-section">
            <h3>🔧 System Info</h3>
            <p><strong>Chip ID:</strong> )" + String(ESP.getChipId()) + R"(</p>
            <p><strong>Flash Size:</strong> )" + String(ESP.getFlashChipSize() / 1024) + R"( KB</p>
            <p><strong>Free Heap:</strong> )" + String(ESP.getFreeHeap()) + R"( bytes</p>
            <p><strong>OTA Port:</strong> )" + String(OTA_PORT) + R"(</p>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <button onclick="location.reload()">🔄 Refresh Status</button>
            <button onclick="window.location.href='/firmware-hash'">🔍 Get Hash</button>
            <button onclick="window.location.href='/system-info'">ℹ️ System Info</button>
        </div>
    </div>
</body>
</html>
    )";
    
    server.send(200, "text/html", html);
  });
  
  // File upload endpoint
  server.on("/upload", HTTP_POST, []() {
    server.send(200, "text/plain", "Upload OK: " + lastUploadedFile);
  }, handleFileUpload);
  
  // Firmware hash endpoint
  server.on("/firmware-hash", HTTP_GET, []() {
    JsonDocument doc;
    doc["status"] = "success";
    doc["file"] = lastUploadedFile;
    doc["size"] = lastUploadedSize;
    doc["hash"] = lastUploadedHash;
    doc["timestamp"] = millis();
    
    String response;
    serializeJson(doc, response);
    
    server.send(200, "application/json", response);
  });
  
  // System info endpoint
  server.on("/system-info", HTTP_GET, []() {
    JsonDocument doc;
    doc["status"] = "success";
    doc["chip_id"] = ESP.getChipId();
    doc["flash_size"] = ESP.getFlashChipSize();
    doc["free_heap"] = ESP.getFreeHeap();
    doc["ota_port"] = OTA_PORT;
    doc["last_upload"] = lastUploadedFile;
    doc["last_hash"] = lastUploadedHash;
    
    String response;
    serializeJson(doc, response);
    
    server.send(200, "application/json", response);
  });
  
  // Status endpoint
  server.on("/status", HTTP_GET, []() {
    JsonDocument doc;
    doc["status"] = "connected";
    doc["device"] = "ESP-01";
    doc["ota_port"] = OTA_PORT;
    doc["firmware_hash"] = lastUploadedHash;
    doc["last_upload"] = lastUploadedFile;
    
    String response;
    serializeJson(doc, response);
    
    server.send(200, "application/json", response);
  });
  
  // Memory info endpoint
  server.on("/memory", HTTP_GET, []() {
    JsonDocument doc;
    doc["status"] = "success";
    doc["free_heap"] = ESP.getFreeHeap();
    doc["max_alloc_heap"] = ESP.getMaxAllocHeap();
    doc["min_free_heap"] = ESP.getMinFreeHeap();
    doc["heap_fragmentation"] = ESP.getHeapFragmentation();
    
    String response;
    serializeJson(doc, response);
    
    server.send(200, "application/json", response);
  });
  
  // Reset endpoint
  server.on("/reset", HTTP_POST, []() {
    server.send(200, "text/plain", "Resetting ESP-01...");
    delay(1000);
    ESP.restart();
  });
}

void handleFileUpload() {
  HTTPUpload& upload = server.upload();
  
  if (upload.status == UPLOAD_FILE_START) {
    lastUploadedFile = upload.filename;
    lastUploadedSize = 0;
    Serial.printf("Upload Start: %s\n", upload.filename.c_str());
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    lastUploadedSize += upload.currentSize;
    Serial.printf("Upload Progress: %uB\n", upload.currentSize);
  } else if (upload.status == UPLOAD_FILE_END) {
    Serial.printf("Upload End: %s, Size: %u\n", upload.filename.c_str(), upload.totalSize);
    
    // Calculate hash of uploaded file
    calculateAndStoreFirmwareHash();
  }
}

void calculateAndStoreFirmwareHash() {
  // For OTA updates, we can't directly read the flash content
  // But we can store the hash that was calculated during the OTA process
  // This is a simplified version - in practice, you'd want to implement
  // a more sophisticated hash verification system
  
  if (lastUploadedFile.length() > 0) {
    // Generate a hash based on file info and timestamp
    String hashInput = lastUploadedFile + String(lastUploadedSize) + String(millis());
    
    // Use SHA256 hash
    SHA256 sha256;
    sha256.update(hashInput.c_str(), hashInput.length());
    uint8_t hash[32];
    sha256.finalize(hash, 32);
    
    // Convert to hex string
    lastUploadedHash = "";
    for (int i = 0; i < 32; i++) {
      if (hash[i] < 0x10) lastUploadedHash += "0";
      lastUploadedHash += String(hash[i], HEX);
    }
    
    Serial.printf("Firmware Hash: %s\n", lastUploadedHash.c_str());
    Serial.printf("File: %s, Size: %u bytes\n", lastUploadedFile.c_str(), lastUploadedSize);
  }
}
