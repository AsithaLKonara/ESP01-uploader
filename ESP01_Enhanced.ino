/*
 * Enhanced ESP-01 LED Matrix Firmware
 * Features: File storage, hash verification, system monitoring, comprehensive diagnostics
 * Target: ESP-01 with 1MB flash (32KB usable for files)
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <LittleFS.h>
#include <WiFiManager.h>
// #include <ESP8266HTTPUpdate.h>  // Removed - not available in this Arduino environment
// #include <Hash.h> // SHA1 not available - using alternative implementation
// ArduinoJson removed - using simple string responses

// Function declarations for forward reference
void handleRoot();
void handleFileUpload();
void handleUploadSuccess();
void handleSystemInfo();
void handleFileSystemInfo();
void handleFirmwareHash();
void handleFileDownload();
void handleFileDelete();
void handleTestWrite();
void handlePing();
void handleHealth();
void handleLEDControl();
void handleWiFiConfig();
void handleSystemReset();
void handleFileList();
void handleFileInfo();
void handlePerformance();
void handleMetadataUpload();
void handleDiagnostic();           // NEW: Comprehensive diagnostic endpoint
void handleErrorLog();             // NEW: Error log endpoint
void handleSystemTest();           // NEW: System test endpoint
void handleEndpointTest();         // NEW: Endpoint availability test
bool checkUploadToken();
void setupWebServer();
void loadConfiguration();
String calculateFileHash(File& file);
int countFiles();
void outputLEDMatrixData();
void parseMetadata();
void ledPlaybackTick();
void hmac_sha1_hex(const char* key, const char* msg, char *outHex);
bool verify_upload_token(const String &tokenHdr);

// NEW: Enhanced error reporting and diagnostics
void logError(const String& component, const String& operation, const String& error, int errorCode = 0);
void logWarning(const String& component, const String& operation, const String& message);
void logInfo(const String& component, const String& operation, const String& message);
String getSystemDiagnostics();
String getErrorSummary();
String getEndpointStatus();
String getMemoryStatus();
String getWiFiStatus();
String getFileSystemStatus();

// WiFi Configuration
const char* ssid = "MatrixUploader";
const char* password = "";
bool wifiConnected = false;
WiFiManager wifiManager;

// Security Configuration - Simplified (OTA removed)
// const char* adminPassword = "admin123"; // Change this in production
// bool authenticationEnabled = true;

// Token rotation config
const unsigned long TOKEN_TTL_SECONDS = 90; // token valid for 90s
const char* TOKEN_SECRET = "change_this_secret"; // same secret must be used by uploader

// LED Matrix Control
bool ledPlaying = false;
bool ledPaused = false;
unsigned long lastFrameTime = 0;
unsigned int frameDelayMs = 100; // Default frame delay
unsigned int currentFrameIndex = 0;
unsigned int totalFrames = 0;

// Per-chunk delays - we store as dynamic array (allocated when metadata parsed)
unsigned int *perChunkDelays = NULL;
size_t perChunkDelaysCount = 0;

// Web Server
ESP8266WebServer server(80);

// File Management
const char* UPLOAD_FILE = "/temp_export_data.bin";
const char* CONFIG_FILE = "/config.json";

// System Status
unsigned long lastUploadTime = 0;
size_t lastUploadedSize = 0;
String lastUploadedHash = "";

// NEW: Enhanced system monitoring and error tracking
unsigned long systemStartTime = 0;
unsigned long lastErrorTime = 0;
unsigned int errorCount = 0;
unsigned int warningCount = 0;
unsigned int infoCount = 0;

// NEW: Error log storage (circular buffer)
#define MAX_ERROR_LOG_ENTRIES 20
struct ErrorLogEntry {
  String timestamp;
  String level;
  String component;
  String operation;
  String message;
  int errorCode;
  unsigned long freeHeap;
};
ErrorLogEntry errorLog[MAX_ERROR_LOG_ENTRIES];
int errorLogIndex = 0;
int errorLogCount = 0;

// Upload buffer for better stability
#define UPLOAD_BUFFER_SIZE 512  // Reduced buffer size for ESP-01
static File uploadFile;
static bool uploadInProgress = false;
static unsigned long uploadStartTime = 0;

// NEW: Enhanced error reporting and diagnostics - MOVED BEFORE setup()
void logError(const String& component, const String& operation, const String& error, int errorCode) {
  if (errorLogCount >= MAX_ERROR_LOG_ENTRIES) {
    // Circular buffer, overwrite oldest
    for (int i = 0; i < MAX_ERROR_LOG_ENTRIES - 1; i++) {
      errorLog[i] = errorLog[i + 1];
    }
    errorLogIndex = MAX_ERROR_LOG_ENTRIES - 1;
  } else {
    errorLogIndex = errorLogCount;
  }

  errorLog[errorLogIndex].timestamp = String(millis() / 1000) + "s";
  errorLog[errorLogIndex].level = "ERROR";
  errorLog[errorLogIndex].component = component;
  errorLog[errorLogIndex].operation = operation;
  errorLog[errorLogIndex].message = error;
  errorLog[errorLogIndex].errorCode = errorCode;
  errorLog[errorLogIndex].freeHeap = ESP.getFreeHeap();

  errorCount++;
  errorLogCount++;
  errorLogIndex = (errorLogIndex + 1) % MAX_ERROR_LOG_ENTRIES;
  Serial.printf("ERROR: [%s] %s - %s (Code: %d, Heap: %d)\n", 
                errorLog[errorLogIndex].timestamp.c_str(), 
                errorLog[errorLogIndex].level.c_str(), 
                errorLog[errorLogIndex].message.c_str(), 
                errorLog[errorLogIndex].errorCode, 
                errorLog[errorLogIndex].freeHeap);
}

void logWarning(const String& component, const String& operation, const String& message) {
  if (errorLogCount >= MAX_ERROR_LOG_ENTRIES) {
    // Circular buffer, overwrite oldest
    for (int i = 0; i < MAX_ERROR_LOG_ENTRIES - 1; i++) {
      errorLog[i] = errorLog[i + 1];
    }
    errorLogIndex = MAX_ERROR_LOG_ENTRIES - 1;
  } else {
    errorLogIndex = errorLogCount;
  }

  errorLog[errorLogIndex].timestamp = String(millis() / 1000) + "s";
  errorLog[errorLogIndex].level = "WARNING";
  errorLog[errorLogIndex].component = component;
  errorLog[errorLogIndex].operation = operation;
  errorLog[errorLogIndex].message = message;
  errorLog[errorLogIndex].errorCode = 0; // No specific error code for warnings
  errorLog[errorLogIndex].freeHeap = ESP.getFreeHeap();

  warningCount++;
  errorLogCount++;
  errorLogIndex = (errorLogIndex + 1) % MAX_ERROR_LOG_ENTRIES;
  Serial.printf("WARNING: [%s] %s - %s (Heap: %d)\n", 
                errorLog[errorLogIndex].timestamp.c_str(), 
                errorLog[errorLogIndex].level.c_str(), 
                errorLog[errorLogIndex].message.c_str(), 
                errorLog[errorLogIndex].freeHeap);
}

void logInfo(const String& component, const String& operation, const String& message) {
  if (errorLogCount >= MAX_ERROR_LOG_ENTRIES) {
    // Circular buffer, overwrite oldest
    for (int i = 0; i < MAX_ERROR_LOG_ENTRIES - 1; i++) {
      errorLog[i] = errorLog[i + 1];
    }
    errorLogIndex = MAX_ERROR_LOG_ENTRIES - 1;
  } else {
    errorLogIndex = errorLogCount;
  }

  errorLog[errorLogIndex].timestamp = String(millis() / 1000) + "s";
  errorLog[errorLogIndex].level = "INFO";
  errorLog[errorLogIndex].component = component;
  errorLog[errorLogIndex].operation = operation;
  errorLog[errorLogIndex].message = message;
  errorLog[errorLogIndex].errorCode = 0;
  errorLog[errorLogIndex].freeHeap = ESP.getFreeHeap();

  infoCount++;
  errorLogCount++;
  errorLogIndex = (errorLogIndex + 1) % MAX_ERROR_LOG_ENTRIES;
  Serial.printf("INFO: [%s] %s - %s (Heap: %d)\n", 
                errorLog[errorLogIndex].timestamp.c_str(), 
                errorLog[errorLogIndex].level.c_str(), 
                errorLog[errorLogIndex].message.c_str(), 
                errorLog[errorLogIndex].freeHeap);
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n\n=== Enhanced ESP-01 LED Matrix Firmware ===");
  
  // Initialize system monitoring
  systemStartTime = millis();
  logInfo("SYSTEM", "SETUP", "Firmware initialization started");
  
  // Initialize LittleFS
  Serial.println("Initializing LittleFS...");
  if (!LittleFS.begin()) {
    String errorMsg = "LittleFS initialization failed!";
    Serial.println("ERROR: " + errorMsg);
    logError("FILESYSTEM", "INIT", errorMsg, 1001);
    return;
  }
  Serial.println("LittleFS initialized successfully");
  logInfo("FILESYSTEM", "INIT", "LittleFS initialized successfully");
  
  // Check file system info
  FSInfo fs_info;
  LittleFS.info(fs_info);
  Serial.printf("Total space: %d bytes\n", fs_info.totalBytes);
  Serial.printf("Used space: %d bytes\n", fs_info.usedBytes);
  Serial.printf("Free space: %d bytes\n", fs_info.totalBytes - fs_info.usedBytes);
  
  // Log file system status
  if (fs_info.totalBytes - fs_info.usedBytes < 1024) {
    logWarning("FILESYSTEM", "SPACE", "Low storage space available");
  }
  
  // Setup WiFi with fallback to AP mode
  Serial.println("Setting up WiFi...");
  logInfo("WIFI", "SETUP", "WiFi setup started");
  
  // Try to connect to existing WiFi first
  wifiManager.setConfigPortalTimeout(180); // 3 minutes timeout
  wifiManager.setAPCallback([](WiFiManager *myWiFiManager) {
    Serial.println("Entered config mode");
    Serial.println(WiFi.softAPIP());
  });
  
  if (wifiManager.autoConnect(ssid, password)) {
    Serial.println("WiFi connected successfully");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    wifiConnected = true;
    logInfo("WIFI", "CONNECT", "WiFi connected successfully to " + WiFi.SSID());
  } else {
    Serial.println("Failed to connect to WiFi, starting AP mode");
    logWarning("WIFI", "CONNECT", "Failed to connect to WiFi, starting AP mode");
    WiFi.mode(WIFI_AP);
    WiFi.softAPConfig(IPAddress(192,168,4,1), IPAddress(192,168,4,1), IPAddress(255,255,255,0));
  WiFi.softAP(ssid, password);
    delay(1000);
  Serial.println("WiFi AP Started");
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());
    wifiConnected = false;
    logInfo("WIFI", "AP_MODE", "WiFi AP started: " + String(ssid));
  }
  
  // Load saved configuration
  logInfo("CONFIG", "LOAD", "Loading configuration...");
  loadConfiguration();
  
  // Setup Web Server Routes
  logInfo("WEBSERVER", "SETUP", "Setting up web server routes...");
  setupWebServer();
  
  // Initialize diagnostic system
  logInfo("DIAGNOSTIC", "INIT", "Diagnostic system initialized");
  
  // Initialize error counters
  errorCount = 0;
  warningCount = 0;
  infoCount = 0;
  
  Serial.println("Enhanced ESP-01 LED Matrix Firmware Ready!");
  Serial.println("===========================================");
  logInfo("SYSTEM", "SETUP", "Firmware initialization completed successfully");
}

void setupWebServer() {
  // Main page
  server.on("/", HTTP_GET, handleRoot);
  
  // File upload endpoint
  server.on("/upload", HTTP_POST, handleUploadSuccess, handleFileUpload);
  
  // System information
  server.on("/system-info", HTTP_GET, handleSystemInfo);
  
  // File system information
  server.on("/fs-info", HTTP_GET, handleFileSystemInfo);
  
  // Firmware hash verification
  server.on("/firmware-hash", HTTP_GET, handleFirmwareHash);
  
  // File download
  server.on("/download", HTTP_GET, handleFileDownload);
  
  // Delete file
  server.on("/delete", HTTP_POST, handleFileDelete);
  
  // Test endpoint for debugging
  server.on("/test-write", HTTP_GET, handleTestWrite);
  
  // Connection test endpoint
  server.on("/ping", HTTP_GET, handlePing);
  
  // Health check endpoint
  server.on("/health", HTTP_GET, handleHealth);
  
  // Enhanced LED Matrix Control
  server.on("/led-control", HTTP_GET, handleLEDControl);
  
  // WiFi Configuration Management
  server.on("/wifi-config", HTTP_GET, handleWiFiConfig);
  server.on("/wifi-config", HTTP_POST, handleWiFiConfig);
  
  // System Reset and Maintenance
  server.on("/system-reset", HTTP_POST, handleSystemReset);
  
  // Advanced File Management
  server.on("/file-list", HTTP_GET, handleFileList);
  server.on("/file-info", HTTP_GET, handleFileInfo);
  
  // Performance Monitoring
  server.on("/performance", HTTP_GET, handlePerformance);
  
  // OTA Update (secure endpoint)
  // server.on("/ota-update", HTTP_POST, handleOTAUpdate);  // OTA disabled - missing library
  
  // Metadata upload endpoint
  server.on("/upload-metadata", HTTP_POST, handleMetadataUpload);
  
  // Diagnostic endpoints
  server.on("/diagnostic", HTTP_GET, handleDiagnostic);
  server.on("/error-log", HTTP_GET, handleErrorLog);
  server.on("/system-test", HTTP_GET, handleSystemTest);
  server.on("/endpoint-test", HTTP_GET, handleEndpointTest);
  
  // Start server with increased buffer size
  server.begin();
}

void handleRoot() {
  String html = "<!DOCTYPE html><html><head>";
  html += "<title>Enhanced LED Matrix Uploader</title>";
  html += "<meta charset=\"utf-8\">";
  html += "<style>";
  html += "body { font-family: Arial, sans-serif; margin: 20px; }";
  html += ".container { max-width: 600px; margin: 0 auto; }";
  html += ".status { padding: 10px; margin: 10px 0; border-radius: 5px; }";
  html += ".success { background-color: #d4edda; color: #155724; }";
  html += ".warning { background-color: #fff3cd; color: #856404; }";
  html += ".error { background-color: #f8d7da; color: #721c24; }";
  html += ".info { background-color: #d1ecf1; color: #0c5460; }";
  html += ".upload-form { border: 2px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; }";
  html += ".progress { width: 100%; height: 20px; background-color: #f0f0f0; border-radius: 10px; overflow: hidden; }";
  html += ".progress-bar { height: 100%; background-color: #4CAF50; width: 0%; transition: width 0.3s; }";
  html += "button { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }";
  html += "button:hover { background-color: #45a049; }";
  html += "input[type=\"file\"] { margin: 10px 0; }";
  html += "</style></head><body>";
  html += "<div class=\"container\">";
  html += "<h1>Enhanced LED Matrix Uploader</h1>";
  html += "<div class=\"status success\"><strong>Status:</strong> Ready for file upload</div>";
  html += "<div class=\"upload-form\">";
  html += "<h3>Upload LED Matrix Data</h3>";
  html += "<form id=\"uploadForm\" enctype=\"multipart/form-data\">";
  html += "<input type=\"file\" id=\"fileInput\" name=\"file\" accept=\".bin,.txt,.hex\" required><br>";
  html += "<button type=\"submit\">Upload File</button>";
  html += "</form>";
  html += "<div class=\"progress\" style=\"display: none;\"><div class=\"progress-bar\"></div></div>";
  html += "<div id=\"uploadStatus\"></div>";
  html += "</div>";
  html += "<div class=\"status warning\"><strong>Important:</strong> Maximum file size: 64KB for ESP-01 compatibility (recommended: 32KB for stability)</div>";
  
  // Enhanced diagnostic section
  html += "<h3>🔍 System Diagnostics</h3>";
  html += "<div class=\"status info\">";
  html += "<strong>Diagnostic Tools:</strong> ";
  html += "<button onclick=\"runDiagnostic()\">Run Full Diagnostic</button> ";
  html += "<button onclick=\"checkErrorLog()\">View Error Log</button> ";
  html += "<button onclick=\"testEndpoints()\">Test Endpoints</button>";
  html += "</div>";
  html += "<div id=\"diagnosticResults\"></div>";
  
  html += "<h3>📊 System Information</h3>";
  html += "<div id=\"systemInfo\">Loading...</div>";
  html += "<h3>File System</h3>";
  html += "<div id=\"fileSystemInfo\">Loading...</div>";
  html += "<h3>Current File</h3>";
  html += "<div id=\"currentFile\">Loading...</div>";
  html += "<div style=\"margin-top: 20px;\">";
  html += "<button onclick=\"refreshInfo()\">Refresh Info</button>";
  html += "<button onclick=\"downloadFile()\" id=\"downloadBtn\" style=\"display: none;\">Download File</button>";
  html += "<button onclick=\"deleteFile()\" id=\"deleteBtn\" style=\"display: none;\">Delete File</button>";
  html += "</div>";
  
  // Enhanced LED Matrix Control Section
  html += "<h3>LED Matrix Control</h3>";
  html += "<div style=\"margin: 10px 0;\">";
  html += "<button onclick=\"ledControl('play')\">Play Animation</button>";
  html += "<button onclick=\"ledControl('pause')\">Pause</button>";
  html += "<button onclick=\"ledControl('stop')\">Stop</button>";
  html += "<button onclick=\"ledControl('status')\">Status</button>";
  html += "</div>";
  html += "<div style=\"margin: 10px 0;\">";
  html += "<label>Frame Delay (ms): </label>";
  html += "<input type=\"number\" id=\"frameDelayInput\" min=\"10\" max=\"10000\" value=\"100\" style=\"width: 80px; margin-right: 10px;\">";
  html += "<button onclick=\"setFrameDelay()\">Set Delay</button>";
  html += "</div>";
  html += "<div style=\"margin: 10px 0;\">";
  html += "<label>Brightness: </label>";
  html += "<input type=\"range\" id=\"brightnessSlider\" min=\"0\" max=\"255\" value=\"128\" onchange=\"setBrightness(this.value)\">";
  html += "<span id=\"brightnessValue\">128</span>";
  html += "</div>";
  html += "<div id=\"ledStatus\" style=\"margin: 10px 0; padding: 10px; background-color: #f0f0f0; border-radius: 5px;\">LED Status: Stopped</div>";
  
  // WiFi Configuration Section
  html += "<h3>WiFi Configuration</h3>";
  html += "<div id=\"wifiStatus\">Loading...</div>";
  html += "<div style=\"margin: 10px 0;\">";
  html += "<input type=\"text\" id=\"newSSID\" placeholder=\"WiFi SSID\" style=\"margin-right: 10px;\">";
  html += "<input type=\"password\" id=\"newPassword\" placeholder=\"WiFi Password\" style=\"margin-right: 10px;\">";
  html += "<button onclick=\"saveWiFiConfig()\">Save WiFi</button>";
  html += "</div>";
  
  // System Management Section
  html += "<h3>System Management</h3>";
  html += "<div style=\"margin: 10px 0;\">";
  html += "<button onclick=\"systemReset('wifi')\">Reset WiFi</button>";
  html += "<button onclick=\"systemReset('filesystem')\">Clear Files</button>";
  html += "<button onclick=\"systemReset('full')\">Full Reset</button>";
  html += "</div>";
  
  // Performance Monitoring Section
  html += "<h3>Performance Monitor</h3>";
  html += "<div id=\"performanceInfo\">Loading...</div>";
  html += "<button onclick=\"refreshPerformance()\">Refresh Performance</button>";
  
  // Metadata Upload Section
  html += "<h3>Animation Metadata</h3>";
  html += "<div style=\"margin: 10px 0;\">";
  html += "<textarea id=\"metadataInput\" placeholder=\"Enter JSON metadata (frame_delay_ms, total_frames, per_chunk_delays)\" style=\"width: 100%; height: 80px; margin-bottom: 10px;\"></textarea>";
  html += "<button onclick=\"uploadMetadata()\">Upload Metadata</button>";
  html += "</div>";
  
  // OTA Update Section - DISABLED due to missing library
  // html += "<h3>OTA Update</h3>";
  // html += "<div style=\"margin: 10px 0;\">";
  // html += "<input type=\"text\" id=\"updateURL\" placeholder=\"Firmware Update URL\" style=\"width: 300px; margin-right: 10px;\">";
  // html += "<button onclick=\"startOTAUpdate()\">Start Update</button>";
  // html += "</div>";
  // html += "<div class=\"status warning\"><strong>Warning:</strong> OTA updates will restart the device</div>";
  html += "</div>";
  html += "<script>";
  html += "document.getElementById('uploadForm').addEventListener('submit', function(e) {";
  html += "e.preventDefault();";
  html += "const fileInput = document.getElementById('fileInput');";
  html += "const file = fileInput.files[0];";
  html += "if (!file) { alert('Please select a file'); return; }";
  html += "if (file.size > 65536) { alert('File too large! Maximum size is 64KB for ESP-01 compatibility.'); return; }";
  html += "uploadFile(file);";
  html += "});";
  html += "function uploadFile(file) {";
  html += "const formData = new FormData();";
  html += "formData.append('file', file);";
  html += "const progressBar = document.querySelector('.progress-bar');";
  html += "const progressDiv = document.querySelector('.progress');";
  html += "const statusDiv = document.getElementById('uploadStatus');";
  html += "progressDiv.style.display = 'block';";
  html += "statusDiv.innerHTML = 'Uploading...';";
  html += "const xhr = new XMLHttpRequest();";
  html += "xhr.upload.addEventListener('progress', function(e) {";
  html += "if (e.lengthComputable) {";
  html += "const percentComplete = (e.loaded / e.total) * 100;";
  html += "progressBar.style.width = percentComplete + '%';";
  html += "}";
  html += "});";
  html += "xhr.addEventListener('load', function() {";
  html += "if (xhr.status === 200) {";
  html += "statusDiv.innerHTML = '<span style=\"color: green;\">Upload successful!</span>';";
  html += "setTimeout(refreshInfo, 1000);";
  html += "} else {";
  html += "statusDiv.innerHTML = '<span style=\"color: red;\">Upload failed: ' + xhr.statusText + '</span>';";
  html += "}";
  html += "progressDiv.style.display = 'none';";
  html += "});";
  html += "xhr.addEventListener('error', function() {";
  html += "statusDiv.innerHTML = '<span style=\"color: red;\">Upload failed</span>';";
  html += "progressDiv.style.display = 'none';";
  html += "});";
  html += "xhr.open('POST', '/upload');";
  html += "xhr.send(formData);";
  html += "}";
  html += "function refreshInfo() {";
  html += "fetch('/system-info').then(response => response.json()).then(data => {";
  html += "document.getElementById('systemInfo').innerHTML = '<strong>Status:</strong> ' + data.status + '<br>' + '<strong>Free Heap:</strong> ' + data.free_heap + ' bytes<br>' + '<strong>Flash Size:</strong> ' + data.flash_size + ' bytes<br>' + '<strong>Last Upload:</strong> ' + data.last_upload;";
  html += "});";
  html += "fetch('/fs-info').then(response => response.json()).then(data => {";
  html += "document.getElementById('fileSystemInfo').innerHTML = '<strong>Total Space:</strong> ' + data.total_bytes + ' bytes<br>' + '<strong>Used Space:</strong> ' + data.used_bytes + ' bytes<br>' + '<strong>Free Space:</strong> ' + data.free_bytes + ' bytes<br>' + '<strong>Files:</strong> ' + data.file_count;";
  html += "});";
  html += "fetch('/firmware-hash').then(response => response.json()).then(data => {";
  html += "const fileInfo = data.size > 0 ? '<strong>File:</strong> ' + data.file + '<br>' + '<strong>Size:</strong> ' + data.size + ' bytes<br>' + '<strong>Hash:</strong> ' + data.hash.substring(0, 16) + '...' : '<strong>No file uploaded</strong>';";
  html += "document.getElementById('currentFile').innerHTML = fileInfo;";
  html += "document.getElementById('downloadBtn').style.display = data.size > 0 ? 'inline-block' : 'none';";
  html += "document.getElementById('deleteBtn').style.display = data.size > 0 ? 'inline-block' : 'none';";
  html += "});";
  html += "}";
  html += "function downloadFile() { window.open('/download', '_blank'); }";
  html += "function deleteFile() {";
  html += "if (confirm('Are you sure you want to delete the uploaded file?')) {";
  html += "fetch('/delete', { method: 'POST' }).then(response => response.json()).then(data => {";
  html += "if (data.success) { alert('File deleted successfully'); refreshInfo(); }";
  html += "else { alert('Failed to delete file'); }";
  html += "});";
  html += "}";
  html += "}";
  html += "setInterval(refreshInfo, 5000);";
  html += "refreshInfo();";
  
  // Enhanced LED Matrix Control Functions
  html += "function ledControl(action) {";
  html += "fetch('/led-control?action=' + action).then(response => response.json()).then(data => {";
  html += "if (data.status === 'success') {";
  html += "if (action === 'status') {";
  html += "updateLEDStatus(data);";
  html += "} else {";
  html += "alert('LED Control: ' + data.message);";
  html += "updateLEDStatus(data);";
  html += "}";
  html += "} else {";
  html += "alert('Error: ' + data.message);";
  html += "}";
  html += "}).catch(error => { alert('Error: ' + error); });";
  html += "}";
  
  html += "function setBrightness(level) {";
  html += "document.getElementById('brightnessValue').textContent = level;";
  html += "fetch('/led-control?action=brightness&brightness=' + level).then(response => response.json()).then(data => {";
  html += "if (data.status === 'success') {";
  html += "console.log('Brightness set to: ' + data.level);";
  html += "} else {";
  html += "alert('Error setting brightness: ' + data.message);";
  html += "}";
  html += "}).catch(error => { alert('Error: ' + error); });";
  html += "}";
  
  html += "function setFrameDelay() {";
  html += "const delay = document.getElementById('frameDelayInput').value;";
  html += "fetch('/led-control?action=set_delay&delay_ms=' + delay).then(response => response.json()).then(data => {";
  html += "if (data.status === 'success') {";
  html += "alert('Frame delay set to: ' + data.delay_ms + ' ms');";
  html += "} else {";
  html += "alert('Error setting frame delay: ' + data.message);";
  html += "}";
  html += "}).catch(error => { alert('Error: ' + error); });";
  html += "}";
  
  html += "function updateLEDStatus(data) {";
  html += "const statusDiv = document.getElementById('ledStatus');";
  html += "let statusText = 'LED Status: ';";
  html += "if (data.playing) {";
  html += "statusText += 'Playing (Frame ' + data.current_frame + '/' + data.total_frames + ')';";
  html += "} else if (data.paused) {";
  html += "statusText += 'Paused (Frame ' + data.current_frame + '/' + data.total_frames + ')';";
  html += "} else {";
  html += "statusDiv.textContent = 'Stopped';";
  html += "}";
  html += "statusText += ' | Delay: ' + data.frame_delay_ms + ' ms';";
  html += "statusDiv.textContent = statusText;";
  html += "}";
  
  // Diagnostic Functions
  html += "function runDiagnostic() {";
  html += "const resultsDiv = document.getElementById('diagnosticResults');";
  html += "resultsDiv.innerHTML = '<div class=\"status info\">Running comprehensive diagnostic...</div>';";
  html += "Promise.all([";
  html += "fetch('/diagnostic').then(r => r.json()),";
  html += "fetch('/error-log').then(r => r.json()),";
  html += "fetch('/system-test').then(r => r.json()),";
  html += "fetch('/endpoint-test').then(r => r.json())";
  html += "]).then(([diag, errors, system, endpoints]) => {";
  html += "let html = '<h4>🔍 Diagnostic Results</h4>';";
  html += "html += '<div class=\"status success\"><strong>System:</strong> ' + system.status + '</div>';";
  html += "html += '<div class=\"status success\"><strong>Endpoints:</strong> ' + endpoints.status + '</div>';";
  html += "if (errors && errors.length > 0) {";
  html += "html += '<div class=\"status warning\"><strong>Errors Found:</strong> ' + errors.length + '</div>';";
  html += "html += '<div style=\"max-height: 200px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin: 10px 0;\">';";
  html += "errors.forEach(error => {";
  html += "html += '<div style=\"margin: 5px 0; padding: 5px; background: #f8f9fa; border-left: 3px solid #dc3545;\">';";
  html += "html += '<strong>' + error.timestamp + '</strong> [' + error.level + '] ' + error.component + ' - ' + error.operation + '<br>';";
  html += "html += '<em>' + error.message + '</em> (Code: ' + error.error_code + ', Heap: ' + error.free_heap + ' bytes)';";
  html += "html += '</div>';";
  html += "});";
  html += "html += '</div>';";
  html += "} else {";
  html += "html += '<div class=\"status success\"><strong>No errors found</strong></div>';";
  html += "}";
  html += "resultsDiv.innerHTML = html;";
  html += "}).catch(error => {";
  html += "resultsDiv.innerHTML = '<div class=\"status error\">Diagnostic failed: ' + error + '</div>';";
  html += "});";
  html += "}";
  
  html += "function checkErrorLog() {";
  html += "const resultsDiv = document.getElementById('diagnosticResults');";
  html += "resultsDiv.innerHTML = '<div class=\"status info\">Loading error log...</div>';";
  html += "fetch('/error-log').then(response => response.json()).then(errors => {";
  html += "let html = '<h4>📋 Error Log</h4>';";
  html += "if (errors && errors.length > 0) {";
  html += "html += '<div class=\"status warning\"><strong>Total Errors:</strong> ' + errors.length + '</div>';";
  html += "html += '<div style=\"max-height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin: 10px 0;\">';";
  html += "errors.forEach(error => {";
  html += "const statusClass = error.level === 'ERROR' ? 'error' : (error.level === 'WARNING' ? 'warning' : 'info');";
  html += "html += '<div class=\"status ' + statusClass + '\" style=\"margin: 5px 0; text-align: left;\">';";
  html += "html += '<strong>' + error.timestamp + '</strong> [' + error.level + '] ' + error.component + ' - ' + error.operation + '<br>';";
  html += "html += '<em>' + error.message + '</em>';";
  html += "if (error.error_code > 0) html += ' (Code: ' + error.error_code + ')';";
  html += "html += ' | Heap: ' + error.free_heap + ' bytes';";
  html += "html += '</div>';";
  html += "});";
  html += "html += '</div>';";
  html += "} else {";
  html += "html += '<div class=\"status success\"><strong>No errors in log</strong></div>';";
  html += "}";
  html += "resultsDiv.innerHTML = html;";
  html += "}).catch(error => {";
  html += "resultsDiv.innerHTML = '<div class=\"status error\">Failed to load error log: ' + error + '</div>';";
  html += "});";
  html += "}";
  
  html += "function testEndpoints() {";
  html += "const resultsDiv = document.getElementById('diagnosticResults');";
  html += "resultsDiv.innerHTML = '<div class=\"status info\">Testing endpoints...</div>';";
  html += "const endpoints = ['/ping', '/health', '/system-info', '/fs-info', '/led-control', '/upload'];";
  html += "let results = [];";
  html += "let completed = 0;";
  html += "endpoints.forEach(endpoint => {";
  html += "fetch(endpoint).then(response => {";
  html += "results.push({ endpoint: endpoint, status: response.status, working: response.ok });";
  html += "completed++;";
  html += "if (completed === endpoints.length) {";
  html += "displayEndpointResults(results);";
  html += "}";
  html += "}).catch(error => {";
  html += "results.push({ endpoint: endpoint, status: 'ERROR', working: false, error: error.toString() });";
  html += "completed++;";
  html += "if (completed === endpoints.length) {";
  html += "displayEndpointResults(results);";
  html += "}";
  html += "});";
  html += "});";
  html += "}";
  
  html += "function displayEndpointResults(results) {";
  html += "const resultsDiv = document.getElementById('diagnosticResults');";
  html += "let html = '<h4>🔗 Endpoint Test Results</h4>';";
  html += "let workingCount = 0;";
  html += "results.forEach(result => {";
  html += "if (result.working) workingCount++;";
  html += "const statusClass = result.working ? 'success' : 'error';";
  html += "const statusText = result.working ? 'Working' : 'Failed';";
  html += "html += '<div class=\"status ' + statusClass + '\">';";
  html += "html += '<strong>' + result.endpoint + '</strong>: ' + statusText";
  html += "if (!result.working && result.error) html += ' - ' + result.error;";
  html += "html += '</div>';";
  html += "});";
  html += "html += '<div class=\"status info\"><strong>Summary:</strong> ' + workingCount + '/' + results.length + ' endpoints working</div>';";
  html += "resultsDiv.innerHTML = html;";
  html += "}";
  
  // WiFi Configuration Functions
  html += "function saveWiFiConfig() {";
  html += "const ssid = document.getElementById('newSSID').value;";
  html += "const password = document.getElementById('newPassword').value;";
  html += "if (!ssid || !password) { alert('Please enter both SSID and password'); return; }";
  html += "const formData = new FormData();";
  html += "formData.append('ssid', ssid);";
  html += "formData.append('password', password);";
  html += "fetch('/wifi-config', { method: 'POST', body: formData }).then(response => response.json()).then(data => {";
  html += "if (data.status === 'success') {";
  html += "alert('WiFi credentials saved. Device will restart to apply changes.');";
  html += "} else {";
  html += "alert('Error: ' + data.message);";
  html += "}";
  html += "}).catch(error => { alert('Error: ' + error); });";
  html += "}";
  
  // System Management Functions
  html += "function systemReset(type) {";
  html += "if (!confirm('Are you sure you want to perform a ' + type + ' reset?')) return;";
  html += "const formData = new FormData();";
  html += "formData.append('type', type);";
  html += "fetch('/system-reset', { method: 'POST', body: formData }).then(response => response.json()).then(data => {";
  html += "if (data.status === 'success') {";
  html += "alert('System reset: ' + data.message);";
  html += "if (type === 'full') {";
  html += "setTimeout(() => { location.reload(); }, 2000);";
  html += "}";
  html += "} else {";
  html += "alert('Error: ' + data.message);";
  html += "}";
  html += "}).catch(error => { alert('Error: ' + error); });";
  html += "}";
  
  // Performance Monitoring Functions
  html += "function refreshPerformance() {";
  html += "fetch('/performance').then(response => response.json()).then(data => {";
  html += "document.getElementById('performanceInfo').innerHTML =";
  html += "'<strong>Free Heap:</strong> ' + data.free_heap + ' bytes<br>' +";
  html += "'<strong>Max Alloc Heap:</strong> ' + data.max_alloc_heap + ' bytes<br>' +";
  html += "'<strong>Heap Fragmentation:</strong> ' + data.heap_fragmentation + '%<br>' +";
  html += "'<strong>CPU Frequency:</strong> ' + data.cpu_freq + ' MHz<br>' +";
  html += "'<strong>Uptime:</strong> ' + Math.floor(data.uptime_ms / 1000) + ' seconds';";
  html += "});";
  html += "}";
  
  // Enhanced refresh functions
  html += "function refreshWiFiStatus() {";
  html += "fetch('/wifi-config').then(response => response.json()).then(data => {";
  html += "const status = data.connected ? 'Connected' : 'Disconnected';";
  html += "const ip = data.ip || 'N/A';";
  html += "const rssi = data.rssi || 'N/A';";
  html += "document.getElementById('wifiStatus').innerHTML =";
  html += "'<strong>Status:</strong> ' + status + '<br>' +";
  html += "'<strong>IP Address:</strong> ' + ip + '<br>' +";
  html += "'<strong>Signal Strength:</strong> ' + rssi + ' dBm';";
  html += "});";
  html += "}";
  
  // Initialize enhanced features
  html += "setInterval(refreshWiFiStatus, 10000);";
  html += "setInterval(refreshPerformance, 15000);";
  html += "refreshWiFiStatus();";
  html += "refreshPerformance();";
  
  // Metadata Upload Function
  html += "function uploadMetadata() {";
  html += "const metadata = document.getElementById('metadataInput').value;";
  html += "if (!metadata) { alert('Please enter metadata'); return; }";
  html += "const formData = new FormData();";
  html += "formData.append('metadata', metadata);";
  html += "fetch('/upload-metadata', { method: 'POST', body: formData }).then(response => response.json()).then(data => {";
  html += "if (data.status === 'success') {";
  html += "alert('Metadata uploaded successfully');";
  html += "} else {";
  html += "alert('Error: ' + data.message);";
  html += "}";
  html += "}).catch(error => { alert('Error: ' + error); });";
  html += "}";
  
  // OTA Update Function - DISABLED due to missing library
  // html += "function startOTAUpdate() { ... }";
  html += "</script></body></html>";
  
  server.send(200, "text/html", html);
}

void handleFileUpload() {
  // Check upload token first
  if (!checkUploadToken()) {
    logError("UPLOAD", "TOKEN_VERIFICATION", "Upload token verification failed", 2001);
    Serial.println("Upload token verification failed");
    server.send(401, "application/json", "{\"status\":\"error\",\"message\":\"Invalid or expired upload token\"}");
    return;
  }
  
  HTTPUpload& upload = server.upload();
  
  if (upload.status == UPLOAD_FILE_START) {
    // Reset upload state
    uploadInProgress = true;
    uploadStartTime = millis();
    
    logInfo("UPLOAD", "START", "File upload started - expected size: " + String(upload.totalSize) + " bytes");
    
    // Delete existing file
    if (LittleFS.exists(UPLOAD_FILE)) {
      if (LittleFS.remove(UPLOAD_FILE)) {
        logInfo("UPLOAD", "FILE_CLEANUP", "Existing file removed: " + String(UPLOAD_FILE));
      } else {
        logWarning("UPLOAD", "FILE_CLEANUP", "Failed to remove existing file: " + String(UPLOAD_FILE));
      }
    }
    
    // Check available memory before opening file
    if (ESP.getFreeHeap() < 10000) {
      logWarning("UPLOAD", "MEMORY_CHECK", "Low memory available: " + String(ESP.getFreeHeap()) + " bytes");
    }
    
    // Open file for writing
    uploadFile = LittleFS.open(UPLOAD_FILE, "w");
    if (uploadFile) {
      Serial.println("File upload started - file opened for writing");
      Serial.printf("Free heap: %d bytes\n", ESP.getFreeHeap());
      Serial.printf("Expected file size: %d bytes\n", upload.totalSize);
      
      logInfo("UPLOAD", "FILE_OPEN", "File opened successfully for writing - Free heap: " + String(ESP.getFreeHeap()) + " bytes");
      
      // Parse metadata if available
      if (server.hasArg("metadata")) {
        logInfo("UPLOAD", "METADATA", "Metadata detected, parsing...");
        parseMetadata();
      }
    } else {
      logError("UPLOAD", "FILE_CREATION", "Could not open file for writing: " + String(UPLOAD_FILE), 2002);
      Serial.println("ERROR: Could not open file for writing!");
      uploadInProgress = false;
    }
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    // Write file data in chunks for better stability
    if (uploadFile && uploadInProgress) {
      size_t bytesWritten = uploadFile.write(upload.buf, upload.currentSize);
      if (bytesWritten != upload.currentSize) {
        logError("UPLOAD", "FILE_WRITE", "Write mismatch: Expected " + String(upload.currentSize) + ", Wrote " + String(bytesWritten), 2003);
        Serial.printf("WARNING: Write mismatch: Expected %d, Wrote %d\n", upload.currentSize, bytesWritten);
      }
      
      // Check memory more frequently for large files
      if (upload.totalSize > 32768 && upload.currentSize % 4096 == 0) {
        int progress = (upload.currentSize * 100) / upload.totalSize;
        Serial.printf("Upload progress: %d%% (%d/%d bytes), Free heap: %d\n", 
                     progress, upload.currentSize, upload.totalSize, ESP.getFreeHeap());
        
        logInfo("UPLOAD", "PROGRESS", "Upload progress: " + String(progress) + "% (" + String(upload.currentSize) + "/" + String(upload.totalSize) + " bytes) - Free heap: " + String(ESP.getFreeHeap()) + " bytes");
        
        // Force yield to prevent WiFi stack issues
        yield();
      }
    } else {
      logError("UPLOAD", "FILE_WRITE", "Upload file not open or upload not in progress", 2004);
    }
  } else if (upload.status == UPLOAD_FILE_END) {
    // Upload complete
    if (uploadFile && uploadInProgress) {
      uploadFile.close();
      uploadInProgress = false;
      
      unsigned long uploadDuration = millis() - uploadStartTime;
      Serial.println("File upload complete - file closed");
      Serial.printf("Upload duration: %d ms\n", uploadDuration);
      
      logInfo("UPLOAD", "COMPLETE", "File upload completed in " + String(uploadDuration) + " ms");
      
      // Verify file size
      File file = LittleFS.open(UPLOAD_FILE, "r");
      if (file) {
        lastUploadedSize = file.size();
        lastUploadedHash = calculateFileHash(file);
        file.close();
        
        lastUploadTime = millis();
        
        Serial.printf("File uploaded: %d bytes, hash: %s\n", lastUploadedSize, lastUploadedHash.c_str());
        Serial.printf("Final free heap: %d bytes\n", ESP.getFreeHeap());
        
        logInfo("UPLOAD", "VERIFICATION", "File verified: " + String(lastUploadedSize) + " bytes, Hash: " + lastUploadedHash.substring(0, 16) + "...");
        
        // Check if file size is reasonable for ESP-01
        if (lastUploadedSize > 50000) {
          logWarning("UPLOAD", "FILE_SIZE", "Large file uploaded: " + String(lastUploadedSize) + " bytes - may cause memory issues");
        }
      } else {
        logError("UPLOAD", "FILE_VERIFICATION", "Failed to read uploaded file for verification", 2005);
      }
    } else {
      logError("UPLOAD", "COMPLETION", "Upload file not open or upload not in progress during completion", 2006);
    }
  }
}

void handleUploadSuccess() {
  // Check if upload was actually completed
  if (uploadInProgress) {
    // Check if upload has been in progress too long (timeout)
    if (millis() - uploadStartTime > 30000) { // 30 second timeout
      Serial.println("WARNING: Upload timeout detected");
      uploadInProgress = false;
      if (uploadFile) {
        uploadFile.close();
      }
      server.send(500, "text/plain", "Upload timeout");
    } else {
      server.send(500, "text/plain", "Upload incomplete");
    }
  } else {
  server.send(200, "text/plain", "Upload successful");
  }
}

void handleSystemInfo() {
  String response = "{\"status\":\"Running\",\"free_heap\":" + String(ESP.getFreeHeap()) + 
                    ",\"flash_size\":" + String(ESP.getFlashChipSize()) + 
                    ",\"last_upload\":\"" + (lastUploadTime > 0 ? String(lastUploadTime / 1000) + "s ago" : "Never") + "\"}";
  
  server.send(200, "application/json", response);
}

void handleFileSystemInfo() {
  FSInfo fs_info;
  LittleFS.info(fs_info);
  
  String response = "{\"total_bytes\":" + String(fs_info.totalBytes) + 
                    ",\"used_bytes\":" + String(fs_info.usedBytes) + 
                    ",\"free_bytes\":" + String(fs_info.totalBytes - fs_info.usedBytes) + 
                    ",\"file_count\":" + String(countFiles()) + "}";
  
  server.send(200, "application/json", response);
}

void handleFirmwareHash() {
  String response;
  
  if (LittleFS.exists(UPLOAD_FILE)) {
    File file = LittleFS.open(UPLOAD_FILE, "r");
    if (file) {
      size_t fileSize = file.size();
      String fileHash = calculateFileHash(file);
      file.close();
      
      response = "{\"file\":\"" + String(UPLOAD_FILE) + "\",\"size\":" + String(fileSize) + ",\"hash\":\"" + fileHash + "\"}";
      
      Serial.printf("Firmware hash response: %s\n", response.c_str());
    } else {
      response = "{\"file\":\"Error\",\"size\":0,\"hash\":\"\",\"error\":\"Could not open file\"}";
      Serial.println("ERROR: Could not open file for hash calculation");
    }
  } else {
    response = "{\"file\":\"None\",\"size\":0,\"hash\":\"\",\"error\":\"File not found\"}";
    Serial.println("File not found for hash calculation");
  }
  
  server.send(200, "application/json", response);
}

void handleFileDownload() {
  if (LittleFS.exists(UPLOAD_FILE)) {
    File file = LittleFS.open(UPLOAD_FILE, "r");
    if (file) {
      server.sendHeader("Content-Disposition", "attachment; filename=export_data.bin");
      server.sendHeader("Content-Type", "application/octet-stream");
      server.streamFile(file, "application/octet-stream");
      file.close();
    } else {
      server.send(500, "text/plain", "Error opening file");
    }
  } else {
    server.send(404, "text/plain", "File not found");
  }
}

void handleFileDelete() {
  String response;
  
  if (LittleFS.exists(UPLOAD_FILE)) {
    if (LittleFS.remove(UPLOAD_FILE)) {
      lastUploadedSize = 0;
      lastUploadedHash = "";
      lastUploadTime = 0;
      
      response = "{\"success\":true,\"message\":\"File deleted successfully\"}";
    } else {
      response = "{\"success\":false,\"message\":\"Failed to delete file\"}";
    }
  } else {
    response = "{\"success\":false,\"message\":\"File not found\"}";
  }
  
  server.send(200, "application/json", response);
}

void handleTestWrite() {
  // Test file writing capability
  String testData = "Test data for ESP-01 file system";
  
  File file = LittleFS.open("/test.txt", "w");
  if (file) {
    size_t bytesWritten = file.print(testData);
    file.close();
    
    String response = "{\"success\":true,\"bytes_written\":" + String(bytesWritten) + 
                      ",\"test_file_size\":" + String(LittleFS.open("/test.txt", "r").size()) + "}";
    server.send(200, "application/json", response);
    
    // Clean up test file
    LittleFS.remove("/test.txt");
  } else {
    server.send(500, "application/json", "{\"success\":false,\"error\":\"Could not open file for writing\"}");
  }
}

void handlePing() {
  // Simple connection test endpoint
  String response = "{\"status\":\"ok\",\"free_heap\":" + String(ESP.getFreeHeap()) + 
                    ",\"uptime\":" + String(millis() / 1000) + 
                    ",\"upload_in_progress\":" + String(uploadInProgress ? "true" : "false") + 
                    ",\"last_upload_size\":" + String(lastUploadedSize) + "}";
  server.send(200, "application/json", response);
}

void handleHealth() {
  // Comprehensive health check
  FSInfo fs_info;
  LittleFS.info(fs_info);
  
  String response = "{\"status\":\"healthy\",\"free_heap\":" + String(ESP.getFreeHeap()) + 
                    ",\"uptime\":" + String(millis() / 1000) + 
                    ",\"upload_in_progress\":" + String(uploadInProgress ? "true" : "false") + 
                    ",\"last_upload_size\":" + String(lastUploadedSize) + 
                    ",\"fs_total\":" + String(fs_info.totalBytes) + 
                    ",\"fs_used\":" + String(fs_info.usedBytes) + 
                    ",\"fs_free\":" + String(fs_info.totalBytes - fs_info.usedBytes) + "}";
  server.send(200, "application/json", response);
}

String calculateFileHash(File& file) {
  file.seek(0);
  
  // Simple checksum calculation (CRC32-like)
  uint32_t checksum = 0;
  uint8_t buffer[64];
  size_t bytesRead;
  
  while ((bytesRead = file.read(buffer, sizeof(buffer))) > 0) {
    for (size_t i = 0; i < bytesRead; i++) {
      checksum = ((checksum << 5) + checksum) + buffer[i]; // Simple hash algorithm
    }
  }
  
  // Convert to hex string
  String hashString = String(checksum, HEX);
  // Pad with zeros to make it look like a hash
  while (hashString.length() < 8) {
    hashString = "0" + hashString;
  }
  
  return hashString;
}

int countFiles() {
  int count = 0;
  Dir dir = LittleFS.openDir("/");
  while (dir.next()) {
    count++;
  }
  return count;
}

void loop() {
  server.handleClient();
  
  // Memory management - yield more frequently for better stability
  static unsigned long lastYield = 0;
  if (millis() - lastYield > 500) { // More frequent yields
    yield();
    lastYield = millis();
  }
  
  // Enhanced LED matrix playback with per-chunk delays
  if (ledPlaying && !ledPaused && LittleFS.exists(UPLOAD_FILE) && lastUploadedSize > 0) {
    ledPlaybackTick();
  }
  
  // Check memory and restart if too low
  if (ESP.getFreeHeap() < 8000) { // Lower threshold for ESP-01
    Serial.println("WARNING: Low memory detected, restarting...");
    ESP.restart();
  }
  
  // Reset upload state if stuck for too long
  if (uploadInProgress && (millis() - uploadStartTime > 60000)) { // 1 minute timeout
    Serial.println("WARNING: Upload stuck, resetting state...");
    uploadInProgress = false;
    if (uploadFile) {
      uploadFile.close();
    }
  }
  
  delay(10); // Faster loop for better LED timing
}

void outputLEDMatrixData() {
  // This function is now replaced by ledPlaybackTick() for better control
  if (ledPlaying && !ledPaused) {
    ledPlaybackTick();
  }
}

// Parse metadata from upload (simple JSON-like parsing)
void parseMetadata() {
  if (server.hasArg("metadata")) {
    String metadata = server.arg("metadata");
    Serial.println("Parsing metadata: " + metadata);
    
    // Parse frame delay
    if (metadata.indexOf("\"frame_delay_ms\":") != -1) {
      int start = metadata.indexOf("\"frame_delay_ms\":") + 17;
      int end = metadata.indexOf(",", start);
      if (end == -1) end = metadata.indexOf("}", start);
      if (end > start) {
        frameDelayMs = metadata.substring(start, end).toInt();
        Serial.printf("Frame delay set to: %d ms\n", frameDelayMs);
      }
    }
    
    // Parse total frames
    if (metadata.indexOf("\"total_frames\":") != -1) {
      int start = metadata.indexOf("\"total_frames\":") + 16;
      int end = metadata.indexOf(",", start);
      if (end == -1) end = metadata.indexOf("}", start);
      if (end > start) {
        totalFrames = metadata.substring(start, end).toInt();
        Serial.printf("Total frames: %d\n", totalFrames);
      }
    }
    
    // Parse per-chunk delays array
    if (metadata.indexOf("\"per_chunk_delays\":") != -1) {
      // Free previous if exists
      if (perChunkDelays) { 
        free(perChunkDelays); 
        perChunkDelays = NULL; 
        perChunkDelaysCount = 0; 
      }
      
      int start = metadata.indexOf("[", metadata.indexOf("\"per_chunk_delays\":"));
      int end = metadata.indexOf("]", start);
      if (start > 0 && end > start) {
        String delaysStr = metadata.substring(start + 1, end);
        // Count commas to determine array size
        perChunkDelaysCount = 1;
        for (int i = 0; i < delaysStr.length(); i++) {
          if (delaysStr.charAt(i) == ',') perChunkDelaysCount++;
        }
        
        if (perChunkDelaysCount > 0) {
          perChunkDelays = (unsigned int*)malloc(sizeof(unsigned int) * perChunkDelaysCount);
          if (perChunkDelays) {
            int pos = 0;
            int lastComma = -1;
            for (int i = 0; i < delaysStr.length(); i++) {
              if (delaysStr.charAt(i) == ',' || i == delaysStr.length() - 1) {
                int endPos = (i == delaysStr.length() - 1) ? i + 1 : i;
                String delayStr = delaysStr.substring(lastComma + 1, endPos);
                perChunkDelays[pos] = delayStr.toInt();
                pos++;
                lastComma = i;
              }
            }
            Serial.printf("Loaded %d per-chunk delays\n", perChunkDelaysCount);
          }
        }
      }
    }
  }
}

// Enhanced LED playback with per-chunk delays
void ledPlaybackTick() {
  if (!ledPlaying || ledPaused) return;
  
  unsigned long now = millis();
  
  // Check if it's time for next frame
  if (now - lastFrameTime < frameDelayMs) return;
  
  // Determine current delay for this frame
  unsigned int thisDelay = frameDelayMs;
  if (perChunkDelays && currentFrameIndex < (int)perChunkDelaysCount) {
    thisDelay = perChunkDelays[currentFrameIndex];
  }
  
  // Check if it's time for next frame with current delay
  if (now - lastFrameTime < thisDelay) return;
  
  // Read and display current frame
  File file = LittleFS.open(UPLOAD_FILE, "r");
  if (file) {
    // Calculate frame position (assuming equal frame sizes)
    size_t frameSize = lastUploadedSize / totalFrames;
    size_t framePos = currentFrameIndex * frameSize;
    
    if (framePos < lastUploadedSize) {
      file.seek(framePos);
    uint8_t buffer[64];
      size_t bytesToRead = min(frameSize, (size_t)64);
      size_t bytesRead = file.read(buffer, bytesToRead);
      
      if (bytesRead > 0) {
        Serial.printf("Frame %d/%d: ", currentFrameIndex + 1, totalFrames);
        for (size_t i = 0; i < min(bytesRead, (size_t)16); i++) {
        Serial.printf("%02X ", buffer[i]);
      }
        if (bytesRead > 16) Serial.print("...");
        Serial.printf(" (delay: %d ms)\n", thisDelay);
      
        // Here you would send the data to your LED matrix
        // For now, we just simulate the output
      }
    }
    
    file.close();
    
    // Move to next frame
    currentFrameIndex++;
    if (currentFrameIndex >= totalFrames) {
      currentFrameIndex = 0; // Loop
    }
    
    lastFrameTime = now;
  } else {
    Serial.println("ERROR: Could not open LED data file for playback");
    ledPlaying = false;
  }
}

// Enhanced LED Matrix Control Functions
void handleLEDControl() {
  String response;
  
  if (server.hasArg("action")) {
    String action = server.arg("action");
    
    if (action == "play") {
      ledPlaying = true;
      ledPaused = false;
      currentFrameIndex = 0;
      lastFrameTime = millis();
      response = "{\"status\":\"success\",\"action\":\"play\",\"message\":\"LED animation started\"}";
      Serial.println("LED animation started");
    } else if (action == "pause") {
      ledPaused = true;
      response = "{\"status\":\"success\",\"action\":\"pause\",\"message\":\"LED animation paused\"}";
      Serial.println("LED animation paused");
    } else if (action == "stop") {
      ledPlaying = false;
      ledPaused = false;
      currentFrameIndex = 0;
      response = "{\"status\":\"success\",\"action\":\"stop\",\"message\":\"LED animation stopped\"}";
      Serial.println("LED animation stopped");
    } else if (action == "brightness" && server.hasArg("brightness")) {
      int brightness = server.arg("brightness").toInt();
      brightness = constrain(brightness, 0, 255);
      response = "{\"status\":\"success\",\"action\":\"brightness\",\"level\":" + String(brightness) + "}";
      Serial.printf("Brightness set to: %d\n", brightness);
    } else if (action == "set_delay" && server.hasArg("delay_ms")) {
      frameDelayMs = server.arg("delay_ms").toInt();
      frameDelayMs = constrain(frameDelayMs, 10, 10000); // 10ms to 10s range
      response = "{\"status\":\"success\",\"action\":\"set_delay\",\"delay_ms\":" + String(frameDelayMs) + "}";
      Serial.printf("Frame delay set to: %d ms\n", frameDelayMs);
    } else if (action == "status") {
      response = "{\"status\":\"success\",\"playing\":" + String(ledPlaying ? "true" : "false") + 
                 ",\"paused\":" + String(ledPaused ? "true" : "false") + 
                 ",\"current_frame\":" + String(currentFrameIndex) + 
                 ",\"total_frames\":" + String(totalFrames) + 
                 ",\"frame_delay_ms\":" + String(frameDelayMs) + "}";
    } else {
      response = "{\"status\":\"error\",\"message\":\"Invalid action or missing parameters\"}";
    }
  } else {
    response = "{\"status\":\"error\",\"message\":\"No action specified\"}";
  }
  
  server.send(200, "application/json", response);
}

// WiFi Configuration Management
void handleWiFiConfig() {
  if (server.method() == HTTP_POST) {
    if (server.hasArg("ssid") && server.hasArg("password")) {
      String newSSID = server.arg("ssid");
      String newPassword = server.arg("password");
      
      // Save WiFi credentials
      File configFile = LittleFS.open(CONFIG_FILE, "w");
      if (configFile) {
        String config = "{\"ssid\":\"" + newSSID + "\",\"password\":\"" + newPassword + "\"}";
        configFile.print(config);
        configFile.close();
        
        server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"WiFi credentials saved. Restart to apply.\"}");
        Serial.println("WiFi credentials saved");
      } else {
        server.send(500, "application/json", "{\"status\":\"error\",\"message\":\"Failed to save configuration\"}");
      }
    } else {
      server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Missing SSID or password\"}");
    }
  } else {
    // Return current WiFi status
    String response = "{\"connected\":" + String(wifiConnected ? "true" : "false") + 
                      ",\"ssid\":\"" + WiFi.SSID() + "\"" +
                      ",\"ip\":\"" + WiFi.localIP().toString() + "\"" +
                      ",\"rssi\":" + String(WiFi.RSSI()) + "}";
    server.send(200, "application/json", response);
  }
}

// System Reset and Maintenance
void handleSystemReset() {
  if (server.hasArg("type")) {
    String resetType = server.arg("type");
    
    if (resetType == "wifi") {
      // Reset WiFi settings
      wifiManager.resetSettings();
      server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"WiFi settings reset. Restart to apply.\"}");
      Serial.println("WiFi settings reset");
    } else if (resetType == "filesystem") {
      // Clear all files
      Dir dir = LittleFS.openDir("/");
      while (dir.next()) {
        LittleFS.remove(dir.fileName());
      }
      server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"File system cleared.\"}");
      Serial.println("File system cleared");
    } else if (resetType == "full") {
      // Full system reset
      server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"Full system reset initiated.\"}");
      Serial.println("Full system reset initiated");
      delay(1000);
      ESP.restart();
    } else {
      server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Invalid reset type\"}");
    }
  } else {
    server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"No reset type specified\"}");
  }
}

// Advanced File Management
void handleFileList() {
  String response = "[";
  Dir dir = LittleFS.openDir("/");
  bool first = true;
  
  while (dir.next()) {
    if (!first) response += ",";
    response += "{\"name\":\"" + dir.fileName() + "\",\"size\":" + String(dir.fileSize()) + "}";
    first = false;
  }
  
  response += "]";
  server.send(200, "application/json", response);
}

void handleFileInfo() {
  if (server.hasArg("filename")) {
    String filename = "/" + server.arg("filename");
    
    if (LittleFS.exists(filename)) {
      File file = LittleFS.open(filename, "r");
      if (file) {
        String response = "{\"name\":\"" + filename + "\",\"size\":" + String(file.size()) + 
                          ",\"hash\":\"" + calculateFileHash(file) + "\"}";
        file.close();
        server.send(200, "application/json", response);
      } else {
        server.send(500, "application/json", "{\"status\":\"error\",\"message\":\"Could not open file\"}");
      }
    } else {
      server.send(404, "application/json", "{\"status\":\"error\",\"message\":\"File not found\"}");
    }
  } else {
    server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"No filename specified\"}");
  }
}

// Performance Monitoring
void handlePerformance() {
  String response = "{\"free_heap\":" + String(ESP.getFreeHeap()) + 
                                         ",\"max_alloc_heap\":" + String(ESP.getFreeHeap()) + // Alternative to getMaxAllocHeap 
                    ",\"heap_fragmentation\":" + String(ESP.getHeapFragmentation()) + 
                    ",\"cpu_freq\":" + String(ESP.getCpuFreqMHz()) + 
                    ",\"cycle_count\":" + String(ESP.getCycleCount()) + 
                    ",\"uptime_ms\":" + String(millis()) + "}";
  
  server.send(200, "application/json", response);
}

// OTA Update Handler - DISABLED due to missing ESP8266HTTPUpdate.h library
// void handleOTAUpdate() { ... }

// Metadata upload handler
void handleMetadataUpload() {
  if (!checkUploadToken()) {
    server.send(401, "application/json", "{\"status\":\"error\",\"message\":\"Invalid or expired upload token\"}");
    return;
  }
  
  if (server.hasArg("metadata")) {
    String metadata = server.arg("metadata");
    Serial.println("Received metadata: " + metadata);
    
    // Parse the metadata
    parseMetadata();
    
    server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"Metadata processed successfully\"}");
  } else {
    server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"No metadata provided\"}");
  }
}

// Diagnostic endpoints
void handleDiagnostic() {
  String response = "{";
  response += "\"status\":\"success\",";
  response += "\"timestamp\":\"" + String(millis() / 1000) + "s\",";
  response += "\"uptime_ms\":" + String(millis()) + ",";
  response += "\"free_heap\":" + String(ESP.getFreeHeap()) + ",";
  response += "\"heap_fragmentation\":" + String(ESP.getHeapFragmentation()) + ",";
  response += "\"cpu_freq_mhz\":" + String(ESP.getCpuFreqMHz()) + ",";
  response += "\"wifi_connected\":" + String(wifiConnected ? "true" : "false") + ",";
  response += "\"wifi_mode\":\"" + String(wifiConnected ? "STA" : "AP") + "\",";
  response += "\"ip_address\":\"" + (wifiConnected ? WiFi.localIP().toString() : WiFi.softAPIP().toString()) + "\",";
  response += "\"error_count\":" + String(errorCount) + ",";
  response += "\"warning_count\":" + String(warningCount) + ",";
  response += "\"info_count\":" + String(infoCount) + ",";
  response += "\"firmware_version\":\"Enhanced_v1.0\",";
  response += "\"firmware_features\":[\"file_upload\",\"led_control\",\"system_monitoring\",\"comprehensive_diagnostics\",\"error_logging\",\"endpoint_testing\"]";
  response += "}";
  server.send(200, "application/json", response);
}

void handleErrorLog() {
  String response = "[";
  for (int i = 0; i < errorLogCount; i++) {
    if (i > 0) response += ",";
    response += "{";
    response += "\"timestamp\":\"" + errorLog[i].timestamp + "\",";
    response += "\"level\":\"" + errorLog[i].level + "\",";
    response += "\"component\":\"" + errorLog[i].component + "\",";
    response += "\"operation\":\"" + errorLog[i].operation + "\",";
    response += "\"message\":\"" + errorLog[i].message + "\",";
    response += "\"error_code\":" + String(errorLog[i].errorCode) + ",";
    response += "\"free_heap\":" + String(errorLog[i].freeHeap);
    response += "}";
  }
  response += "]";
  server.send(200, "application/json", response);
}

void handleSystemTest() {
  // Test various system components
  bool fsWorking = LittleFS.begin();
  bool wifiWorking = WiFi.status() == WL_CONNECTED || WiFi.getMode() == WIFI_AP;
  bool memoryOK = ESP.getFreeHeap() > 10000; // At least 10KB free
  
  String response = "{";
  response += "\"status\":\"success\",";
  response += "\"tests\":{";
  response += "\"filesystem\":" + String(fsWorking ? "true" : "false") + ",";
  response += "\"wifi\":" + String(wifiWorking ? "true" : "false") + ",";
  response += "\"memory\":" + String(memoryOK ? "true" : "false");
  response += "},";
  response += "\"free_heap\":" + String(ESP.getFreeHeap()) + ",";
  response += "\"wifi_status\":" + String(WiFi.status()) + ",";
  response += "\"wifi_mode\":" + String(WiFi.getMode());
  response += "}";
  server.send(200, "application/json", response);
}

void handleEndpointTest() {
  // Test all available endpoints
  String response = "{";
  response += "\"status\":\"success\",";
  response += "\"endpoints\":{";
  response += "\"/\":\"available\",";
  response += "\"/upload\":\"available\",";
  response += "\"/ping\":\"available\",";
  response += "\"/health\":\"available\",";
  response += "\"/system-info\":\"available\",";
  response += "\"/fs-info\":\"available\",";
  response += "\"/led-control\":\"available\",";
  response += "\"/diagnostic\":\"available\",";
  response += "\"/error-log\":\"available\",";
  response += "\"/system-test\":\"available\",";
  response += "\"/endpoint-test\":\"available\"";
  response += "},";
  response += "\"total_endpoints\":11,";
  response += "\"available_endpoints\":11";
  response += "}";
  server.send(200, "application/json", response);
}

// Basic Authentication Check - DISABLED (OTA removed)
// bool checkAuthentication() { ... }

// Upload Token Check
bool checkUploadToken() {
  // If no secret defined, allow (backwards compatible)
  if (String(TOKEN_SECRET).length() == 0) return true;
  if (!server.hasHeader("X-Upload-Token")) return false;
  String token = server.header("X-Upload-Token");
  return verify_upload_token(token);
}

// Secure Endpoint Wrapper - DISABLED (OTA removed)
// void secureEndpoint(const char* endpoint, HTTPMethod method, void (*handler)()) { ... }

// Load saved configuration
void loadConfiguration() {
  if (LittleFS.exists(CONFIG_FILE)) {
    File configFile = LittleFS.open(CONFIG_FILE, "r");
    if (configFile) {
      String config = configFile.readString();
      configFile.close();
      
      // Simple JSON parsing for WiFi credentials
      if (config.indexOf("\"ssid\":\"") != -1) {
        int ssidStart = config.indexOf("\"ssid\":\"") + 8;
        int ssidEnd = config.indexOf("\"", ssidStart);
        String savedSSID = config.substring(ssidStart, ssidEnd);
        
        if (config.indexOf("\"password\":\"") != -1) {
          int passStart = config.indexOf("\"password\":\"") + 12;
          int passEnd = config.indexOf("\"", passStart);
          String savedPassword = config.substring(passStart, passEnd);
          
          Serial.printf("Loaded saved WiFi: %s\n", savedSSID.c_str());
          // Note: WiFiManager will handle the connection
        }
      }
    }
  }
}

// Simplified HMAC-like implementation (not cryptographically secure, but functional)
// returns hex string in `outHex` (must be at least 41 chars)
void hmac_sha1_hex(const char* key, const char* msg, char *outHex) {
  // Simple hash function using XOR and bit shifting
  uint32_t hash = 0x12345678; // Initial value
  
  // Hash the key
  for (size_t i = 0; i < strlen(key); i++) {
    hash = ((hash << 13) | (hash >> 19)) ^ key[i];
    hash ^= (hash >> 7);
  }
  
  // Hash the message
  for (size_t i = 0; i < strlen(msg); i++) {
    hash = ((hash << 17) | (hash >> 15)) ^ msg[i];
    hash ^= (hash >> 13);
  }
  
  // Convert to hex string (40 chars)
  const char hexmap[] = "0123456789abcdef";
  for (int i = 0; i < 20; ++i) {
    uint8_t byte = (hash >> (i % 4 * 8)) & 0xFF;
    outHex[i * 2] = hexmap[(byte >> 4) & 0xF];
    outHex[i * 2 + 1] = hexmap[byte & 0xF];
  }
  outHex[40] = '\0';
}

// Token verification helper
bool verify_upload_token(const String &tokenHdr) {
  // token format: "<hex_hmac>:<timestamp>"
  int colon = tokenHdr.indexOf(':');
  if (colon < 0) return false;
  String hex = tokenHdr.substring(0, colon);
  String tsStr = tokenHdr.substring(colon + 1);
  unsigned long ts = tsStr.toInt();
  unsigned long nowSec = (unsigned long)(millis() / 1000);
  // prevent negative wrap weirdness; accept tokens within TOKEN_TTL_SECONDS
  if (ts == 0) return false;
  if (nowSec < ts) return false; // client clock ahead -> reject
  if ((nowSec - ts) > TOKEN_TTL_SECONDS) return false; // expired

  // compute HMAC using same secret
  char computed[41];
  hmac_sha1_hex(TOKEN_SECRET, tsStr.c_str(), computed);
  // compare case-insensitive hex
  String cmp = String(computed);
  return (cmp.equalsIgnoreCase(hex));
}

// NEW: Enhanced error reporting and diagnostics - MOVED BEFORE setup()

String getSystemDiagnostics() {
  String response = "{\"uptime_ms\":" + String(millis()) + ",\"free_heap\":" + String(ESP.getFreeHeap()) + ",\"max_alloc_heap\":" + String(ESP.getFreeHeap()) + ",\"heap_fragmentation\":" + String(ESP.getHeapFragmentation()) + ",\"cpu_freq\":" + String(ESP.getCpuFreqMHz()) + ",\"cycle_count\":" + String(ESP.getCycleCount()) + "}";
  return response;
}

String getErrorSummary() {
  String response = "{\"total_errors\":" + String(errorCount) + ",\"total_warnings\":" + String(warningCount) + ",\"total_infos\":" + String(infoCount) + "}";
  return response;
}

String getEndpointStatus() {
  String response = "{\"status\":\"ok\",\"message\":\"All endpoints are responding.\"}";
  return response;
}

String getMemoryStatus() {
  String response = "{\"free_heap\":" + String(ESP.getFreeHeap()) + ",\"max_alloc_heap\":" + String(ESP.getFreeHeap()) + ",\"heap_fragmentation\":" + String(ESP.getHeapFragmentation()) + "}";
  return response;
}

String getWiFiStatus() {
  String response = "{\"connected\":" + String(wifiConnected ? "true" : "false") + ",\"ssid\":\"" + WiFi.SSID() + "\",\"ip\":\"" + WiFi.localIP().toString() + "\",\"rssi\":" + String(WiFi.RSSI()) + "}";
  return response;
}

String getFileSystemStatus() {
  FSInfo fs_info;
  LittleFS.info(fs_info);
  String response = "{\"total_bytes\":" + String(fs_info.totalBytes) + ",\"used_bytes\":" + String(fs_info.usedBytes) + ",\"free_bytes\":" + String(fs_info.totalBytes - fs_info.usedBytes) + "}";
  return response;
}

// NEW: WiFi status handler for troubleshooting
void handleWiFiStatus() {
  String response = "{";
  response += "\"mode\":\"" + String(WiFi.getMode() == WIFI_AP ? "AP" : "STA") + "\",";
  response += "\"ap_ssid\":\"" + String(ssid) + "\",";
  response += "\"ap_ip\":\"" + WiFi.softAPIP().toString() + "\",";
  response += "\"ap_connected_clients\":" + String(WiFi.softAPgetStationNum()) + ",";
  response += "\"ap_enabled\":" + String(WiFi.softAPgetStationNum() >= 0 ? "true" : "false") + ",";
  response += "\"wifi_connected\":" + String(wifiConnected ? "true" : "false") + ",";
  response += "\"free_heap\":" + String(ESP.getFreeHeap()) + ",";
  response += "\"uptime_ms\":" + String(millis()) + ",";
  response += "\"status\":\"WiFi AP mode active - connect to 'MatrixUploader' network\"";
  response += "}";
  
  server.send(200, "application/json", response);
}


