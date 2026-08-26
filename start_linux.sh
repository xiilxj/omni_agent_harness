#!/usr/bin/env bash
set -e

echo "================================================================"
echo "          Omni Agent Harness (Codex-DSH 架构) - Linux/macOS"
echo "================================================================"
echo ""

# 1. 检查 Python 3 环境
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "[错误] 未检测到 Python 3 环境！"
    echo "请先安装 Python 3.10 或更高版本。"
    exit 1
fi

# 2. 检查 .env 配置文件是否存在，若不存在则从模板复制
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "[提示] 正在创建初始 .env 配置文件模板..."
        cp .env.example .env
        echo "[提示] 已生成 .env 文件。"
    fi
fi

# 3. 自动安装依赖
echo "[1/3] 正在检查与安装必要依赖库..."
$PYTHON_CMD -m pip install -r requirements.txt --quiet --disable-pip-version-check

# 4. 准备启动
echo "[2/3] Omni Agent Harness 服务已就绪！"
echo "[3/3] 正在启动 Web 控制台..."
echo ""
echo "================================================================"
echo "  控制台地址: http://127.0.0.1:7890"
echo "  如需停止运行，请按 Ctrl + C。"
echo "================================================================"
echo ""

$PYTHON_CMD harness/cli.py --ui --host 127.0.0.1 --port 7890
