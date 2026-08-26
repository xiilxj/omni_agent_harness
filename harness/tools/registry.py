"""
Tool Registry (工具注册中心与 Schema 自动生成)
兼容 OpenAI、Anthropic 与 DeepSeek 格式的工具管理与执行调度器
"""

import inspect
import json
from typing import Any, Callable, Dict, List, Optional
from harness.core.models import ToolDefinition


class ToolRegistry:
    """Agent 工具注册表与执行分发器"""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_schemas: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any]
    ):
        """装饰器：注册一个工具函数"""
        def decorator(func: Callable):
            self._tools[name] = func
            self._tool_schemas[name] = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            }
            return func
        return decorator

    def register_raw(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        func: Callable,
        is_async: bool = False
    ):
        """直接注册一个现成的工具函数 (用于 MCP 动态装载)"""
        self._tools[name] = func
        self._tool_schemas[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """获取兼容 OpenAI / DeepSeek 格式的 tools 列表（字典序稳定排序以最大化 Prompt Cache 命中）"""
        return sorted(self._tool_schemas.values(), key=lambda t: t["function"]["name"])

    def get_anthropic_tools(self) -> List[Dict[str, Any]]:
        """获取兼容 Anthropic Claude 格式的 tools 列表"""
        anthropic_tools = []
        for item in self._tool_schemas.values():
            func_data = item["function"]
            anthropic_tools.append({
                "name": func_data["name"],
                "description": func_data["description"],
                "input_schema": func_data["parameters"]
            })
        return anthropic_tools

    async def execute(self, name: str, arguments: Any) -> str:
        """异步执行指定名称的工具并返回字符串输出结果"""
        if name not in self._tools:
            return f"Error: Tool '{name}' is not registered."

        func = self._tools[name]
        
        # 解析参数 (若是 JSON 字符串则转换为 dict)
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments) if arguments.strip() else {}
            except Exception as e:
                return f"Error parsing arguments JSON for tool '{name}': {e}"
        elif arguments is None:
            arguments = {}

        try:
            if inspect.iscoroutinefunction(func):
                result = await func(**arguments)
            else:
                result = func(**arguments)
            return str(result)
        except TypeError as te:
            return f"Error calling tool '{name}' with invalid parameters: {te}"
        except Exception as e:
            return f"Exception occurred while executing tool '{name}': {e}"


# 全局默认单例
global_tools = ToolRegistry()
