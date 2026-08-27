@echo off & chcp 65001 >nul 2>&1
title Omni Agent Harness - 依赖安装与修复
echo ================================================================
echo           Omni Agent Harness - Windows 依赖安装与校验
echo ================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未检测到 Python 环境！
    echo 请先安装 Python (推荐 3.10-3.12) 并勾选 Add Python to PATH。
    pause
    exit /b 1
)

echo [1/2] 正在安装与更新 Python 核心依赖库...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade

echo [2/2] 正在校验 pydantic-core 动态链接库兼容性...
python -c "import pydantic_core; print('  ✓ pydantic-core 动态链接库校验通过')" 2>nul
if %errorlevel% neq 0 (
    echo [自动修复] 正在重新拉取适配当前 Python 环境的 pydantic 与 pydantic-core...
    pip install --upgrade --force-reinstall --no-cache-dir pydantic pydantic-core
)

echo.
echo ================================================================
echo [成功] 所有依赖安装与健康校验完毕！
echo 您可以直接双击运行 start_windows.bat 启动系统。
echo ================================================================
echo.
pause
