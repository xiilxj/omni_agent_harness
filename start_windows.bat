@echo off
setlocal
cd /d "%~dp0"

echo [Omni Agent Harness] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ================================================================
    echo [ERROR] Python is not found in your system PATH!
    echo Please install Python (3.10-3.12 recommended) from:
    echo https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo ================================================================
    echo.
    pause
    exit /b 1
)

echo [Omni Agent Harness] Launching Python engine...
python harness\launcher.py

echo.
echo ================================================================
echo [Omni Agent Harness] Process finished.
echo ================================================================
pause
