#!/usr/bin/env bash
# Omni Agent Harness - Linux / WSL 快速启动脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# 若提供了 --dsh 参数，则直接启动底层深度改造的 DeepSeek Harness
if [ "$1" = "--dsh" ] || [ "$1" = "dsh" ]; then
    shift
    exec dsh "$@"
fi

if [ "$1" = "--dsh-web" ] || [ "$1" = "dsh-web" ]; then
    shift
    exec dsh web "$@"
fi

# 默认启动 Python Omni Harness (支持 --ui, -p, 或终端交互)
exec python3 "${SCRIPT_DIR}/harness/cli.py" "$@"
