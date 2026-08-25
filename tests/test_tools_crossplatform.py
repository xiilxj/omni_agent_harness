"""
Unit Tests for Cross-Platform Tools
验证跨平台文件读写、行级精准替换 (StrReplace)、目录列表与搜索工具
"""

import pytest
from pathlib import Path
from harness.tools.file_ops import view_file, write_file, replace_file_content
from harness.tools.search_ops import list_dir, grep_search, find_by_name
from harness.tools.bash_executor import run_shell_command
from harness.tools.registry import ToolRegistry


def test_file_operations(tmp_path):
    test_file = tmp_path / "sample.py"
    content = "line 1: hello\nline 2: world\nline 3: python\n"

    # 1. 写入
    w_res = write_file(str(test_file), content)
    assert "Successfully wrote" in w_res
    assert test_file.exists()

    # 2. 切片读取
    v_res = view_file(str(test_file), start_line=2, end_line=3)
    assert "line 2: world" in v_res
    assert "line 3: python" in v_res
    assert "line 1: hello" not in v_res

    # 3. 精准 StrReplace 替换
    r_res = replace_file_content(str(test_file), "line 2: world", "line 2: UNIVERSE")
    assert "Successfully replaced" in r_res
    new_content = test_file.read_text(encoding="utf-8")
    assert "line 2: UNIVERSE" in new_content


def test_search_operations(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "algo.c").write_text("void solve() { int a = 100; }", encoding="utf-8")
    (tmp_path / "readme.txt").write_text("Project manual", encoding="utf-8")

    # 1. 目录列表
    l_res = list_dir(str(tmp_path))
    assert "algo.c" in l_res
    assert "readme.txt" in l_res

    # 2. Grep 搜索
    g_res = grep_search("solve", search_path=str(tmp_path))
    assert "algo.c" in g_res
    assert "void solve()" in g_res

    # 3. 按名称查找
    f_res = find_by_name("*.c", search_dir=str(tmp_path))
    assert "algo.c" in f_res


@pytest.mark.asyncio
async def test_bash_execution():
    res = await run_shell_command("echo 'Omni Harness OK'")
    assert "Omni Harness OK" in res
