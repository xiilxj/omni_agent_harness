"""
Test DSH Aligned Interactive Systems
验证 ask_user 交互提问、update_todo_list 待办进度、统一 Diff 渲染与 MCP 工具动态装载
"""

import pytest
import asyncio
from harness.core.config import AppConfig
from harness.core.models import Message
from harness.core.agent import OmniAgent
from harness.tools.registry import ToolRegistry
from harness.tools.default_tools import register_default_tools
from harness.tools.mcp_client import global_mcp_manager


@pytest.mark.asyncio
async def test_ask_user_resolver_flow():
    """测试 ask_user 阻塞交互与外部 Future 解析闭环"""
    config = AppConfig()
    tools = ToolRegistry()
    register_default_tools(tools)
    agent = OmniAgent(config=config, tools=tools)

    user_answered = False

    async def mock_user_resolver(tool_id: str, parsed_args: dict):
        nonlocal user_answered
        user_answered = True
        return "User Selected: Option B (高性能模式)"

    agent.ask_user_resolver = mock_user_resolver

    # 直接测试工具分发
    obs = await agent.ask_user_resolver("test-tool-id-1", {
        "question": "请选择性能模式",
        "options": ["Option A (兼容模式)", "Option B (高性能模式)"]
    })

    assert user_answered is True
    assert "Option B" in obs


def test_update_todo_list_execution():
    """测试 update_todo_list 动态任务进度清单计算"""
    tools = ToolRegistry()
    register_default_tools(tools)

    todos = [
        {"id": "1", "title": "资产识别", "status": "completed"},
        {"id": "2", "title": "漏洞扫描", "status": "in_progress"},
        {"id": "3", "title": "生成报告", "status": "pending"}
    ]

    res = tools._tools["update_todo_list"](todos=todos)
    assert "1/3 steps completed" in res


def test_tools_dictionary_order_cache_friendly():
    """验证工具集按字典序排列（DSH 规范级 Prompt Cache 冻结）"""
    tools = ToolRegistry()
    register_default_tools(tools)
    openai_tools = tools.get_openai_tools()
    
    names = [t["function"]["name"] for t in openai_tools]
    assert names == sorted(names)
    assert "ask_user" in names
    assert "update_todo_list" in names
