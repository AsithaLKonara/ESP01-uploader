# J Tech Pixel LED ESP01 Uploader - Installation Guide

## 🚀 Quick Installation

### **Option 1: Run Directly (Recommended)**
1. **Download** the project files to your computer
2. **Double-click** `run_uploader.bat` to start the application
3. **Enjoy!** The application will automatically install any missing requirements

### **Option 2: Command Line**
1. **Open Command Prompt** in the project directory
2. **Run**: `python main.py`
3. **The application will start** with automatic requirements management

## 🛠️ Detailed Installation

### **Prerequisites**
- **Windows 10/11** (64-bit recommended)
- **Python 3.8 or higher**
- **Internet connection** (for automatic package installation)

### **Step 1: Install Python**
1. **Download Python** from [python.org](https://www.python.org/downloads/)
2. **Run installer** and check "Add Python to PATH"
3. **Verify installation**:
   ```bash
   python --version
   ```

### **Step 2: Download Project**
1. **Clone or download** the project files
2. **Extract** to a folder (e.g., `C:\ESP01\`)
3. **Navigate** to the project directory

### **Step 3: Run Application**
```bash
# Navigate to project directory
cd C:\ESP01

# Run the application
python main.py
```

## 🎯 First Run Setup

### **Automatic Requirements Installation**
On first run, the application will:
1. **Check** for required Python packages
2. **Install** any missing dependencies automatically
3. **Verify** all requirements are met
4. **Start** the main application

### **What Gets Installed**
- `requests` - HTTP client for ESP-01 communication
- `hashlib` - Built-in hash calculation
- `json` - Built-in JSON processing
- `threading` - Built-in threading support
- `time` - Built-in time functions
- `os` - Built-in operating system interface
- `pathlib` - Built-in path handling

## 🖥️ Desktop Shortcut (Optional)

### **Create Desktop Shortcut**
1. **Install required modules**:
   ```bash
   pip install pywin32 winshell
   ```

2. **Run shortcut creator**:
   ```bash
   python create_shortcut.py
   ```

3. **Launch from desktop** - Double-click the new shortcut!

## 🔧 Manual Package Installation

### **If Automatic Installation Fails**
```bash
# Install all requirements manually
pip install -r requirements.txt

# Or install individual packages
pip install requests
pip install Pillow
pip install numpy
pip install matplotlib
```

## 🚨 Troubleshooting

### **Python Not Found**
- **Error**: `'python' is not recognized`
- **Solution**: Install Python and check "Add Python to PATH"

### **Permission Errors**
- **Error**: Access denied or permission errors
- **Solution**: Run Command Prompt as Administrator

### **Package Installation Fails**
- **Error**: Failed to install packages
- **Solution**: Check internet connection and try again

### **Icon Not Loading**
- **Error**: Icon file not found
- **Solution**: Ensure `LEDMatrixStudio_Icon.ico` is in the project directory

## 📁 File Structure

```
ESP01/
├── main.py                              # Main application
├── smart_esp_uploader_with_requirements.py  # Core uploader
├── led_matrix_preview.py               # LED matrix preview
├── file_manager.py                     # File operations
├── wifi_manager.py                     # WiFi management
├── requirements.txt                    # Python dependencies
├── run_uploader.bat                   # Windows batch file
├── create_shortcut.py                  # Desktop shortcut creator
├── LEDMatrixStudio_Icon.ico           # Application icon
├── README.md                           # Main documentation
└── INSTALLATION.md                     # This file
```

## 🎉 Success Indicators

### **Application Started Successfully**
- **Window opens** with "J Tech Pixel LED ESP01 Uploader" title
- **Icon appears** in the window title bar
- **Interface loads** with connection settings and file selection
- **No error messages** in the console

### **Requirements Installed**
- **Log shows**: "✅ All required packages are available"
- **No missing package errors**
- **Application functions normally**

## 🔄 Updates and Maintenance

### **Automatic Updates**
- **Requirements checked** on every startup
- **Missing packages installed** automatically
- **No manual intervention** required

### **Manual Updates**
```bash
# Update Python packages
pip install --upgrade requests Pillow numpy matplotlib

# Update application
# Download new project files and replace old ones
```

## 📞 Support

### **Installation Issues**
1. **Check** this installation guide
2. **Verify** Python installation
3. **Check** internet connection
4. **Review** error messages in console

### **Getting Help**
- **Documentation**: README.md and this file
- **Error Logs**: Check console output for details
- **Community**: GitHub issues and discussions

---

## 🎯 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Project files downloaded
- [ ] `run_uploader.bat` double-clicked
- [ ] Application window opened
- [ ] No error messages
- [ ] Ready to connect to ESP-01!

**Happy ESP-01 Development! 🚀✨**
