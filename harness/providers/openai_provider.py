"""
OpenAI & DeepSeek Compatible Provider
适配 DeepSeek-V3/R1、OpenAI GPT-4o/o3、vLLM、Ollama 等标准 API 规范
"""

import json
import asyncio
import httpx
from typing import Any, AsyncGenerator, Dict, List, Optional
from harness.core.models import LLMResponse, Message, ToolCall, ToolFunction, UsageStats
from harness.providers.base import BaseProvider


class OpenAICompatibleProvider(BaseProvider):
    """OpenAI / DeepSeek 协议兼容适配器"""

    def _convert_messages_to_payload(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """将内部 Message 序列转换为 OpenAI / Gemini 规范的 messages payload (支持 Vision 多模态与文件挂载)"""
        from harness.tools.uploader import encode_image_to_data_uri, is_image_file
        payload = []
        for msg in messages:
            content_val = msg.content or ""
            
            # 处理多模态图片与文件附件
            if msg.attachments and msg.role == "user":
                image_parts = []
                file_notices = []
                for att in msg.attachments:
                    att_path = att.get("path", "")
                    att_name = att.get("name", "file")
                    if att.get("is_image") or (att_path and is_image_file(att_path)):
                        data_uri = encode_image_to_data_uri(att_path)
                        if data_uri:
                            image_parts.append({
                                "type": "image_url",
                                "image_url": {"url": data_uri}
                            })
                    else:
                        file_notices.append(f"- 📎 附件: `{att_name}` (路径: `{att_path}`, 大小: {att.get('size', 0)} 字节)")

                # 如果有图片，组装多模态 Content Parts
                if image_parts:
                    text_content = str(content_val)
                    if file_notices:
                        text_content += "\n\n[用户挂载的文件列表]:\n" + "\n".join(file_notices)
                    parts = [{"type": "text", "text": text_content}]
                    parts.extend(image_parts)
                    content_val = parts
                elif file_notices:
                    text_content = str(content_val) + "\n\n[用户挂载的文件列表，可直接使用工具 view_file / grep_search 查看与分析]:\n" + "\n".join(file_notices)
                    content_val = text_content

            item: Dict[str, Any] = {
                "role": msg.role,
                "content": content_val
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

    def _format_model_for_upstream(self, model: str) -> str:
        """针对 Google Gemini 官方 OpenAI 端点自动补充 models/ 前缀"""
        if "generativelanguage.googleapis.com" in self.base_url:
            if not model.startswith("models/"):
                return f"models/{model}"
        return model

    def _get_api_keys_pool(self) -> List[str]:
        """获取当前配置的可用 API Key 列表"""
        raw = str(self.api_key or "").strip()
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        return keys if keys else ["EMPTY"]

    async def chat(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """执行同步/非流式请求（内置多 Key 轮询故障转移与 503/429 指数退避自动重试）"""
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        api_keys = self._get_api_keys_pool()

        body: Dict[str, Any] = {
            "model": self._format_model_for_upstream(model),
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

        client_timeout = httpx.Timeout(connect=20.0, read=180.0, write=60.0, pool=60.0)
        max_retries = max(3, len(api_keys))
        last_error = ""

        for attempt in range(max_retries):
            current_key = api_keys[attempt % len(api_keys)]
            headers = {
                "Authorization": f"Bearer {current_key}",
                "Content-Type": "application/json"
            }
            try:
                async with httpx.AsyncClient(timeout=client_timeout) as client:
                    resp = await client.post(url, headers=headers, json=body)
                    if resp.status_code != 200:
                        err_text = resp.text
                        last_error = f"HTTP {resp.status_code}: {err_text}"
                        if (resp.status_code in (429, 500, 502, 503, 504) or "UNAVAILABLE" in err_text) and attempt < max_retries - 1:
                            await asyncio.sleep(1.2 * (attempt + 1))
                            continue
                        raise RuntimeError(f"OpenAI API Error ({resp.status_code}): {err_text}")

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
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError, httpx.ConnectTimeout, httpx.PoolTimeout) as ne:
                last_error = str(ne)
                if attempt == max_retries - 1:
                    raise RuntimeError(f"上游 API 网络连接中断/超时 (已重试 {max_retries} 次): {str(ne)}。请检查网络状态、API Key 或 Base URL。")
                await asyncio.sleep(1.2 * (attempt + 1))

    async def stream_chat(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行流式请求并逐帧解析 SSE（内置多 Key 轮询故障转移与 503/429 指数退避自动重试）"""
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        api_keys = self._get_api_keys_pool()

        body: Dict[str, Any] = {
            "model": self._format_model_for_upstream(model),
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

        client_timeout = httpx.Timeout(connect=20.0, read=180.0, write=60.0, pool=60.0)
        max_retries = max(3, len(api_keys))

        for attempt in range(max_retries):
            current_key = api_keys[attempt % len(api_keys)]
            headers = {
                "Authorization": f"Bearer {current_key}",
                "Content-Type": "application/json"
            }
            try:
                async with httpx.AsyncClient(timeout=client_timeout) as client:
                    async with client.stream("POST", url, headers=headers, json=body) as response:
                        if response.status_code != 200:
                            err_body = await response.aread()
                            err_text = err_body.decode("utf-8", errors="ignore")
                            # 如果是临时过载或配额耗尽 (503 / 429 / 500 / 502 / 504 / UNAVAILABLE / RESOURCE_EXHAUSTED)，执行退避重试并尝试轮询下一个 Key
                            if (response.status_code in (429, 500, 502, 503, 504) or "UNAVAILABLE" in err_text or "RESOURCE_EXHAUSTED" in err_text) and attempt < max_retries - 1:
                                await asyncio.sleep(1.2 * (attempt + 1))
                                continue
                            raise RuntimeError(f"OpenAI Stream Error ({response.status_code}): {err_text}")

                        has_yielded = False
                        async for line in response.aiter_lines():
                            line = line.strip()
                            if not line or not line.startswith("data:"):
                                continue
                            data_str = line[5:].strip()
                            if data_str == "[DONE]":
                                yield {"type": "done"}
                                has_yielded = True
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
                                has_yielded = True
                            except json.JSONDecodeError:
                                continue
                        if has_yielded:
                            return
                return
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError, httpx.ConnectTimeout, httpx.PoolTimeout) as ne:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"上游 API 流式连接超时/中断 (已重试 {max_retries} 次): {str(ne)}。请检查网络状态、API Key 或 Base URL。")
                await asyncio.sleep(1.2 * (attempt + 1))
