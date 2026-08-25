"""
File Operations Toolbox (文件精准操作工具集)
提供文件查看（带行号切片）、完整写入、精确字符串/行替换（StrReplace）
"""

import os
from pathlib import Path
from typing import Optional


def view_file(
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    cwd: Optional[str] = None
) -> str:
    """查看文件内容，支持指定起止行号切片"""
    target = Path(file_path)
    if not target.is_absolute() and cwd:
        target = Path(cwd) / target

    if not target.exists():
        return f"Error: File '{file_path}' does not exist."
    if not target.is_file():
        return f"Error: Path '{file_path}' is not a regular file."

    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        s = max(1, start_line) if start_line is not None else 1
        e = min(total_lines, end_line) if end_line is not None else total_lines

        if s > total_lines:
            return f"Error: start_line {s} exceeds total lines ({total_lines})."
        if s > e:
            return f"Error: start_line ({s}) cannot be greater than end_line ({e})."

        output_lines = []
        for idx in range(s, e + 1):
            output_lines.append(f"{idx:4d} | {lines[idx - 1].rstrip()}")

        header = f"=== File: {file_path} (Lines {s}-{e} of {total_lines}) ===\n"
        return header + "\n".join(output_lines)
    except Exception as e:
        return f"Error reading file '{file_path}': {e}"


def write_file(
    file_path: str,
    content: str,
    overwrite: bool = True,
    cwd: Optional[str] = None
) -> str:
    """写入文件内容，自动创建父目录"""
    target = Path(file_path)
    if not target.is_absolute() and cwd:
        target = Path(cwd) / target

    if target.exists() and not overwrite:
        return f"Error: File '{file_path}' already exists and overwrite is set to False."

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: Successfully wrote {len(content)} characters to '{file_path}'."
    except Exception as e:
        return f"Error writing to file '{file_path}': {e}"


def replace_file_content(
    file_path: str,
    old_content: str,
    new_content: str,
    cwd: Optional[str] = None
) -> str:
    """精准替换文件中的指定字符串块（兼容 Codex / DeepSeek Harness 编辑规范）"""
    target = Path(file_path)
    if not target.is_absolute() and cwd:
        target = Path(cwd) / target

    if not target.exists():
        return f"Error: File '{file_path}' does not exist."

    try:
        with open(target, "r", encoding="utf-8") as f:
            full_text = f.read()

        count = full_text.count(old_content)
        if count == 0:
            return f"Error: The target string `old_content` was not found in '{file_path}'. Please check line breaks and indentation."
        if count > 1:
            return f"Error: Found {count} occurrences of `old_content` in '{file_path}'. Please specify a larger, unique context block."

        replaced_text = full_text.replace(old_content, new_content, 1)
        with open(target, "w", encoding="utf-8") as f:
            f.write(replaced_text)

        return f"Success: Successfully replaced target content in '{file_path}'."
    except Exception as e:
        return f"Error replacing content in file '{file_path}': {e}"
