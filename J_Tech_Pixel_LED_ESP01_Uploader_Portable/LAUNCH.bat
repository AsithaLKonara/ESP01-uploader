@echo off
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
