"""
Unit Tests for Omni Agent ReAct Loop
使用 Mock Provider 验证 Agent 的思考、工具调用派发、结果观察与最终结论闭环
"""

import pytest
from typing import Any, AsyncGenerator, Dict, List, Optional
from harness.core.agent import OmniAgent
from harness.core.config import AppConfig
from harness.core.models import LLMResponse, Message, ToolCall, ToolFunction, UsageStats
from harness.providers.base import BaseProvider
from harness.tools.registry import ToolRegistry


class MockProvider(BaseProvider):
    """模拟大模型交互响应"""
    def __init__(self):
        super().__init__("mock", "http://mock", "mock-key")
        self.step_idx = 0

    async def chat(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        self.step_idx += 1
        if self.step_idx == 1:
            # 步骤 1: 思考并决定调用 view_file 工具
            return LLMResponse(
                content="I need to inspect the file first.",
                tool_calls=[
                    ToolCall(
                        id="call_001",
                        type="function",
                        function=ToolFunction(
                            name="test_tool",
                            arguments={"value": "hello_mock"}
                        )
                    )
                ],
                usage=UsageStats(prompt_tokens=10, completion_tokens=5, total_tokens=15)
            )
        else:
            # 步骤 2: 观察到工具输出后给出最终结论
            return LLMResponse(
                content="Task completed successfully with output: hello_mock.",
                tool_calls=None,
                usage=UsageStats(prompt_tokens=15, completion_tokens=10, total_tokens=25)
            )

    async def stream_chat(self, *args, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        self.step_idx += 1
        if self.step_idx == 1:
            yield {"type": "delta", "reasoning_content": "Planning steps...", "content": "I need to inspect the file first."}
            yield {"type": "delta", "tool_calls": [{"index": 0, "id": "call_001", "function": {"name": "test_tool", "arguments": '{"value": "hello_mock"}'}}]}
            yield {"type": "done"}
        else:
            yield {"type": "delta", "content": "Task completed successfully with output: hello_mock."}
            yield {"type": "done"}


@pytest.mark.asyncio
async def test_agent_react_loop():
    config = AppConfig()
    custom_tools = ToolRegistry()

    @custom_tools.register(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"]}
    )
    def _test_func(value: str) -> str:
        return f"Executed with: {value}"

    agent = OmniAgent(config=config, tools=custom_tools)
    # 替换为 Mock Provider
    mock_prov = MockProvider()
    agent.router._providers["deepseek"] = mock_prov

    result = await agent.run_task("Please run the mock test.")
    assert "Task completed successfully" in result
    assert len(agent.messages) >= 3
