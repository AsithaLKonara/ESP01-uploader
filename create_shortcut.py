#!/usr/bin/env python3
"""
Create Desktop Shortcut for J Tech Pixel LED ESP01 Uploader
"""

import os
import sys
import winshell
from win32com.client import Dispatch

def create_desktop_shortcut():
    """Create a desktop shortcut for the application"""
    
    try:
        # Get current directory and main.py path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        main_py_path = os.path.join(current_dir, "main.py")
        
        # Get desktop path
        desktop = winshell.desktop()
        
        # Create shortcut path
        shortcut_path = os.path.join(desktop, "J Tech Pixel LED ESP01 Uploader.lnk")
        
        # Create shortcut
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        
        # Set shortcut properties
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{main_py_path}"'
        shortcut.WorkingDirectory = current_dir
        shortcut.Description = "J Tech Pixel LED ESP01 Uploader - Professional ESP-01 WiFi Firmware Uploader"
        
        # Set icon if available
        icon_path = os.path.join(current_dir, "LEDMatrixStudio_Icon.ico")
        if os.path.exists(icon_path):
            shortcut.IconLocation = icon_path
        
        # Save shortcut
        shortcut.save()
        
        print("✅ Desktop shortcut created successfully!")
        print(f"📁 Location: {shortcut_path}")
        print(f"🎯 Target: {sys.executable}")
        print(f"📂 Working Directory: {current_dir}")
        
        if os.path.exists(icon_path):
            print(f"🎨 Icon: {icon_path}")
        else:
            print("⚠️  Icon file not found")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating shortcut: {e}")
        return False

def main():
    """Main function"""
    print("J Tech Pixel LED ESP01 Uploader - Desktop Shortcut Creator")
    print("=" * 60)
    
    # Check if required modules are available
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError as e:
        print(f"❌ Required modules not available: {e}")
        print("\nTo install required modules, run:")
        print("pip install pywin32 winshell")
        return False
    
    # Check if main.py exists
    if not os.path.exists("main.py"):
        print("❌ main.py not found in current directory")
        print("Please run this script from the project directory")
        return False
    
    # Create shortcut
    success = create_desktop_shortcut()
    
    if success:
        print("\n🎉 Shortcut creation completed!")
        print("You can now launch the application from your desktop.")
    else:
        print("\n⚠️  Shortcut creation failed.")
        print("Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    main()
