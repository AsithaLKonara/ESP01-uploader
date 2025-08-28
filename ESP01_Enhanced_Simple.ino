/*
 * Simplified ESP-01 LED Matrix Firmware
 * Features: File storage, hash verification, system monitoring
 * Target: ESP-01 with 1MB flash (32KB usable for files)
 * No external libraries required - uses built-in ESP8266 features
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <LittleFS.h>
#include <Hash.h>

// WiFi Configuration
const char* ssid = "MatrixUploader";
const char* password = "12345678";

// Web Server
ESP8266WebServer server(80);

// File Management
const char* UPLOAD_FILE = "/temp_export_data.bin";

// System Status
unsigned long lastUploadTime = 0;
size_t lastUploadedSize = 0;
String lastUploadedHash = "";

void setup() {
  Serial.begin(115200);
  
  // Initialize LittleFS
  if (!LittleFS.begin()) {
    Serial.println("LittleFS initialization failed!");
    return;
  }
  
  // Setup WiFi Access Point
  WiFi.softAP(ssid, password);
  Serial.println("WiFi AP Started");
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());
  
  // Setup Web Server Routes
  setupWebServer();
  
  Serial.println("Enhanced ESP-01 LED Matrix Firmware Ready!");
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
  
  // Start server
  server.begin();
}

void handleRoot() {
  String html = R"(
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced LED Matrix Uploader</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; }
        .warning { background-color: #fff3cd; color: #856404; }
        .error { background-color: #f8d7da; color: #721c24; }
        .upload-form { border: 2px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; }
        .progress { width: 100%; height: 20px; background-color: #f0f0f0; border-radius: 10px; overflow: hidden; }
        .progress-bar { height: 100%; background-color: #4CAF50; width: 0%; transition: width 0.3s; }
        button { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #45a049; }
        input[type="file"] { margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Enhanced LED Matrix Uploader</h1>
        
        <div class="status success">
            <strong>Status:</strong> Ready for file upload
        </div>
        
        <div class="upload-form">
            <h3>Upload LED Matrix Data</h3>
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" id="fileInput" name="file" accept=".bin,.txt,.hex" required>
                <br>
                <button type="submit">Upload File</button>
            </form>
            <div class="progress" style="display: none;">
                <div class="progress-bar"></div>
            </div>
            <div id="uploadStatus"></div>
        </div>
        
        <div class="status warning">
            <strong>Important:</strong> Maximum file size: 32KB for ESP-01 compatibility
        </div>
        
        <h3>System Information</h3>
        <div id="systemInfo">Loading...</div>
        
        <h3>File System</h3>
        <div id="fileSystemInfo">Loading...</div>
        
        <h3>Current File</h3>
        <div id="currentFile">Loading...</div>
        
        <div style="margin-top: 20px;">
            <button onclick="refreshInfo()">Refresh Info</button>
            <button onclick="downloadFile()" id="downloadBtn" style="display: none;">Download File</button>
            <button onclick="deleteFile()" id="deleteBtn" style="display: none;">Delete File</button>
        </div>
    </div>

    <script>
        // Upload handling
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a file');
                return;
            }
            
            if (file.size > 32768) {
                alert('File too large! Maximum size is 32KB for ESP-01 compatibility.');
                return;
            }
            
            uploadFile(file);
        });
        
        function uploadFile(file) {
            const formData = new FormData();
            formData.append('file', file);
            
            const progressBar = document.querySelector('.progress-bar');
            const progressDiv = document.querySelector('.progress');
            const statusDiv = document.getElementById('uploadStatus');
            
            progressDiv.style.display = 'block';
            statusDiv.innerHTML = 'Uploading...';
            
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    progressBar.style.width = percentComplete + '%';
                }
            });
            
            xhr.addEventListener('load', function() {
                if (xhr.status === 200) {
                    statusDiv.innerHTML = '<span style="color: green;">Upload successful!</span>';
                    setTimeout(refreshInfo, 1000);
                } else {
                    statusDiv.innerHTML = '<span style="color: red;">Upload failed: ' + xhr.statusText + '</span>';
                }
                progressDiv.style.display = 'none';
            });
            
            xhr.addEventListener('error', function() {
                statusDiv.innerHTML = '<span style="color: red;">Upload failed</span>';
                progressDiv.style.display = 'none';
            });
            
            xhr.open('POST', '/upload');
            xhr.send(formData);
        }
        
        function refreshInfo() {
            // Load system info
            fetch('/system-info')
                .then(response => response.text())
                .then(data => {
                    document.getElementById('systemInfo').innerHTML = data;
                });
            
            // Load file system info
            fetch('/fs-info')
                .then(response => response.text())
                .then(data => {
                    document.getElementById('fileSystemInfo').innerHTML = data;
                });
            
            // Load current file info
            fetch('/firmware-hash')
                .then(response => response.text())
                .then(data => {
                    document.getElementById('currentFile').innerHTML = data;
                    
                    // Show/hide download/delete buttons based on content
                    const hasFile = data.indexOf('No file uploaded') === -1;
                    document.getElementById('downloadBtn').style.display = hasFile ? 'inline-block' : 'none';
                    document.getElementById('deleteBtn').style.display = hasFile ? 'inline-block' : 'none';
                });
        }
        
        function downloadFile() {
            window.open('/download', '_blank');
        }
        
        function deleteFile() {
            if (confirm('Are you sure you want to delete the uploaded file?')) {
                fetch('/delete', { method: 'POST' })
                    .then(response => response.text())
                    .then(data => {
                        if (data.indexOf('success') !== -1) {
                            alert('File deleted successfully');
                            refreshInfo();
                        } else {
                            alert('Failed to delete file');
                        }
                    });
            }
        }
        
        // Auto-refresh every 5 seconds
        setInterval(refreshInfo, 5000);
        
        // Initial load
        refreshInfo();
    </script>
</body>
</html>
  )";
  
  server.send(200, "text/html", html);
}

void handleFileUpload() {
  HTTPUpload& upload = server.upload();
  
  if (upload.status == UPLOAD_FILE_START) {
    // Delete existing file
    if (LittleFS.exists(UPLOAD_FILE)) {
      LittleFS.remove(UPLOAD_FILE);
    }
    
    Serial.println("File upload started");
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    // Write file data
    File file = LittleFS.open(UPLOAD_FILE, "a");
    if (file) {
      file.write(upload.buf, upload.currentSize);
      file.close();
      Serial.printf("Wrote %d bytes\n", upload.currentSize);
    }
  } else if (upload.status == UPLOAD_FILE_END) {
    // Upload complete
    Serial.println("File upload complete");
    
    // Calculate file hash
    File file = LittleFS.open(UPLOAD_FILE, "r");
    if (file) {
      lastUploadedSize = file.size();
      lastUploadedHash = calculateFileHash(file);
      file.close();
      
      lastUploadTime = millis();
      
      Serial.printf("File uploaded: %d bytes, hash: %s\n", lastUploadedSize, lastUploadedHash.c_str());
    }
  }
}

void handleUploadSuccess() {
  server.send(200, "text/plain", "Upload successful");
}

void handleSystemInfo() {
  String response = "Status: Running<br>";
  response += "Free Heap: " + String(ESP.getFreeHeap()) + " bytes<br>";
  response += "Flash Size: " + String(ESP.getFlashChipSize()) + " bytes<br>";
  response += "Last Upload: " + (lastUploadTime > 0 ? String(lastUploadTime / 1000) + "s ago" : "Never");
  
  server.send(200, "text/html", response);
}

void handleFileSystemInfo() {
  FSInfo fs_info;
  LittleFS.info(fs_info);
  
  String response = "Total Space: " + String(fs_info.totalBytes) + " bytes<br>";
  response += "Used Space: " + String(fs_info.usedBytes) + " bytes<br>";
  response += "Free Space: " + String(fs_info.totalBytes - fs_info.usedBytes) + " bytes<br>";
  response += "Files: " + String(countFiles());
  
  server.send(200, "text/html", response);
}

void handleFirmwareHash() {
  if (LittleFS.exists(UPLOAD_FILE)) {
    File file = LittleFS.open(UPLOAD_FILE, "r");
    if (file) {
      String response = "File: " + String(UPLOAD_FILE) + "<br>";
      response += "Size: " + String(file.size()) + " bytes<br>";
      response += "Hash: " + calculateFileHash(file);
      file.close();
      server.send(200, "text/html", response);
    } else {
      server.send(200, "text/html", "File: Error<br>Size: 0 bytes<br>Hash: ");
    }
  } else {
    server.send(200, "text/html", "No file uploaded");
  }
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
  if (LittleFS.exists(UPLOAD_FILE)) {
    if (LittleFS.remove(UPLOAD_FILE)) {
      lastUploadedSize = 0;
      lastUploadedHash = "";
      lastUploadTime = 0;
      
      server.send(200, "text/plain", "success: File deleted successfully");
    } else {
      server.send(200, "text/plain", "error: Failed to delete file");
    }
  } else {
    server.send(200, "text/plain", "error: File not found");
  }
}

String calculateFileHash(File& file) {
  file.seek(0);
  
  SHA256 sha256;
  uint8_t buffer[64];
  size_t bytesRead;
  
  while ((bytesRead = file.read(buffer, sizeof(buffer))) > 0) {
    sha256.update(buffer, bytesRead);
  }
  
  uint8_t hash[SHA256_SIZE];
  sha256.finalize(hash);
  
  String hashString = "";
  for (int i = 0; i < SHA256_SIZE; i++) {
    hashString += String(hash[i], HEX);
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
  
  // Output LED matrix data if file exists
  if (LittleFS.exists(UPLOAD_FILE) && lastUploadedSize > 0) {
    outputLEDMatrixData();
  }
  
  delay(100);
}

void outputLEDMatrixData() {
  File file = LittleFS.open(UPLOAD_FILE, "r");
  if (file) {
    Serial.println("=== LED Matrix Data Output ===");
    
    // Read and output data in chunks
    uint8_t buffer[64];
    size_t bytesRead;
    int frameCount = 0;
    
    while ((bytesRead = file.read(buffer, sizeof(buffer))) > 0) {
      Serial.printf("Frame %d: ", frameCount++);
      for (size_t i = 0; i < bytesRead; i++) {
        Serial.printf("%02X ", buffer[i]);
      }
      Serial.println();
      
      // Simulate LED output delay
      delay(100);
    }
    
    file.close();
    Serial.println("=== End LED Matrix Data ===");
  }
}
