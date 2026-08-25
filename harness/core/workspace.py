"""
Workspace Management & File Explorer Engine
支持项目目录树获取、文件夹创建、文件创建及工作区动态切换
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class WorkspaceManager:
    """工作区管理工具"""

    def __init__(self, default_cwd: Optional[str] = None):
        self.cwd = Path(default_cwd or os.getcwd()).resolve()

    def set_cwd(self, new_cwd: str) -> Path:
        p = Path(new_cwd).resolve()
        if p.exists() and p.is_dir():
            self.cwd = p
            os.chdir(str(p))
            return self.cwd
        raise ValueError(f"Directory does not exist: {new_cwd}")

    def list_tree(self, max_depth: int = 3, max_entries: int = 150) -> Dict[str, Any]:
        """递归获取工作区目录树结构"""
        def _build_tree(cur_path: Path, depth: int) -> Dict[str, Any]:
            node = {
                "name": cur_path.name if cur_path != self.cwd else str(self.cwd),
                "path": str(cur_path),
                "is_dir": cur_path.is_dir(),
                "children": []
            }
            if depth >= max_depth or not cur_path.is_dir():
                return node

            try:
                entries = sorted(list(cur_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
                for entry in entries:
                    if entry.name.startswith(".") and entry.name not in [".env.example"]:
                        continue
                    if entry.name in ["__pycache__", "node_modules", ".git", ".pytest_cache"]:
                        continue
                    node["children"].append(_build_tree(entry, depth + 1))
            except PermissionError:
                pass

            return node

        return _build_tree(self.cwd, 0)

    def create_directory(self, rel_path: str) -> str:
        """在当前工作区创建新目录"""
        target = (self.cwd / rel_path).resolve()
        target.mkdir(parents=True, exist_ok=True)
        return str(target)

    def create_file(self, rel_path: str, initial_content: str = "") -> str:
        """在当前工作区创建新文件"""
        target = (self.cwd / rel_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with open(target, "w", encoding="utf-8") as f:
                f.write(initial_content)
        return str(target)


# 全局单例
global_workspace_manager = WorkspaceManager()
