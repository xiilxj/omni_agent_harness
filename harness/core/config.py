"""
Harness Configuration Loader & Manager
支持 YAML 配置文件加载、环境变量动态替换、跨平台工作区与系统检测
"""

import os
import re
import sys
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkspaceConfig(BaseModel):
    default_cwd: str = "."
    auto_detect_os: bool = True
    allow_shell_execution: bool = True


class MasterPromptConfig(BaseModel):
    file_path: str = "MASTER_SYSTEM_PROMPT.md"
    mode: str = "absolute_pinning"
    zero_token_waste: bool = True
    enable_template_vars: bool = True


class ProviderConfig(BaseModel):
    type: str = "openai_compatible"
    base_url: str = "https://api.deepseek.com/v1"
    api_key: str = ""
    models: List[str] = Field(default_factory=list)
    timeout: int = 120
    max_retries: int = 3


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 7890
    open_browser_on_start: bool = False


# DSH 模型档位映射规范
MODEL_TIERS = {
    "flash": {
        "name": "Flash (极速档)",
        "icon": "⚡",
        "description": "极速响应、低延迟、适合快速检索与高频日常问答",
        "model": "deepseek-v4-flash"
    },
    "pro": {
        "name": "Pro (专业工程档)",
        "icon": "🛠️",
        "description": "高精逻辑、代码生成、完整系统重构与架构落地",
        "model": "deepseek-v4-pro"
    },
    "reasoner": {
        "name": "Reasoner (深度推理档)",
        "icon": "🧠",
        "description": "强推理链、复杂算法、数学推演与底层逆向攻防",
        "model": "deepseek-reasoner"
    },
    "vision": {
        "name": "Vision (多模态档)",
        "icon": "👁️",
        "description": "视觉感知、图像解析与混合模态推理",
        "model": "deepseek-v4-flash-vision-exp"
    }
}

# DSH 权限模式规范
PERMISSION_MODES = {
    "unrestricted": {
        "name": "Unrestricted (无限制自主执行)",
        "badge": "Unrestricted",
        "color": "emerald",
        "description": "智能体全自动调用 Shell、写文件与读网络，完全自主执行"
    },
    "ask_confirmation": {
        "name": "Ask Confirmation (受控审批模式)",
        "badge": "Controlled",
        "color": "amber",
        "description": "读操作自动放行，Shell执行与文件覆写需确认"
    },
    "read_only": {
        "name": "Read-Only (只读沙箱审查)",
        "badge": "Read-Only",
        "color": "blue",
        "description": "禁用命令执行与文件写操作，仅允许文件查看与检索"
    }
}

# 5 档真实推理强度 (Reasoning Effort / Thinking Budget)
REASONING_EFFORT_TIERS = {
    "none": {
        "name": "Off (零思考/极速直出)",
        "label": "Off",
        "description": "关闭深度推理链，以毫秒级延迟直接生成答案",
        "budget_tokens": 0,
        "api_effort": "low"
    },
    "low": {
        "name": "Low (低强度/快速推理)",
        "label": "Low",
        "description": "轻量思考 (预算 2K Tokens)，适合快速问答与简单代码",
        "budget_tokens": 2048,
        "api_effort": "low"
    },
    "medium": {
        "name": "Medium (中强度/平衡模式 - 默认)",
        "label": "Med",
        "description": "标准思考 (预算 8K Tokens)，平衡推理深度与响应速度",
        "budget_tokens": 8192,
        "api_effort": "medium"
    },
    "high": {
        "name": "High (高强度/深度推演)",
        "label": "High",
        "description": "深度推理 (预算 16K Tokens)，适合复杂代码重构与系统设计",
        "budget_tokens": 16384,
        "api_effort": "high"
    },
    "max": {
        "name": "Max (极限推理/算法攻防)",
        "label": "Max",
        "description": "极限推演 (预算 32K Tokens)，适合复杂数学证明、逆向与漏洞分析",
        "budget_tokens": 32768,
        "api_effort": "high"
    }
}


class AppConfig(BaseModel):
    version: str = "1.0.0"
    model_tier: str = "pro"
    permission_mode: str = "unrestricted"
    reasoning_effort: str = "medium"
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    master_prompt: MasterPromptConfig = Field(default_factory=MasterPromptConfig)
    providers: Dict[str, Any] = Field(default_factory=dict)
    server: ServerConfig = Field(default_factory=ServerConfig)


def _expand_env_vars(data: Any) -> Any:
    """递归替换字符串中的 ${ENV_VAR} 格式环境变量"""
    if isinstance(data, str):
        pattern = re.compile(r'\$\{([^}]+)\}')
        def replace(match):
            env_name = match.group(1)
            return os.environ.get(env_name, "")
        return pattern.sub(replace, data)
    elif isinstance(data, dict):
        return {k: _expand_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_expand_env_vars(item) for item in data]
    return data


def _load_dotenv_if_exists(base_dir: Path):
    """自动扫描并加载 .env 文件中的环境变量到 os.environ"""
    candidates = [
        Path.cwd() / ".env",
        base_dir / ".env",
        Path.home() / ".config" / "dsh" / ".env",
        Path.home() / ".env"
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            try:
                with open(c, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
            except Exception:
                pass


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """加载并解析全局配置文件"""
    base_dir = Path(__file__).resolve().parent.parent.parent
    _load_dotenv_if_exists(base_dir)

    if not config_path:
        # 默认寻找 config/config.yaml 或当前工作目录下的 config.yaml
        candidates = [
            base_dir / "config" / "config.yaml",
            Path.cwd() / "config.yaml",
            Path.home() / ".harness" / "config.yaml"
        ]
        for c in candidates:
            if c.exists():
                config_path = str(c)
                break

    if config_path and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            raw_yaml = yaml.safe_load(f) or {}
            expanded_data = _expand_env_vars(raw_yaml)
            return AppConfig(**expanded_data)

    return AppConfig()


def get_os_type() -> str:
    """获取当前宿主操作系统类型"""
    if sys.platform.startswith("win"):
        return "Windows"
    elif sys.platform.startswith("linux"):
        return "Linux"
    elif sys.platform.startswith("darwin"):
        return "macOS"
    return sys.platform

