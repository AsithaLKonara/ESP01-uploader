# 🔧 ESP-01 Enhanced Firmware Flashing Guide

## 📋 **Prerequisites**

- **ESP-01 Module** (ESP8266-based)
- **USB-to-TTL Converter** (CH340, CP2102, or FTDI)
- **Arduino IDE** with ESP8266 board support
- **Required Libraries** (install via Arduino Library Manager):
  - `ESP8266WiFi`
  - `ESP8266WebServer` 
  - `LittleFS`
  - `ArduinoJson`
  - `Hash`

## 🔌 **Hardware Connection**

Connect your ESP-01 to the USB-to-TTL converter:

```
ESP-01 Pin    USB-TTL Pin    Description
----------    -----------    -----------
VCC          3.3V           Power (3.3V only!)
GND          GND            Ground
TX           RX             ESP-01 transmits to USB-TTL receives
RX           TX             ESP-01 receives from USB-TTL transmits
CH_PD/EN    3.3V           Chip enable (must be HIGH)
GPIO0       3.3V           Normal operation mode
GPIO2       3.3V           Normal operation mode
```

⚠️ **IMPORTANT**: 
- **NEVER** connect ESP-01 to 5V - it will be destroyed!
- Use 3.3V only for all power pins
- Ensure all connections are secure

## 📱 **Arduino IDE Setup**

### 1. Install ESP8266 Board Support
1. Open Arduino IDE
2. Go to `File` → `Preferences`
3. Add this URL to "Additional Board Manager URLs":
   ```
   https://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
4. Go to `Tools` → `Board` → `Boards Manager`
5. Search for "ESP8266" and install "ESP8266 by ESP8266 Community"

### 2. Configure Board Settings
1. Select `Tools` → `Board` → `ESP8266 Boards` → `Generic ESP8266 Module`
2. Set these parameters:
   - **Upload Speed**: `115200`
   - **Flash Size**: `1M (64K SPIFFS)`
   - **Debug port**: `Disabled`
   - **Debug Level**: `None`
   - **Reset Method**: `ck`
   - **Crystal Frequency**: `26 MHz`
   - **Flash Frequency**: `40 MHz`
   - **Flash Mode**: `DIO`
   - **Port**: Select your USB-TTL converter port

### 3. Install Required Libraries
Go to `Tools` → `Manage Libraries` and install:
- `ESP8266WiFi` (usually pre-installed)
- `ESP8266WebServer` (usually pre-installed)
- `LittleFS` (usually pre-installed)
- `ArduinoJson` by Benoit Blanchon
- `Hash` (usually pre-installed)

## 🚀 **Flashing Process**

### 1. Prepare ESP-01 for Flashing
1. **Power off** ESP-01
2. **Hold down** the `FLASH` button (or connect GPIO0 to GND)
3. **Power on** ESP-01 while holding FLASH
4. **Release** FLASH button after power-on
5. ESP-01 should now be in flash mode

### 2. Upload Firmware
1. Open `ESP01_Enhanced.ino` in Arduino IDE
2. Verify the code compiles (`Sketch` → `Verify/Compile`)
3. Select the correct COM port
4. Click `Upload` button
5. Wait for upload to complete

### 3. Verify Upload
1. Open `Tools` → `Serial Monitor`
2. Set baud rate to `115200`
3. Reset ESP-01 (power cycle or press reset button)
4. You should see:
   ```
   WiFi AP Started
   IP Address: 192.168.4.1
   Enhanced ESP-01 LED Matrix Firmware Ready!
   ```

## 🔍 **Testing the Firmware**

### 1. Connect to WiFi
1. Look for WiFi network named `MatrixUploader`
2. Connect with password: `12345678`
3. Your device should get IP address like `192.168.4.x`

### 2. Access Web Interface
1. Open web browser
2. Navigate to `http://192.168.4.1`
3. You should see the enhanced upload interface

### 3. Test File Upload
1. Use the web interface to upload a small test file
2. Check that file size and hash are displayed correctly
3. Verify system information shows proper values

## 🛠️ **Troubleshooting**

### Common Issues:

#### **Upload Fails**
- Check all connections
- Ensure ESP-01 is in flash mode (GPIO0 LOW)
- Try different upload speeds
- Check USB driver installation

#### **ESP-01 Not Responding**
- Verify power supply is 3.3V
- Check CH_PD/EN is connected to 3.3V
- Ensure all ground connections are secure

#### **WiFi Not Working**
- Check that ESP-01 is not in flash mode
- Verify GPIO0 is HIGH (3.3V)
- Reset ESP-01 after upload

#### **File Upload Issues**
- Check file size (must be <32KB)
- Verify LittleFS is working
- Check serial monitor for error messages

### **Serial Monitor Commands**
If you need to debug, you can add these commands to the firmware:

```cpp
void handleSerialCommands() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "reset") {
      ESP.restart();
    } else if (command == "info") {
      Serial.printf("Free heap: %d bytes\n", ESP.getFreeHeap());
      Serial.printf("Flash size: %d bytes\n", ESP.getFlashChipSize());
    } else if (command == "format") {
      LittleFS.format();
      Serial.println("LittleFS formatted");
    }
  }
}
```

## 📱 **Using with LED Matrix Studio**

### 1. Enable ESP01 Optimization
1. In LED Matrix Studio, go to Export panel
2. Check "ESP01 Optimization"
3. Select compression type (RLE, Delta, or Combined)
4. Set target size to 32KB or less

### 2. Export and Optimize
1. Export your animation
2. Use the Python optimizer: `python optimize_for_esp01.py export_file.bin`
3. Upload the optimized file to ESP-01

### 3. Monitor Performance
- Check file size before and after optimization
- Monitor ESP-01 memory usage
- Verify hash matches between PC and ESP-01

## 🔒 **Security Notes**

- The default WiFi password is `12345678` - change this in production
- The web interface has no authentication - add if needed
- Consider adding HTTPS for production use
- Monitor for unauthorized access attempts

## 📚 **Advanced Features**

### Custom WiFi Configuration
Modify these lines in the firmware:
```cpp
const char* ssid = "YourWiFiName";
const char* password = "YourWiFiPassword";
```

### File Size Limits
Adjust the target size:
```cpp
const int MAX_FILE_SIZE = 32 * 1024; // 32KB
```

### LED Matrix Output
Modify `outputLEDMatrixData()` function to interface with your actual LED matrix hardware.

## 🎯 **Next Steps**

1. **Flash the enhanced firmware** to your ESP-01
2. **Test the web interface** and file upload
3. **Use LED Matrix Studio** with ESP01 optimization
4. **Optimize your animations** to fit within 32KB
5. **Connect your LED matrix** hardware

## 📞 **Support**

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all connections and power supply
3. Check serial monitor for error messages
4. Ensure you're using the correct board settings
5. Verify all required libraries are installed

---

**Happy Flashing! 🚀**
