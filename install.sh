#!/usr/bin/env bash
# Omni Agent Harness (Codex-DSH Core) - Linux/WSL 一键全局安装部署脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
mkdir -p "${BIN_DIR}"

echo "=========================================================="
echo "  正在安装 Omni Agent Harness 到全局系统环境..."
echo "=========================================================="

# 1. 创建全局软链接 harness
ln -sf "${SCRIPT_DIR}/harness.sh" "${BIN_DIR}/harness"
chmod +x "${BIN_DIR}/harness"
chmod +x "${SCRIPT_DIR}/harness.sh"

# 2. 初始化全局配置目录与 MASTER_SYSTEM_PROMPT.md
GLOBAL_CONF="${HOME}/.config/dsh"
mkdir -p "${GLOBAL_CONF}"
if [ ! -f "${GLOBAL_CONF}/MASTER_SYSTEM_PROMPT.md" ]; then
    cp "${SCRIPT_DIR}/MASTER_SYSTEM_PROMPT.md" "${GLOBAL_CONF}/MASTER_SYSTEM_PROMPT.md"
fi

echo ""
echo "✅ 安装成功!"
echo "可执行命令已注册至: ${BIN_DIR}/harness"
echo "全局最高系统指令文件: ${GLOBAL_CONF}/MASTER_SYSTEM_PROMPT.md"
echo ""
echo "使用说明:"
echo "  1) 启动 Web UI:               harness --ui"
echo "  2) 运行单任务模式:             harness -p '编写一个快速排序并测试'"
echo "  3) 交互式终端:                 harness"
echo "  4) 启动底层 DSH 官方 Web 端:   harness --dsh-web"
echo "=========================================================="
