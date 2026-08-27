"""
Provider Configuration & Preset Manager (多模型供应商配置与自由切换中心)
支持任意大模型供应商 (DeepSeek, Gemini, OpenAI, Claude, SiliconFlow, Ollama, 自定义上游) 独立并存、
随时自由切换、零互相覆盖，并支持一键在线探测拉取上游模型列表 (Fetch Models)。
"""

import json
import os
import httpx
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


BUILTIN_PROVIDER_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "deepseek": {
        "id": "deepseek",
        "name": "DeepSeek 官方",
        "type": "openai_compatible",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner", "deepseek-v4-flash", "deepseek-v4-pro"],
        "default_model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
        "description": "DeepSeek 官方大模型 API，支持 DeepSeek-V3/R1 深度思考推理"
    },
    "gemini": {
        "id": "gemini",
        "name": "Google Gemini",
        "type": "openai_compatible",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-thinking-exp-01-21",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ],
        "default_model": "gemini-2.5-flash",
        "env_key": "GEMINI_API_KEY",
        "description": "Google Gemini 官方 OpenAI 兼容接口，支持全系列 Gemini 多模态与长上下文模型"
    },
    "openai": {
        "id": "openai",
        "name": "OpenAI 官方",
        "type": "openai_compatible",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"],
        "default_model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
        "description": "OpenAI 官方接口，支持 GPT-4o 及 o1/o3 复杂推理模型"
    },
    "anthropic": {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "type": "anthropic",
        "base_url": "https://api.anthropic.com/v1",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        "default_model": "claude-3-5-sonnet-20241022",
        "env_key": "ANTHROPIC_API_KEY",
        "description": "Anthropic Claude 官方接口"
    },
    "siliconflow": {
        "id": "siliconflow",
        "name": "SiliconFlow (硅基流动)",
        "type": "openai_compatible",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": [
            "deepseek-ai/DeepSeek-V3",
            "deepseek-ai/DeepSeek-R1",
            "Qwen/Qwen2.5-72B-Instruct",
            "meta-llama/Llama-3.3-70B-Instruct"
        ],
        "default_model": "deepseek-ai/DeepSeek-V3",
        "env_key": "SILICONFLOW_API_KEY",
        "description": "硅基流动高性能大模型托管平台"
    },
    "moonshot": {
        "id": "moonshot",
        "name": "Moonshot (Kimi)",
        "type": "openai_compatible",
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "default_model": "moonshot-v1-8k",
        "env_key": "MOONSHOT_API_KEY",
        "description": "月之暗面 Kimi 长文本大模型"
    },
    "ollama": {
        "id": "ollama",
        "name": "Ollama (本地私有化)",
        "type": "openai_compatible",
        "base_url": "http://localhost:11434/v1",
        "models": ["llama3.3", "qwen2.5-coder", "deepseek-r1:8b"],
        "default_model": "llama3.3",
        "env_key": "OLLAMA_API_KEY",
        "description": "本地部署的 Ollama 开源模型服务"
    }
}


def mask_key(key: Optional[str]) -> str:
    """对 API Key 进行安全掩码展示，支持多 Key 轮询池展示"""
    if not key or key == "EMPTY":
        return "未配置"
    keys = [k.strip() for k in key.split(",") if k.strip()]
    if not keys:
        return "未配置"
    first = keys[0]
    masked_first = f"{first[:4]}...{first[-4:]}" if len(first) >= 8 else "******"
    if len(keys) > 1:
        return f"{masked_first} (+{len(keys)-1} Key轮询)"
    return masked_first


class ProviderManager:
    """模型供应商配置管理与多上游路由持久化中心"""

    def __init__(self, config_dir: Optional[Path] = None, env_file: Optional[Path] = None):
        self.config_dir = config_dir or (Path.cwd() / "config")
        self.storage_file = self.config_dir / "custom_providers.json"
        self.env_file = env_file or (Path.cwd() / ".env")
        self._ensure_storage()

    def _ensure_storage(self):
        """确保存储文件存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.storage_file.exists():
            initial_data = {
                "active_provider": "deepseek",
                "providers": BUILTIN_PROVIDER_TEMPLATES
            }
            try:
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Warning initializing custom_providers.json: {e}")

    def load_data(self) -> Dict[str, Any]:
        """读取供应商配置"""
        self._ensure_storage()
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 补充可能缺失的内置预设
                providers = data.get("providers", {})
                for k, v in BUILTIN_PROVIDER_TEMPLATES.items():
                    if k not in providers:
                        providers[k] = v
                data["providers"] = providers
                return data
        except Exception as e:
            print(f"Error reading custom_providers.json: {e}")
            return {"active_provider": "deepseek", "providers": BUILTIN_PROVIDER_TEMPLATES}

    def save_data(self, data: Dict[str, Any]):
        """保存供应商配置"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_providers(self) -> List[Dict[str, Any]]:
        """获取所有供应商列表及详细信息"""
        try:
            from harness.providers.router import load_env_keys
            load_env_keys(override=True)
        except Exception:
            pass

        data = self.load_data()
        active_id = data.get("active_provider", "deepseek")
        providers = data.get("providers", {})

        result = []
        for p_id, p_info in providers.items():
            env_var = p_info.get("env_key") or f"{p_id.upper()}_API_KEY"
            raw_key = os.environ.get(env_var) or p_info.get("api_key", "")
            
            item = {
                "id": p_id,
                "name": p_info.get("name", p_id),
                "type": p_info.get("type", "openai_compatible"),
                "base_url": p_info.get("base_url", ""),
                "models": p_info.get("models", []),
                "default_model": p_info.get("default_model") or (p_info.get("models", [""])[0] if p_info.get("models") else ""),
                "is_active": (p_id == active_id),
                "is_configured": bool(raw_key and raw_key != "EMPTY"),
                "masked_key": mask_key(raw_key),
                "env_key": env_var,
                "description": p_info.get("description", "")
            }
            result.append(item)
        return result

    def get_provider_info(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """获取单个供应商详情"""
        providers = self.load_data().get("providers", {})
        return providers.get(provider_id.lower())

    def get_active_provider_id(self) -> str:
        """获取当前激活的供应商 ID"""
        return self.load_data().get("active_provider", "deepseek")

    def set_active_provider(self, provider_id: str) -> bool:
        """切换当前激活的供应商"""
        p_id = provider_id.lower().strip()
        data = self.load_data()
        if p_id in data.get("providers", {}):
            data["active_provider"] = p_id
            self.save_data(data)
            return True
        return False

    def save_provider(
        self,
        provider_id: str,
        name: str,
        base_url: str,
        provider_type: str = "openai_compatible",
        api_key: Optional[str] = None,
        models: Optional[List[str]] = None,
        default_model: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """新增或更新指定供应商配置，永不覆盖其他供应商！"""
        p_id = provider_id.lower().strip()
        data = self.load_data()
        providers = data.get("providers", {})

        existing = providers.get(p_id, {})
        env_var = existing.get("env_key") or f"{p_id.upper()}_API_KEY"

        # 如果传入了新 Key，持久化到 .env
        if api_key and api_key.strip():
            clean_key = api_key.strip()
            os.environ[env_var] = clean_key
            self._write_to_env(env_var, clean_key)

        updated_models = models if models is not None else existing.get("models", [])
        if not updated_models and default_model:
            updated_models = [default_model]

        def_model = default_model or existing.get("default_model") or (updated_models[0] if updated_models else "")

        providers[p_id] = {
            "id": p_id,
            "name": name or existing.get("name", p_id),
            "type": provider_type or existing.get("type", "openai_compatible"),
            "base_url": base_url.strip(),
            "models": updated_models,
            "default_model": def_model,
            "env_key": env_var,
            "description": description or existing.get("description", "")
        }

        data["providers"] = providers
        self.save_data(data)
        return providers[p_id]

    def delete_provider(self, provider_id: str) -> bool:
        """删除自定义供应商（内置预设不可删除，仅可清空）"""
        p_id = provider_id.lower().strip()
        data = self.load_data()
        providers = data.get("providers", {})

        if p_id in BUILTIN_PROVIDER_TEMPLATES:
            # 内置供应商恢复默认初始配置
            providers[p_id] = dict(BUILTIN_PROVIDER_TEMPLATES[p_id])
            data["providers"] = providers
            self.save_data(data)
            return True
        elif p_id in providers:
            del providers[p_id]
            if data.get("active_provider") == p_id:
                data["active_provider"] = "deepseek"
            data["providers"] = providers
            self.save_data(data)
            return True
        return False

    def _write_to_env(self, env_var: str, key_val: str):
        """安全写入私有 .env 文件"""
        env_file = self.env_file
        try:
            lines = []
            found = False
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

            new_lines = []
            for line in lines:
                if line.startswith(f"{env_var}="):
                    new_lines.append(f"{env_var}={key_val}\n")
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"{env_var}={key_val}\n")

            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception as e:
            print(f"Warning writing to .env ({env_file}): {e}")

    @staticmethod
    async def fetch_upstream_models(base_url: str, api_key: str) -> Tuple[bool, List[str], str]:
        """
        在线探测并获取上游可用的全部模型列表 (/v1/models 或 /models)
        :return: (success, model_ids, message)
        """
        if not base_url:
            return False, [], "Base URL 不能为空"

        clean_base = base_url.rstrip("/")
        # 尝试标准 OpenAI 规范端点
        test_urls = [
            f"{clean_base}/models",
            f"{clean_base}/v1/models" if not clean_base.endswith("/v1") else f"{clean_base}/models"
        ]
        # 去重
        unique_urls = list(dict.fromkeys(test_urls))

        headers = {
            "Authorization": f"Bearer {api_key}" if api_key and api_key != "EMPTY" else "",
            "Content-Type": "application/json"
        }
        if not headers["Authorization"]:
            del headers["Authorization"]

        last_error = ""
        async with httpx.AsyncClient(timeout=15.0) as client:
            for u in unique_urls:
                try:
                    resp = await client.get(u, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        models = []
                        if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                            for item in data["data"]:
                                if isinstance(item, dict) and "id" in item:
                                    models.append(str(item["id"]))
                                elif isinstance(item, str):
                                    models.append(item)
                        elif isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and "id" in item:
                                    models.append(str(item["id"]))
                                elif isinstance(item, str):
                                    models.append(item)

                        if models:
                            # 过滤并排序
                            sorted_models = sorted(list(set(models)))
                            return True, sorted_models, f"成功从上游获取到 {len(sorted_models)} 个可用模型"
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text[:150]}"
                except Exception as e:
                    last_error = str(e)

        return False, [], f"拉取上游模型列表失败: {last_error}"
