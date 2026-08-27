"""
Billing & Token Cost Calculation Engine (DSH 对齐计费核心)
支持按模型费率精确计算输入未命中、缓存命中、输出 Token 费用及会话累积成本。
"""

from typing import Any, Dict

# 官方标准费率 (单位: 元/百万 Tokens, CNY / 1M tokens)
MODEL_PRICING_RMB_PER_M = {
    "gemini": {"input_miss": 0.0, "input_hit": 0.0, "output": 0.0, "currency": "¥", "is_free": True, "note": "Google 官方免费/独立配额"},
    "gemma": {"input_miss": 0.0, "input_hit": 0.0, "output": 0.0, "currency": "¥", "is_free": True, "note": "Google 官方开源免费配额"},
    "deepseek-chat": {"input_miss": 1.0, "input_hit": 0.1, "output": 2.0, "currency": "¥"},
    "deepseek-v3": {"input_miss": 1.0, "input_hit": 0.1, "output": 2.0, "currency": "¥"},
    "deepseek-v4-pro": {"input_miss": 1.0, "input_hit": 0.1, "output": 2.0, "currency": "¥"},
    "deepseek-v4-flash": {"input_miss": 0.5, "input_hit": 0.05, "output": 1.0, "currency": "¥"},
    "deepseek-reasoner": {"input_miss": 4.0, "input_hit": 1.0, "output": 16.0, "currency": "¥"},
    "deepseek-r1": {"input_miss": 4.0, "input_hit": 1.0, "output": 16.0, "currency": "¥"},
    "deepseek-v4-flash-vision-exp": {"input_miss": 1.0, "input_hit": 0.1, "output": 2.0, "currency": "¥"},
    "gpt-4o": {"input_miss": 18.0, "input_hit": 9.0, "output": 72.0, "currency": "¥"},
    "gpt-4o-mini": {"input_miss": 1.1, "input_hit": 0.55, "output": 4.4, "currency": "¥"},
    "claude-3-5-sonnet": {"input_miss": 21.0, "input_hit": 2.1, "output": 105.0, "currency": "¥"},
    "claude-3-7-sonnet": {"input_miss": 21.0, "input_hit": 2.1, "output": 105.0, "currency": "¥"},
    "default": {"input_miss": 1.0, "input_hit": 0.1, "output": 2.0, "currency": "¥"},
}


def calculate_token_cost(
    model_name: str,
    prompt_tokens: int,
    prompt_cache_hit_tokens: int,
    completion_tokens: int
) -> Dict[str, Any]:
    """计算单次推理的精确费用明细"""
    m_lower = (model_name or "").lower()
    pricing = MODEL_PRICING_RMB_PER_M.get("default")
    for k, v in MODEL_PRICING_RMB_PER_M.items():
        if k in m_lower:
            pricing = v
            break

    hit_tokens = max(0, min(prompt_cache_hit_tokens or 0, prompt_tokens or 0))
    miss_tokens = max(0, (prompt_tokens or 0) - hit_tokens)

    cost_input_miss = (miss_tokens / 1_000_000.0) * pricing["input_miss"]
    cost_input_hit = (hit_tokens / 1_000_000.0) * pricing["input_hit"]
    cost_output = ((completion_tokens or 0) / 1_000_000.0) * pricing["output"]
    total_cost = cost_input_miss + cost_input_hit + cost_output

    return {
        "model": model_name,
        "pricing": pricing,
        "prompt_tokens": prompt_tokens,
        "prompt_cache_hit_tokens": hit_tokens,
        "prompt_cache_miss_tokens": miss_tokens,
        "completion_tokens": completion_tokens,
        "cost_input_miss": round(cost_input_miss, 6),
        "cost_input_hit": round(cost_input_hit, 6),
        "cost_output": round(cost_output, 6),
        "turn_cost": round(total_cost, 6),
        "currency": pricing.get("currency", "¥"),
        "formatted_cost": f"{pricing.get('currency', '¥')}{total_cost:.5f}"
    }
