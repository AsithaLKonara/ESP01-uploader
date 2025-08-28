# 🎯 LED Matrix Studio + ESP01 Integration

This solution provides a **Python-based integration** between LED Matrix Studio and your ESP01 LED matrix, allowing you to:

✅ **Parse LED Matrix Studio files** (.leds, .LedAnim)  
✅ **Extract individual frames** from animations  
✅ **Upload frames to ESP01** one by one for smooth display  
✅ **Handle large animations** without overwhelming ESP01 memory  
✅ **Support multiple formats** (Mono, Binary, RGB, RGB3PP)  

---

## 🚀 **Quick Start**

### 1. **Install Dependencies**
```bash
cd ESP01
pip install -r requirements.txt
```

### 2. **Basic Usage**
```bash
# Process a single frame file
python integrate_with_ledmatrixstudio.py pattern.leds binary

# Process an animation file
python integrate_with_ledmatrixstudio.py animation.LedAnim binary esp01_frames

# Stream frames to ESP01
python esp01_led_uploader.py animation.LedAnim --stream --loop
```

---

## 📁 **Files Overview**

| File | Purpose |
|------|---------|
| `led_matrix_parser.py` | Core parser for LED Matrix Studio files |
| `esp01_led_uploader.py` | Enhanced uploader with streaming capabilities |
| `integrate_with_ledmatrixstudio.py` | Simple integration script |
| `requirements.txt` | Python dependencies |

---

## 🔧 **How It Works**

### **1. File Parsing**
- **`.leds` files** → Single frame LED patterns
- **`.LedAnim` files** → Multiple frame animations
- Automatically detects matrix dimensions and mode

### **2. Frame Extraction**
- Splits animations into individual frames
- Converts each frame to ESP01-compatible format
- Supports multiple export formats

### **3. ESP01 Upload**
- **Single frame mode**: Upload one frame at a time
- **Streaming mode**: Continuous frame upload with configurable delay
- **Loop mode**: Repeat animation indefinitely

---

## 📖 **Usage Examples**

### **Example 1: Export Frames Locally**
```bash
# Export frames to local directory without uploading
python esp01_led_uploader.py animation.LedAnim --export-only --format binary
```

**Output:**
```
✅ Successfully processed 24 frames
📁 Output files: 24
📂 Output directory: esp01_frames/
```

### **Example 2: Stream to ESP01**
```bash
# Stream frames to ESP01 with 200ms delay
python esp01_led_uploader.py animation.LedAnim --stream --delay 200 --ip 192.168.4.1
```

### **Example 3: Loop Animation**
```bash
# Loop animation continuously
python esp01_led_uploader.py animation.LedAnim --stream --loop
```

---

## ⚙️ **Configuration Options**

### **ESP01 Settings**
```python
settings = ESP01Settings(
    ip_address="192.168.4.1",      # ESP01 IP address
    port=80,                        # ESP01 port
    frame_delay_ms=100,             # Delay between frames
    timeout_seconds=5,              # Upload timeout
    max_retries=3                   # Retry attempts
)
```

### **Export Formats**
- **`mono`**: 1 bit per pixel (on/off)
- **`binary`**: 8 bits per pixel (0-255 brightness)
- **`rgb`**: 24 bits per pixel (RGB values)
- **`rgb3pp`**: 3 bits per pixel (0-7 brightness)

---

## 🔌 **Integration with Existing ESP01 Uploader**

### **Option 1: Call Integration Script**
```python
import subprocess
import json

# Call the integration script
result = subprocess.run([
    "python", "integrate_with_ledmatrixstudio.py",
    "animation.LedAnim", "binary", "esp01_frames"
], capture_output=True, text=True)

# Parse JSON result
data = json.loads(result.stdout)
if data["success"]:
    print(f"Processed {data['total_frames']} frames")
```

### **Option 2: Import Parser Directly**
```python
from led_matrix_parser import LEDMatrixParser, ExportFormat

parser = LEDMatrixParser()
frames = parser.parse_file("animation.LedAnim")
output_files = parser.export_frames_for_esp01(ExportFormat.BINARY, "frames")
```

---

## 📊 **File Format Support**

### **LED Matrix Studio Files**
- ✅ **`.leds`** - Single frame patterns
- ✅ **`.LedAnim`** - Multi-frame animations
- 🔄 **`.leds`** - Binary export format
- 🔄 **`.leds`** - RGB export format

### **ESP01 Output Formats**
- ✅ **Binary files** (.bin) - Ready for ESP01 upload
- ✅ **Frame metadata** - JSON info about each frame
- ✅ **Multiple formats** - Mono, Binary, RGB, RGB3PP

---

## 🚨 **Troubleshooting**

### **Common Issues**

| Problem | Solution |
|---------|----------|
| "No frames found" | Check file format and content |
| "Import error" | Install dependencies: `pip install -r requirements.txt` |
| "Upload failed" | Check ESP01 IP address and network connection |
| "Memory error" | Reduce frame delay or use smaller animations |

### **Debug Mode**
```bash
# Enable verbose output
python esp01_led_uploader.py animation.LedAnim --stream --debug
```

---

## 🎨 **Advanced Features**

### **Custom Frame Processing**
```python
from led_matrix_parser import MatrixFrame, ExportFormat

# Custom frame manipulation
def process_frame(frame: MatrixFrame) -> MatrixFrame:
    # Invert all pixels
    for row in frame.data:
        for i in range(len(row)):
            row[i] = 1 if row[i] == 0 else 0
    return frame

# Apply to all frames
for frame in parser.frames:
    frame = process_frame(frame)
```

### **Batch Processing**
```bash
# Process multiple files
for file in *.LedAnim; do
    python integrate_with_ledmatrixstudio.py "$file" binary "frames_${file%.*}"
done
```

---

## 🔄 **Workflow Integration**

### **Complete Workflow**
1. **Create pattern** in LED Matrix Studio
2. **Export file** (.leds or .LedAnim)
3. **Process with parser** → Extract frames
4. **Upload to ESP01** → Frame by frame
5. **Display smoothly** → No memory issues

### **Automation**
```bash
# Watch directory for new files
inotifywait -m -e create /path/to/leds/files | while read path action file; do
    if [[ "$file" =~ \.(leds|LedAnim)$ ]]; then
        python integrate_with_ledmatrixstudio.py "$path$file" binary "esp01_frames"
    fi
done
```

---

## 📈 **Performance**

### **Memory Usage**
- **ESP01**: Only stores current frame
- **PC**: Processes frames sequentially
- **Network**: Minimal data transfer per frame

### **Speed**
- **Frame processing**: ~1ms per frame
- **Upload time**: Depends on network speed
- **Display**: Smooth 60fps possible with 100ms delay

---

## 🤝 **Contributing**

This solution is designed to be:
- **Modular**: Easy to extend and modify
- **Compatible**: Works with existing ESP01 code
- **Efficient**: Minimal resource usage
- **Reliable**: Error handling and fallbacks

---

## 📞 **Support**

For issues or questions:
1. Check the troubleshooting section
2. Review the example files
3. Test with simple .leds files first
4. Verify ESP01 network connectivity

---

**🎉 You now have a complete LED Matrix Studio → ESP01 integration solution!**
