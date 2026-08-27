@echo off
cd /d "%~dp0"

echo ================================================================
echo           Omni Agent Harness - Windows Startup
echo ================================================================
echo.

set PY_CMD=

if exist "%ProgramFiles%\Python310\python.exe" set PY_CMD="%ProgramFiles%\Python310\python.exe"
if defined PY_CMD goto FOUND_PY

if exist "%ProgramFiles%\Python311\python.exe" set PY_CMD="%ProgramFiles%\Python311\python.exe"
if defined PY_CMD goto FOUND_PY

if exist "%ProgramFiles%\Python312\python.exe" set PY_CMD="%ProgramFiles%\Python312\python.exe"
if defined PY_CMD goto FOUND_PY

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if defined PY_CMD goto FOUND_PY

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if defined PY_CMD goto FOUND_PY

if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
if defined PY_CMD goto FOUND_PY

if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if defined PY_CMD goto FOUND_PY

python -V >nul 2>&1
if not errorlevel 1 set PY_CMD=python
if defined PY_CMD goto FOUND_PY

py -V >nul 2>&1
if not errorlevel 1 set PY_CMD=py
if defined PY_CMD goto FOUND_PY

echo.
echo ================================================================
echo [ERROR] Python was not found on your system!
echo Please install Python from https://www.python.org/downloads/
echo ================================================================
echo.
pause
exit /b 1

:FOUND_PY
echo [1/2] Using Python: %PY_CMD%
echo [2/2] Launching Omni Agent Harness...
echo.

%PY_CMD% harness\launcher.py

echo.
echo ================================================================
echo [Omni Agent Harness] Execution finished.
echo ================================================================
pause
