# J Tech Pixel LED ESP01 Uploader

**Professional ESP-01 WiFi Firmware Uploader with LED Matrix Support**

A comprehensive Windows-based graphical application for uploading firmware and data files to ESP-01 modules over WiFi, with automatic requirements management, SHA256 verification, and LED Matrix pattern preview capabilities.

## 🚀 Features

### ✨ **Core Functionality**
- **WiFi File Upload**: Upload `.bin`, `.hex`, `.dat`, `.lms`, `.json`, `.txt`, and `.csv` files to ESP-01
- **Automatic Requirements Management**: Self-installing Python dependencies
- **Smart Verification**: SHA256 hash verification for upload integrity
- **Real-time Progress**: Live upload progress monitoring with detailed logging
- **Upload History**: Track and verify previous uploads

### 🔧 **ESP-01 Integration**
- **HTTP Upload Protocol**: Works with existing ESP-01 firmware
- **Smart Connectivity**: Automatic ESP-01 detection and connection testing
- **Multiple File Formats**: Support for firmware, data, and LED matrix files
- **Verification System**: Local hash calculation and upload success confirmation

### 🎨 **LED Matrix Support**
- **Pattern Preview**: Virtual LED matrix emulator for pattern visualization
- **Multiple Sizes**: Support for 8x8, 16x16, 32x32, and 64x64 matrices
- **File Format Support**: Native LED Matrix Studio (.lms) file support
- **Playback Controls**: Speed control and pattern animation

### 📊 **Professional Features**
- **Comprehensive Logging**: Detailed step-by-step process logging
- **Upload Reports**: Export detailed upload history and verification data
- **Configuration Management**: Persistent settings and connection preferences
- **Error Handling**: Robust error handling with user-friendly messages

## 🛠️ Installation

### **Prerequisites**
- Windows 10/11
- Python 3.8 or higher
- ESP-01 module with WiFi capability

### **Quick Start**
1. **Clone or Download** the project files
2. **Run the Application**:
   ```bash
   python main.py
   ```
3. **Automatic Setup**: The application will automatically check and install required dependencies

### **Manual Installation** (if needed)
```bash
pip install -r requirements.txt
```

## 📱 Usage

### **1. Connect to ESP-01**
- Enter your ESP-01's IP address (default: 192.168.4.1)
- Click "Connect" to test connectivity
- Status will show connection status

### **2. Select and Upload Files**
- Click "Browse" to select your file
- Choose upload options (verification, streaming)
- Click "Upload File" to begin
- Monitor progress in real-time

### **3. Monitor Upload Process**
- **Step 1**: Requirements check and installation
- **Step 2**: File validation
- **Step 3**: ESP-01 connectivity test
- **Step 4**: SHA256 hash calculation
- **Step 5**: File upload via HTTP
- **Step 6**: Upload verification

### **4. LED Matrix Preview**
- Switch to "LED Matrix Preview" tab
- Load `.lms` pattern files
- Preview patterns on virtual matrix
- Control playback speed and matrix size

## 🔌 ESP-01 Firmware Requirements

The uploader works with ESP-01 modules that have:
- **HTTP Server**: Web server running on port 80
- **Upload Endpoint**: `/upload` endpoint for file uploads
- **WiFi Access Point**: ESP-01 creates its own WiFi network

### **Default ESP-01 Settings**
- **SSID**: ESP01_AP
- **Password**: 12345678
- **IP Address**: 192.168.4.1
- **Port**: 80

## 📁 Supported File Formats

| Format | Extension | Description | Use Case |
|--------|-----------|-------------|----------|
| Binary | `.bin` | Raw binary data | Firmware, data files |
| Intel HEX | `.hex` | Intel HEX format | Firmware, memory dumps |
| Data | `.dat` | Generic data files | Configuration, data storage |
| LED Matrix Studio | `.lms` | LED pattern files | LED matrix animations |
| JSON | `.json` | JSON data files | Configuration, data exchange |
| Text | `.txt` | Plain text files | Logs, configuration |
| CSV | `.csv` | Comma-separated values | Data tables, logs |

## 🏗️ Architecture

### **Core Components**
- **`SmartESPUploaderWithRequirements`**: Main uploader with auto-requirements
- **`RequirementsManager`**: Automatic dependency management
- **`LEDMatrixPreview`**: LED matrix visualization engine
- **`FileManager`**: File operations and configuration
- **`WiFiManager`**: Network connectivity management

### **Key Features**
- **Thread-safe Operations**: Concurrent uploads and UI updates
- **Callback System**: Real-time progress and status updates
- **Error Recovery**: Graceful error handling and user feedback
- **Configuration Persistence**: Save and restore user preferences

## 🔒 Security Features

### **Upload Verification**
- **SHA256 Hashing**: Local file hash calculation
- **Upload Confirmation**: HTTP 200 response verification
- **File Integrity**: Size and hash consistency checking
- **Smart Verification**: Combines local hash with upload success

### **Data Protection**
- **Local Processing**: File hashes calculated locally
- **No Data Storage**: Upload history stored locally only
- **Secure Protocols**: HTTP over local network only

## 📊 Monitoring and Reporting

### **Real-time Logging**
- **Timestamped Entries**: Every action logged with time
- **Step-by-step Process**: Detailed upload workflow logging
- **Error Tracking**: Comprehensive error logging and reporting
- **Progress Updates**: Real-time upload progress monitoring

### **Upload Reports**
- **JSON Export**: Detailed upload history and verification data
- **Requirements Status**: Package installation and availability reports
- **ESP Interface**: Connection and capability information
- **Verification Results**: Hash verification and upload status

## 🎯 Use Cases

### **ESP-01 Development**
- Firmware updates and testing
- Configuration file uploads
- Data file transfers
- Development and debugging

### **LED Matrix Projects**
- Pattern file uploads
- Animation testing
- Pattern verification
- Project development

### **IoT Applications**
- Sensor configuration
- Data logging setup
- Remote updates
- Configuration management

## 🚨 Troubleshooting

### **Common Issues**

#### **Connection Failed**
- Verify ESP-01 is powered and running
- Check WiFi connection to ESP-01 network
- Confirm IP address (default: 192.168.4.1)
- Ensure ESP-01 web server is running

#### **Upload Failed**
- Check file size and format
- Verify ESP-01 has sufficient storage
- Check upload endpoint availability
- Review error logs for specific issues

#### **Requirements Issues**
- Application automatically installs missing packages
- Check internet connection for package downloads
- Verify Python version compatibility
- Review requirements.txt for dependencies

### **Debug Mode**
Enable detailed logging by checking the log tab during operations. All steps are logged with timestamps for easy troubleshooting.

## 🔄 Updates and Maintenance

### **Automatic Updates**
- Requirements are automatically checked on startup
- Missing packages are automatically installed
- No manual intervention required

### **Configuration Backup**
- Settings are automatically saved
- Configuration persists between sessions
- Easy backup and restore of preferences

## 📈 Performance

### **Upload Speeds**
- **Small Files** (< 1KB): Near-instantaneous
- **Medium Files** (1KB - 100KB): 1-5 seconds
- **Large Files** (> 100KB): 5+ seconds depending on network

### **Memory Usage**
- **Lightweight**: Minimal memory footprint
- **Efficient**: Optimized for ESP-01 constraints
- **Scalable**: Handles files of various sizes

## 🤝 Contributing

### **Development Setup**
1. Clone the repository
2. Install development dependencies
3. Run tests: `python test_auto_requirements.py`
4. Make your changes
5. Test thoroughly
6. Submit pull request

### **Testing**
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end functionality testing
- **Manual Testing**: Real ESP-01 hardware testing

## 📄 License

© 2025 J Tech Solutions. All rights reserved.

This software is provided for educational and development purposes. Commercial use requires explicit permission.

## 🆘 Support

### **Documentation**
- **User Guide**: Built into the application
- **API Reference**: Code documentation and examples
- **Troubleshooting**: Common issues and solutions

### **Community**
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and ideas
- **Examples**: Sample files and use cases

## 🔮 Future Features

### **Planned Enhancements**
- **Batch Uploads**: Multiple file upload support
- **Advanced Verification**: ESP-side hash verification
- **Network Discovery**: Automatic ESP-01 detection
- **Cloud Integration**: Remote upload capabilities
- **Mobile Support**: Web-based interface

### **Roadmap**
- **v1.1**: Enhanced LED matrix preview
- **v1.2**: Batch upload capabilities
- **v1.3**: Advanced verification systems
- **v2.0**: Cloud and mobile support

---

**J Tech Pixel LED ESP01 Uploader** - Professional ESP-01 development made simple! 🚀✨
#   E S P 0 1 - u p l o a d e r  
 