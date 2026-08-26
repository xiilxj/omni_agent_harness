"""
Default Tools Initializer
根据宿主操作系统自动装配与注册全套 Agent 工具箱
"""

import sys
from typing import Optional

from harness.core.config import get_os_type
from harness.tools.registry import ToolRegistry, global_tools
from harness.tools.bash_executor import run_shell_command
from harness.tools.win_executor import run_powershell_command
from harness.tools.file_ops import view_file, write_file, replace_file_content
from harness.tools.search_ops import list_dir, grep_search, find_by_name


def register_default_tools(registry: Optional[ToolRegistry] = None) -> ToolRegistry:
    """注册开箱即用的 Agent 工具集"""
    reg = registry or global_tools
    os_name = get_os_type()

    # 1. 跨平台 Shell 执行器
    if os_name == "Windows":
        @reg.register(
            name="run_command",
            description="Execute a PowerShell command on the Windows host and return stdout/stderr.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The exact PowerShell command line to execute."},
                    "cwd": {"type": "string", "description": "Optional working directory."}
                },
                "required": ["command"]
            }
        )
        async def _run_cmd_win(command: str, cwd: Optional[str] = None) -> str:
            return await run_powershell_command(command, cwd=cwd)
    else:
        @reg.register(
            name="run_command",
            description="Execute a shell command (Bash) on the Linux/macOS host and return stdout/stderr.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The exact bash command line to execute."},
                    "cwd": {"type": "string", "description": "Optional working directory."}
                },
                "required": ["command"]
            }
        )
        async def _run_cmd_linux(command: str, cwd: Optional[str] = None) -> str:
            return await run_shell_command(command, cwd=cwd)

    # 2. 文件查看
    @reg.register(
        name="view_file",
        description="View file contents with line numbers. Supports slice viewing with start_line and end_line.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file to view."},
                "start_line": {"type": "integer", "description": "Optional starting line number (1-indexed)."},
                "end_line": {"type": "integer", "description": "Optional ending line number (1-indexed)."}
            },
            "required": ["file_path"]
        }
    )
    def _view_file(file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        return view_file(file_path, start_line=start_line, end_line=end_line)

    # 3. 文件写入
    @reg.register(
        name="write_file",
        description="Create a new file or completely overwrite an existing file with the provided content.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the target file."},
                "content": {"type": "string", "description": "Full text content to write."},
                "overwrite": {"type": "boolean", "description": "Whether to overwrite if file exists (default: true)."}
            },
            "required": ["file_path", "content"]
        }
    )
    def _write_file(file_path: str, content: str, overwrite: bool = True) -> str:
        return write_file(file_path, content, overwrite=overwrite)

    # 4. 文件精准替换 (StrReplace / Diff Edit)
    @reg.register(
        name="replace_file_content",
        description="Replace a unique contiguous block of text in an existing file. Exactly matches old_content and replaces it with new_content.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file to modify."},
                "old_content": {"type": "string", "description": "The exact string chunk in the file to be replaced."},
                "new_content": {"type": "string", "description": "The replacement string chunk."}
            },
            "required": ["file_path", "old_content", "new_content"]
        }
    )
    def _replace_file(file_path: str, old_content: str, new_content: str) -> str:
        return replace_file_content(file_path, old_content, new_content)

    # 5. 目录列表
    @reg.register(
        name="list_dir",
        description="List files and subdirectories within a given directory.",
        parameters={
            "type": "object",
            "properties": {
                "directory_path": {"type": "string", "description": "Directory path to list (default: '.')."},
                "max_depth": {"type": "integer", "description": "Maximum directory depth to traverse (default: 2)."}
            }
        }
    )
    def _list_dir(directory_path: str = ".", max_depth: int = 2) -> str:
        return list_dir(directory_path, max_depth=max_depth)

    # 6. 正则文本搜索
    @reg.register(
        name="grep_search",
        description="Search for exact text or regex patterns within files in a directory or file.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The text pattern to search for."},
                "search_path": {"type": "string", "description": "File or directory path to search within (default: '.')."},
                "is_regex": {"type": "boolean", "description": "Whether to treat query as a regex."},
                "file_pattern": {"type": "string", "description": "Optional glob pattern to filter filenames (e.g. '*.py')."}
            },
            "required": ["query"]
        }
    )
    def _grep(query: str, search_path: str = ".", is_regex: bool = False, file_pattern: Optional[str] = None) -> str:
        return grep_search(query, search_path=search_path, is_regex=is_regex, file_pattern=file_pattern)

    # 7. 文件名匹配查找
    @reg.register(
        name="find_by_name",
        description="Search for files and directories by name glob pattern.",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Filename glob pattern to match (e.g. '*.json', 'config*')."},
                "search_dir": {"type": "string", "description": "Root directory to search within (default: '.')."}
            },
            "required": ["pattern"]
        }
    )
    def _find(pattern: str, search_dir: str = ".") -> str:
        return find_by_name(pattern, search_dir=search_dir)

    # 8. Web 网页抓取与 Markdown 提取
    from harness.tools.web_ops import read_url_content as _read_url_fn

    @reg.register(
        name="read_url_content",
        description="Fetch webpage content via HTTP GET, strip HTML tags, and convert into clean markdown/text.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The exact URL to fetch and read."},
                "max_length": {"type": "integer", "description": "Maximum text characters to return (default: 8000)."}
            },
            "required": ["url"]
        }
    )
    async def _read_url(url: str, max_length: int = 8000) -> str:
        return await _read_url_fn(url, max_length=max_length)

    # 9. 交互式向用户提问与选项卡片 (Interactive Choice Modal)
    @reg.register(
        name="ask_user",
        description="Ask the user a question with selectable options or open input when encountering ambiguity, design decisions, or needing user confirmation. Pauses execution until the user selects an option in the UI.",
        parameters={
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The exact question or decision point to present to the user."},
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of 2 to 5 actionable options for the user to choose from."
                },
                "is_multi_select": {
                    "type": "boolean",
                    "description": "Whether the user can select multiple options (default: false)."
                }
            },
            "required": ["question", "options"]
        }
    )
    async def _ask_user(question: str, options: list, is_multi_select: bool = False) -> str:
        return f"Interactive question presented to user: '{question}'. Awaiting response."

    # 10. 动态任务待办里程碑清单 (Dynamic Todo Checklist)
    @reg.register(
        name="update_todo_list",
        description="Create or update the structured execution todo checklist. Use this to track multi-step task progress, display visual milestones, and mark steps as pending, in_progress, completed, or failed in real-time.",
        parameters={
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Unique ID for the step (e.g. '1', 'step-recon')."},
                            "title": {"type": "string", "description": "Clear description of the step (e.g. '探测目标开放端口与服务')."},
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "completed", "failed"],
                                "description": "Current status of this step."
                            }
                        },
                        "required": ["id", "title", "status"]
                    },
                    "description": "The complete list of todo steps reflecting current progress."
                }
            },
            "required": ["todos"]
        }
    )
    def _update_todos(todos: list) -> str:
        completed = sum(1 for t in todos if t.get("status") == "completed")
        return f"Todo checklist updated: {completed}/{len(todos)} steps completed."

    # 11. Codex 级代码符号与定义检索 (AST / Symbol Indexing)
    from harness.tools.search_ops import find_symbol_definition as _find_symbol_fn

    @reg.register(
        name="find_symbol_definition",
        description="Locate declarations and definitions of classes, functions, methods, structs, or interfaces across the codebase by symbol name. Returns exact file locations, line numbers, and signature code snippets without loading entire large files.",
        parameters={
            "type": "object",
            "properties": {
                "symbol_name": {"type": "string", "description": "The name of the class, function, method, or struct to locate (e.g. 'OmniAgent', 'run_task', 'User')."},
                "search_path": {"type": "string", "description": "Directory or file to search within (default: '.')."}
            },
            "required": ["symbol_name"]
        }
    )
    def _find_symbol(symbol_name: str, search_path: str = ".") -> str:
        return _find_symbol_fn(symbol_name, search_path=search_path)

    return reg
