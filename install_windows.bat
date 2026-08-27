@echo off
setlocal
cd /d "%~dp0"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python environment is not detected in PATH!
    echo Please install Python (3.10-3.12 recommended) from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

python harness\launcher.py --install-only
pause
