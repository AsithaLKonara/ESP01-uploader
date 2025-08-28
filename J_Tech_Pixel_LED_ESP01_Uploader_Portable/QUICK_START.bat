@echo off
echo ========================================
echo    ESP-01 FIRMWARE UPLOADER LAUNCHER
echo ========================================
echo.
echo This will launch the ESP-01 firmware uploader.
echo.
echo BEFORE STARTING:
echo 1. Connect your ESP-01 via USB
echo 2. Make sure ESP-01 is in flash mode (GPIO0 pulled low)
echo 3. Note your ESP-01 COM port
echo.
echo PRESS ANY KEY TO CONTINUE...
pause >nul

echo.
echo Launching uploader...
echo.
echo INSTRUCTIONS:
echo 1. Select firmware: ESP01_Flash.ino
echo 2. Choose your ESP-01 COM port
echo 3. Click Upload
echo 4. Wait for completion
echo 5. ESP-01 will restart automatically
echo.
echo After upload, connect to "MatrixUploader" WiFi
echo and open http://192.168.4.1 in your browser
echo.

start "" "J_Tech_Pixel_LED_ESP01_Uploader.exe"

echo Uploader launched! Follow the instructions above.
echo.
pause
