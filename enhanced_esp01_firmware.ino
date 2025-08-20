/*
 * Enhanced ESP-01 Firmware with Hash Verification
 * Provides /upload and /firmware-hash endpoints for true file verification
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPUpdateServer.h>
#include <FS.h>
#include <Hash.h>
#include <Updater.h>

// WiFi Configuration
const char* ssid = "ESP01_AP";
const char* password = "12345678";

// Server Configuration
ESP8266WebServer server(80);
ESP8266HTTPUpdateServer httpUpdater;

// File storage
String lastUploadedFile = "";
size_t lastUploadedSize = 0;
String lastUploadedHash = "";

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Enhanced ESP-01 Firmware ===");
  
  // Initialize SPIFFS
  if (!SPIFFS.begin()) {
    Serial.println("SPIFFS initialization failed");
    return;
  }
  Serial.println("SPIFFS initialized");
  
  // Setup WiFi Access Point
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ssid, password);
  
  Serial.print("WiFi AP Started: ");
  Serial.println(ssid);
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());
  
  // Setup web server endpoints
  setupWebServer();
  
  // Setup OTA (optional, for future firmware updates)
  setupArduinoOTA();
  
  Serial.println("Server started");
}

void setupWebServer() {
  // Root page - shows current status
  server.on("/", HTTP_GET, []() {
    String html = R"(
      <!DOCTYPE html>
      <html>
      <head>
        <title>Enhanced ESP-01 Uploader</title>
        <meta charset="utf-8">
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          .container { max-width: 600px; margin: 0 auto; }
          .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
          .success { background-color: #d4edda; color: #155724; }
          .info { background-color: #d1ecf1; color: #0c5460; }
          .upload-form { border: 2px dashed #ccc; padding: 20px; margin: 20px 0; }
          .hash-display { font-family: monospace; background: #f8f9fa; padding: 10px; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>🚀 Enhanced ESP-01 Uploader</h1>
          <p>Professional ESP-01 WiFi firmware uploader with hash verification</p>
          
          <div class="status info">
            <strong>Status:</strong> Ready for uploads
          </div>
          
          <div class="upload-form">
            <h3>📁 File Upload</h3>
            <form action="/upload" method="post" enctype="multipart/form-data">
              <input type="file" name="file" required>
              <input type="submit" value="Upload File">
            </form>
          </div>
          
          <div class="status success">
            <h3>📊 Last Upload Info</h3>
            <p><strong>File:</strong> )" + (lastUploadedFile.length() > 0 ? lastUploadedFile : "None") + R"(</p>
            <p><strong>Size:</strong> )" + String(lastUploadedSize) + R"( bytes</p>
            <p><strong>Hash:</strong> <span class="hash-display">)" + (lastUploadedHash.length() > 0 ? lastUploadedHash : "None") + R"(</span></p>
          </div>
          
          <div class="status info">
            <h3>🔗 Available Endpoints</h3>
            <ul>
              <li><strong>GET /</strong> - This page</li>
              <li><strong>POST /upload</strong> - File upload</li>
              <li><strong>GET /firmware-hash</strong> - Get uploaded file hash</li>
              <li><strong>GET /status</strong> - System status</li>
              <li><strong>GET /system-info</strong> - System information</li>
            </ul>
          </div>
        </div>
      </body>
      </html>
    )";
    
    server.send(200, "text/html", html);
  });
  
  // File upload endpoint
  server.on("/upload", HTTP_POST, []() {
    server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"Upload completed\",\"file\":\"" + lastUploadedFile + "\",\"size\":" + String(lastUploadedSize) + ",\"hash\":\"" + lastUploadedHash + "\"}");
  }, handleFileUpload);
  
  // Firmware hash endpoint - CRITICAL for verification
  server.on("/firmware-hash", HTTP_GET, []() {
    if (lastUploadedHash.length() > 0) {
      // Return the hash of the last uploaded file
      String response = "{\"status\":\"success\",\"file\":\"" + lastUploadedFile + "\",\"size\":" + String(lastUploadedSize) + ",\"hash\":\"" + lastUploadedHash + "\"}";
      server.send(200, "application/json", response);
    } else {
      server.send(404, "application/json", "{\"status\":\"error\",\"message\":\"No firmware file uploaded yet\"}");
    }
  });
  
  // System status endpoint
  server.on("/status", HTTP_GET, []() {
    String response = "{\"status\":\"online\",\"uptime\":" + String(millis()) + ",\"free_heap\":" + String(ESP.getFreeHeap()) + ",\"last_upload\":\"" + lastUploadedFile + "\"}";
    server.send(200, "application/json", response);
  });
  
  // System info endpoint
  server.on("/system-info", HTTP_GET, []() {
    String response = "{\"chip_id\":\"" + String(ESP.getChipId(), HEX) + "\",\"flash_size\":" + String(ESP.getFlashChipSize()) + ",\"sdk_version\":\"" + ESP.getSdkVersion() + "\"}";
    server.send(200, "application/json", response);
  });
  
  server.begin();
  Serial.println("Web server endpoints configured");
}

void handleFileUpload() {
  HTTPUpload& upload = server.upload();
  
  if (upload.status == UPLOAD_FILE_START) {
    // Start of file upload
    lastUploadedFile = upload.filename;
    lastUploadedSize = 0;
    lastUploadedHash = "";
    
    Serial.printf("Upload Start: %s\n", upload.filename.c_str());
    
    // Remove existing file if it exists
    if (SPIFFS.exists("/" + lastUploadedFile)) {
      SPIFFS.remove("/" + lastUploadedFile);
    }
    
    // Create new file
    File f = SPIFFS.open("/" + lastUploadedFile, "w");
    if (f) {
      f.close();
      Serial.println("File created successfully");
    } else {
      Serial.println("Failed to create file");
    }
    
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    // Writing file data
    File f = SPIFFS.open("/" + lastUploadedFile, "a");
    if (f) {
      f.write(upload.buf, upload.currentSize);
      lastUploadedSize += upload.currentSize;
      f.close();
      
      // Calculate hash incrementally
      if (lastUploadedHash.length() == 0) {
        // Initialize hash calculation
        lastUploadedHash = calculateFileHash("/" + lastUploadedFile);
      }
      
      Serial.printf("Upload Write: %u bytes, Total: %u\n", upload.currentSize, lastUploadedSize);
    } else {
      Serial.println("Failed to write to file");
    }
    
  } else if (upload.status == UPLOAD_FILE_END) {
    // End of file upload
    Serial.printf("Upload End: %s, Size: %u\n", upload.filename.c_str(), upload.totalSize);
    
    // Final hash calculation to ensure accuracy
    lastUploadedHash = calculateFileHash("/" + lastUploadedFile);
    
    Serial.printf("File Hash: %s\n", lastUploadedHash.c_str());
    Serial.printf("File: %s, Size: %u bytes\n", lastUploadedFile.c_str(), lastUploadedSize);
    
    // Verify file integrity
    if (SPIFFS.exists("/" + lastUploadedFile)) {
      File f = SPIFFS.open("/" + lastUploadedFile, "r");
      if (f) {
        size_t actualSize = f.size();
        f.close();
        
        if (actualSize == lastUploadedSize) {
          Serial.println("✅ File upload verified successfully");
        } else {
          Serial.printf("⚠️  Size mismatch: Expected %u, Got %u\n", lastUploadedSize, actualSize);
        }
      }
    }
  }
}

String calculateFileHash(String filePath) {
  // Calculate SHA256 hash of the uploaded file
  File f = SPIFFS.open(filePath, "r");
  if (!f) {
    Serial.println("Failed to open file for hash calculation");
    return "";
  }
  
  // Use SHA256 hash
  SHA256 sha256;
  uint8_t buf[512];
  
  while (f.available()) {
    size_t len = f.read(buf, sizeof(buf));
    sha256.update(buf, len);
  }
  f.close();
  
  uint8_t hash[32];
  sha256.finalize(hash, 32);
  
  // Convert to hex string
  String hashString = "";
  for (int i = 0; i < 32; i++) {
    if (hash[i] < 0x10) hashString += "0";
    hashString += String(hash[i], HEX);
  }
  
  return hashString;
}

void setupArduinoOTA() {
  // Optional: Setup OTA for future firmware updates
  httpUpdater.setup(&server);
  Serial.println("OTA update server configured");
}

void loop() {
  server.handleClient();
  
  // Optional: Add periodic tasks here
  static unsigned long lastReport = 0;
  if (millis() - lastReport > 30000) { // Every 30 seconds
    lastReport = millis();
    Serial.printf("System Status - Free Heap: %u bytes, Uptime: %lu ms\n", 
                  ESP.getFreeHeap(), millis());
  }
}
