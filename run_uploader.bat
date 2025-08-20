@echo off
title J Tech Pixel LED ESP01 Uploader
echo.
echo ========================================
echo   J Tech Pixel LED ESP01 Uploader
echo ========================================
echo.
echo Starting application...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    echo.
    pause
    exit /b 1
)

REM Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found in current directory
    echo Please run this batch file from the project directory
    echo.
    pause
    exit /b 1
)

REM Run the application
echo Starting J Tech Pixel LED ESP01 Uploader...
echo.
python main.py

REM If we get here, the application has closed
echo.
echo Application closed.
pause
