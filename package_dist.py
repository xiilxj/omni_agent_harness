"""
Omni Agent Harness Packaging & Distribution Tool
一键将 Harness 打包为跨平台独立绿色免安装包，并分发至宿主机桌面 (D 盘 / 外部目录)
"""

import os
import shutil
import zipfile
from pathlib import Path


def create_dist_package():
    base_dir = Path(__file__).resolve().parent
    dist_dir = base_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    zip_name = "Omni_Agent_Harness_Master_Edition.zip"
    zip_path = dist_dir / zip_name

    print(f"[Packaging] 正在打包 Harness 工程至: {zip_path} ...")

    # 包含的文件与目录（严禁包含 .env 敏感密钥文件）
    include_paths = [
        "harness",
        "config",
        "MASTER_SYSTEM_PROMPT.md",
        "README.md",
        "DEV_DOCS.md",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "harness.sh",
        "harness.bat",
        "install.sh",
        "install.ps1"
    ]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in include_paths:
            src = base_dir / item
            if src.is_file():
                zf.write(src, arcname=item)
            elif src.is_dir():
                for root, _, files in os.walk(src):
                    if any(ign in root for ign in ["__pycache__", ".pytest_cache", ".git"]):
                        continue
                    for f in files:
                        if f.endswith(".pyc") or f == ".env":
                            continue
                        f_path = Path(root) / f
                        arcname = f_path.relative_to(base_dir)
                        zf.write(f_path, arcname=str(arcname))

    print(f"[Packaging] 打包成功! 文件大小: {zip_path.stat().st_size / 1024:.2f} KB")

    # 尝试复制至宿主机桌面 (D 盘 / C 盘)
    desktop_candidates = [
        Path("/mnt/d/Desktop"),
        Path("/mnt/d/桌面"),
        Path("/mnt/d"),
        Path("/mnt/c/Users/Lenovo/Desktop"),
        Path("/mnt/c/Users/Lenovo/桌面")
    ]

    copied_to = []
    for d in desktop_candidates:
        if d.exists() and d.is_dir():
            target = d / zip_name
            try:
                shutil.copy2(zip_path, target)
                copied_to.append(str(target))
                print(f"[Export] 已成功导出分发包至宿主机: {target}")
            except Exception as e:
                print(f"[Export Warning] 导出至 {target} 失败: {e}")

    return str(zip_path), copied_to


if __name__ == "__main__":
    create_dist_package()
