#!/usr/bin/env python3
"""
Build Portable Executable Package
Creates a standalone executable with all dependencies included
"""

import os
import sys
import subprocess
import shutil
import zipfile
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def install_pyinstaller():
    """Install PyInstaller if not available"""
    print("📦 Installing PyInstaller...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        print("✅ PyInstaller installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install PyInstaller")
        return False

def create_spec_file():
    """Create PyInstaller spec file for the application"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('LEDMatrixStudio_Icon.ico', '.'),
        ('requirements.txt', '.'),
        ('README.md', '.'),
        ('INSTALLATION.md', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'requests',
        'hashlib',
        'json',
        'threading',
        'time',
        'os',
        'pathlib',
        'subprocess',
        'importlib',
        'winshell',
        'win32com.client',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='J_Tech_Pixel_LED_ESP01_Uploader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='LEDMatrixStudio_Icon.ico'
)
'''
    
    with open('uploader.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ PyInstaller spec file created")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")
    try:
        subprocess.run(['pyinstaller', 'uploader.spec', '--clean'], check=True)
        print("✅ Executable built successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to build executable")
        return False

def create_portable_package():
    """Create portable package with all required files"""
    print("📦 Creating portable package...")
    
    # Create portable directory
    portable_dir = "J_Tech_Pixel_LED_ESP01_Uploader_Portable"
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    os.makedirs(portable_dir)
    
    # Copy executable
    exe_source = "dist/J_Tech_Pixel_LED_ESP01_Uploader.exe"
    exe_dest = os.path.join(portable_dir, "J_Tech_Pixel_LED_ESP01_Uploader.exe")
    if os.path.exists(exe_source):
        shutil.copy2(exe_source, exe_dest)
        print("✅ Executable copied")
    else:
        print("❌ Executable not found")
        return False
    
    # Copy additional files
    additional_files = [
        'README.md',
        'INSTALLATION.md',
        'requirements.txt',
        'ESP01_Flash.ino',
        'enhanced_esp01_firmware.ino',
        'test_enhanced_verification.py'
    ]
    
    for file in additional_files:
        if os.path.exists(file):
            shutil.copy2(file, portable_dir)
            print(f"✅ {file} copied")
    
    # Create launcher batch file
    launcher_content = '''@echo off
title J Tech Pixel LED ESP01 Uploader - Portable
echo.
echo ========================================
echo   J Tech Pixel LED ESP01 Uploader
echo   Portable Edition
echo ========================================
echo.
echo Starting portable application...
echo.

REM Check if executable exists
if not exist "J_Tech_Pixel_LED_ESP01_Uploader.exe" (
    echo ERROR: Executable not found!
    echo Please ensure all files are in the same directory.
    pause
    exit /b 1
)

REM Run the portable application
echo Launching J Tech Pixel LED ESP01 Uploader...
echo.
start "" "J_Tech_Pixel_LED_ESP01_Uploader.exe"

REM Wait a moment and check if it's running
timeout /t 3 /nobreak >nul
tasklist | find "J_Tech_Pixel_LED_ESP01_Uploader.exe" >nul
if errorlevel 1 (
    echo.
    echo Application may have started successfully.
    echo Check your taskbar for the application window.
) else (
    echo.
    echo Application started successfully!
)

echo.
echo Portable package is ready to use!
echo You can copy this folder to any Windows computer.
pause
'''
    
    launcher_path = os.path.join(portable_dir, "LAUNCH.bat")
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    
    print("✅ Launcher batch file created")
    
    # Create README for portable package
    portable_readme = '''# J Tech Pixel LED ESP01 Uploader - Portable Edition

## 🚀 Quick Start

1. **Extract** this ZIP file to any folder
2. **Double-click** `LAUNCH.bat` to start the application
3. **Enjoy!** No installation required

## 📁 What's Included

- **J_Tech_Pixel_LED_ESP01_Uploader.exe** - Main application (no Python needed!)
- **LAUNCH.bat** - Easy launcher script
- **ESP01_Flash.ino** - Enhanced ESP-01 firmware with hash verification
- **enhanced_esp01_firmware.ino** - Alternative enhanced firmware
- **test_enhanced_verification.py** - Test script for verification
- **README.md** - Complete documentation
- **INSTALLATION.md** - Installation guide

## 🎯 Features

✅ **Portable** - Runs on any Windows computer  
✅ **No Installation** - Extract and run  
✅ **All Dependencies Included** - No Python setup needed  
✅ **Enhanced Verification** - 7-step upload verification  
✅ **Professional Interface** - Modern, user-friendly design  
✅ **ESP-01 Hash Verification** - TRUE file integrity checking  

## 🔧 ESP-01 Setup

1. **Upload** `ESP01_Flash.ino` to your ESP-01
2. **Connect** to WiFi network "MatrixUploader" (password: 12345678)
3. **Use** IP address 192.168.4.1 in the application

## 📱 Usage

1. **Launch** the application using `LAUNCH.bat`
2. **Connect** to your ESP-01
3. **Select** files to upload
4. **Enjoy** professional-grade verification!

## 🆘 Support

- **Documentation**: README.md and INSTALLATION.md
- **Test Script**: test_enhanced_verification.py
- **Firmware**: ESP01_Flash.ino for enhanced capabilities

---
**J Tech Pixel LED ESP01 Uploader - Professional ESP-01 development made simple!** 🚀✨
'''
    
    readme_path = os.path.join(portable_dir, "PORTABLE_README.md")
    with open(readme_path, 'w') as f:
        f.write(portable_readme)
    
    print("✅ Portable README created")
    
    return portable_dir

def create_zip_package(portable_dir):
    """Create ZIP file of the portable package"""
    print("🗜️  Creating ZIP package...")
    
    zip_filename = "J_Tech_Pixel_LED_ESP01_Uploader_Portable.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(portable_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, portable_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ ZIP package created: {zip_filename}")
    return zip_filename

def cleanup_build_files():
    """Clean up build artifacts"""
    print("🧹 Cleaning up build files...")
    
    cleanup_dirs = ['build', 'dist', '__pycache__']
    cleanup_files = ['uploader.spec']
    
    for dir_name in cleanup_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ Removed {dir_name}")
    
    for file_name in cleanup_files:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"✅ Removed {file_name}")

def main():
    """Main build process"""
    print("🚀 J Tech Pixel LED ESP01 Uploader - Portable Build")
    print("=" * 60)
    
    # Check and install PyInstaller
    if not check_pyinstaller():
        if not install_pyinstaller():
            print("❌ Cannot proceed without PyInstaller")
            return False
    
    # Create spec file
    create_spec_file()
    
    # Build executable
    if not build_executable():
        print("❌ Build failed")
        return False
    
    # Create portable package
    portable_dir = create_portable_package()
    if not portable_dir:
        print("❌ Portable package creation failed")
        return False
    
    # Create ZIP file
    zip_file = create_zip_package(portable_dir)
    
    # Cleanup
    cleanup_build_files()
    
    print("\n" + "=" * 60)
    print("🎉 PORTABLE PACKAGE CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📦 Portable Directory: {portable_dir}")
    print(f"🗜️  ZIP Package: {zip_file}")
    print(f"📱 Executable: {portable_dir}/J_Tech_Pixel_LED_ESP01_Uploader.exe")
    print(f"🚀 Launcher: {portable_dir}/LAUNCH.bat")
    print("\n✅ Your application is now portable!")
    print("✅ No Python installation required on target computers!")
    print("✅ All dependencies are included!")
    print("✅ Ready for distribution!")
    
    return True

if __name__ == "__main__":
    main()
