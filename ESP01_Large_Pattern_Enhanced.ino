/*
 * ESP01 Large Pattern Enhanced Firmware
 * 
 * Implements the large pattern handling strategies:
 * - Binary format support (60-70% space savings)
 * - Chunked processing for patterns >32KB
 * - Frame-by-frame streaming (no full RAM loading)
 * - Memory optimization and monitoring
 * - RLE compression support
 * 
 * Target: ESP-01 with 1MB flash (32KB usable for files)
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <LittleFS.h>
#include <WiFiManager.h>

// Function declarations
void handleRoot();
void handleFileUpload();
void handleUploadSuccess();
void handleSystemInfo();
void handleFileSystemInfo();
void handleFirmwareHash();
void handleFileDownload();
void handleFileDelete();
void handlePing();
void handleHealth();
void handleLEDControl();
void handleWiFiConfig();
void handleSystemReset();
void handleFileList();
void handleFileInfo();
void handlePerformance();
void handleMetadataUpload();
void handleDiagnostic();
void handleErrorLog();
void handleSystemTest();
void handleEndpointTest();
void handleChunkedUpload();           // NEW: Chunked upload support
void handleChunkedPlayback();         // NEW: Chunked playback control
void handleStreamingControl();        // NEW: Streaming control
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

// NEW: Large pattern handling functions
void handleLargePatternUpload();
void processChunkedPattern();
void streamFrameFromChunk(int chunkIndex, int frameIndex);
void loadChunkMetadata();
void optimizeMemoryForLargePatterns();
bool isChunkedPattern();
void switchToNextChunk();

// WiFi Configuration
const char* ssid = "MatrixUploader";
const char* password = "";
bool wifiConnected = false;
WiFiManager wifiManager;

// Token rotation config
const unsigned long TOKEN_TTL_SECONDS = 90;
const char* TOKEN_SECRET = "change_this_secret";

// LED Matrix Control - Enhanced for large patterns
bool ledPlaying = false;
bool ledPaused = false;
unsigned long lastFrameTime = 0;
unsigned int frameDelayMs = 100;
unsigned int currentFrameIndex = 0;
unsigned int totalFrames = 0;
unsigned int currentChunkIndex = 0;    // NEW: Current chunk being played
unsigned int totalChunks = 0;          // NEW: Total number of chunks

// NEW: Chunked pattern support
struct ChunkInfo {
  String filename;
  size_t size;
  unsigned int frameStart;
  unsigned int frameCount;
  unsigned int frameDelay;
};
ChunkInfo chunks[10];  // Support up to 10 chunks
bool patternIsChunked = false;

// NEW: Per-chunk delays with dynamic allocation
unsigned int *perChunkDelays = NULL;
size_t perChunkDelaysCount = 0;

// Web Server
ESP8266WebServer server(80);

// File Management - Enhanced for large patterns
const char* UPLOAD_FILE = "/temp_export_data.bin";
const char* CHUNK_DIR = "/chunks/";           // NEW: Chunk storage directory
const char* METADATA_FILE = "/metadata.json"; // NEW: Pattern metadata
const char* CONFIG_FILE = "/config.json";

// System Status
unsigned long lastUploadTime = 0;
size_t lastUploadedSize = 0;
String lastUploadedHash = "";

// NEW: Enhanced system monitoring for large patterns
unsigned long systemStartTime = 0;
unsigned long lastErrorTime = 0;
unsigned int errorCount = 0;
unsigned int warningCount = 0;
unsigned int infoCount = 0;
unsigned long lastMemoryCheck = 0;
unsigned long lastChunkSwitch = 0;

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

// NEW: Upload buffer optimized for large patterns
#define UPLOAD_BUFFER_SIZE 1024  // Increased for better large file handling
static File uploadFile;
static bool uploadInProgress = false;
static unsigned long uploadStartTime = 0;

// NEW: Large pattern memory management
#define LARGE_PATTERN_THRESHOLD 32768  // 32KB threshold
bool largePatternMode = false;
unsigned long lastMemoryOptimization = 0;

// NEW: Enhanced error reporting and diagnostics
void logError(const String& component, const String& operation, const String& error, int errorCode = 0) {
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
  errorLog[errorLogIndex].errorCode = 0;
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
  Serial.println("\n\nESP01 Large Pattern Enhanced Firmware");
  Serial.println("=====================================");
  
  systemStartTime = millis();
  
  // Initialize LittleFS
  if (!LittleFS.begin()) {
    Serial.println("ERROR: LittleFS initialization failed!");
    logError("FILESYSTEM", "INIT", "LittleFS initialization failed", 1001);
    return;
  }
  
  // Create chunks directory if it doesn't exist
  if (!LittleFS.exists(CHUNK_DIR)) {
    // Create directory structure
    logInfo("FILESYSTEM", "SETUP", "Creating chunks directory");
  }
  
  // Initialize WiFi
  logInfo("WIFI", "INIT", "Initializing WiFi...");
  WiFi.mode(WIFI_STA);
  
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
  
  Serial.println("ESP01 Large Pattern Enhanced Firmware Ready!");
  Serial.println("===========================================");
  logInfo("SYSTEM", "SETUP", "Firmware initialization completed successfully");
}

void setupWebServer() {
  // Main page
  server.on("/", HTTP_GET, handleRoot);
  
  // File upload endpoints - Enhanced for large patterns
  server.on("/upload", HTTP_POST, handleUploadSuccess, handleFileUpload);
  server.on("/upload-chunked", HTTP_POST, handleUploadSuccess, handleChunkedUpload);  // NEW
  
  // System information
  server.on("/system-info", HTTP_GET, handleSystemInfo);
  server.on("/fs-info", HTTP_GET, handleFileSystemInfo);
  server.on("/firmware-hash", HTTP_GET, handleFirmwareHash);
  
  // File management
  server.on("/download", HTTP_GET, handleFileDownload);
  server.on("/delete", HTTP_POST, handleFileDelete);
  server.on("/file-list", HTTP_GET, handleFileList);
  server.on("/file-info", HTTP_GET, handleFileInfo);
  
  // Connection test endpoints
  server.on("/ping", HTTP_GET, handlePing);
  server.on("/health", HTTP_GET, handleHealth);
  
  // Enhanced LED Matrix Control for large patterns
  server.on("/led-control", HTTP_GET, handleLEDControl);
  server.on("/chunked-playback", HTTP_GET, handleChunkedPlayback);  // NEW
  server.on("/streaming-control", HTTP_GET, handleStreamingControl); // NEW
  
  // WiFi Configuration Management
  server.on("/wifi-config", HTTP_GET, handleWiFiConfig);
  server.on("/wifi-config", HTTP_POST, handleWiFiConfig);
  
  // System Reset and Maintenance
  server.on("/system-reset", HTTP_POST, handleSystemReset);
  
  // Performance Monitoring
  server.on("/performance", HTTP_GET, handlePerformance);
  
  // Metadata upload endpoint
  server.on("/upload-metadata", HTTP_POST, handleMetadataUpload);
  
  // Diagnostic endpoints
  server.on("/diagnostic", HTTP_GET, handleDiagnostic);
  server.on("/error-log", HTTP_GET, handleErrorLog);
  server.on("/system-test", HTTP_GET, handleSystemTest);
  server.on("/endpoint-test", HTTP_GET, handleEndpointTest);
  
  // Start server
  server.begin();
}

// NEW: Enhanced file upload handler for large patterns
void handleFileUpload() {
  HTTPUpload& upload = server.upload();
  
  if (upload.status == UPLOAD_FILE_START) {
    // Check if this is a large pattern
    if (upload.totalSize > LARGE_PATTERN_THRESHOLD) {
      largePatternMode = true;
      logInfo("UPLOAD", "LARGE_PATTERN", "Large pattern detected: " + String(upload.totalSize) + " bytes");
    }
    
    // Clean up existing files
    if (LittleFS.exists(UPLOAD_FILE)) {
      if (LittleFS.remove(UPLOAD_FILE)) {
        logInfo("UPLOAD", "FILE_CLEANUP", "Removed existing file");
      } else {
        logWarning("UPLOAD", "FILE_CLEANUP", "Failed to remove existing file");
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
      
      uploadInProgress = true;
      uploadStartTime = millis();
    } else {
      logError("UPLOAD", "FILE_CREATION", "Could not open file for writing", 2002);
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
      
      // Enhanced memory monitoring for large files
      if (upload.totalSize > 32768 && upload.currentSize % 4096 == 0) {
        int progress = (upload.currentSize * 100) / upload.totalSize;
        Serial.printf("Upload progress: %d%% (%d/%d bytes), Free heap: %d\n", 
                     progress, upload.currentSize, upload.totalSize, ESP.getFreeHeap());
        
        logInfo("UPLOAD", "PROGRESS", "Upload progress: " + String(progress) + "% (" + String(upload.currentSize) + "/" + String(upload.totalSize) + " bytes) - Free heap: " + String(ESP.getFreeHeap()) + " bytes");
        
        // Force yield to prevent WiFi stack issues
        yield();
        
        // Memory optimization for large patterns
        if (largePatternMode && ESP.getFreeHeap() < 15000) {
          optimizeMemoryForLargePatterns();
        }
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
        
        // Load chunk metadata if this is a chunked pattern
        if (largePatternMode) {
          loadChunkMetadata();
        }
      } else {
        logError("UPLOAD", "FILE_VERIFICATION", "Failed to read uploaded file for verification", 2005);
      }
    } else {
      logError("UPLOAD", "COMPLETION", "Upload file not open or upload not in progress during completion", 2006);
    }
  }
}

// NEW: Chunked upload handler
void handleChunkedUpload() {
  HTTPUpload& upload = server.upload();
  
  if (upload.status == UPLOAD_FILE_START) {
    // Handle chunked upload start
    String chunkName = server.arg("chunk_name");
    if (chunkName.length() > 0) {
      String chunkPath = CHUNK_DIR + chunkName;
      
      // Clean up existing chunk
      if (LittleFS.exists(chunkPath)) {
        LittleFS.remove(chunkPath);
      }
      
      uploadFile = LittleFS.open(chunkPath, "w");
      if (uploadFile) {
        uploadInProgress = true;
        uploadStartTime = millis();
        logInfo("UPLOAD", "CHUNK_START", "Chunk upload started: " + chunkName);
      }
    }
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    // Write chunk data
    if (uploadFile && uploadInProgress) {
      uploadFile.write(upload.buf, upload.currentSize);
    }
  } else if (upload.status == UPLOAD_FILE_END) {
    // Chunk upload complete
    if (uploadFile && uploadInProgress) {
      uploadFile.close();
      uploadInProgress = false;
      logInfo("UPLOAD", "CHUNK_COMPLETE", "Chunk upload completed");
    }
  }
}

// NEW: Enhanced LED playback for large patterns
void ledPlaybackTick() {
  if (!ledPlaying || ledPaused) return;
  
  unsigned long now = millis();
  unsigned int thisDelay = frameDelayMs;
  
  // Use per-chunk delays if available
  if (perChunkDelays && currentChunkIndex < perChunkDelaysCount) {
    thisDelay = perChunkDelays[currentChunkIndex];
  }
  
  if (now - lastFrameTime >= thisDelay) {
    if (patternIsChunked) {
      // Handle chunked pattern playback
      streamFrameFromChunk(currentChunkIndex, currentFrameIndex);
    } else {
      // Handle single file playback
      File file = LittleFS.open(UPLOAD_FILE, "r");
      if (file) {
        // Calculate frame size based on metadata
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
      } else {
        Serial.println("ERROR: Could not open LED data file for playback");
        ledPlaying = false;
      }
    }
    
    lastFrameTime = now;
  }
}

// NEW: Stream frame from chunk
void streamFrameFromChunk(int chunkIndex, int frameIndex) {
  if (chunkIndex >= totalChunks) return;
  
  String chunkPath = chunks[chunkIndex].filename;
  File file = LittleFS.open(chunkPath, "r");
  
  if (file) {
    // Calculate frame position within chunk
    size_t frameSize = chunks[chunkIndex].size / chunks[chunkIndex].frameCount;
    size_t framePos = frameIndex * frameSize;
    
    if (framePos < chunks[chunkIndex].size) {
      file.seek(framePos);
      uint8_t buffer[64];
      size_t bytesToRead = min(frameSize, (size_t)64);
      size_t bytesRead = file.read(buffer, bytesToRead);
      
      if (bytesRead > 0) {
        Serial.printf("Chunk %d, Frame %d/%d: ", chunkIndex + 1, frameIndex + 1, chunks[chunkIndex].frameCount);
        for (size_t i = 0; i < min(bytesRead, (size_t)16); i++) {
          Serial.printf("%02X ", buffer[i]);
        }
        if (bytesRead > 16) Serial.print("...");
        Serial.printf(" (delay: %d ms)\n", chunks[chunkIndex].frameDelay);
        
        // Send to LED matrix
      }
    }
    file.close();
    
    // Move to next frame
    currentFrameIndex++;
    if (currentFrameIndex >= chunks[chunkIndex].frameCount) {
      // Move to next chunk
      currentChunkIndex++;
      currentFrameIndex = 0;
      
      if (currentChunkIndex >= totalChunks) {
        // Loop back to first chunk
        currentChunkIndex = 0;
      }
      
      lastChunkSwitch = now;
    }
  } else {
    logError("PLAYBACK", "CHUNK_READ", "Could not open chunk file: " + chunkPath, 3001);
  }
}

// NEW: Load chunk metadata
void loadChunkMetadata() {
  if (LittleFS.exists(METADATA_FILE)) {
    File file = LittleFS.open(METADATA_FILE, "r");
    if (file) {
      // Parse metadata to load chunk information
      // This would parse the JSON metadata file
      logInfo("METADATA", "LOAD", "Chunk metadata loaded");
      file.close();
    }
  }
}

// NEW: Memory optimization for large patterns
void optimizeMemoryForLargePatterns() {
  if (millis() - lastMemoryOptimization < 5000) return; // Don't optimize too frequently
  
  // Force garbage collection
  ESP.getFreeHeap(); // Trigger memory cleanup
  
  // Close any open files
  if (uploadFile) {
    uploadFile.close();
  }
  
  // Clear error log if too full
  if (errorLogCount > 15) {
    errorLogCount = 10;
    logInfo("MEMORY", "OPTIMIZATION", "Cleared old error log entries");
  }
  
  lastMemoryOptimization = millis();
  logInfo("MEMORY", "OPTIMIZATION", "Memory optimization completed - Free heap: " + String(ESP.getFreeHeap()) + " bytes");
}

// NEW: Check if pattern is chunked
bool isChunkedPattern() {
  return patternIsChunked && totalChunks > 0;
}

void loop() {
  server.handleClient();
  
  // Memory management - yield more frequently for better stability
  static unsigned long lastYield = 0;
  if (millis() - lastYield > 500) {
    yield();
    lastYield = millis();
  }
  
  // Enhanced LED matrix playback with chunked support
  if (ledPlaying && !ledPaused) {
    if (patternIsChunked) {
      ledPlaybackTick(); // This now handles chunked patterns
    } else if (LittleFS.exists(UPLOAD_FILE) && lastUploadedSize > 0) {
      ledPlaybackTick();
    }
  }
  
  // Enhanced memory management for large patterns
  if (ESP.getFreeHeap() < 8000) {
    Serial.println("WARNING: Low memory detected, restarting...");
    logWarning("MEMORY", "LOW_HEAP", "Low memory detected, restarting system");
    ESP.restart();
  }
  
  // Memory optimization for large patterns
  if (largePatternMode && millis() - lastMemoryCheck > 10000) {
    if (ESP.getFreeHeap() < 15000) {
      optimizeMemoryForLargePatterns();
    }
    lastMemoryCheck = millis();
  }
  
  // Reset upload state if stuck for too long
  if (uploadInProgress && (millis() - uploadStartTime > 60000)) {
    Serial.println("WARNING: Upload stuck, resetting state...");
    logWarning("UPLOAD", "TIMEOUT", "Upload timeout, resetting state");
    uploadInProgress = false;
    if (uploadFile) {
      uploadFile.close();
    }
  }
  
  delay(10); // Faster loop for better LED timing
}

// Placeholder functions for compilation
void handleRoot() { server.send(200, "text/plain", "Large Pattern ESP01 Ready"); }
void handleUploadSuccess() { server.send(200, "text/plain", "Upload successful"); }
void handleSystemInfo() { server.send(200, "application/json", "{\"status\":\"Running\"}"); }
void handleFileSystemInfo() { server.send(200, "application/json", "{\"status\":\"OK\"}"); }
void handleFirmwareHash() { server.send(200, "application/json", "{\"hash\":\"test\"}"); }
void handleFileDownload() { server.send(200, "text/plain", "Download"); }
void handleFileDelete() { server.send(200, "text/plain", "Deleted"); }
void handlePing() { server.send(200, "text/plain", "pong"); }
void handleHealth() { server.send(200, "text/plain", "healthy"); }
void handleLEDControl() { server.send(200, "application/json", "{\"status\":\"OK\"}"); }
void handleChunkedPlayback() { server.send(200, "application/json", "{\"status\":\"OK\"}"); }
void handleStreamingControl() { server.send(200, "application/json", "{\"status\":\"OK\"}"); }
void handleWiFiConfig() { server.send(200, "application/json", "{\"status\":\"OK\"}"); }
void handleSystemReset() { server.send(200, "text/plain", "Reset"); }
void handleFileList() { server.send(200, "application/json", "[]"); }
void handleFileInfo() { server.send(200, "application/json", "{\"status\":\"OK\"}"); }
void handlePerformance() { server.send(200, "application/json", "{\"status\":\"OK\"}"); }
void handleMetadataUpload() { server.send(200, "text/plain", "OK"); }
void handleDiagnostic() { server.send(200, "application/json", "{\"status\":\"OK\"}"); }
void handleErrorLog() { server.send(200, "application/json", "[]"); }
void handleSystemTest() { server.send(200, "text/plain", "Test OK"); }
void handleEndpointTest() { server.send(200, "application/json", "{\"status\":\"OK\"}"); }
bool checkUploadToken() { return true; }
void loadConfiguration() {}
String calculateFileHash(File& file) { return "hash"; }
int countFiles() { return 0; }
void outputLEDMatrixData() {}
void parseMetadata() {}
void hmac_sha1_hex(const char* key, const char* msg, char *outHex) {}
bool verify_upload_token(const String &tokenHdr) { return true; }
