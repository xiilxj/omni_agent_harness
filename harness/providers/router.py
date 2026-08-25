"""
Provider Router & Key Pool Manager
支持多厂商路由、多 Key 轮询负载均衡与故障转移 (Failover)
"""

import itertools
import os
from typing import Any, Dict, List, Optional
from harness.core.config import AppConfig
from harness.providers.base import BaseProvider
from harness.providers.openai_provider import OpenAICompatibleProvider
from harness.providers.anthropic_provider import AnthropicProvider


class ProviderRouter:
    """Provider 路由管理器与多 Key 轮询调度器"""

    def __init__(self, config: AppConfig):
        self.config = config
        self._providers: Dict[str, BaseProvider] = {}
        self._key_iterators: Dict[str, Any] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """初始化配置文件中定义的所有 Provider"""
        providers_data = self.config.providers

        for name, p_data in providers_data.items():
            if not isinstance(p_data, dict):
                continue

            p_type = p_data.get("type", "openai_compatible")
            base_url = p_data.get("base_url", "")
            raw_keys = p_data.get("api_key", "")
            timeout = p_data.get("timeout", 120)

            # 支持逗号分隔的多 Key 轮询
            if isinstance(raw_keys, str) and "," in raw_keys:
                key_list = [k.strip() for k in raw_keys.split(",") if k.strip()]
            elif isinstance(raw_keys, list):
                key_list = [str(k).strip() for k in raw_keys if str(k).strip()]
            else:
                key_list = [str(raw_keys).strip()] if str(raw_keys).strip() else ["EMPTY"]

            # 设置循环迭代器
            self._key_iterators[name] = itertools.cycle(key_list)
            first_key = next(self._key_iterators[name])

            if p_type == "anthropic":
                self._providers[name] = AnthropicProvider(
                    name=name,
                    base_url=base_url,
                    api_key=first_key,
                    timeout=timeout
                )
            else:
                self._providers[name] = OpenAICompatibleProvider(
                    name=name,
                    base_url=base_url,
                    api_key=first_key,
                    timeout=timeout
                )

    def get_provider(self, provider_name: Optional[str] = None) -> BaseProvider:
        """获取指定或默认的 Provider 实例，并执行 Key 轮询"""
        p_name = provider_name or self.config.providers.get("default_provider", "deepseek")
        if p_name not in self._providers:
            # 兜底回退至首个可用 Provider
            if self._providers:
                p_name = list(self._providers.keys())[0]
            else:
                # 默认创建一个 DeepSeek provider
                return OpenAICompatibleProvider(
                    name="deepseek",
                    base_url="https://api.deepseek.com/v1",
                    api_key=os.environ.get("DEEPSEEK_API_KEY", "EMPTY")
                )

        provider = self._providers[p_name]
        # 轮询下一张 API Key
        if p_name in self._key_iterators:
            provider.api_key = next(self._key_iterators[p_name])

        return provider
