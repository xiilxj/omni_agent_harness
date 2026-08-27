@echo off
cd /d "%~dp0"

echo ================================================================
echo           Omni Agent Harness - Dependencies Installer
echo ================================================================
echo.

set "PY_CMD="

python -V >nul 2>&1
if not errorlevel 1 set "PY_CMD=python"

if "%PY_CMD%"=="" (
    py -V >nul 2>&1
    if not errorlevel 1 set "PY_CMD=py"
)

if "%PY_CMD%"=="" (
    if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
)

if "%PY_CMD%"=="" goto NO_PYTHON

echo [1/2] Detected Python: %PY_CMD%
echo [2/2] Installing dependencies...
echo.

"%PY_CMD%" harness\launcher.py --install-only
goto FINISH

:NO_PYTHON
echo.
echo ================================================================
echo [ERROR] Python was not found on your system!
echo Please install Python (3.10-3.12 recommended) from:
echo https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo ================================================================
echo.

:FINISH
echo.
pause
