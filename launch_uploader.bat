@echo off
REM ESP01 Uploader Launcher
REM This batch file launches the ESP01 uploader with the provided file

if "%1"=="" (
    echo Usage: launch_uploader.bat [file_path]
    echo.
    echo This will launch the ESP01 uploader with the specified file.
    echo If no file is specified, the uploader will run normally.
    echo.
    pause
    exit /b 1
)

echo Launching ESP01 Uploader with file: %1
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and ensure it's accessible from command line
    pause
    exit /b 1
)

REM Launch the Python script
python "%~dp0main.py" "%1"

echo.
echo ESP01 Uploader finished.
pause
