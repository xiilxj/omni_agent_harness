@echo off & chcp 65001 >nul 2>&1
title Omni Agent Harness - Windows 控制台
echo ================================================================
echo           Omni Agent Harness (Codex-DSH) - Windows
echo ================================================================
echo.

REM 1. 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未检测到 Python 环境！
    echo 请先安装 Python (推荐 3.10-3.12) 并勾选 Add Python to PATH.
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM 2. 检查并生成 .env 配置文件
if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" >nul 2>&1
        echo [提示] 已自动创建 .env 配置文件模板。
    )
)

REM 3. 检查与安装必要依赖
echo [1/3] 正在检查必要依赖库...
pip install -r requirements.txt --quiet --disable-pip-version-check

REM 4. 针对 Windows 环境下 pydantic-core DLL 的自动健康校验与自愈修复
python -c "import pydantic_core" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 正在自动修复当前 Python 环境的 pydantic 动态链接库...
    pip install --upgrade --force-reinstall --no-cache-dir pydantic pydantic-core
)

REM 5. 启动服务并唤起浏览器
echo [2/3] 正在启动 Web 控制台...
start "" "http://127.0.0.1:7890"

echo [3/3] Omni Agent Harness 服务已就绪！
echo ================================================================
echo   控制台地址: http://127.0.0.1:7890
echo   如需停止服务，请直接关闭本窗口或按 Ctrl + C。
echo ================================================================
echo.

python harness\cli.py --ui --host 127.0.0.1 --port 7890

if %errorlevel% neq 0 (
    echo.
    echo ================================================================
    echo [启动异常排查指引]
    echo 若提示 DLL load failed，通常是由于缺少微软 Visual C++ 运行库或 Python 预览版二进制不匹配。
    echo 解决方案：
    echo 1. 下载安装微软官方 Visual C++ 2015-2022 x64 运行库:
    echo    https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo 2. 或在命令行手动执行: pip install --upgrade --force-reinstall pydantic pydantic-core
    echo 3. 或推荐安装 Python 3.11 / 3.12 长期稳定版。
    echo ================================================================
)

pause
