"""
Unit Tests for Master Response Suffix Engine (最高回答词自动化测试套件)
验证最高回答词定位、读写、自动拼接到 AI 回答末尾、融入上下文历史以及下一次对话无缝读取。
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from harness.core.config import AppConfig, MasterSuffixConfig
from harness.core.models import Message
from harness.prompt.master_injector import MasterPromptInjector
from harness.core.agent import OmniAgent
from harness.ui.app import create_app


def test_master_suffix_reading_and_applying(tmp_path):
    """测试最高回答词文件的读写与自动附加算法"""
    suffix_file = tmp_path / "MASTER_RESPONSE_SUFFIX.md"
    suffix_content = "\n\n---\n**【海鸥执行签结】** 本轮代码已验证，请下发下一步指令。"
    suffix_file.write_text(suffix_content, encoding="utf-8")

    config = AppConfig(
        master_suffix=MasterSuffixConfig(
            file_path=str(suffix_file),
            enabled=True
        )
    )

    injector = MasterPromptInjector(config)
    read_text = injector.read_master_suffix()
    assert "【海鸥执行签结】" in read_text

    # 测试无缝融入 AI 回答末尾
    raw_ai_answer = "我已完成对当前项目的安全加固。"
    merged_answer = injector.apply_master_suffix(raw_ai_answer)

    assert merged_answer.startswith("我已完成对当前项目的安全加固。")
    assert "【海鸥执行签结】" in merged_answer

    # 验证幂等性（若已包含该后缀，不重复追加）
    idempotent_answer = injector.apply_master_suffix(merged_answer)
    assert idempotent_answer == merged_answer


@pytest.mark.asyncio
async def test_agent_incorporates_suffix_into_context():
    """测试 OmniAgent 在完成回答后将最高回答词融入会话上下文，并在下一轮对话中自然保留"""
    config = AppConfig()
    custom_suffix = "\n\n[STATUS: PHASE_1_COMPLETE]"
    
    agent = OmniAgent(
        config=config,
        custom_master_suffix=custom_suffix
    )

    # 模拟第一轮对话输入
    agent.messages.append(Message(role="user", content="请分析系统状态"))
    
    # 模拟模型生成回答并触发结束
    assistant_content = "系统运行正常，端口 7890 处于监听状态。"
    agent.messages.append(Message(role="assistant", content=assistant_content))

    # 应用最高回答词
    final_output = agent.injector.apply_master_suffix(assistant_content, custom_suffix=agent.custom_master_suffix)
    agent.messages[-1].content = final_output

    assert "[STATUS: PHASE_1_COMPLETE]" in agent.messages[-1].content
    assert agent.messages[-1].content == f"{assistant_content}\n\n[STATUS: PHASE_1_COMPLETE]"

    # 模拟第二轮对话：AI 读取上下文历史
    agent.messages.append(Message(role="user", content="继续执行第二阶段"))
    
    # 验证第一轮助手回答在上下文中完整保留了最高回答词
    assert agent.messages[1].role == "assistant"
    assert "[STATUS: PHASE_1_COMPLETE]" in agent.messages[1].content


def test_api_master_suffix_endpoints(tmp_path):
    """测试 Web API 的 /api/master-suffix GET 与 POST 端点"""
    app = create_app()
    client = TestClient(app)

    # 1. POST 保存最高回答词
    new_suffix = "--- \n**自动签语**：任务完毕。"
    post_res = client.post("/api/master-suffix", json={"content": new_suffix})
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "success"

    # 2. GET 获取最高回答词
    get_res = client.get("/api/master-suffix")
    assert get_res.status_code == 200
    assert get_res.json()["content"] == new_suffix
    assert get_res.json()["char_count"] == len(new_suffix)
