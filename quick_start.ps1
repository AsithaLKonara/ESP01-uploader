# ESP-01 WiFi Uploader - Quick Start (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ESP-01 WiFi Uploader - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python found! Version:" -ForegroundColor Green
        Write-Host $pythonVersion -ForegroundColor Green
        Write-Host ""
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if pip is available
try {
    $pipVersion = pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "pip found!" -ForegroundColor Green
        Write-Host $pipVersion -ForegroundColor Green
        Write-Host ""
    } else {
        throw "pip not found"
    }
} catch {
    Write-Host "ERROR: pip is not available" -ForegroundColor Red
    Write-Host "Please reinstall Python with pip included" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Installing required packages..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first run..." -ForegroundColor Yellow
Write-Host ""

# Install requirements
try {
    pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "All packages installed successfully!" -ForegroundColor Green
        Write-Host ""
    } else {
        throw "pip install failed"
    }
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to install requirements" -ForegroundColor Red
    Write-Host "Please check your internet connection and try again" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Starting ESP-01 WiFi Uploader..." -ForegroundColor Green
Write-Host ""

# Run the application
try {
    python main.py
} catch {
    Write-Host "ERROR: Failed to start application" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "Application closed." -ForegroundColor Yellow
Read-Host "Press Enter to exit"
