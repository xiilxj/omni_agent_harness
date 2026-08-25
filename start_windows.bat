@echo off
chcp 65001 >nul
title Omni Agent Harness - Windows 控制台
echo ================================================================
echo           Omni Agent Harness (Codex-DSH 架构) - Windows
echo ================================================================
echo.

:: 1. 检查 Python 环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境！
    echo 请先安装 Python 3.10 或更高版本 (https://www.python.org/downloads/)
    echo 并确保在安装时勾选 "Add Python to PATH"。
    echo.
    pause
    exit /b 1
)

:: 2. 检查 .env 配置文件是否存在，若不存在则从模板复制
if not exist ".env" (
    if exist ".env.example" (
        echo [提示] 正在创建初始 .env 配置文件模板...
        copy ".env.example" ".env" >nul
        echo [提示] 已生成 .env 文件，请在 Web 页面中设置您的 API 密钥。
    )
)

:: 3. 自动安装缺失的依赖
echo [1/3] 正在检查与安装必要依赖库...
pip install -r requirements.txt --quiet --disable-pip-version-check

:: 4. 自动在浏览器中打开控制台
echo [2/3] 正在准备 Web 控制台...
start "" "http://127.0.0.1:7890"

:: 5. 启动 Omni Agent Harness 后台服务
echo [3/3] Omni Agent Harness 服务已启动！
echo.
echo ================================================================
echo   控制台地址: http://127.0.0.1:7890
echo   如需停止运行，请直接关闭本窗口或按 Ctrl + C。
echo ================================================================
echo.

python harness\cli.py --ui --host 127.0.0.1 --port 7890

pause
