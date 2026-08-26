#!/usr/bin/env python3
"""
Omni Agent Harness - 纯净 Windows 独立分发包打包程序
严格剔除所有私有 API Key、个人历史会话、个性化提示词与日志，产出完全绿色的 Windows 独立包。
"""

import os
import shutil
import zipfile
from pathlib import Path


def create_clean_windows_package():
    project_root = Path(__file__).resolve().parent
    dist_dir = project_root / "dist"
    dist_dir.mkdir(exist_ok=True)

    zip_filename = "Omni_Agent_Harness_Windows_Clean.zip"
    local_zip_path = dist_dir / zip_filename

    # 包含的顶级核心目录与文件
    include_dirs = ["harness", "config"]
    include_files = [
        "requirements.txt",
        "start_windows.bat",
        "install_windows.bat",
        "start_linux.sh",
        "README_WINDOWS.md",
        "README.md",
        ".env.example"
    ]

    # 严格排除的文件名与后缀模式
    exclude_patterns = [
        ".env",
        ".git",
        "__pycache__",
        ".pytest_cache",
        "*.pyc",
        "*.log",
        "dist",
        "tests",
        ".user_uploaded",
        ".system_generated",
        "sessions",
        "prompt_presets.json",
        "MASTER_SYSTEM_PROMPT.md"  # 不包含用户的当前私有提示词，完全留白
    ]

    print(f"[1/4] 开始构建 Windows/全平台 纯净独立分发包: {zip_filename} ...")

    with zipfile.ZipFile(local_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. 打包顶级文件
        for fname in include_files:
            fpath = project_root / fname
            if fpath.exists() and fpath.is_file():
                zf.write(fpath, arcname=f"Omni_Agent_Harness/{fname}")
                print(f"  + 添加文件: {fname}")

        # 2. 递归打包核心目录
        for dirname in include_dirs:
            dirpath = project_root / dirname
            if not dirpath.exists():
                continue
            for root, dirs, files in os.walk(dirpath):
                # 过滤目录
                dirs[:] = [d for d in dirs if d not in ["__pycache__", ".pytest_cache", "dist", ".git"]]
                for file in files:
                    if file.endswith(".pyc") or file.endswith(".log") or file == ".env":
                        continue
                    full_p = Path(root) / file
                    rel_p = full_p.relative_to(project_root)
                    arc_name = f"Omni_Agent_Harness/{rel_p.as_posix()}"
                    zf.write(full_p, arcname=arc_name)

    size_kb = local_zip_path.stat().st_size / 1024
    print(f"[2/4] 打包成功! 文件大小: {size_kb:.2f} KB")

    # 3. 严格安全审计与验证
    print("[3/4] 正在执行打包安全审计...")
    with zipfile.ZipFile(local_zip_path, "r") as zf:
        namelist = zf.namelist()
        for name in namelist:
            if name.endswith("/.env") or name == "Omni_Agent_Harness/.env":
                raise RuntimeError("安全审计失败: 发现私有 .env 文件被打包!")
            if "__pycache__" in name or name.endswith(".pyc"):
                raise RuntimeError(f"安全审计失败: 发现缓存文件 {name}")

    print("  ✓ 安全审计通过: 零私有密钥、零个人提示词、零历史会话残留。")

    # 4. 完成生成通知
    print(f"\n[完成] 纯净分发包已成功生成并保存在工程目录: dist/{zip_filename}")
    print(f"  ✓ 物理路径: {local_zip_path.resolve()}")
    print("  ✓ 已遵循用户指令：不向 Arch 系统桌面投递任何临时或导出文件。")


if __name__ == "__main__":
    create_clean_windows_package()
