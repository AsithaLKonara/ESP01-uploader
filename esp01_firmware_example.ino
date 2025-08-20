/*
 * ESP-01 WiFi OTA Firmware
 * Provides WiFi Access Point and OTA (Over-The-Air) firmware update capability
 * 
 * Features:
 * - WiFi Access Point mode
 * - ArduinoOTA for firmware updates
 * - Basic status endpoints
 * - LED status indication
 * 
 * Upload this sketch via USB first, then use OTA for future updates
 */

#include <ESP8266WiFi.h>
#include <ArduinoOTA.h>
#include <ESP8266WebServer.h>
#include <ArduinoJson.h>
#include <FS.h>

// WiFi Configuration
const char* ssid = "ESP01_AP";
const char* password = "12345678";

// Pin Configuration
const int STATUS_LED = 2;  // Built-in LED on ESP-01
const int OTA_LED = 0;     // GPIO0 (if available)

// Web Server
ESP8266WebServer server(80);

// OTA Configuration
const int OTA_PORT = 8266;

// Status variables
bool otaInProgress = false;
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 5000; // 5 seconds

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.println("\n\n=== ESP-01 WiFi OTA Firmware ===");
  
  // Initialize pins
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, HIGH); // Turn off (ESP-01 LED is active low)
  
  if (OTA_LED != STATUS_LED) {
    pinMode(OTA_LED, OUTPUT);
    digitalWrite(OTA_LED, LOW);
  }
  
  // Initialize file system
  if (!SPIFFS.begin()) {
    Serial.println("SPIFFS initialization failed");
  } else {
    Serial.println("SPIFFS initialized successfully");
  }
  
  // Setup WiFi Access Point
  setupWiFiAP();
  
  // Setup ArduinoOTA
  setupArduinoOTA();
  
  // Setup web server
  setupWebServer();
  
  // Start web server
  server.begin();
  Serial.println("Web server started on port 80");
  
  // Initial status
  Serial.println("ESP-01 ready for OTA updates!");
  Serial.printf("Connect to WiFi: %s (Password: %s)\n", ssid, password);
  Serial.printf("OTA Port: %d\n", OTA_PORT);
  Serial.printf("Web Interface: http://%s\n", WiFi.softAPIP().toString().c_str());
  
  // Blink LED to indicate ready
  blinkLED(STATUS_LED, 3, 200);
}

void loop() {
  // Handle OTA updates
  ArduinoOTA.handle();
  
  // Handle web server requests
  server.handleClient();
  
  // Handle periodic tasks
  handlePeriodicTasks();
  
  // Yield to prevent watchdog reset
  yield();
}

void setupWiFiAP() {
  Serial.println("Setting up WiFi Access Point...");
  
  // Configure WiFi mode
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ssid, password);
  
  // Wait for AP to start
  delay(1000);
  
  // Get AP IP address
  IPAddress apIP = WiFi.softAPIP();
  Serial.printf("WiFi AP started: %s\n", apIP.toString().c_str());
  Serial.printf("SSID: %s\n", ssid);
  Serial.printf("Password: %s\n", password);
  
  // Blink LED to indicate WiFi ready
  blinkLED(STATUS_LED, 2, 100);
}

void setupArduinoOTA() {
  Serial.println("Setting up ArduinoOTA...");
  
  // Set OTA port
  ArduinoOTA.setPort(OTA_PORT);
  
  // Set hostname
  ArduinoOTA.setHostname("ESP01_Device");
  
  // Set password (optional)
  // ArduinoOTA.setPassword("admin");
  
  // Set OTA callbacks
  ArduinoOTA.onStart([]() {
    Serial.println("OTA Update Started");
    otaInProgress = true;
    
    // Turn on OTA LED
    if (OTA_LED != STATUS_LED) {
      digitalWrite(OTA_LED, HIGH);
    }
    
    // Blink status LED rapidly
    digitalWrite(STATUS_LED, LOW);
  });
  
  ArduinoOTA.onEnd([]() {
    Serial.println("OTA Update Completed");
    otaInProgress = false;
    
    // Turn off OTA LED
    if (OTA_LED != STATUS_LED) {
      digitalWrite(OTA_LED, LOW);
    }
    
    // Blink status LED to indicate completion
    blinkLED(STATUS_LED, 5, 100);
  });
  
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    int percent = (progress / (total / 100));
    Serial.printf("OTA Progress: %u%%\r", percent);
    
    // Blink status LED during progress
    if (percent % 10 == 0) {
      digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
    }
  });
  
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("OTA Error[%u]: ", error);
    otaInProgress = false;
    
    // Turn off OTA LED
    if (OTA_LED != STATUS_LED) {
      digitalWrite(OTA_LED, LOW);
    }
    
    // Rapid blink to indicate error
    blinkLED(STATUS_LED, 10, 100);
    
    switch (error) {
      case OTA_AUTH_ERROR:
        Serial.println("Auth Failed");
        break;
      case OTA_BEGIN_ERROR:
        Serial.println("Begin Failed");
        break;
      case OTA_CONNECT_ERROR:
        Serial.println("Connect Failed");
        break;
      case OTA_RECEIVE_ERROR:
        Serial.println("Receive Failed");
        break;
      case OTA_END_ERROR:
        Serial.println("End Failed");
        break;
    }
  });
  
  // Start ArduinoOTA
  ArduinoOTA.begin();
  Serial.println("ArduinoOTA initialized successfully");
}

void setupWebServer() {
  Serial.println("Setting up web server...");
  
  // Root endpoint - status page
  server.on("/", HTTP_GET, []() {
    String html = generateStatusPage();
    server.send(200, "text/html", html);
  });
  
  // Status endpoint - JSON API
  server.on("/status", HTTP_GET, []() {
    DynamicJsonDocument doc(512);
    doc["status"] = "ok";
    doc["device"] = "ESP-01";
    doc["uptime"] = millis() / 1000;
    doc["free_heap"] = ESP.getFreeHeap();
    doc["ota_in_progress"] = otaInProgress;
    doc["wifi_connected"] = WiFi.softAPgetStationNum();
    doc["ip_address"] = WiFi.softAPIP().toString();
    doc["ota_port"] = OTA_PORT;
    
    String response;
    serializeJson(doc, response);
    server.send(200, "application/json", response);
  });
  
  // Memory info endpoint
  server.on("/memory", HTTP_GET, []() {
    DynamicJsonDocument doc(256);
    doc["free_heap"] = ESP.getFreeHeap();
    doc["heap_fragmentation"] = ESP.getHeapFragmentation();
    doc["max_alloc_heap"] = ESP.getMaxAllocHeap();
    doc["free_sketch_space"] = ESP.getFreeSketchSpace();
    
    String response;
    serializeJson(doc, response);
    server.send(200, "application/json", response);
  });
  
  // Device info endpoint
  server.on("/info", HTTP_GET, []() {
    DynamicJsonDocument doc(512);
    doc["chip_id"] = ESP.getChipId();
    doc["flash_chip_id"] = ESP.getFlashChipId();
    doc["flash_chip_size"] = ESP.getFlashChipSize();
    doc["sdk_version"] = ESP.getSdkVersion();
    doc["core_version"] = ESP.getCoreVersion();
    doc["cpu_freq"] = ESP.getCpuFreqMHz();
    doc["cycle_count"] = ESP.getCycleCount();
    
    String response;
    serializeJson(doc, response);
    server.send(200, "application/json", response);
  });
  
  // Ping endpoint
  server.on("/ping", HTTP_GET, []() {
    server.send(200, "text/plain", "pong");
  });
  
  // Reset endpoint
  server.on("/reset", HTTP_POST, []() {
    server.send(200, "text/plain", "Resetting...");
    delay(1000);
    ESP.restart();
  });
  
  // 404 handler
  server.onNotFound([]() {
    server.send(404, "text/plain", "Not Found");
  });
  
  Serial.println("Web server routes configured");
}

void handlePeriodicTasks() {
  unsigned long currentTime = millis();
  
  // Handle heartbeat
  if (currentTime - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    lastHeartbeat = currentTime;
    
    // Blink status LED to show activity
    if (!otaInProgress) {
      digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
      delay(50);
      digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
    }
    
    // Print status every 30 seconds
    static int heartbeatCount = 0;
    if (++heartbeatCount >= 6) { // 6 * 5 seconds = 30 seconds
      heartbeatCount = 0;
      Serial.printf("Status: Uptime=%lus, FreeHeap=%u, Connected=%d\n", 
                   millis() / 1000, ESP.getFreeHeap(), WiFi.softAPgetStationNum());
    }
  }
}

String generateStatusPage() {
  String html = R"(
<!DOCTYPE html>
<html>
<head>
    <title>ESP-01 Status</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; border-bottom: 2px solid #007cba; padding-bottom: 10px; margin-bottom: 20px; }
        .status-item { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #eee; }
        .status-label { font-weight: bold; color: #555; }
        .status-value { color: #007cba; }
        .ota-section { background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .button:hover { background: #005a8b; }
        .warning { color: #d63384; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ESP-01 WiFi OTA Firmware</h1>
            <p>Device Status & Information</p>
        </div>
        
        <div class="ota-section">
            <h3>📡 OTA (Over-The-Air) Update</h3>
            <p><strong>Status:</strong> <span id="ota-status">Checking...</span></p>
            <p><strong>Port:</strong> )" + String(OTA_PORT) + R"(</p>
            <p class="warning">⚠️ Use Arduino IDE or compatible OTA tool to upload firmware</p>
        </div>
        
        <div id="status-content">
            <h3>📊 Device Status</h3>
            <div class="status-item">
                <span class="status-label">Device:</span>
                <span class="status-value" id="device">ESP-01</span>
            </div>
            <div class="status-item">
                <span class="status-label">Uptime:</span>
                <span class="status-value" id="uptime">-</span>
            </div>
            <div class="status-item">
                <span class="status-label">Free Memory:</span>
                <span class="status-value" id="memory">-</span>
            </div>
            <div class="status-item">
                <span class="status-label">WiFi Clients:</span>
                <span class="status-value" id="clients">-</span>
            </div>
            <div class="status-item">
                <span class="status-label">IP Address:</span>
                <span class="status-value" id="ip">)" + WiFi.softAPIP().toString() + R"(</span>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 20px;">
            <button class="button" onclick="refreshStatus()">🔄 Refresh Status</button>
            <button class="button" onclick="resetDevice()">🔄 Reset Device</button>
        </div>
    </div>
    
    <script>
        function refreshStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('uptime').textContent = data.uptime + 's';
                    document.getElementById('memory').textContent = data.free_heap + ' bytes';
                    document.getElementById('clients').textContent = data.wifi_connected;
                    document.getElementById('ota-status').textContent = data.ota_in_progress ? 'Update in Progress' : 'Ready';
                })
                .catch(error => console.error('Error:', error));
        }
        
        function resetDevice() {
            if (confirm('Are you sure you want to reset the device?')) {
                fetch('/reset', {method: 'POST'})
                    .then(() => {
                        alert('Device is resetting...');
                        setTimeout(() => location.reload(), 3000);
                    });
            }
        }
        
        // Auto-refresh every 5 seconds
        setInterval(refreshStatus, 5000);
        refreshStatus(); // Initial load
    </script>
</body>
</html>
)";
  
  return html;
}

void blinkLED(int pin, int count, int delayMs) {
  for (int i = 0; i < count; i++) {
    digitalWrite(pin, !digitalRead(pin));
    delay(delayMs);
    digitalWrite(pin, !digitalRead(pin));
    if (i < count - 1) delay(delayMs);
  }
}
