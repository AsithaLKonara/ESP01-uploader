@echo off
echo ========================================
echo ESP-01 WiFi Uploader - Quick Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python found! Checking version...
python --version
echo.

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please reinstall Python with pip included
    echo.
    pause
    exit /b 1
)

echo Installing required packages...
echo This may take a few minutes on first run...
echo.

REM Install requirements
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install requirements
    echo Please check your internet connection and try again
    echo.
    pause
    exit /b 1
)

echo.
echo All packages installed successfully!
echo.
echo Starting ESP-01 WiFi Uploader...
echo.

REM Run the application
python main.py

echo.
echo Application closed.
pause
