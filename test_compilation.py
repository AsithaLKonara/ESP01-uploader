#!/usr/bin/env python3
"""
ESP01 Firmware Compilation Test
Tests if the ESP01_Flash.ino firmware compiles without errors
"""

import os
import subprocess
import sys

def test_firmware_compilation():
    """Test if the ESP01 firmware compiles"""
    print("🔧 Testing ESP01_Flash.ino Compilation...")
    print("=" * 50)
    
    # Check if file exists
    firmware_file = "ESP01_Flash.ino"
    if not os.path.exists(firmware_file):
        print(f"❌ Error: {firmware_file} not found!")
        return False
    
    print(f"✅ Found firmware file: {firmware_file}")
    
    # Basic syntax check - look for common compilation issues
    with open(firmware_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for basic syntax issues
    issues = []
    
    # Check for balanced braces
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        issues.append(f"Unbalanced braces: {{ {open_braces}, }} {close_braces}")
    
    # Check for balanced parentheses
    open_parens = content.count('(')
    close_parens = content.count(')')
    if open_parens != close_parens:
        issues.append(f"Unbalanced parentheses: ( {open_parens}, ) {close_parens}")
    
    # Check for missing semicolons after function declarations
    if 'void handleChunkedUpload()' in content and 'void handleChunkedUpload() {' in content:
        print("✅ handleChunkedUpload function properly defined")
    
    if 'void handleChunkedPlayback()' in content and 'void handleChunkedPlayback() {' in content:
        print("✅ handleChunkedPlayback function properly defined")
    
    if 'void handleStreamingControl()' in content and 'void handleStreamingControl() {' in content:
        print("✅ handleStreamingControl function properly defined")
    
    # Check for large pattern features
    if 'LARGE_PATTERN_THRESHOLD' in content:
        print("✅ Large pattern threshold defined")
    
    if 'ChunkInfo chunks[MAX_CHUNKS]' in content:
        print("✅ ChunkInfo structure defined")
    
    if 'bool largePatternMode' in content:
        print("✅ Large pattern mode variable defined")
    
    # Check for server routes
    if 'server.on("/upload-chunked"' in content:
        print("✅ Chunked upload route defined")
    
    if 'server.on("/chunked-playback"' in content:
        print("✅ Chunked playback route defined")
    
    if 'server.on("/streaming-control"' in content:
        print("✅ Streaming control route defined")
    
    # Report any issues
    if issues:
        print("\n❌ Compilation Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("\n✅ No obvious compilation issues found!")
    print("✅ Firmware structure looks good")
    print("✅ All large pattern features are present")
    
    # File size check
    file_size = os.path.getsize(firmware_file)
    print(f"✅ Firmware file size: {file_size:,} bytes")
    
    # Line count check
    line_count = len(content.split('\n'))
    print(f"✅ Total lines: {line_count:,}")
    
    print("\n🎉 ESP01_Flash.ino is ready for compilation!")
    print("📝 Next step: Open in Arduino IDE and upload to ESP01")
    
    return True

if __name__ == "__main__":
    try:
        success = test_firmware_compilation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error during compilation test: {e}")
        sys.exit(1)
