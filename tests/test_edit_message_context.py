"""
Tests for Editing Assistant Messages and Context Substitution in Subsequent Turns
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from harness.ui.app import create_app
from harness.core.config import AppConfig
from harness.core.session import SessionItem, SessionManager, global_session_manager
from harness.core.models import Message
from harness.core.agent import OmniAgent
from harness.tools.registry import ToolRegistry


@pytest.fixture
def client(tmp_path):
    app = create_app()
    return TestClient(app)


def test_edit_session_message_endpoint(client, tmp_path):
    """测试修改模型回答接口并验证数据持久化"""
    # 1. 创建会话
    create_res = client.post("/api/sessions", json={"title": "Test Edit Session"})
    assert create_res.status_code == 200
    session_id = create_res.json()["session"]["id"]

    # 2. 模拟注入历史消息 (包含 User 和 Assistant 回答)
    session = global_session_manager.get_session(session_id)
    session.messages = [
        {"role": "user", "content": "1 + 1 等于多少？"},
        {"role": "assistant", "content": "1 + 1 等于 3（错误答案）"}
    ]
    global_session_manager.save_session(session)

    # 3. 调用编辑接口，修改第 1 条消息（Assistant 回答）
    edit_res = client.post(
        f"/api/sessions/{session_id}/messages/1/edit",
        json={"content": "1 + 1 等于 2（已纠正并替换为正确答案）"}
    )
    assert edit_res.status_code == 200
    edit_data = edit_res.json()
    assert edit_data["status"] == "success"
    assert edit_data["content"] == "1 + 1 等于 2（已纠正并替换为正确答案）"

    # 4. 再次获取会话，确认持久化已完全更新
    updated_session_res = client.get(f"/api/sessions/{session_id}")
    messages = updated_session_res.json()["session"]["messages"]
    assert len(messages) == 2
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "1 + 1 等于 2（已纠正并替换为正确答案）"


def test_context_substitution_in_agent_runner(tmp_path):
    """验证 Agent 接收到编辑后的会话消息时，大模型提示词注入层会真实携带修改后的回答"""
    config = AppConfig()
    config.workspace.default_cwd = str(tmp_path)
    tools = ToolRegistry()
    agent = OmniAgent(config=config, tools=tools)

    # 模拟从会话加载已编辑的消息
    edited_history = [
        {"role": "user", "content": "你的名字叫什么？"},
        {"role": "assistant", "content": "我的名字叫海鸥（用户手动修改后的回答）"}
    ]

    for m in edited_history:
        agent.messages.append(Message(**m))

    # 执行物理注入层
    injected = agent.injector.inject(
        messages=agent.messages,
        workspace=str(tmp_path)
    )

    # 验证注入给大模型的上下文列表中包含用户修改后的回答
    assistant_msgs = [msg for msg in injected if msg.role == "assistant"]
    assert len(assistant_msgs) >= 1
    assert assistant_msgs[0].content == "我的名字叫海鸥（用户手动修改后的回答）"
