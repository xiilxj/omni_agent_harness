"""
Unit Test for Gemini thought_signature automatic '继续' injection and self-healing
"""

import pytest
from harness.core.agent import OmniAgent
from harness.core.config import load_config
from harness.core.models import Message, LLMResponse
from harness.tools.registry import global_tools


@pytest.mark.asyncio
async def test_thought_signature_auto_inject_continue():
    """测试当模型上游报 thought_signature 错误时，系统自动注入「继续」指令并无缝自愈继续执行"""
    config = load_config()
    agent = OmniAgent(config=config, tools=global_tools)

    events = []
    async def on_step(ev):
        events.append(ev)

    # 模拟第一次 step_stream 抛出 thought_signature 错误，第二次正常返回结果
    call_count = 0
    async def mock_step_stream(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("OpenAI Stream Error (400): Function call is missing a thought_signature in functionCall parts.")
        return LLMResponse(content="已成功自愈并继续完成后续任务。", finish_reason="stop")

    agent.step_stream = mock_step_stream

    result = await agent.run_task(
        task_prompt="开始执行某项任务",
        max_steps=5,
        on_step_callback=on_step
    )

    # 验证是否拦截并触发了 thought_signature_injected 事件
    injected_events = [e for e in events if e.get("type") == "thought_signature_injected"]
    assert len(injected_events) == 1
    assert injected_events[0]["injected_prompt"] == "继续"

    # 验证消息历史中是否被自动注入了「继续」
    user_msgs = [m.content for m in agent.messages if m.role == "user"]
    assert "继续" in user_msgs
    assert "已成功自愈并继续完成后续任务。" in result
