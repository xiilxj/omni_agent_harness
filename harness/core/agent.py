"""
Omni Agent ReAct Engine (智能体核心状态机与思考循环)
继承 Codex & DeepSeek Harness 架构，实现多步工具调度、反思闭环与 100% 绝对系统指令注入。
"""

import json
import logging
from typing import Any, Callable, Dict, List, Optional
from harness.core.config import AppConfig, load_config
from harness.core.models import LLMResponse, Message, ToolCall, UsageStats
from harness.prompt.master_injector import MasterPromptInjector
from harness.providers.router import ProviderRouter
from harness.tools.registry import ToolRegistry, global_tools
from harness.tools.default_tools import register_default_tools

logger = logging.getLogger("OmniAgent")


class OmniAgent:
    """具备 100% 绝对系统提示词注入与全套工具闭环的智能体核心"""

    def __init__(
        self,
        config: AppConfig,
        tools: Optional[ToolRegistry] = None,
        custom_master_prompt: Optional[str] = None,
        permission_mode: Optional[str] = None,
        reasoning_effort: Optional[str] = None
    ):
        self.config = config
        self.tools = tools or global_tools
        self.permission_mode = permission_mode or config.permission_mode or "unrestricted"
        self.reasoning_effort = reasoning_effort or getattr(config, "reasoning_effort", "medium")
        self.custom_master_prompt = custom_master_prompt
        self.router = ProviderRouter(config)
        self.injector = MasterPromptInjector()
        self.messages: List[Message] = []
        self.total_usage = UsageStats()
        self.current_provider_name: Optional[str] = None
        self.current_model_name: Optional[str] = None
        self.current_todos: List[Dict[str, Any]] = []
        self.ask_user_resolver: Optional[Callable[[str, Dict[str, Any]], Any]] = None

    def reset_conversation(self):
        """重置会话上下文历史"""
        self.messages = []
        self.total_usage = UsageStats()
        self.current_todos = []

    async def step(
        self,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None
    ) -> LLMResponse:
        """执行单步 LLM 推理并应用 100% 绝对 Master 提示词注入"""
        p_name = provider_name or self.config.providers.get("default_provider", "deepseek")
        provider = self.router.get_provider(p_name)
        m_name = model_name or self.config.providers.get("default_model", "deepseek-chat")

        # 1. 核心关键：通过 Injector 确保 MASTER_SYSTEM_PROMPT.md 100% 绝对置顶与三层锚定
        injected_messages = self.injector.inject(
            messages=self.messages,
            workspace=self.config.workspace.default_cwd,
            custom_master_prompt=self.custom_master_prompt
        )

        # 2. 获取兼容工具定义列表
        tool_schemas = self.tools.get_openai_tools()

        extra_params = {}
        effort = reasoning_effort or self.reasoning_effort
        if effort:
            extra_params["reasoning_effort"] = effort

        # 3. 发起请求
        response = await provider.chat(
            messages=injected_messages,
            model=m_name,
            tools=tool_schemas if tool_schemas else None,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_params=extra_params
        )

        # 4. 累计 Token 消耗与真实缓存命中
        if response.usage:
            self.total_usage.prompt_tokens += response.usage.prompt_tokens
            self.total_usage.completion_tokens += response.usage.completion_tokens
            self.total_usage.total_tokens += response.usage.total_tokens
            self.total_usage.prompt_cache_hit_tokens += response.usage.prompt_cache_hit_tokens
            self.total_usage.prompt_cache_miss_tokens += response.usage.prompt_cache_miss_tokens

        return response

    async def run_task(
        self,
        task_prompt: str,
        max_steps: int = 30,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        on_step_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
    ) -> str:
        """
        运行完整 Agent 任务闭环 (ReAct 思考循环)
        接收用户指令 -> 思考决策 -> 调用工具 -> 观察输出 -> 迭代修正 -> 最终交付
        """
        # 添加用户输入
        self.messages.append(Message(role="user", content=task_prompt))

        step_count = 0
        final_answer = ""
        effort = reasoning_effort or self.reasoning_effort

        while step_count < max_steps:
            step_count += 1
            if on_step_callback:
                await on_step_callback({
                    "type": "step_start",
                    "step": step_count
                })

            # 执行单步推理
            try:
                response = await self.step(
                    provider_name=provider_name,
                    model_name=model_name,
                    reasoning_effort=effort
                )
            except Exception as e:
                err_msg = f"LLM Call Failed at step {step_count}: {e}"
                if on_step_callback:
                    await on_step_callback({"type": "error", "error": err_msg})
                return err_msg

            # 记录回复内容
            assistant_content = response.content or ""
            tool_calls = response.tool_calls

            # 保存 Assistant 消息到会话历史
            self.messages.append(
                Message(
                    role="assistant",
                    content=assistant_content,
                    tool_calls=tool_calls
                )
            )

            # 智能提取思考过程（支持 ReAct 决策思考与 <think>...</think> 深度推理链）
            import re
            thought_text = ""
            clean_answer = assistant_content

            think_match = re.search(r'<think>([\s\S]*?)</think>', assistant_content, flags=re.IGNORECASE)
            if think_match:
                thought_text = think_match.group(1).strip()
                clean_answer = re.sub(r'<think>[\s\S]*?</think>', '', assistant_content, flags=re.IGNORECASE).strip()
            elif tool_calls and assistant_content:
                thought_text = assistant_content

            # 如果存在思考内容，推送给前端展示为正在思考折叠盒
            if thought_text and on_step_callback:
                await on_step_callback({
                    "type": "assistant_thought",
                    "content": thought_text
                })

            # 若无工具调用，说明 Agent 任务已彻底完成，此内容即为最终结论
            if not tool_calls:
                final_answer = clean_answer or assistant_content
                if on_step_callback:
                    await on_step_callback({
                        "type": "task_completed",
                        "final_answer": final_answer,
                        "total_steps": step_count,
                        "usage": self.total_usage.model_dump()
                    })
                break

            # 依次执行工具调用
            for tc in tool_calls:
                t_name = tc.function.name
                t_args = tc.function.arguments

                if on_step_callback:
                    await on_step_callback({
                        "type": "tool_executing",
                        "tool_name": t_name,
                        "tool_args": t_args,
                        "tool_id": tc.id
                    })

                # 1. 交互式向用户提问 (ask_user 阻塞等待)
                if t_name == "ask_user":
                    parsed_args = json.loads(t_args) if isinstance(t_args, str) else (t_args or {})
                    if on_step_callback:
                        await on_step_callback({
                            "type": "ask_user",
                            "tool_id": tc.id,
                            "question": parsed_args.get("question", ""),
                            "options": parsed_args.get("options", []),
                            "is_multi_select": parsed_args.get("is_multi_select", False)
                        })
                    if self.ask_user_resolver:
                        observation = await self.ask_user_resolver(tc.id, parsed_args)
                    else:
                        observation = await self.tools.execute(t_name, t_args)

                # 2. 动态待办清单更新 (update_todo_list 进度事件)
                elif t_name == "update_todo_list":
                    parsed_args = json.loads(t_args) if isinstance(t_args, str) else (t_args or {})
                    self.current_todos = parsed_args.get("todos", [])
                    observation = await self.tools.execute(t_name, t_args)
                    if on_step_callback:
                        await on_step_callback({
                            "type": "todo_update",
                            "todos": self.current_todos
                        })

                # 3. 权限控制检查 (DSH Permission Enforcer)
                elif self.permission_mode == "read_only" and t_name in ("run_command", "write_file", "replace_file_content"):
                    observation = f"Permission Denied: Agent is running in 'read_only' mode. Destructive tool '{t_name}' execution is blocked by safety policy."
                else:
                    observation = await self.tools.execute(t_name, t_args)

                # 4. 生成统一红绿 Diff 补丁 (针对 replace_file_content)
                diff_text = None
                if t_name == "replace_file_content":
                    try:
                        import difflib
                        p_args = json.loads(t_args) if isinstance(t_args, str) else (t_args or {})
                        old_lines = p_args.get("old_content", "").splitlines(keepends=True)
                        new_lines = p_args.get("new_content", "").splitlines(keepends=True)
                        f_name = p_args.get("file_path", "modified_file")
                        diff_lines = list(difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{f_name}", tofile=f"b/{f_name}"))
                        diff_text = "".join(diff_lines)
                    except Exception:
                        diff_text = None

                if on_step_callback:
                    await on_step_callback({
                        "type": "tool_result",
                        "tool_name": t_name,
                        "tool_id": tc.id,
                        "observation": observation,
                        "diff": diff_text
                    })

                # 将工具执行结果装载入历史上下文
                self.messages.append(
                    Message(
                        role="tool",
                        name=t_name,
                        tool_call_id=tc.id,
                        content=observation
                    )
                )

        if step_count >= max_steps and not final_answer:
            final_answer = f"Task reached maximum allowed steps ({max_steps}) without final conclusion."

        return final_answer
