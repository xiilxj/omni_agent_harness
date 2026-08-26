"""
OpenAI & DeepSeek Compatible Provider
适配 DeepSeek-V3/R1、OpenAI GPT-4o/o3、vLLM、Ollama 等标准 API 规范
"""

import json
import httpx
from typing import Any, AsyncGenerator, Dict, List, Optional
from harness.core.models import LLMResponse, Message, ToolCall, ToolFunction, UsageStats
from harness.providers.base import BaseProvider


class OpenAICompatibleProvider(BaseProvider):
    """OpenAI / DeepSeek 协议兼容适配器"""

    def _convert_messages_to_payload(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """将内部 Message 序列转换为 OpenAI 规范的 messages payload"""
        payload = []
        for msg in messages:
            item: Dict[str, Any] = {
                "role": msg.role,
                "content": msg.content or ""
            }
            if msg.name:
                item["name"] = msg.name
            if msg.tool_call_id:
                item["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                item["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": (
                                json.dumps(tc.function.arguments)
                                if isinstance(tc.function.arguments, dict)
                                else str(tc.function.arguments)
                            )
                        }
                    }
                    for tc in msg.tool_calls
                ]
            payload.append(item)
        return payload

    async def chat(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """执行同步/非流式请求"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        body: Dict[str, Any] = {
            "model": model,
            "messages": self._convert_messages_to_payload(messages),
            "temperature": temperature,
            "stream": False
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        if max_tokens:
            body["max_tokens"] = max_tokens
        if extra_params:
            ep = dict(extra_params)
            effort = ep.pop("reasoning_effort", None)
            if effort:
                if effort in ("low", "medium", "high"):
                    body["reasoning_effort"] = effort
                elif effort == "max":
                    body["reasoning_effort"] = "high"
                    if not max_tokens:
                        body["max_tokens"] = 32768
            body.update(ep)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API Error ({resp.status_code}): {resp.text}")

            data = resp.json()
            choice = data["choices"][0]
            msg_data = choice.get("message", {})

            # 解析 Tool Calls
            tool_calls = None
            if "tool_calls" in msg_data and msg_data["tool_calls"]:
                tool_calls = []
                for tc in msg_data["tool_calls"]:
                    func = tc["function"]
                    tool_calls.append(
                        ToolCall(
                            id=tc["id"],
                            type=tc.get("type", "function"),
                            function=ToolFunction(
                                name=func["name"],
                                arguments=func.get("arguments", "{}")
                            )
                        )
                    )

            usage_data = data.get("usage", {})
            usage = UsageStats(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
                prompt_cache_hit_tokens=usage_data.get("prompt_cache_hit_tokens", 0),
                prompt_cache_miss_tokens=usage_data.get("prompt_cache_miss_tokens", 0)
            )

            return LLMResponse(
                content=msg_data.get("content"),
                reasoning_content=msg_data.get("reasoning_content"),
                tool_calls=tool_calls,
                finish_reason=choice.get("finish_reason", "stop"),
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
        """执行流式请求并逐帧解析 SSE"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        body: Dict[str, Any] = {
            "model": model,
            "messages": self._convert_messages_to_payload(messages),
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True}
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        if max_tokens:
            body["max_tokens"] = max_tokens
        if extra_params:
            ep = dict(extra_params)
            effort = ep.pop("reasoning_effort", None)
            if effort:
                if effort in ("low", "medium", "high"):
                    body["reasoning_effort"] = effort
                elif effort == "max":
                    body["reasoning_effort"] = "high"
                    if not max_tokens:
                        body["max_tokens"] = 32768
            body.update(ep)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, headers=headers, json=body) as response:
                if response.status_code != 200:
                    err_body = await response.aread()
                    raise RuntimeError(f"OpenAI Stream Error ({response.status_code}): {err_body.decode('utf-8')}")

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        yield {"type": "done"}
                        break

                    try:
                        chunk = json.loads(data_str)
                        if "usage" in chunk and chunk["usage"]:
                            yield {"type": "usage", "usage": chunk["usage"]}

                        choices = chunk.get("choices", [])
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        finish_reason = choices[0].get("finish_reason")

                        yield {
                            "type": "delta",
                            "content": delta.get("content"),
                            "reasoning_content": delta.get("reasoning_content"),
                            "tool_calls": delta.get("tool_calls"),
                            "finish_reason": finish_reason
                        }
                    except json.JSONDecodeError:
                        continue
