@echo off
cd /d "%~dp0"

echo ================================================================
echo           Omni Agent Harness - Dependencies Installer
echo ================================================================
echo.

echo [1/2] Checking Python environment...
python -V >nul 2>&1
if errorlevel 1 goto NO_PYTHON

echo [2/2] Installing dependencies...
python harness\launcher.py --install-only
goto FINISH

:NO_PYTHON
echo.
echo ================================================================
echo [ERROR] Python is not found in your system PATH!
echo Please install Python (3.10-3.12 recommended) from:
echo https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo ================================================================
echo.

:FINISH
echo.
pause
