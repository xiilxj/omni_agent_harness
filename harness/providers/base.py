"""
Base Provider Interface
规范多厂商 LLM 适配器的统一调用接口
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional
from harness.core.models import LLMResponse, Message


class BaseProvider(ABC):
    """LLM Provider 抽象基类"""

    def __init__(self, name: str, base_url: str, api_key: str, timeout: int = 120):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """执行单次请求并返回 LLMResponse 结构"""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行流式请求并逐 chunk 产出数据（支持实时文字与 Tool Call 片段）"""
        pass
