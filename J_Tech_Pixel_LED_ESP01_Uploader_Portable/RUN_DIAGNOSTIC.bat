@echo off
echo ========================================
echo    ESP-01 COMPREHENSIVE DIAGNOSTIC
echo ========================================
echo.
echo This will run a comprehensive diagnostic to identify
echo exactly why your ESP-01 uploads are failing.
echo.
echo BEFORE STARTING:
echo 1. Make sure ESP-01 is powered on
echo 2. Connect to "MatrixUploader" WiFi network (no password)
echo 3. ESP-01 should be accessible at 192.168.4.1
echo.
echo PRESS ANY KEY TO CONTINUE...
pause >nul

echo.
echo Running comprehensive diagnostic...
echo.

python comprehensive_diagnostic.py

echo.
echo Diagnostic completed!
echo Check the detailed report above for solutions.
echo.
pause
