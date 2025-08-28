# Enhanced ESP-01 LED Matrix Firmware

## Overview
This is an enhanced version of the ESP-01 LED Matrix firmware with advanced features including WiFi management, OTA updates, enhanced LED control, and comprehensive system monitoring.

## Features

### 🚀 Core Features
- **File Upload & Storage**: Upload LED matrix data files (.bin, .txt, .hex)
- **Hash Verification**: File integrity checking with checksum verification
- **Web Interface**: Modern, responsive web UI for device management
- **Real-time Monitoring**: Live system status and performance metrics

### 📡 WiFi Management
- **WiFi Manager Integration**: Easy WiFi configuration via captive portal
- **Dual Mode**: Connects to existing WiFi or creates access point
- **Configuration Persistence**: Saves WiFi credentials to flash memory
- **Fallback AP**: Automatically switches to AP mode if WiFi connection fails

### 💡 Enhanced LED Matrix Control
- **Play/Pause/Stop**: Control LED animation playback
- **Brightness Control**: Adjustable brightness levels (0-255)
- **Real-time Commands**: Instant LED control via web interface
- **Animation Management**: Start, pause, and stop LED patterns

### 🔧 System Management
- **OTA Updates**: Over-the-air firmware updates
- **System Reset Options**: WiFi reset, filesystem clear, full reset
- **Configuration Backup**: Save and restore device settings
- **Maintenance Tools**: Comprehensive system maintenance utilities

### 📊 Performance Monitoring
- **Memory Usage**: Real-time heap and fragmentation monitoring
- **CPU Metrics**: Frequency and cycle count tracking
- **System Health**: Comprehensive health check endpoints
- **Performance Analytics**: Detailed performance metrics

### 🔒 Security Features
- **Basic Authentication**: Password protection for sensitive operations
- **Secure Endpoints**: Protected system management functions
- **Access Control**: Configurable security levels
- **Admin Protection**: Secure administrative functions

### 📁 Advanced File Management
- **Multiple File Support**: Handle various file types and formats
- **File Information**: Detailed file metadata and hash verification
- **File Operations**: Download, delete, and manage uploaded files
- **Storage Optimization**: Efficient file system management

## Hardware Requirements

- **ESP-01 Module**: ESP8266-based WiFi module
- **Flash Memory**: 1MB (minimum)
- **RAM**: 80KB available
- **Power**: 3.3V regulated power supply
- **LED Matrix**: Compatible with standard LED matrix protocols

## Installation

### 1. Prerequisites
- Arduino IDE 1.8.x or later
- ESP8266 board package installed
- Required libraries:
  - `ESP8266WiFi`
  - `ESP8266WebServer`
  - `LittleFS`
  - `WiFiManager`
  - `ESP8266HTTPUpdate`

### 2. Upload Firmware
1. Connect ESP-01 to USB-to-TTL converter
2. Open `ESP01_Enhanced.ino` in Arduino IDE
3. Select correct board (ESP8266 Generic)
4. Upload firmware to device

### 3. First Boot
1. Device will start in AP mode with SSID "MatrixUploader"
2. Connect to the WiFi network
3. Navigate to `192.168.4.1` in your browser
4. Configure WiFi settings if desired

## Web Interface

### Main Dashboard
- **File Upload**: Drag & drop file upload interface
- **System Status**: Real-time device status
- **File Information**: Current uploaded file details
- **Quick Actions**: Download, delete, and manage files

### LED Matrix Control
- **Animation Controls**: Play, pause, and stop buttons
- **Brightness Slider**: Adjustable brightness control
- **Status Display**: Current animation state

### WiFi Configuration
- **Current Status**: Connection information and signal strength
- **Network Setup**: Configure new WiFi networks
- **Settings Management**: Save and manage WiFi credentials

### System Management
- **Reset Options**: Various system reset functions
- **Performance Monitor**: Real-time system metrics
- **OTA Updates**: Firmware update functionality

### Performance Monitoring
- **Memory Usage**: Heap and fragmentation statistics
- **CPU Metrics**: Frequency and performance data
- **System Health**: Overall device health status

## API Endpoints

### File Management
- `GET /` - Main web interface
- `POST /upload` - File upload endpoint
- `GET /download` - File download
- `POST /delete` - File deletion
- `GET /firmware-hash` - File hash verification
- `GET /file-list` - List all files
- `GET /file-info` - File information

### System Information
- `GET /system-info` - Basic system status
- `GET /fs-info` - File system information
- `GET /health` - Health check
- `GET /ping` - Connection test
- `GET /performance` - Performance metrics

### LED Control
- `GET /led-control` - LED matrix control
- `GET /wifi-config` - WiFi configuration
- `POST /wifi-config` - Save WiFi settings

### System Management
- `POST /system-reset` - System reset operations
- `POST /ota-update` - OTA firmware update

## Configuration

### WiFi Settings
```cpp
const char* ssid = "MatrixUploader";        // Default AP SSID
const char* password = "";                   // Default AP password
```

### Security Settings
```cpp
const char* adminPassword = "admin123";      // Admin password
bool authenticationEnabled = true;           // Enable/disable auth
```

### Upload Settings
```cpp
#define UPLOAD_BUFFER_SIZE 512              // Upload buffer size
const char* UPLOAD_FILE = "/temp_export_data.bin"; // Default upload file
```

## Usage Examples

### Upload LED Matrix Data
1. Prepare your LED matrix data file (.bin, .txt, or .hex)
2. Access the web interface at device IP address
3. Use the file upload form to upload your data
4. Verify upload success and file hash
5. Use LED control buttons to start animation

### Configure WiFi
1. Access WiFi configuration section
2. Enter your WiFi network credentials
3. Save configuration
4. Device will restart and connect to new network

### OTA Update
1. Host firmware binary on web server
2. Enter update URL in OTA section
3. Confirm update process
4. Device will download and install new firmware

### Monitor Performance
1. Access performance monitoring section
2. View real-time metrics
3. Monitor memory usage and system health
4. Use health check endpoints for diagnostics

## Troubleshooting

### Common Issues

#### Upload Failures
- Check file size (max 64KB for ESP-01)
- Verify WiFi connection stability
- Monitor memory usage during upload
- Check serial output for error messages

#### WiFi Connection Issues
- Ensure WiFi credentials are correct
- Check signal strength
- Try resetting WiFi settings
- Verify network compatibility

#### Memory Issues
- Monitor heap usage via web interface
- Reduce file sizes if possible
- Check for memory leaks in custom code
- Use performance monitoring tools

#### System Crashes
- Check power supply stability
- Monitor temperature
- Verify firmware compatibility
- Check serial output for crash logs

### Debug Information
- Serial output at 115200 baud
- Web interface status indicators
- Performance monitoring metrics
- Health check endpoints

## Development

### Adding New Features
1. Define new handler functions
2. Add endpoints to `setupWebServer()`
3. Update HTML interface as needed
4. Test thoroughly on hardware

### Customization
- Modify LED control logic in `handleLEDControl()`
- Adjust upload buffer sizes for your needs
- Customize web interface styling
- Add new API endpoints

### Testing
- Use built-in test endpoints
- Monitor serial output
- Test with various file types
- Verify memory usage patterns

## License
This project is open source. Please respect the original authors and contribute improvements.

## Support
For issues and questions:
1. Check the troubleshooting section
2. Review serial output for errors
3. Verify hardware connections
4. Test with minimal configuration

## Version History
- **v2.0**: Enhanced features, WiFi manager, OTA updates
- **v1.0**: Basic file upload and LED matrix support

---
**Note**: This firmware is optimized for ESP-01 modules with limited resources. For larger ESP8266 boards, consider increasing buffer sizes and adding more features.