/*
 * WS2812 LED Strip Firmware for ESP-01
 * Uses FastLED library for proper WS2812 timing
 * Compatible with 5V LED strips connected to GPIO3 (RX)
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <LittleFS.h>
#include <FastLED.h>
#include <bearssl/bearssl_hash.h>

// Wi-Fi Access Point credentials - OPEN NETWORK (no password)
const char* apSSID = "WS2812_Uploader";
const char* apPASS = "";  // Empty password = open network

// LED Matrix Configuration
#define LED_PIN 3        // GPIO3 (RX) - your soldered connection
#define NUM_LEDS 64      // Adjust based on your LED strip (8x8 = 64, 16x16 = 256, etc.)
#define BRIGHTNESS 50    // Brightness (0-255)

// Create LED array
CRGB leds[NUM_LEDS];

ESP8266WebServer server(80);

// File storage and hash tracking
String lastUploadedFile = "";
size_t lastUploadedSize = 0;
String lastUploadedHash = "";

// Handle root page - SIMPLIFIED for reliability
void handleRoot() {
  String page = "<html><head><title>WS2812 LED Strip Uploader</title>"
                "<meta charset='utf-8'>"
                "<style>"
                "body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }"
                ".container { max-width: 500px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }"
                "h1 { color: #2c3e50; text-align: center; margin-bottom: 20px; }"
                ".upload-form { border: 2px dashed #3498db; padding: 20px; margin: 20px 0; text-align: center; }"
                ".upload-form input[type='file'] { margin: 10px 0; }"
                ".upload-form input[type='submit'] { background: #3498db; color: white; padding: 10px 25px; border: none; border-radius: 5px; cursor: pointer; }"
                ".status { padding: 10px; margin: 15px 0; border-radius: 5px; }"
                ".success { background-color: #d4edda; color: #155724; }"
                ".info { background-color: #d1ecf1; color: #0c5460; }"
                ".warning { background-color: #fff3cd; color: #856404; }"
                "</style></head>"
                "<body>"
                "<div class='container'>"
                "<h1>🎨 WS2812 LED Strip Uploader</h1>"
                "<p style='text-align: center; color: #7f8c8d;'>Upload LED patterns to your WS2812 strip</p>"
                
                "<div style='background: #fff3cd; border: 1px solid #ffeaa7; padding: 8px; margin: 10px 0; text-align: center;'>"
                "<strong>🔓 OPEN NETWORK:</strong> Connect to 'WS2812_Uploader' without password"
                "</div>"
                
                "<div class='upload-form'>"
                "<h3>📁 Pattern File Upload</h3>"
                "<form method='POST' action='/upload' enctype='multipart/form-data'>"
                "<input type='file' name='file' accept='.bin,.dat,.hex' required><br><br>"
                "<input type='submit' value='Upload Pattern'>"
                "</form>"
                "<p style='font-size: 11px; color: #e74c3c; margin-top: 8px;'>"
                "⚠️  <strong>File Size Limit:</strong> Maximum 32KB for stable operation"
                "</p>"
                "</div>";
  
  // Add upload status if available
  if (lastUploadedFile.length() > 0) {
    page += "<div class='status success'>";
    page += "<h3>📊 Last Upload</h3>";
    page += "<p><strong>File:</strong> " + lastUploadedFile + "</p>";
    page += "<p><strong>Size:</strong> " + String(lastUploadedSize) + " bytes</p>";
    page += "<p><strong>Status:</strong> Ready for LED display</p>";
    page += "</div>";
  } else {
    page += "<div class='status info'>";
    page += "<strong>Status:</strong> Ready for pattern uploads";
    page += "</div>";
  }
  
  page += "<div class='status warning'>";
  page += "<h3>🎨 LED Strip Info</h3>";
  page += "<p><strong>Data Pin:</strong> GPIO3 (RX)</p>";
  page += "<p><strong>LED Count:</strong> " + String(NUM_LEDS) + " LEDs</p>";
  page += "<p><strong>Protocol:</strong> WS2812/NeoPixel</p>";
  page += "</div>";
  
  page += "<div class='status info'>";
  page += "<h3>🔗 Endpoints</h3>";
  page += "<p><strong>GET /</strong> - This page</p>";
  page += "<p><strong>POST /upload</strong> - Upload patterns</p>";
  page += "<p><strong>POST /test-pattern</strong> - Test LED strip</p>";
  page += "<p><strong>GET /status</strong> - System status</p>";
  page += "<p><strong>GET /ping</strong> - Connection test</p>";
  page += "<p><strong>GET /firmware-hash</strong> - Get uploaded file hash</p>";
  page += "</div>";
  
  page += "</div></body></html>";
  
  server.send(200, "text/html", page);
}

// Handle uploaded file with memory optimization
File uploadFile;
#define UPLOAD_BUFFER_SIZE 1024  // Smaller buffer for ESP-01
#define MAX_FILE_SIZE 32768      // 32KB max file size

void handleFileUpload() {
  HTTPUpload& upload = server.upload();
  
  if (upload.status == UPLOAD_FILE_START) {
    String filename = "/" + upload.filename;
    Serial.printf("Upload Start: %s\n", filename.c_str());
    
    // Check file size before starting
    if (upload.totalSize > MAX_FILE_SIZE) {
      Serial.printf("❌ File too large: %u bytes (max: %u)\n", upload.totalSize, MAX_FILE_SIZE);
      server.send(413, "text/plain", "File too large. Maximum size: 32KB");
      return;
    }
    
    // Reset tracking variables
    lastUploadedFile = upload.filename;
    lastUploadedSize = 0;
    lastUploadedHash = "";
    
    // Remove existing file if it exists
    if (LittleFS.exists(filename)) {
      LittleFS.remove(filename);
      Serial.println("Removed existing file");
    }
    
    // Create new file
    uploadFile = LittleFS.open(filename, "w");
    if (uploadFile) {
      Serial.println("File created successfully");
      Serial.printf("📊 Free heap: %u bytes\n", ESP.getFreeHeap());
    } else {
      Serial.println("Failed to create file");
      server.send(500, "text/plain", "Failed to create file");
      return;
    }
    
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    if (uploadFile) {
      size_t bytesWritten = uploadFile.write(upload.buf, upload.currentSize);
      lastUploadedSize += bytesWritten;
      
      // Progress indicator every 1KB with memory status
      if (lastUploadedSize % 1024 == 0) {
        Serial.printf("📤 Upload Progress: %u bytes | Free Heap: %u\n", 
                     lastUploadedSize, ESP.getFreeHeap());
      }
      
      // Check memory periodically
      if (ESP.getFreeHeap() < 5000) {
        Serial.println("⚠️  Low memory warning!");
      }
    }
    
  } else if (upload.status == UPLOAD_FILE_END) {
    if (uploadFile) {
      uploadFile.close();
      Serial.printf("Upload End: %s (%u bytes)\n", upload.filename.c_str(), upload.totalSize);
      Serial.printf("📊 Final free heap: %u bytes\n", ESP.getFreeHeap());
      
      // Calculate hash of uploaded file
      lastUploadedHash = calculateFileHash("/" + lastUploadedFile);
      Serial.printf("File Hash (SHA256): %s\n", lastUploadedHash.c_str());
      
      // Automatically display the pattern
      Serial.println("🎨 Displaying uploaded pattern on LED strip...");
      displayPatternFromFile("/" + lastUploadedFile);
      
      String response = "{\"status\":\"success\",\"message\":\"Pattern uploaded and displayed\",\"file\":\"" + lastUploadedFile + "\",\"size\":" + String(lastUploadedSize) + ",\"hash\":\"" + lastUploadedHash + "\"}";
      server.send(200, "application/json", response);
    }
  }
}

// Calculate SHA256 hash of file
String calculateFileHash(String filePath) {
  File f = LittleFS.open(filePath, "r");
  if (!f) {
    Serial.println("Failed to open file for hash calculation");
    return "";
  }
  
  br_sha256_context sha256_ctx;
  br_sha256_init(&sha256_ctx);
  
  uint8_t buf[512];
  
  while (f.available()) {
    size_t len = f.read(buf, sizeof(buf));
    br_sha256_update(&sha256_ctx, buf, len);
  }
  f.close();
  
  uint8_t hash[32];
  br_sha256_out(&sha256_ctx, hash);
  
  String hashString = "";
  for (int i = 0; i < 32; i++) {
    if (hash[i] < 0x10) hashString += "0";
    hashString += String(hash[i], HEX);
  }
  
  hashString.toUpperCase();
  return hashString;
}

// Display pattern from uploaded file on LED strip
void displayPatternFromFile(String filePath) {
  File f = LittleFS.open(filePath, "r");
  if (!f) {
    Serial.println("⚠️ Failed to open file for LED display");
    return;
  }

  Serial.println("➡️ Displaying pattern on WS2812 LED strip...");
  Serial.printf("📁 File: %s\n", filePath.c_str());
  Serial.printf("📏 Size: %u bytes\n", f.size());
  
  // Clear LEDs first
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  
  // Read file and display pattern
  uint8_t buffer[64];
  
  while (f.available()) {
    size_t bytesRead = f.read(buffer, sizeof(buffer));
    
    for (size_t i = 0; i < bytesRead && i < NUM_LEDS; i++) {
      // Convert byte to LED color (simple mapping)
      uint8_t value = buffer[i];
      leds[i] = CRGB(value, value, value); // Grayscale
    }
    
    FastLED.show();
    delay(50); // Small delay for visibility
  }
  
  f.close();
  
  Serial.printf("✅ Pattern displayed on %u LEDs\n", NUM_LEDS);
  Serial.println("🎉 Your LED strip should now show the uploaded pattern!");
}

// Test pattern endpoint
void handleTestPattern() {
  Serial.println("🧪 Testing LED strip with demo pattern...");
  
  // Create a moving rainbow pattern
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CHSV(i * 256 / NUM_LEDS, 255, 255);
  }
  
  FastLED.show();
  delay(1000);
  
  // Clear
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  
  String response = "{\"status\":\"success\",\"message\":\"Test pattern displayed\",\"leds\":\"" + String(NUM_LEDS) + "\"}";
  server.send(200, "application/json", response);
}

// Manual pattern display endpoint
void handleDisplayPattern() {
  if (lastUploadedFile.length() > 0) {
    Serial.println("🔄 Manual pattern display requested...");
    displayPatternFromFile("/" + lastUploadedFile);
    
    String response = "{\"status\":\"success\",\"message\":\"Pattern displayed\",\"file\":\"" + lastUploadedFile + "\"}";
    server.send(200, "application/json", response);
  } else {
    server.send(404, "application/json", "{\"status\":\"error\",\"message\":\"No pattern uploaded yet\"}");
  }
}

// System status endpoint
void handleStatus() {
  String response = "{\"status\":\"online\",\"uptime\":" + String(millis()) + ",\"free_heap\":" + String(ESP.getFreeHeap()) + ",\"last_upload\":\"" + lastUploadedFile + "\",\"led_count\":" + String(NUM_LEDS) + ",\"data_pin\":3}";
  server.send(200, "application/json", response);
}

// Simple ping endpoint for connection testing
void handlePing() {
  server.send(200, "text/plain", "pong");
}

// Firmware hash endpoint for verification
void handleFirmwareHash() {
  if (lastUploadedFile.length() > 0) {
    String response = "{\"status\":\"success\",\"file\":\"" + lastUploadedFile + "\",\"size\":" + String(lastUploadedSize) + ",\"hash\":\"" + lastUploadedHash + "\"}";
    server.send(200, "application/json", response);
  } else {
    server.send(404, "application/json", "{\"status\":\"error\",\"message\":\"No firmware uploaded yet\"}");
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== WS2812 LED Strip Uploader ===");
  
  // Initialize LittleFS
  if (!LittleFS.begin()) {
    Serial.println("LittleFS initialization failed");
    return;
  }
  Serial.println("LittleFS initialized");
  
  // Initialize FastLED
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.clear();
  FastLED.show();
  
  Serial.println("🎨 WS2812 LED strip initialized:");
  Serial.printf("   Data Pin: GPIO3 (RX)\n");
  Serial.printf("   LED Count: %u\n", NUM_LEDS);
  Serial.printf("   Brightness: %u\n", BRIGHTNESS);
  Serial.println("   Protocol: WS2812/NeoPixel");

  // Start Wi-Fi AP (OPEN NETWORK - no password)
  WiFi.softAP(apSSID, apPASS);
  Serial.println("WiFi AP Started (OPEN NETWORK)");
  Serial.print("SSID: ");
  Serial.println(apSSID);
  Serial.print("Password: ");
  Serial.println(strlen(apPASS) > 0 ? apPASS : "NONE (Open Network)");
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());
  Serial.println("Go to http://192.168.4.1/");
  Serial.println("⚠️  WARNING: This is an OPEN network - anyone can connect!");

  // Setup web server routes
  server.on("/", HTTP_GET, handleRoot);
  server.on(
    "/upload",
    HTTP_POST,
    []() { server.send(200, "text/plain", "Upload complete"); },
    handleFileUpload
  );
  server.on("/display-pattern", HTTP_POST, handleDisplayPattern);
  server.on("/test-pattern", HTTP_POST, handleTestPattern);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/ping", HTTP_GET, handlePing);
  server.on("/firmware-hash", HTTP_GET, handleFirmwareHash);

  server.begin();
  Serial.println("Web server started with WS2812 endpoints");
  Serial.println("🎨 LED strip test endpoint /test-pattern is available!");
  Serial.println("🎉 Your ESP-01 now supports WS2812 LED strip control!");
  
  // Show startup pattern
  Serial.println("🚀 Showing startup pattern...");
  fill_solid(leds, NUM_LEDS, CRGB::Blue);
  FastLED.show();
  delay(1000);
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
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
      Serial.printf("Last Upload: %s (%u bytes) - Ready for LED display\n", 
                    lastUploadedFile.c_str(), lastUploadedSize);
    }
  }
}
