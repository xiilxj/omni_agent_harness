@echo off
chcp 65001 >nul
title Omni Agent Harness - 依赖安装
echo ================================================================
echo           Omni Agent Harness - Windows 依赖环境安装程序
echo ================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+ 并勾选 Add to PATH。
    pause
    exit /b 1
)

echo 正在安装 Python 依赖库 (fastapi, uvicorn, jinja2, httpx 等)...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade

if %errorlevel% equ 0 (
    echo.
    echo [成功] 所有依赖安装完毕！您可以直接双击运行 start_windows.bat 启动系统。
) else (
    echo.
    echo [警告] 依赖安装可能遇到网络问题，请检查网络后重试。
)

echo.
pause
