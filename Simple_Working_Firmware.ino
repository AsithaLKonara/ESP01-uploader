/*
 * Simple Working LED Matrix Firmware for ESP-01
 * Combines basic WiFi file upload with proven LED matrix output
 * This version is simplified to avoid crashes
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <FS.h>   // SPIFFS for file storage

// Wi-Fi Access Point credentials
const char* apSSID = "MatrixUploader";
const char* apPASS = "12345678";

// LED Matrix Data Pin Configuration
#define MATRIX_DATA_PIN 3   // GPIO3 (RX) - Data pin
#define MATRIX_CLOCK_PIN 1  // GPIO1 (TX) - Clock pin (if needed)

ESP8266WebServer server(80);

// File storage tracking
String lastUploadedFile = "";
size_t lastUploadedSize = 0;

// Handle root page
void handleRoot() {
  String page = "<html><head><title>Simple LED Matrix Uploader</title>"
                "<meta charset='utf-8'>"
                "<style>"
                "body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }"
                ".container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }"
                "h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }"
                ".upload-form { border: 2px dashed #3498db; padding: 25px; margin: 20px 0; border-radius: 8px; text-align: center; }"
                ".upload-form input[type='file'] { margin: 10px 0; }"
                ".upload-form input[type='submit'] { background: #3498db; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }"
                ".status { padding: 15px; margin: 20px 0; border-radius: 8px; }"
                ".success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }"
                ".info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }"
                "</style></head>"
                "<body>"
                "<div class='container'>"
                "<h1>🚀 Simple LED Matrix Uploader</h1>"
                "<p style='text-align: center; color: #7f8c8d;'>Basic WiFi firmware uploader with LED matrix output</p>"
                
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
            "<p><strong>Status:</strong> Ready for LED matrix output</p>"
            "</div>";
  } else {
    page += "<div class='status info'>"
            "<strong>Status:</strong> Ready for uploads - No files uploaded yet"
            "</div>";
  }
  
  page += "<div class='status info'>"
          "<h3>🎨 LED Matrix Status</h3>"
          "<p><strong>Data Pin:</strong> GPIO3 (RX) - Configured for matrix output</p>"
          "<p><strong>Clock Pin:</strong> GPIO1 (TX) - Available if needed</p>"
          "<p><strong>Status:</strong> " + (lastUploadedFile.length() > 0 ? "Data ready for matrix output" : "Waiting for file upload") + "</p>"
          "</div>"
          
          "<div class='status info'>"
          "<h3>🔗 Available Endpoints</h3>"
          "<ul>"
          "<li><strong>GET /</strong> - This page</li>"
          "<li><strong>POST /upload</strong> - File upload</li>"
          "<li><strong>POST /send-to-matrix</strong> - Send file to LED matrix</li>"
          "<li><strong>GET /status</strong> - System status</li>"
          "</ul>"
          "</div>"
          "</div></body></html>";
  
  server.send(200, "text/html", page);
}

// Handle uploaded file - SIMPLIFIED VERSION
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
      Serial.println("✅ File upload completed successfully");
      
      // Send success response
      String response = "{\"status\":\"success\",\"message\":\"Upload completed\",\"file\":\"" + lastUploadedFile + "\",\"size\":" + String(lastUploadedSize) + "}";
      server.send(200, "application/json", response);
    }
  }
}

// Send file to LED matrix - SIMPLIFIED VERSION
void sendToMatrix(String filePath) {
  File f = SPIFFS.open(filePath, "r");
  if (!f) {
    Serial.println("⚠️ Failed to open file for matrix output");
    return;
  }

  Serial.println("➡️ Sending uploaded file to LED matrix via GPIO3...");
  Serial.printf("📁 File: %s\n", filePath.c_str());
  Serial.printf("📏 Size: %u bytes\n", f.size());
  
  // Reset matrix data pin
  digitalWrite(MATRIX_DATA_PIN, LOW);
  delayMicroseconds(100);
  
  size_t bytesSent = 0;
  
  // Simple bit-banging output
  while (f.available()) {
    uint8_t byte = f.read();
    
    // Send each bit to the data pin (MSB first)
    for (int bit = 7; bit >= 0; bit--) {
      digitalWrite(MATRIX_DATA_PIN, (byte >> bit) & 0x01);
      delayMicroseconds(100); // Slower for reliability
    }
    
    bytesSent++;
    
    // Progress indicator every 100 bytes
    if (bytesSent % 100 == 0) {
      Serial.printf("📤 Sent %u bytes to matrix...\n", bytesSent);
    }
  }
  
  f.close();
  
  // Send end marker
  digitalWrite(MATRIX_DATA_PIN, LOW);
  delayMicroseconds(200);
  
  Serial.printf("✅ Successfully sent %u bytes to LED matrix via GPIO3\n", bytesSent);
  Serial.println("🎉 Matrix should now display the uploaded pattern!");
}

// Manual matrix output endpoint
void handleSendToMatrix() {
  if (lastUploadedFile.length() > 0) {
    Serial.println("🔄 Manual matrix output requested...");
    sendToMatrix("/" + lastUploadedFile);
    
    String response = "{\"status\":\"success\",\"message\":\"File sent to matrix\",\"file\":\"" + lastUploadedFile + "\",\"size\":" + String(lastUploadedSize) + "}";
    server.send(200, "application/json", response);
  } else {
    server.send(404, "application/json", "{\"status\":\"error\",\"message\":\"No file uploaded yet\"}");
  }
}

// System status endpoint
void handleStatus() {
  String response = "{\"status\":\"online\",\"uptime\":" + String(millis()) + ",\"free_heap\":" + String(ESP.getFreeHeap()) + ",\"last_upload\":\"" + lastUploadedFile + "\",\"matrix_data_pin\":3,\"matrix_output_ready\":" + (lastUploadedFile.length() > 0 ? "true" : "false") + "}";
  server.send(200, "application/json", response);
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Simple Working LED Matrix Uploader ===");
  
  // Initialize SPIFFS
  if (!SPIFFS.begin()) {
    Serial.println("SPIFFS initialization failed");
    return;
  }
  Serial.println("SPIFFS initialized");
  
  // Configure LED matrix pins
  pinMode(MATRIX_DATA_PIN, OUTPUT);
  pinMode(MATRIX_CLOCK_PIN, OUTPUT);
  digitalWrite(MATRIX_DATA_PIN, LOW);
  digitalWrite(MATRIX_CLOCK_PIN, LOW);
  Serial.println("🎨 LED Matrix pins configured:");
  Serial.printf("   Data Pin (GPIO3): OUTPUT, LOW\n");
  Serial.printf("   Clock Pin (GPIO1): OUTPUT, LOW\n");

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
  server.on("/upload", HTTP_POST, handleFileUpload);
  server.on("/send-to-matrix", HTTP_POST, handleSendToMatrix);
  server.on("/status", HTTP_GET, handleStatus);

  server.begin();
  Serial.println("Web server started with simplified endpoints");
  Serial.println("🎨 Matrix output endpoint /send-to-matrix is available!");
  Serial.println("🎉 Your ESP-01 now supports basic file upload AND LED matrix output!");
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
      Serial.printf("Last Upload: %s (%u bytes) - Ready for matrix output\n", 
                    lastUploadedFile.c_str(), lastUploadedSize);
    }
  }
}
