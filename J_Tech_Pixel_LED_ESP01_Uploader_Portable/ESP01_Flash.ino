#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <FS.h>   // SPIFFS for file storage
#include <bearssl/bearssl_hash.h> // Built-in SHA256 support for ESP8266

// Wi-Fi Access Point credentials
const char* apSSID = "MatrixUploader";
const char* apPASS = "12345678";

ESP8266WebServer server(80);

// File storage and hash tracking
String lastUploadedFile = "";
size_t lastUploadedSize = 0;
String lastUploadedHash = "";

// Handle root page with enhanced upload form and status display
void handleRoot() {
  String page = "<html><head><title>Enhanced LED Matrix Uploader</title>"
                "<meta charset='utf-8'>"
                "<style>"
                "body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }"
                ".container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }"
                "h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }"
                ".upload-form { border: 2px dashed #3498db; padding: 25px; margin: 20px 0; border-radius: 8px; text-align: center; }"
                ".upload-form input[type='file'] { margin: 10px 0; }"
                ".upload-form input[type='submit'] { background: #3498db; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }"
                ".upload-form input[type='submit']:hover { background: #2980b9; }"
                ".status { padding: 15px; margin: 20px 0; border-radius: 8px; }"
                ".success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }"
                ".info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }"
                ".hash-display { font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #dee2e6; word-break: break-all; }"
                ".endpoints { background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; }"
                ".endpoints h3 { margin-top: 0; color: #2c3e50; }"
                ".endpoints ul { margin: 10px 0; padding-left: 20px; }"
                ".endpoints li { margin: 5px 0; }"
                "</style></head>"
                "<body>"
                "<div class='container'>"
                "<h1>🚀 Enhanced LED Matrix Uploader</h1>"
                "<p style='text-align: center; color: #7f8c8d;'>Professional ESP-01 WiFi firmware uploader with hash verification</p>"
                
                "<div class='upload-form'>"
                "<h3>📁 File Upload</h3>"
                "<form method='POST' action='/upload' enctype='multipart/form-data'>"
                "<input type='file' name='file' required><br><br>"
                "<input type='submit' value='Upload File'>"
                "</form>"
                "</div>";
  
  // Add upload status if available
  if (lastUploadedFile.length() > 0) {
    page += "<div class='status success'>"
            "<h3>📊 Last Upload Info</h3>"
            "<p><strong>File:</strong> " + lastUploadedFile + "</p>"
            "<p><strong>Size:</strong> " + String(lastUploadedSize) + " bytes</p>"
            "<p><strong>Hash (SHA256):</strong></p>"
            "<div class='hash-display'>" + (lastUploadedHash.length() > 0 ? lastUploadedHash : "Calculating...") + "</div>"
            "</div>";
  } else {
    page += "<div class='status info'>"
            "<strong>Status:</strong> Ready for uploads - No files uploaded yet"
            "</div>";
  }
  
  page += "<div class='endpoints'>"
          "<h3>🔗 Available Endpoints</h3>"
          "<ul>"
          "<li><strong>GET /</strong> - This page</li>"
          "<li><strong>POST /upload</strong> - File upload</li>"
          "<li><strong>GET /firmware-hash</strong> - Get uploaded file hash (JSON)</li>"
          "<li><strong>GET /status</strong> - System status (JSON)</li>"
          "<li><strong>GET /system-info</strong> - System information (JSON)</li>"
          "</ul>"
          "</div>"
          "</div></body></html>";
  
  server.send(200, "text/html", page);
}

// Handle uploaded file with hash calculation
File uploadFile;

void handleFileUpload() {
  HTTPUpload& upload = server.upload();
  
  if (upload.status == UPLOAD_FILE_START) {
    // Start of file upload
    String filename = "/" + upload.filename;
    Serial.printf("Upload Start: %s\n", filename.c_str());
    
    // Reset tracking variables
    lastUploadedFile = upload.filename;
    lastUploadedSize = 0;
    lastUploadedHash = "";
    
    // Remove existing file if it exists
    if (SPIFFS.exists(filename)) {
      SPIFFS.remove(filename);
      Serial.println("Removed existing file");
    }
    
    // Create new file
    uploadFile = SPIFFS.open(filename, "w");
    if (uploadFile) {
      Serial.println("File created successfully");
    } else {
      Serial.println("Failed to create file");
    }
    
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    // Writing file data
    if (uploadFile) {
      uploadFile.write(upload.buf, upload.currentSize);
      lastUploadedSize += upload.currentSize;
      Serial.printf("Upload Write: %u bytes, Total: %u\n", upload.currentSize, lastUploadedSize);
    }
    
  } else if (upload.status == UPLOAD_FILE_END) {
    // End of file upload
    if (uploadFile) {
      uploadFile.close();
      Serial.printf("Upload End: %s (%u bytes)\n", upload.filename.c_str(), upload.totalSize);
      
      // Calculate hash of uploaded file
      lastUploadedHash = calculateFileHash("/" + lastUploadedFile);
      Serial.printf("File Hash (SHA256): %s\n", lastUploadedHash.c_str());
      
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
      
      // Send success response with file info
      String response = "{\"status\":\"success\",\"message\":\"Upload completed\",\"file\":\"" + lastUploadedFile + "\",\"size\":" + String(lastUploadedSize) + ",\"hash\":\"" + lastUploadedHash + "\"}";
      server.send(200, "application/json", response);
    }
  }
}

// Calculate SHA256 hash of file using BearSSL
String calculateFileHash(String filePath) {
  File f = SPIFFS.open(filePath, "r");
  if (!f) {
    Serial.println("Failed to open file for hash calculation");
    return "";
  }
  
  // Initialize SHA256 context
  br_sha256_context sha256_ctx;
  br_sha256_init(&sha256_ctx);
  
  uint8_t buf[512];
  
  while (f.available()) {
    size_t len = f.read(buf, sizeof(buf));
    br_sha256_update(&sha256_ctx, buf, len);
  }
  f.close();
  
  // Finalize hash
  uint8_t hash[32];
  br_sha256_out(&sha256_ctx, hash);
  
  // Convert to hex string
  String hashString = "";
  for (int i = 0; i < 32; i++) {
    if (hash[i] < 0x10) hashString += "0";
    hashString += String(hash[i], HEX);
  }
  
  return hashString;
}

// Handle firmware hash endpoint - CRITICAL for verification
void handleFirmwareHash() {
  if (lastUploadedHash.length() > 0) {
    // Return the hash of the last uploaded file
    String response = "{\"status\":\"success\",\"file\":\"" + lastUploadedFile + "\",\"size\":" + String(lastUploadedSize) + ",\"hash\":\"" + lastUploadedHash + "\"}";
    server.send(200, "application/json", response);
  } else {
    server.send(404, "application/json", "{\"status\":\"error\",\"message\":\"No firmware file uploaded yet\"}");
  }
}

// Handle system status endpoint
void handleStatus() {
  String response = "{\"status\":\"online\",\"uptime\":" + String(millis()) + ",\"free_heap\":" + String(ESP.getFreeHeap()) + ",\"last_upload\":\"" + lastUploadedFile + "\",\"supports_hash_verification\":true}";
  server.send(200, "application/json", response);
}

// Handle system info endpoint
void handleSystemInfo() {
  String response = "{\"chip_id\":\"" + String(ESP.getChipId(), HEX) + "\",\"flash_size\":" + String(ESP.getFlashChipSize()) + ",\"sdk_version\":\"" + ESP.getSdkVersion() + "\",\"firmware_type\":\"enhanced_led_matrix_uploader_with_hash_verification\"}";
  server.send(200, "application/json", response);
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Enhanced LED Matrix Uploader with Hash Verification ===");
  
  // Initialize SPIFFS
  if (!SPIFFS.begin()) {
    Serial.println("SPIFFS initialization failed");
    return;
  }
  Serial.println("SPIFFS initialized");
  
  // Start Wi-Fi AP
  WiFi.softAP(apSSID, apPASS);
  Serial.println("WiFi AP Started");
  Serial.print("SSID: ");
  Serial.println(apSSID);
  Serial.print("Password: ");
  Serial.println(apPASS);
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());
  Serial.println("Go to http://192.168.4.1/");

  // Setup web server routes
  server.on("/", HTTP_GET, handleRoot);
  
  // File upload endpoint
  server.on("/upload", HTTP_POST, []() {
    server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"Upload endpoint ready\"}");
  }, handleFileUpload);
  
  // Firmware hash endpoint - CRITICAL for verification
  server.on("/firmware-hash", HTTP_GET, handleFirmwareHash);
  
  // System status endpoint
  server.on("/status", HTTP_GET, handleStatus);
  
  // System info endpoint
  server.on("/system-info", HTTP_GET, handleSystemInfo);

  server.begin();
  Serial.println("Web server started with enhanced endpoints");
  Serial.println("✅ Hash verification endpoint /firmware-hash is now available!");
  Serial.println("🎉 Your ESP-01 now supports TRUE verification!");
}

void loop() {
  server.handleClient();
  
  // Optional: Add periodic status reporting
  static unsigned long lastReport = 0;
  if (millis() - lastReport > 30000) { // Every 30 seconds
    lastReport = millis();
    Serial.printf("System Status - Free Heap: %u bytes, Uptime: %lu ms\n", 
                  ESP.getFreeHeap(), millis());
    if (lastUploadedFile.length() > 0) {
      Serial.printf("Last Upload: %s (%u bytes)\n", lastUploadedFile.c_str(), lastUploadedSize);
    }
  }
}
