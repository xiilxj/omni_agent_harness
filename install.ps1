# Omni Agent Harness (Codex-DSH Core) - Windows PowerShell 一键安装部署脚本
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  正在为 Windows 系统配置 Omni Agent Harness..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. 确保全局配置目录与最高指令文件
$UserHome = [Environment]::GetFolderPath("UserProfile")
$GlobalConf = Join-Path $UserHome ".config\dsh"
if (-not (Test-Path $GlobalConf)) {
    New-Item -ItemType Directory -Path $GlobalConf -Force | Out-Null
}

$DestPrompt = Join-Path $GlobalConf "MASTER_SYSTEM_PROMPT.md"
if (-not (Test-Path $DestPrompt)) {
    Copy-Item (Join-Path $ScriptDir "MASTER_SYSTEM_PROMPT.md") $DestPrompt -Force
}

# 2. 生成 Windows 桌面快捷启动脚本
$DesktopPath = [Environment]::GetFolderPath("Desktop")
# 适配 D 盘桌面环境（如果存在）
if (Test-Path "D:\Desktop") {
    $DesktopPath = "D:\Desktop"
}

$LnkBatch = Join-Path $DesktopPath "启动OmniHarness.bat"
"@echo off`r`ncd /d `"$ScriptDir`"`r`ncall harness.bat --ui`r`npause" | Out-File -FilePath $LnkBatch -Encoding ASCII

Write-Host ""
Write-Host "✅ Windows 环境配置成功!" -ForegroundColor Green
Write-Host "桌面快捷启动已生成至: $LnkBatch" -ForegroundColor Green
Write-Host "全局最高系统指令位置: $DestPrompt" -ForegroundColor Green
Write-Host ""
Write-Host "命令行用法:"
Write-Host "  harness.bat --ui           启动 Web UI 可视化控制台"
Write-Host "  harness.bat -p `"任务内容`"  直接执行单次任务"
Write-Host "  harness.bat                进入交互式命令行模式"
Write-Host "==========================================================" -ForegroundColor Cyan
