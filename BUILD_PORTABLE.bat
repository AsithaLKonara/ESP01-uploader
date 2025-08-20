@echo off
title Build Portable ESP01 Uploader
echo.
echo ========================================
echo   Building Portable ESP01 Uploader
echo ========================================
echo.
echo This will create a standalone executable
echo with all dependencies included.
echo.
echo Press any key to start building...
pause >nul

echo.
echo Starting build process...
echo.

REM Run the build script
python build_portable.py

echo.
echo Build process completed!
echo.
echo Check the output above for results.
echo.
pause
