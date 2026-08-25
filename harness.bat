@echo off
REM Omni Agent Harness - Windows 一键启动脚本
REM 支持运行 Web UI、命令行单任务 (-p) 或直接进入交互终端

set SCRIPT_DIR=%~dp0
set PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%

if "%1"=="--dsh" (
    shift
    dsh %*
    goto :eof
)

if "%1"=="--dsh-web" (
    shift
    dsh web %*
    goto :eof
)

python "%SCRIPT_DIR%harness\cli.py" %*
