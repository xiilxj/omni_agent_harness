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


def load_env_keys(override: bool = True):
    """自动加载本地与全局 .env 中的 API 密钥"""
    from pathlib import Path
    candidate_envs = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path.home() / ".config" / "dsh" / ".env"
    ]
    for env_path in candidate_envs:
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k:
                            if override or not os.environ.get(k):
                                os.environ[k] = v
            except Exception:
                pass


def infer_provider_from_model(model_name: Optional[str], default_provider: str = "deepseek") -> str:
    """根据模型名称智能推导对应的供应商 ID"""
    if not model_name:
        return default_provider
    m = model_name.lower().strip()
    if m.startswith("gemini-") or m.startswith("models/gemini") or m.startswith("models/gemma") or "gemini" in m:
        return "gemini"
    if m.startswith("deepseek-"):
        return "deepseek"
    if m.startswith("claude-"):
        return "anthropic"
    if m.startswith("gpt-") or m.startswith("o1-") or m.startswith("o3-") or m.startswith("text-embedding"):
        return "openai"
    if m.startswith("moonshot-"):
        return "moonshot"
    return default_provider


class ProviderRouter:
    """Provider 路由管理器与多 Key 轮询调度器"""

    def __init__(self, config: AppConfig):
        self.config = config
        self._providers: Dict[str, BaseProvider] = {}
        self._key_iterators: Dict[str, Any] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """初始化配置文件与持久化管理器中定义的所有 Provider"""
        load_env_keys()
        from harness.providers.manager import ProviderManager
        self.mgr = ProviderManager()
        custom_data = self.mgr.load_data().get("providers", {})

        # 合并默认配置与用户自定义供应商
        all_providers = dict(self.config.providers)
        for k, v in custom_data.items():
            if k not in all_providers or not isinstance(all_providers[k], dict):
                all_providers[k] = v

        for name, p_data in all_providers.items():
            if not isinstance(p_data, dict):
                continue

            p_type = p_data.get("type", "openai_compatible")
            base_url = p_data.get("base_url", "")
            env_key = os.environ.get(f"{name.upper()}_API_KEY") or os.environ.get(f"{name.upper()}_KEY") or ""
            if not env_key and name == "deepseek":
                env_key = os.environ.get("OPENAI_API_KEY", "")
            raw_keys = env_key or p_data.get("api_key", "")
            timeout = p_data.get("timeout", 180)

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
        """获取指定或默认的 Provider 实例，并执行 Key 轮询与动态热刷新"""
        p_name = (provider_name or getattr(self.config, "default_provider", "deepseek") or "deepseek").lower().strip()
        load_env_keys()

        # 如果 requested provider 尚未缓存，尝试从 ProviderManager 动态加载
        if p_name not in self._providers:
            from harness.providers.manager import ProviderManager
            mgr = ProviderManager()
            p_info = mgr.get_provider_info(p_name)
            if p_info:
                p_type = p_info.get("type", "openai_compatible")
                base_url = p_info.get("base_url", "")
                env_var = p_info.get("env_key") or f"{p_name.upper()}_API_KEY"
                k_val = os.environ.get(env_var) or p_info.get("api_key", "EMPTY")
                if p_type == "anthropic":
                    self._providers[p_name] = AnthropicProvider(name=p_name, base_url=base_url, api_key=k_val)
                else:
                    self._providers[p_name] = OpenAICompatibleProvider(name=p_name, base_url=base_url, api_key=k_val)
            elif self._providers:
                p_name = list(self._providers.keys())[0]
            else:
                return OpenAICompatibleProvider(
                    name="deepseek",
                    base_url="https://api.deepseek.com/v1",
                    api_key=os.environ.get("DEEPSEEK_API_KEY", "EMPTY")
                )

        provider = self._providers[p_name]

        # 动态检测并热刷新环境变量中的最新 API Key 及 Base URL
        from harness.providers.manager import ProviderManager
        mgr = ProviderManager()
        p_info = mgr.get_provider_info(p_name)
        if p_info and p_info.get("base_url"):
            provider.base_url = p_info["base_url"].rstrip("/")

        current_env_key = os.environ.get(f"{p_name.upper()}_API_KEY") or os.environ.get(f"{p_name.upper()}_KEY") or ""
        if current_env_key and (provider.api_key == "EMPTY" or not provider.api_key or provider.api_key != current_env_key):
            provider.api_key = current_env_key

        # 若存在多 Key，执行轮询切换
        if p_name in self._key_iterators:
            current_key = next(self._key_iterators[p_name])
            if current_key != "EMPTY":
                provider.api_key = current_key

        return provider
