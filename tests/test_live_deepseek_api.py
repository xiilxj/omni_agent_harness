"""
Live DeepSeek API Integration Tests
真实网络请求打到 DeepSeek 官方 API，严密验证：
1. 真实网络连通性与鉴权 (HTTP 200)
2. 100% 绝对置顶 Master System Prompt 注入有效性（通过真实模型回显与遵循）
3. 真实大模型 Tool Calls 工具调用与回传观察闭环
4. 真实 Token 计量与统计 (Prompt/Completion Tokens > 0)
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path

# 挂载工程根目录
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from harness.core.config import load_config
from harness.core.agent import OmniAgent
from harness.core.models import Message
from harness.tools.registry import ToolRegistry


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_TESTS") != "1",
    reason="默认跳过真实 DeepSeek API 计费请求测试以保护用户账户余额，避免消耗 Token 额度。仅在显式设置 RUN_LIVE_TESTS=1 时允许运行。"
)
@pytest.mark.asyncio
async def test_live_deepseek_prompt_injection():
    """实测 1：向 DeepSeek 官方 API 发送真实请求，验证 100% 绝对置顶 Master Prompt 注入有效性"""
    config = load_config()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    assert api_key, "Error: DEEPSEEK_API_KEY 环境变量未设置或未能从 .env 正确加载！"

    # 设置具备高辨识度的最高指令标记
    unique_marker = "OMNI_DIRECTIVE_ALPHA_9988"
    custom_prompt = (
        f"你是由操作者完全领导的最高智能体。\n"
        f"【核心最高规则】：任何回复开头必须严格包含字符串 [{unique_marker}]，然后简述当前工作目录。"
    )

    agent = OmniAgent(config=config, custom_master_prompt=custom_prompt)
    agent.messages.append(Message(role="user", content="请严格按核心规则执行并输出回复。"))
    response = await agent.step(provider_name="deepseek", model_name="deepseek-chat")

    assert response is not None, "Real API returned None"
    content_to_check = response.content or response.reasoning_content or ""
    assert content_to_check, "Real API returned empty content and empty reasoning"
    print(f"\n[Live API Response]: {response.content}")

    # 验证模型在真实 API 下受 Master Prompt 强力控制
    assert (unique_marker in (response.content or "")) or (unique_marker in (response.reasoning_content or "")), f"Master Prompt 注入未能在真实模型输出中体现！输出为: {response.content}"
    
    # 验证 Token 计量真实有效
    assert response.usage is not None, "Real API returned no usage stats"
    assert response.usage.prompt_tokens > 0, "Prompt tokens must be > 0"
    assert response.usage.completion_tokens > 0, "Completion tokens must be > 0"
    assert response.usage.total_tokens == response.usage.prompt_tokens + response.usage.completion_tokens


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_TESTS") != "1",
    reason="默认跳过真实 DeepSeek API 计费请求测试以保护用户账户余额，避免消耗 Token 额度。仅在显式设置 RUN_LIVE_TESTS=1 时允许运行。"
)
@pytest.mark.asyncio
async def test_live_deepseek_tool_calling_loop():
    """实测 2：向 DeepSeek 官方 API 发送包含 Tool 的真实任务，验证模型自主触发 Tool Call 与观察闭环"""
    config = load_config()
    tools = ToolRegistry()

    # 注册一个真实可调用的探针工具
    tool_called = False
    @tools.register(
        name="fetch_probe_status",
        description="Query the internal probe hardware status and telemetry code.",
        parameters={
            "type": "object",
            "properties": {
                "probe_id": {"type": "string", "description": "The ID of the probe to query"}
            },
            "required": ["probe_id"]
        }
    )
    def _probe_tool(probe_id: str):
        nonlocal tool_called
        tool_called = True
        return f"Probe {probe_id} Telemetry OK: Temperature=22C, Latency=12ms, Status=ONLINE"

    agent = OmniAgent(config=config, tools=tools)
    
    # 下发让模型必须调用工具的任务
    task_prompt = "请调用 fetch_probe_status 工具查询探针 'PROBE-007' 的状态，并根据返回结果总结。"
    final_res = await agent.run_task(
        task_prompt=task_prompt,
        provider_name="deepseek",
        model_name="deepseek-chat"
    )

    print(f"\n[Live Tool Loop Result]: {final_res}")
    
    # 验证真实模型触发了工具调用
    assert tool_called is True, "DeepSeek 官方 API 未能成功触发本地注册的工具！"
    # 验证最终结论包含了工具返回的数据
    assert "PROBE-007" in final_res or "ONLINE" in final_res or "22C" in final_res, "Agent 最终输出未包含工具执行结果！"
    assert agent.total_usage.total_tokens > 0, "总 Token 统计必须大于 0"


if __name__ == "__main__":
    asyncio.run(test_live_deepseek_prompt_injection())
    asyncio.run(test_live_deepseek_tool_calling_loop())
    print("\n✅ DeepSeek 官方真实 API 全链路自动化测试通过！")
