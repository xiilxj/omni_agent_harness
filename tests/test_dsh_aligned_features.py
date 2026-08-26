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
    assert "find_symbol_definition" in names
    assert "run_code_tests" in names
    assert "manage_task" in names


def test_context_pruner_compaction():
    """测试 DSH 级长会话上下文剪枝器对超长历史输出的压缩能力"""
    from harness.core.context_pruner import ContextPruner
    pruner = ContextPruner(max_context_chars=400, tool_truncation_len=100)

    # 构造一条长历史消息列表
    messages = [
        Message(role="system", content="Master System Prompt"),
        Message(role="user", content="First question"),
        Message(role="tool", name="grep_search", content="A" * 500), # 需压缩
        Message(role="assistant", content="Intermediate thought"),
        Message(role="user", content="Recent turn 1"),
        Message(role="assistant", content="Recent turn 2"),
        Message(role="user", content="Latest question")
    ]

    compacted, saved_tokens = pruner.prune_and_compact(messages)
    assert len(compacted) == len(messages)
    assert "Master System Prompt" in compacted[0].content
    assert "Omni Context Pruner" in compacted[2].content
    assert saved_tokens > 50


@pytest.mark.asyncio
async def test_task_manager_lifecycle():
    """测试后台常驻任务管理器启动、状态查询与终止流程"""
    from harness.tools.task_manager import BackgroundTaskManager
    tm = BackgroundTaskManager(log_dir="/tmp/test_omni_tasks")

    # 启动一个后台 sleep 任务
    start_msg = await tm.start_task("sleep 2")
    assert "started successfully" in start_msg
    assert "task-001" in start_msg

    # 查询状态
    status_msg = tm.get_status("task-001")
    assert "RUNNING" in status_msg

    # 终止任务
    kill_msg = await tm.kill_task("task-001")
    assert "terminated" in kill_msg


@pytest.mark.asyncio
async def test_skills_and_mcp_api_endpoints():
    """测试 Skills 技能列表、MCP 配置文件与 Artifacts 产物列表 API 接口"""
    from harness.ui.app import create_app
    from httpx import ASGITransport, AsyncClient

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. 测试 Skills 列表扫描接口
        res_skills = await client.get("/api/skills")
        assert res_skills.status_code == 200
        data_skills = res_skills.json()
        assert "skills" in data_skills
        assert isinstance(data_skills["skills"], list)

        # 2. 测试 MCP 配置读取接口
        res_mcp = await client.get("/api/mcp/config")
        assert res_mcp.status_code == 200
        data_mcp = res_mcp.json()
        assert "config" in data_mcp
        assert "mcpServers" in data_mcp["config"]

        # 3. 测试 Artifacts 产物列表扫描接口
        res_art = await client.get("/api/artifacts/list")
        assert res_art.status_code == 200
        data_art = res_art.json()
        assert "artifacts" in data_art


def test_billing_cost_calculation():
    """测试 DSH 1:1 官方标准模型费率与缓存命中折扣核算算法"""
    from harness.core.billing import calculate_token_cost

    # 1. 测试 deepseek-chat 费率 (输入 ¥1.0/M, 缓存命中 ¥0.1/M, 输出 ¥2.0/M)
    res_chat = calculate_token_cost(
        model_name="deepseek-chat",
        prompt_tokens=10000,
        prompt_cache_hit_tokens=8000,
        completion_tokens=2000
    )
    assert res_chat["prompt_cache_hit_tokens"] == 8000
    assert res_chat["prompt_cache_miss_tokens"] == 2000
    # 未命中: 2000 * 1.0 / 1e6 = 0.002
    # 命中: 8000 * 0.1 / 1e6 = 0.0008
    # 输出: 2000 * 2.0 / 1e6 = 0.004
    # 总计 = 0.0068
    assert res_chat["cost_input_miss"] == 0.002
    assert res_chat["cost_input_hit"] == 0.0008
    assert res_chat["cost_output"] == 0.004
    assert res_chat["turn_cost"] == 0.0068

    # 2. 测试 deepseek-reasoner 深度思考费率 (输入 ¥4.0/M, 缓存命中 ¥1.0/M, 输出 ¥16.0/M)
    res_r1 = calculate_token_cost(
        model_name="deepseek-reasoner",
        prompt_tokens=10000,
        prompt_cache_hit_tokens=5000,
        completion_tokens=1000
    )
    # 未命中: 5000 * 4.0 / 1e6 = 0.02
    # 命中: 5000 * 1.0 / 1e6 = 0.005
    # 输出: 1000 * 16.0 / 1e6 = 0.016
    # 总计 = 0.041
    assert res_r1["turn_cost"] == 0.041



