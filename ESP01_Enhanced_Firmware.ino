/*
  ESP-01 / ESP8266 LED Matrix Uploader (FastLED + LittleFS)
  - Accepts full file uploads and chunked uploads
  - Stores files under /patterns/ on LittleFS
  - Expects raw frames: each frame = NUM_LEDS * 3 bytes (R,G,B)
  - Non-blocking frame playback using millis()
  - Simple token-based protection for upload endpoints
  - Author: ChatGPT (adapted for your project)
*/

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <LittleFS.h>
#include <FastLED.h>
#include <ArduinoJson.h> // used for metadata handling (install via Library Manager)

///////// User configuration /////////
// WiFi AP credentials (change if you want)
const char* apSSID = "MatrixUploader_ESP01";
const char* apPASS = "MatrixSecure2024!"; // change before production

// Simple upload token - required as ?token=YOUR_TOKEN in POST/GET requests that alter FS
const char* UPLOAD_TOKEN = "upload_token_2025";

// LED config
#define DATA_PIN 2         // GPIO2 (D4) - safe for ESP-01 (change only if you know pin consequences)
#define LED_TYPE WS2812    // change if using APA102 or other
#define COLOR_ORDER GRB
const uint16_t NUM_LEDS = 64; // total LEDs in your matrix (adjust)
CRGB leds[NUM_LEDS];

// Frame format: raw frames of NUM_LEDS*3 bytes
const size_t FRAME_BYTES = (size_t)NUM_LEDS * 3;

// File size / storage limits
const size_t MAX_UPLOAD_SIZE = 200 * 1024UL; // 200KB (adjust to your flash)
const char* PATTERNS_DIR = "/patterns";

// Web server
ESP8266WebServer server(80);

// Playback state (non-blocking)
bool playing = false;
String currentPatternPath = "";
unsigned long frameDelayMs = 100; // default frame delay (ms) if not in metadata
size_t totalFrames = 0;
size_t currentFrame = 0;
unsigned long lastFrameMillis = 0;
File playbackFile;

// Metadata structure stored as JSON at /patterns/metadata.json
// Example metadata:
 // {
 //   "patterns": {
 //     "name.bin": { "frames": 50, "delay": 50, "size": 9600 },
 //     "chunk_001.bin": { "frames": 80, "delay": 40, "size": 15360 }
 //   }
 // }
DynamicJsonDocument metadataDoc(8 * 1024);

////////// Utilities //////////

// Simple CRC32 implementation for basic integrity check
uint32_t crc32_update(uint32_t crc, const uint8_t *buf, size_t len) {
  static const uint32_t table[256] PROGMEM = {
    0x00000000L,0x77073096L,0xEE0E612CL,0x990951BAL,0x076DC419L,0x706AF48FL,0xE963A535L,0x9E6495A3L,
    // table truncated for readability in source — we'll compute programmatically below if needed
  };
  // To avoid using the incomplete table above, use a simple rolling checksum (not CRC32) here:
  uint32_t s = crc;
  for (size_t i=0;i<len;i++) s = s * 31 + buf[i];
  return s;
}

// Check free LittleFS space before write
bool hasEnoughSpace(size_t incoming) {
  FSInfo fi;
  LittleFS.info(fi);
  if (incoming + 8192 > fi.totalBytes - fi.usedBytes) { // keep safety margin
    return false;
  }
  if (incoming > MAX_UPLOAD_SIZE) return false;
  return true;
}

// Ensure patterns directory exists
void ensurePatternsDir() {
  if (!LittleFS.exists(PATTERNS_DIR)) {
    LittleFS.mkdir(PATTERNS_DIR);
  }
}

// Save metadataDoc to disk
void saveMetadata() {
  ensurePatternsDir();
  File f = LittleFS.open(String(PATTERNS_DIR) + "/metadata.json", "w");
  if (f) {
    serializeJson(metadataDoc, f);
    f.close();
  } else {
    Serial.println("Failed to save metadata.json");
  }
}

// Load metadataDoc from disk
void loadMetadata() {
  ensurePatternsDir();
  if (LittleFS.exists(String(PATTERNS_DIR) + "/metadata.json")) {
    File f = LittleFS.open(String(PATTERNS_DIR) + "/metadata.json", "r");
    if (f) {
      DeserializationError err = deserializeJson(metadataDoc, f);
      if (err) {
        Serial.println("metadata.json parse error, resetting metadata");
        metadataDoc.clear();
      }
      f.close();
    }
  }
}

////////// File upload handlers //////////

// Handler for full upload (/upload) - requires ?token=...
void handleUpload() {
  if (!server.hasArg("token") || server.arg("token") != String(UPLOAD_TOKEN)) {
    server.send(401, "application/json", "{\"status\":\"error\",\"message\":\"Invalid token\"}");
    return;
  }

  HTTPUpload& upload = server.upload();
  static String filename;
  static File out;

  if (upload.status == UPLOAD_FILE_START) {
    filename = upload.filename;
    if (!filename.length()) filename = "upload.bin";
    String path = String(PATTERNS_DIR) + "/" + filename;
    Serial.printf("Upload start: %s, size=%u\n", filename.c_str(), (unsigned)upload.totalSize);

    if (!hasEnoughSpace(upload.totalSize)) {
      Serial.println("Not enough storage space for upload");
      server.send(413, "application/json", "{\"status\":\"error\",\"message\":\"Not enough storage space\"}");
      return;
    }

    // remove existing
    if (LittleFS.exists(path)) LittleFS.remove(path);

    out = LittleFS.open(path, "w");
    if (!out) {
      Serial.println("Failed to open file for writing");
      server.send(500, "application/json", "{\"status\":\"error\",\"message\":\"File create failed\"}");
      return;
    }
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    if (out) {
      out.write(upload.buf, upload.currentSize);
    }
  } else if (upload.status == UPLOAD_FILE_END) {
    if (out) {
      out.close();
      // Update metadata (frames & delay detection require user-provided values or separate metadata upload)
      size_t size = 0;
      String path = String(PATTERNS_DIR) + "/" + filename;
      File f = LittleFS.open(path, "r");
      if (f) {
        size = f.size();
        f.close();
      }
      // Store metadata default (user should upload metadata if required)
      JsonObject root = metadataDoc.as<JsonObject>();
      JsonObject patterns = root.createNestedObject("patterns");
      JsonObject entry = patterns.createNestedObject(filename);
      entry["size"] = size;
      entry["frames"] = (size / FRAME_BYTES);
      entry["delay"] = frameDelayMs; // default
      saveMetadata();

      Serial.printf("Upload end: %s (%u bytes)\n", filename.c_str(), (unsigned)size);
      server.send(200, "application/json", "{\"status\":\"success\",\"file\":\"" + filename + "\"}");
      return;
    }
  }
}

// Handler for chunked upload (/upload-chunked) - requires ?token=...
// The client must send 'chunk_name' parameter to name the chunk file (e.g. chunk_001.bin)
void handleUploadChunked() {
  if (!server.hasArg("token") || server.arg("token") != String(UPLOAD_TOKEN)) {
    server.send(401, "application/json", "{\"status\":\"error\",\"message\":\"Invalid token\"}");
    return;
  }

  HTTPUpload& upload = server.upload();
  static String chunkName;
  static File out;
  static size_t totalWritten = 0;

  if (upload.status == UPLOAD_FILE_START) {
    chunkName = server.arg("chunk_name");
    if (chunkName.length() == 0) chunkName = upload.filename;
    String path = String(PATTERNS_DIR) + "/" + chunkName;

    Serial.printf("Chunk upload start: %s, size hint=%u\n", chunkName.c_str(), (unsigned)upload.totalSize);

    if (!hasEnoughSpace(upload.totalSize)) {
      server.send(413, "application/json", "{\"status\":\"error\",\"message\":\"Not enough storage\"}");
      return;
    }

    if (LittleFS.exists(path)) {
      // remove or append? For chunk uploads we create/overwrite
      LittleFS.remove(path);
    }

    out = LittleFS.open(path, "w");
    totalWritten = 0;
    if (!out) {
      Serial.println("Failed to open chunk file for write");
      server.send(500, "application/json", "{\"status\":\"error\",\"message\":\"File create failed\"}");
      return;
    }
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    if (out) {
      out.write(upload.buf, upload.currentSize);
      totalWritten += upload.currentSize;
    }
  } else if (upload.status == UPLOAD_FILE_END) {
    if (out) {
      out.close();
      // Update metadata entry for the chunk
      String path = String(PATTERNS_DIR) + "/" + chunkName;
      File f = LittleFS.open(path, "r");
      size_t size = f ? f.size() : totalWritten;
      if (f) f.close();

      loadMetadata();
      JsonObject root = metadataDoc.as<JsonObject>();
      if (!root.containsKey("patterns")) root.createNestedObject("patterns");
      JsonObject patterns = root["patterns"].as<JsonObject>();
      JsonObject entry = patterns.createNestedObject(chunkName.c_str());
      entry["size"] = size;
      entry["frames"] = (size / FRAME_BYTES);
      entry["delay"] = frameDelayMs; // default; user can later modify via /set-metadata
      saveMetadata();

      Serial.printf("Chunk upload complete: %s (%u bytes)\n", chunkName.c_str(), (unsigned)size);
      server.send(200, "application/json", "{\"status\":\"success\",\"chunk\":\"" + chunkName + "\"}");
      return;
    }
  }
}

// Set metadata for a specific pattern: POST JSON { "file":"name.bin", "frames":N, "delay":50 }
// Requires ?token=
void handleSetMetadata() {
  if (!server.hasArg("token") || server.arg("token") != String(UPLOAD_TOKEN)) {
    server.send(401, "application/json", "{\"status\":\"error\",\"message\":\"Invalid token\"}");
    return;
  }
  if (server.method() != HTTP_POST) {
    server.send(405, "application/json", "{\"status\":\"error\",\"message\":\"Use POST with JSON body\"}");
    return;
  }

  String body = server.arg("plain");
  if (body.length() == 0) {
    server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Empty body\"}");
    return;
  }

  DynamicJsonDocument doc(1024);
  DeserializationError err = deserializeJson(doc, body);
  if (err) {
    server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Invalid JSON\"}");
    return;
  }

  const char* fname = doc["file"];
  if (!fname) {
    server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"file missing\"}");
    return;
  }
  size_t frames = doc["frames"] | 0;
  unsigned long delayMs = doc["delay"] | frameDelayMs;

  loadMetadata();
  JsonObject root = metadataDoc.as<JsonObject>();
  if (!root.containsKey("patterns")) root.createNestedObject("patterns");
  JsonObject patterns = root["patterns"].as<JsonObject>();
  JsonObject entry = patterns.createNestedObject(fname);
  entry["frames"] = frames;
  entry["delay"] = delayMs;
  // keep size if present
  String path = String(PATTERNS_DIR) + "/" + fname;
  if (LittleFS.exists(path)) {
    File f = LittleFS.open(path, "r");
    if (f) { entry["size"] = f.size(); f.close(); }
  }
  saveMetadata();

  server.send(200, "application/json", "{\"status\":\"success\",\"file\":\"" + String(fname) + "\"}");
}

// Start playback of a file: GET /play?file=name.bin
void handlePlay() {
  if (!server.hasArg("file")) { server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"file param required\"}"); return; }
  String fname = server.arg("file");
  String path = String(PATTERNS_DIR) + "/" + fname;
  if (!LittleFS.exists(path)) { server.send(404, "application/json", "{\"status\":\"error\",\"message\":\"file not found\"}"); return; }

  if (playing && currentPatternPath == path) {
    server.send(200, "application/json", "{\"status\":\"ok\",\"message\":\"already playing\"}");
    return;
  }

  if (playbackFile) {
    playbackFile.close();
    playbackFile = File();
  }

  playbackFile = LittleFS.open(path, "r");
  if (!playbackFile) { server.send(500, "application/json", "{\"status\":\"error\",\"message\":\"open failed\"}"); return; }

  // Load metadata entry for delay and frames
  loadMetadata();
  JsonObject root = metadataDoc.as<JsonObject>();
  frameDelayMs = 100;
  totalFrames = 0;
  if (root.containsKey("patterns")) {
    JsonObject patterns = root["patterns"].as<JsonObject>();
    if (patterns.containsKey(fname)) {
      JsonObject entry = patterns[fname].as<JsonObject>();
      frameDelayMs = entry["delay"] | frameDelayMs;
      totalFrames = entry["frames"] | (playbackFile.size() / FRAME_BYTES);
    }
  } else {
    totalFrames = playbackFile.size() / FRAME_BYTES;
  }

  currentPatternPath = path;
  currentFrame = 0;
  playing = true;
  lastFrameMillis = millis() - frameDelayMs; // trigger immediate frame
  server.send(200, "application/json", "{\"status\":\"playing\",\"file\":\"" + fname + "\",\"frames\":" + String(totalFrames) + "}");
}

// Stop playback
void handleStop() {
  playing = false;
  if (playbackFile) { playbackFile.close(); }
  server.send(200, "application/json", "{\"status\":\"stopped\"}");
}

// Status endpoint (GET)
void handleStatus() {
  String resp = "{";
  resp += "\"uptime\":" + String(millis()) + ",";
  resp += "\"free_heap\":" + String(ESP.getFreeHeap()) + ",";
  resp += "\"playing\":" + String(playing ? "true" : "false") + ",";
  resp += "\"current_file\":\"" + currentPatternPath + "\"";
  resp += "}";
  server.send(200, "application/json", resp);
}

// Serve simple root page with upload forms (no auth in UI; forms must include token in URL)
void handleRoot() {
  String page = "<!doctype html><html><head><meta charset='utf-8'><title>ESP Matrix Uploader</title></head><body>";
  page += "<h2>ESP Matrix Uploader</h2>";
  page += "<p>Upload token must be supplied as <code>?token=...</code></p>";
  page += "<h3>Full Upload</h3>";
  page += "<form method='POST' action='/upload?token=" + String(UPLOAD_TOKEN) + "' enctype='multipart/form-data'>";
  page += "<input type='file' name='file'><input type='submit' value='Upload'></form>";
  page += "<h3>Chunk Upload</h3>";
  page += "<form method='POST' action='/upload-chunked?token=" + String(UPLOAD_TOKEN) + "' enctype='multipart/form-data'>";
  page += "<input type='text' name='chunk_name' placeholder='chunk_001.bin' required><br>";
  page += "<input type='file' name='file'><input type='submit' value='Upload Chunk'></form>";
  page += "<h3>Playback</h3>";
  page += "<form method='GET' action='/play'><input type='text' name='file' placeholder='name.bin'><input type='submit' value='Play'></form>";
  page += "<form method='GET' action='/stop'><input type='submit' value='Stop'></form>";
  page += "<p><a href='/status'>Status JSON</a></p>";
  page += "</body></html>";
  server.send(200, "text/html", page);
}

////////// Setup & Loop //////////
void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("=== ESP Matrix Uploader (FastLED) ===");

  // LittleFS init
  if (!LittleFS.begin()) {
    Serial.println("LittleFS begin failed - device may need formatting");
  } else {
    Serial.println("LittleFS mounted");
  }
  ensurePatternsDir();
  loadMetadata();

  // FastLED init
  FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
  FastLED.setBrightness(120);

  // Start AP
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(IPAddress(192,168,4,1), IPAddress(192,168,4,1), IPAddress(255,255,255,0));
  bool apOk = WiFi.softAP(apSSID, apPASS);
  if (apOk) {
    Serial.print("AP started: ");
    Serial.println(apSSID);
    Serial.print("IP: ");
    Serial.println(WiFi.softAPIP());
  } else {
    Serial.println("AP start failed");
  }

  // Web routes
  server.on("/", HTTP_GET, handleRoot);
  server.on("/upload", HTTP_POST, [](){ server.send(200); }, handleUpload);
  server.on("/upload-chunked", HTTP_POST, [](){ server.send(200); }, handleUploadChunked);
  server.on("/set-metadata", HTTP_POST, handleSetMetadata);
  server.on("/play", HTTP_GET, handlePlay);
  server.on("/stop", HTTP_GET, handleStop);
  server.on("/status", HTTP_GET, handleStatus);

  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();

  // Non-blocking playback
  if (playing && playbackFile) {
    unsigned long now = millis();
    if ((now - lastFrameMillis) >= frameDelayMs) {
      // Read one frame
      size_t framePos = currentFrame * FRAME_BYTES;
      if (framePos + FRAME_BYTES > playbackFile.size()) {
        // end or loop
        currentFrame = 0;
        playbackFile.seek(0);
      } else {
        playbackFile.seek(framePos);
      }

      // read into buffer
      static uint8_t frameBuf[1024]; // ensure frameBuf >= FRAME_BYTES if NUM_LEDS*3 <= 1024; otherwise dynamic read
      if (FRAME_BYTES <= sizeof(frameBuf)) {
        size_t r = playbackFile.read(frameBuf, FRAME_BYTES);
        if (r == FRAME_BYTES) {
          // copy into leds
          for (uint16_t i = 0; i < NUM_LEDS; i++) {
            uint16_t idx = i * 3;
            leds[i].r = frameBuf[idx];
            leds[i].g = frameBuf[idx + 1];
            leds[i].b = frameBuf[idx + 2];
          }
          FastLED.show();
        } else {
          // short read — stop
          Serial.println("Frame read short; stopping playback");
          playing = false;
          playbackFile.close();
        }
      } else {
        // handle large frames by streaming in chunks
        size_t toRead = FRAME_BYTES;
        size_t readSoFar = 0;
        while (readSoFar < FRAME_BYTES) {
          size_t chunk = min((size_t)512, FRAME_BYTES - readSoFar);
          size_t r = playbackFile.read(frameBuf, chunk);
          if (!r) { playing = false; playbackFile.close(); break; }
          // write into leds progressively
          for (size_t p = 0; p < r; p++) {
            size_t absolute = readSoFar + p;
            uint16_t ledIndex = absolute / 3;
            uint8_t colorByte = frameBuf[p];
            uint8_t channel = absolute % 3; // 0:R,1:G,2:B
            if (ledIndex < NUM_LEDS) {
              if (channel == 0) leds[ledIndex].r = colorByte;
              else if (channel == 1) leds[ledIndex].g = colorByte;
              else leds[ledIndex].b = colorByte;
            }
          }
          readSoFar += r;
        }
        FastLED.show();
      }

      currentFrame++;
      if (currentFrame >= totalFrames && totalFrames > 0) {
        // loop back
        currentFrame = 0;
        playbackFile.seek(0);
      }
      lastFrameMillis = now;
    }
  }
}
