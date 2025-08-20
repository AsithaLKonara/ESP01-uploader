# ESP-01 WiFi OTA Firmware Uploader

## 🎯 Project Overview

A Windows-based graphical application for uploading firmware files to ESP-01 modules over WiFi using the **OTA (Over-The-Air)** protocol. This tool implements the ArduinoOTA protocol for reliable WiFi firmware updates without requiring USB connections.

## 🔧 Key Technical Concepts

### OTA vs Traditional Upload Methods

| Method | Description | Pros | Cons |
|--------|-------------|------|------|
| **UART/Serial** | Traditional USB connection with esptool.py | Reliable, works with any ESP | Requires physical connection |
| **OTA (WiFi)** | Over-the-air updates via WiFi | No physical connection needed | Requires ESP to have OTA firmware |

### Why OTA is the Right Approach

- ✅ **esptool.py cannot work over WiFi** - ESP8266 bootloader only speaks UART
- ✅ **ArduinoOTA is the standard** - Used by Arduino IDE and other tools
- ✅ **Reliable protocol** - Built-in error checking and verification
- ✅ **Industry standard** - Compatible with existing ESP development tools

## 🚀 Getting Started

### Prerequisites

1. **ESP-01 Module** with WiFi capability
2. **Windows 10/11** (64-bit)
3. **Python 3.8+** with required packages
4. **Arduino IDE** (for initial firmware upload)

### Step 1: Initial ESP-01 Setup

**IMPORTANT**: You must first upload the OTA firmware via USB!

1. Connect ESP-01 to USB via USB-to-TTL converter
2. Open `esp01_firmware_example.ino` in Arduino IDE
3. Select correct board: "Generic ESP8266 Module"
4. Upload via USB (Tools → Upload)
5. **Verify upload success** - ESP-01 should create WiFi AP

### Step 2: WiFi Connection

1. **Power ESP-01** (can now disconnect USB)
2. **Connect to WiFi**: `ESP01_AP` (Password: `12345678`)
3. **Verify connection**: ESP-01 IP should be `192.168.4.1`

### Step 3: Test OTA Connection

```bash
python test_ota_connection.py
```

Expected output:
```
=== Testing ESP-01 OTA Connection ===
Attempting to connect to ESP-01 OTA service at 192.168.4.1:8266
Connecting to OTA service...
✓ Connected to ESP-01 OTA service!
✓ OTA header acknowledged - protocol working!
✓ Test block acknowledged - OTA protocol fully functional!
```

### Step 4: Run Main Application

```bash
python main.py
```

## 📁 Project Structure

```
ESP01/
├── main.py                    # Main GUI application
├── esp_uploader.py           # OTA upload implementation
├── wifi_manager.py           # WiFi connection management
├── led_matrix_preview.py     # LED matrix visualization
├── file_manager.py           # File operations
├── esp01_firmware_example.ino # ESP-01 OTA firmware
├── test_ota_connection.py    # OTA connection testing
├── requirements.txt          # Python dependencies
└── quick_start.bat          # Windows installer
```

## 🔌 ESP-01 Firmware Features

### WiFi Configuration
- **SSID**: `ESP01_AP`
- **Password**: `12345678`
- **IP Address**: `192.168.4.1`
- **OTA Port**: `8266`

### OTA Protocol Implementation
- **ArduinoOTA library** for standard compatibility
- **TCP socket communication** on port 8266
- **Block-based upload** with acknowledgment
- **MD5 hash verification** for integrity

### Web Interface
- **Status endpoint**: `http://192.168.4.1/status`
- **Memory info**: `http://192.168.4.1/memory`
- **Device info**: `http://192.168.4.1/info`
- **Reset endpoint**: `http://192.168.4.1/reset`

## 📤 Upload Process

### 1. Connection Phase
```
User connects to ESP01_AP WiFi → Application connects to 192.168.4.1:8266
```

### 2. OTA Handshake
```
Send OTA header → ESP-01 acknowledges → Begin firmware transfer
```

### 3. Firmware Transfer
```
Split firmware into blocks → Send each block → Wait for ACK → Repeat
```

### 4. Verification
```
ESP-01 calculates MD5 hash → Compare with local hash → Success/failure
```

## 🧪 Testing & Troubleshooting

### Connection Test
```bash
python test_ota_connection.py
```

### Manual OTA Test
```bash
# Using espota.py (if available)
python espota.py -i 192.168.4.1 -p 8266 -f your_firmware.bin

# Using Arduino IDE
# Tools → Upload via Network → Enter IP: 192.168.4.1
```

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| **Connection refused** | ESP-01 not running OTA firmware | Upload OTA firmware via USB first |
| **Timeout** | WiFi signal weak | Move closer to ESP-01 |
| **Upload fails** | Insufficient memory | Check ESP-01 free heap |
| **No WiFi AP** | ESP-01 not powered | Check power supply |

### Debug Information

**ESP-01 Serial Output** (if connected via USB):
```
=== ESP-01 WiFi OTA Firmware ===
WiFi AP started: 192.168.4.1
SSID: ESP01_AP
Password: 12345678
OTA Port: 8266
Web Interface: http://192.168.4.1
ESP-01 ready for OTA updates!
```

**Web Status Check**:
```bash
curl http://192.168.4.1/status
```

## 🔄 OTA Protocol Details

### Header Format
```
[command][size][md5][block_size][block_count]
- command: 0x01 (Flash command)
- size: Firmware size in bytes
- md5: 32-byte MD5 hash (padded)
- block_size: Size of each block (1024 bytes)
- block_count: Total number of blocks
```

### Block Format
```
[block_num][block_size][block_data]
- block_num: Sequential block number
- block_size: Size of this block
- block_data: Actual firmware data
```

### Acknowledgment
- **Header ACK**: 0x06 byte after header
- **Block ACK**: 0x06 byte after each block
- **Timeout**: 30 seconds for entire operation

## 🎨 LED Matrix Preview

### Supported Formats
- **LED Matrix Studio**: `.lms` files
- **JSON**: Custom pattern format
- **Text/CSV**: Simple matrix data
- **Binary**: Raw LED data

### Features
- **Virtual Display**: 8x8, 16x16, 32x32 matrices
- **Pattern Playback**: Animated LED sequences
- **Real-time Control**: Play, pause, speed adjustment
- **Export Options**: Save patterns in various formats

## ⚙️ Configuration

### Application Settings
```ini
[DEFAULT]
default_ip = 192.168.4.1
default_port = 8266
default_stream = false  # OTA always streams to flash
default_verify = true
chunk_size = 1024
timeout = 30.0
retry_count = 3
retry_delay = 1.0
```

### WiFi Settings
- **Connection Type**: Access Point mode
- **Security**: WPA2-PSK
- **Channel**: Auto-selected
- **Max Clients**: 4 simultaneous connections

## 🚀 Advanced Usage

### Batch Uploads
```python
from esp_uploader import ESPUploader
from wifi_manager import WiFiManager

uploader = ESPUploader()
wifi_mgr = WiFiManager()

# Connect to ESP-01
wifi_mgr.connect("192.168.4.1", 8266)

# Upload multiple files
files = ["firmware1.bin", "firmware2.bin", "data.dat"]
for file_path in files:
    success = uploader.upload_file(file_path, wifi_mgr)
    print(f"Upload {file_path}: {'Success' if success else 'Failed'}")
```

### Custom OTA Implementation
```python
# Custom OTA client
import socket
import struct

def custom_ota_upload(esp_ip, file_path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((esp_ip, 8266))
    
    # Send OTA header
    header = struct.pack('<II32sII', 0x01, file_size, md5_hash, 1024, block_count)
    sock.send(header)
    
    # Handle response and upload blocks
    # ... implementation details
```

## 🔍 Monitoring & Logging

### Upload Log
- **Progress tracking**: Real-time percentage and byte count
- **Error logging**: Detailed error messages and stack traces
- **Timing information**: Upload duration and speed metrics

### ESP-01 Monitoring
- **Serial output**: Real-time status via USB connection
- **Web interface**: Status page with device information
- **LED indicators**: Visual feedback during operations

## 🛠️ Development

### Building from Source
```bash
git clone <repository>
cd ESP01
pip install -r requirements.txt
python main.py
```

### Testing
```bash
# Run all tests
python test_ota_connection.py

# Test specific components
python -c "from esp_uploader import ESPUploader; print('OK')"
```

### Contributing
1. Fork the repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Submit pull request

## 📚 References

### ESP8266 Documentation
- [ESP8266 Arduino Core](https://github.com/esp8266/Arduino)
- [ArduinoOTA Library](https://github.com/esp8266/Arduino/tree/master/libraries/ArduinoOTA)
- [ESP8266 WiFi Documentation](https://docs.espressif.com/projects/esp8266-rtos-sdk/en/latest/api-guides/wifi.html)

### OTA Protocol
- [ArduinoOTA Protocol](https://github.com/esp8266/Arduino/blob/master/libraries/ArduinoOTA/ArduinoOTA.cpp)
- [ESP8266 OTA Examples](https://github.com/esp8266/Arduino/tree/master/libraries/ArduinoOTA/examples)

### Related Tools
- [esptool.py](https://github.com/espressif/esptool) - Serial flashing tool
- [espota.py](https://github.com/esp8266/Arduino/blob/master/tools/espota.py) - Command-line OTA tool

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

### Getting Help
1. Check this README and troubleshooting section
2. Run connection tests to identify issues
3. Check ESP-01 serial output for errors
4. Verify WiFi connection and IP address

### Reporting Issues
When reporting issues, please include:
- ESP-01 firmware version
- Python version and package versions
- Error messages and logs
- Steps to reproduce the issue

---

**Happy OTA Flashing! 🚀**

*Remember: OTA updates require the ESP-01 to have OTA firmware loaded first via USB.*
