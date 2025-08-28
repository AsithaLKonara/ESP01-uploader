@echo off
echo ========================================
echo    ESP-01 STATUS TEST SCRIPT
echo ========================================
echo.
echo This will test if your ESP-01 is working properly
echo after firmware upload.
echo.
echo BEFORE STARTING:
echo 1. Make sure ESP-01 firmware was uploaded successfully
echo 2. Connect to "MatrixUploader" WiFi network (no password)
echo 3. ESP-01 should be accessible at 192.168.4.1
echo.
echo PRESS ANY KEY TO CONTINUE...
pause >nul

echo.
echo Running ESP-01 status test...
echo.

python test_esp01_status.py

echo.
echo Test completed!
echo.
pause
