"""
Anthropic Claude Provider
适配 Anthropic Claude 3.5 Sonnet/Haiku/Opus API 规范
"""

import json
import httpx
from typing import Any, AsyncGenerator, Dict, List, Optional
from harness.core.models import LLMResponse, Message, ToolCall, ToolFunction, UsageStats
from harness.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API 适配器"""

    def _convert_messages_to_anthropic(self, messages: List[Message]):
        """将内部 Message 格式转换为 Anthropic (system 参数独立，消息数组规范化)"""
        system_prompt = ""
        anthropic_messages = []

        for msg in messages:
            if msg.role in ("system", "developer"):
                system_prompt += (str(msg.content or "") + "\n\n")
            elif msg.role == "user":
                anthropic_messages.append({"role": "user", "content": str(msg.content or "")})
            elif msg.role == "assistant":
                content_blocks = []
                if msg.content:
                    content_blocks.append({"type": "text", "text": str(msg.content)})
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        args = tc.function.arguments
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                args = {"raw": args}
                        content_blocks.append({
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.function.name,
                            "input": args
                        })
                anthropic_messages.append({"role": "assistant", "content": content_blocks if content_blocks else ""})
            elif msg.role == "tool":
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id or "",
                        "content": str(msg.content or "")
                    }]
                })

        return system_prompt.strip(), anthropic_messages

    async def chat(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        system_str, ant_messages = self._convert_messages_to_anthropic(messages)

        body: Dict[str, Any] = {
            "model": model,
            "messages": ant_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature
        }
        if system_str:
            body["system"] = system_str
        if tools:
            body["tools"] = tools
        if extra_params:
            body.update(extra_params)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code != 200:
                raise RuntimeError(f"Anthropic API Error ({resp.status_code}): {resp.text}")

            data = resp.json()
            content_text = ""
            tool_calls = []

            for block in data.get("content", []):
                if block.get("type") == "text":
                    content_text += block.get("text", "")
                elif block.get("type") == "tool_use":
                    tool_calls.append(
                        ToolCall(
                            id=block["id"],
                            type="function",
                            function=ToolFunction(
                                name=block["name"],
                                arguments=block.get("input", {})
                            )
                        )
                    )

            usage_info = data.get("usage", {})
            usage = UsageStats(
                prompt_tokens=usage_info.get("input_tokens", 0),
                completion_tokens=usage_info.get("output_tokens", 0),
                total_tokens=usage_info.get("input_tokens", 0) + usage_info.get("output_tokens", 0)
            )

            return LLMResponse(
                content=content_text if content_text else None,
                tool_calls=tool_calls if tool_calls else None,
                finish_reason=data.get("stop_reason", "stop"),
                usage=usage,
                raw_response=data
            )

    async def stream_chat(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        system_str, ant_messages = self._convert_messages_to_anthropic(messages)

        body: Dict[str, Any] = {
            "model": model,
            "messages": ant_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
            "stream": True
        }
        if system_str:
            body["system"] = system_str
        if tools:
            body["tools"] = tools
        if extra_params:
            body.update(extra_params)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, headers=headers, json=body) as response:
                if response.status_code != 200:
                    err_body = await response.aread()
                    raise RuntimeError(f"Anthropic Stream Error ({response.status_code}): {err_body.decode('utf-8')}")

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    try:
                        chunk = json.loads(data_str)
                        ev_type = chunk.get("type")
                        if ev_type == "content_block_delta":
                            delta = chunk.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield {"type": "delta", "content": delta.get("text")}
                        elif ev_type == "message_stop":
                            yield {"type": "done"}
                    except json.JSONDecodeError:
                        continue
