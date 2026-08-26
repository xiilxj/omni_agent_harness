"""
Search Operations Toolbox (搜索与目录浏览工具集)
提供跨平台目录列表、正则文本搜索 (Grep) 与文件名模式查找
"""

import fnmatch
import os
import re
from pathlib import Path
from typing import List, Optional


def list_dir(
    directory_path: str = ".",
    max_depth: int = 2,
    cwd: Optional[str] = None
) -> str:
    """列出指定目录下的文件与子目录结构"""
    target = Path(directory_path)
    if not target.is_absolute() and cwd:
        target = Path(cwd) / target

    if not target.exists():
        return f"Error: Directory '{directory_path}' does not exist."
    if not target.is_dir():
        return f"Error: Path '{directory_path}' is not a directory."

    output_lines = [f"=== Directory: {directory_path} ==="]
    try:
        base_level = len(target.resolve().parts)
        for root, dirs, files in os.walk(target):
            curr_path = Path(root)
            level = len(curr_path.resolve().parts) - base_level
            if level >= max_depth:
                dirs.clear()
                continue

            indent = "  " * level
            if level > 0:
                output_lines.append(f"{indent}[DIR] {curr_path.name}/")

            sub_indent = "  " * (level + 1)
            for d in sorted(dirs):
                output_lines.append(f"{sub_indent}[DIR] {d}/")
            for f in sorted(files):
                f_path = curr_path / f
                size = f_path.stat().st_size if f_path.exists() else 0
                output_lines.append(f"{sub_indent}[FILE] {f} ({size} bytes)")

        return "\n".join(output_lines[:200])
    except Exception as e:
        return f"Error listing directory '{directory_path}': {e}"


def grep_search(
    query: str,
    search_path: str = ".",
    is_regex: bool = False,
    file_pattern: Optional[str] = None,
    cwd: Optional[str] = None,
    max_matches: int = 50
) -> str:
    """在文件或目录中搜索匹配的文本内容"""
    target = Path(search_path)
    if not target.is_absolute() and cwd:
        target = Path(cwd) / target

    if not target.exists():
        return f"Error: Search path '{search_path}' does not exist."

    matches = []
    pattern = None
    if is_regex:
        try:
            pattern = re.compile(query, re.IGNORECASE)
        except Exception as e:
            return f"Error compiling regex '{query}': {e}"

    search_files: List[Path] = []
    if target.is_file():
        search_files.append(target)
    else:
        for root, _, files in os.walk(target):
            # 过滤常见大型无用目录
            if any(ign in root for ign in [".git", "node_modules", "__pycache__", ".venv"]):
                continue
            for f in files:
                if file_pattern and not fnmatch.fnmatch(f, file_pattern):
                    continue
                search_files.append(Path(root) / f)

    for f_path in search_files:
        if len(matches) >= max_matches:
            break
        try:
            with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f, 1):
                    is_match = False
                    if pattern:
                        is_match = bool(pattern.search(line))
                    else:
                        is_match = query.lower() in line.lower()

                    if is_match:
                        matches.append(f"{f_path.relative_to(target.parent if target.is_file() else target)}:{line_idx}: {line.strip()}")
                        if len(matches) >= max_matches:
                            break
        except Exception:
            continue

    if not matches:
        return f"No matches found for query '{query}' in '{search_path}'."

    header = f"=== Grep Matches for '{query}' (Found {len(matches)}) ===\n"
    return header + "\n".join(matches)


def find_by_name(
    pattern: str,
    search_dir: str = ".",
    cwd: Optional[str] = None,
    max_results: int = 50
) -> str:
    """按文件名通配符查找文件与目录"""
    target = Path(search_dir)
    if not target.is_absolute() and cwd:
        target = Path(cwd) / target

    if not target.exists() or not target.is_dir():
        return f"Error: Search directory '{search_dir}' does not exist or is not a directory."

    results = []
    for root, dirs, files in os.walk(target):
        if any(ign in root for ign in [".git", "node_modules", "__pycache__", ".venv"]):
            continue
        for d in dirs:
            if fnmatch.fnmatch(d, pattern):
                results.append(f"[DIR] {os.path.relpath(os.path.join(root, d), target)}")
                if len(results) >= max_results:
                    break
        for f in files:
            if fnmatch.fnmatch(f, pattern):
                results.append(f"[FILE] {os.path.relpath(os.path.join(root, f), target)}")
                if len(results) >= max_results:
                    break
        if len(results) >= max_results:
            break

    if not results:
        return f"No files or directories matching pattern '{pattern}' found in '{search_dir}'."

    return f"=== Found {len(results)} items matching '{pattern}' ===\n" + "\n".join(results)


def find_symbol_definition(
    symbol_name: str,
    search_path: str = ".",
    cwd: Optional[str] = None,
    max_results: int = 15
) -> str:
    """
    Codex 级代码符号与定义检索器 (AST / Signature Matcher)
    在整个工程代码库中精准定位类定义 (class)、函数/方法 (def/async def/function/fn)、接口与结构体。
    返回精准的文件位置、行号及函数签名代码块，无需加载整个超大文件。
    """
    target = Path(search_path)
    if not target.is_absolute() and cwd:
        target = Path(cwd) / target

    if not target.exists():
        return f"Error: Search path '{search_path}' does not exist."

    # 构造跨语言主流符号定义的匹配正则
    # Python: def func / class Cls / async def func
    # JS/TS: function func / const func = / class Cls / interface Cls / type Cls
    # Rust/Go: fn func / type Struct struct / func (r) Method / func Func
    # C/C++: void func(...) / class Cls / struct Cls
    clean_sym = re.escape(symbol_name.strip())
    patterns = [
        re.compile(rf'^\s*(?:async\s+)?def\s+{clean_sym}\s*\(', re.IGNORECASE),
        re.compile(rf'^\s*class\s+{clean_sym}\b', re.IGNORECASE),
        re.compile(rf'^\s*(?:export\s+)?(?:default\s+)?function\s+{clean_sym}\s*\(', re.IGNORECASE),
        re.compile(rf'^\s*(?:export\s+)?(?:const|let|var)\s+{clean_sym}\s*=\s*(?:async\s+)?(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>', re.IGNORECASE),
        re.compile(rf'^\s*(?:pub\s+)?(?:async\s+)?fn\s+{clean_sym}\b', re.IGNORECASE),
        re.compile(rf'^\s*func\s+(?:\([^)]*\)\s+)?{clean_sym}\s*\(', re.IGNORECASE),
        re.compile(rf'^\s*(?:export\s+)?(?:interface|type|struct|enum)\s+{clean_sym}\b', re.IGNORECASE),
    ]

    results = []
    valid_exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".java", ".cs", ".php", ".rb"}

    search_files: List[Path] = []
    if target.is_file():
        search_files.append(target)
    else:
        for root, _, files in os.walk(target):
            if any(ign in root for ign in [".git", "node_modules", "__pycache__", ".venv", "dist", "build"]):
                continue
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in valid_exts:
                    search_files.append(Path(root) / f)

    for f_path in search_files:
        if len(results) >= max_results:
            break
        try:
            with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_idx, line in enumerate(lines, 1):
                if any(p.search(line) for p in patterns):
                    # 提取签名块（包含上下文 12 行代码与文档注释）
                    start_snippet = max(0, line_idx - 1)
                    end_snippet = min(len(lines), line_idx + 12)
                    snippet_code = "".join(lines[start_snippet:end_snippet]).rstrip()
                    rel_path = f_path.relative_to(target.parent if target.is_file() else target)
                    results.append(
                        f"--- Symbol Match in [{rel_path}:{line_idx}] ---\n```\n{snippet_code}\n```"
                    )
                    if len(results) >= max_results:
                        break
        except Exception:
            continue

    if not results:
        return f"No symbol definition found for '{symbol_name}' in '{search_path}'. Try using grep_search for raw text matches."

    return f"=== Found {len(results)} definitions for symbol '{symbol_name}' ===\n\n" + "\n\n".join(results)

