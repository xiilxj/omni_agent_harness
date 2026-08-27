"""
Harness Core Models
定义通用的 Canonical Intermediate Representation (IR) 数据模型
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ToolFunction(BaseModel):
    """工具函数定义与调用参数模型"""
    name: str
    arguments: Union[str, Dict[str, Any]]


class ToolCall(BaseModel):
    """大模型返回的工具调用结构"""
    id: str
    type: str = "function"
    function: ToolFunction


class Message(BaseModel):
    """统一消息对象结构（兼容 OpenAI / Anthropic / DeepSeek）"""
    role: str = Field(..., description="角色: system, user, assistant, tool")
    content: Optional[Union[str, List[Dict[str, Any]]]] = ""
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    refusal_notices: Optional[List[str]] = Field(default_factory=list, description="本轮被熔断拦截的拒绝事件记录")


class ToolParamSchema(BaseModel):
    """工具入参 JSON Schema"""
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class ToolDefinition(BaseModel):
    """提供给大模型的标准工具定义"""
    type: str = "function"
    function: Dict[str, Any]


class UsageStats(BaseModel):
    """Token 消耗与精确遥测统计（支持 DeepSeek 缓存命中率与上下文窗口计量）"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_cache_hit_tokens: int = 0
    prompt_cache_miss_tokens: int = 0
    current_context_tokens: int = 0


class LLMResponse(BaseModel):
    """统一大模型响应结构"""
    content: Optional[str] = None
    reasoning_content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = "stop"
    usage: Optional[UsageStats] = None
    raw_response: Optional[Dict[str, Any]] = None


class AgentStepResult(BaseModel):
    """Agent ReAct 单步执行结果"""
    thought: Optional[str] = None
    action_tool: Optional[str] = None
    action_args: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    is_terminal: bool = False
    output: Optional[str] = None
