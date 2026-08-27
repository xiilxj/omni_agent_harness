"""
Omni Agent ReAct Engine (智能体核心状态机与思考循环)
继承 Codex & DeepSeek Harness 架构，实现多步工具调度、反思闭环与 100% 绝对系统指令注入。
"""

import re
import json
import time
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
from harness.core.config import AppConfig, load_config
from harness.core.models import LLMResponse, Message, ToolCall, ToolFunction, UsageStats
from harness.core.context_pruner import ContextPruner
from harness.core.subagent import SubagentManager
from harness.prompt.master_injector import MasterPromptInjector
from harness.providers.router import ProviderRouter
from harness.tools.registry import ToolRegistry, global_tools
from harness.tools.default_tools import register_default_tools

from harness.core.slash_commands import parse_and_transform_slash_command

logger = logging.getLogger("OmniAgent")


class OmniAgent:
    """具备 100% 绝对系统提示词注入与全套工具闭环的智能体核心"""

    def __init__(
        self,
        config: AppConfig,
        tools: Optional[ToolRegistry] = None,
        custom_master_prompt: Optional[str] = None,
        custom_master_suffix: Optional[str] = None,
        permission_mode: Optional[str] = None,
        reasoning_effort: Optional[str] = None
    ):
        self.config = config
        self.tools = tools or global_tools
        self.permission_mode = permission_mode or config.permission_mode or "unrestricted"
        self.reasoning_effort = reasoning_effort or getattr(config, "reasoning_effort", "medium")
        self.custom_master_prompt = custom_master_prompt
        self.custom_master_suffix = custom_master_suffix
        self.router = ProviderRouter(config)
        self.injector = MasterPromptInjector()
        self.pruner = ContextPruner()
        self.subagent_manager = SubagentManager(parent_config=config, parent_tools=self.tools)
        self.messages: List[Message] = []
        self.total_usage = UsageStats()
        self.current_provider_name: Optional[str] = None
        self.current_model_name: Optional[str] = None
        self.current_todos: List[Dict[str, Any]] = []
        self.ask_user_resolver: Optional[Callable[[str, Dict[str, Any]], Any]] = None
        self._abort_requested: bool = False
        self._steer_queue: List[str] = []
        self.current_turn_refusal_notices: List[str] = []

    def request_abort(self):
        """用户触发紧急制动打断 (Emergency Stop / Abort)"""
        self._abort_requested = True

    def steer_message(self, text: str):
        """用户在工作中实时穿插追问、补充约束与纠偏 (Mid-flight Steer)"""
        self._steer_queue.append(text)

    def reset_conversation(self):
        """重置会话上下文历史"""
        self.messages = []
        self.total_usage = UsageStats()
        self.current_todos = []
        self._abort_requested = False
        self._steer_queue = []
        self.current_turn_refusal_notices = []

    async def step(
        self,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None
    ) -> LLMResponse:
        """执行单步 LLM 推理并应用 100% 绝对 Master 提示词注入"""
        from harness.providers.router import infer_provider_from_model
        m_name = model_name or self.config.providers.get("default_model", "deepseek-chat")
        p_name = provider_name or infer_provider_from_model(m_name, self.config.providers.get("default_provider", "deepseek"))
        # 再次核验：若用户选取的模型属于其他厂商（如选了 Gemini 模型但 provider 传了 deepseek），自动智能纠正
        inferred = infer_provider_from_model(m_name, p_name)
        if inferred != p_name and ("gemini" in m_name or "claude" in m_name or "gpt" in m_name or "o1" in m_name or "o3" in m_name):
            p_name = inferred

        provider = self.router.get_provider(p_name)

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
            self.total_usage.current_context_tokens = response.usage.prompt_tokens + response.usage.completion_tokens

        return response

    def extract_pseudo_tool_calls(self, text: str) -> Tuple[str, List[ToolCall]]:
        """
        智能伪工具调用提取与文本分离器：
        支持 [调用工具 write_file 参数: {...}]、[调用_api:write_file{...}]、<tool_call> 及弱 JSON 语法的智能提取与执行分离。
        """
        if not text or not text.strip():
            return text, []

        extracted_tool_calls: List[ToolCall] = []
        cleaned_text = text

        def parse_lenient_args(raw: str) -> str:
            raw_str = raw.strip()
            # 1. 尝试标准 JSON 解析
            try:
                parsed = json.loads(raw_str)
                return json.dumps(parsed, ensure_ascii=False)
            except Exception:
                pass

            # 2. 尝试换行符转义修补
            try:
                fixed = re.sub(r'(?<!\\)\n', r'\\n', raw_str)
                parsed = json.loads(fixed)
                return json.dumps(parsed, ensure_ascii=False)
            except Exception:
                pass

            # 3. 弱键值对提取（针对如 {content:...,file_path:count_chars.py,overwrite:true}）
            content_inside = raw_str
            if content_inside.startswith("{") and content_inside.endswith("}"):
                content_inside = content_inside[1:-1].strip()

            keys = ["file_path", "filepath", "path", "content", "command", "cwd", "overwrite", "query", "search_path", "url", "tool_name", "action"]
            found_keys = []
            for k in keys:
                m_k = re.search(r"(?:^|[,，\s])" + re.escape(k) + r"\s*[:：]", content_inside)
                if m_k:
                    found_keys.append((m_k.start(), k, m_k.end()))

            if found_keys:
                found_keys.sort()
                res_dict = {}
                for idx, (start_pos, k, val_start) in enumerate(found_keys):
                    if idx + 1 < len(found_keys):
                        val_end = found_keys[idx + 1][0]
                        val = content_inside[val_start:val_end].strip()
                    else:
                        val = content_inside[val_start:].strip()
                    val = val.rstrip(",，").strip()
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    elif val.lower() == "true":
                        val = True
                    elif val.lower() == "false":
                        val = False
                    res_dict[k] = val
                return json.dumps(res_dict, ensure_ascii=False)

            return raw_str

        # 1. 匹配 [调用工具 tool_name 参数: {...}] 或 [调用_api:tool_name{...}]
        pattern_bracket = re.compile(
            r"\[\s*(?:调用_api|调用api|调用工具|api|tool_call|tool|action)\s*[:：]?\s*([a-zA-Z0-9_\-]+)\s*(?:参数|args|parameters)?\s*[:：]?\s*(\{[\s\S]*?\})\s*\]",
            re.IGNORECASE
        )

        for i, match in enumerate(pattern_bracket.finditer(text)):
            full_match = match.group(0)
            tool_name = match.group(1).strip()
            raw_args = match.group(2).strip()
            args_str = parse_lenient_args(raw_args)

            extracted_tool_calls.append(
                ToolCall(
                    id=f"call_extracted_{i}_{int(time.time()*1000)}",
                    type="function",
                    function=ToolFunction(name=tool_name, arguments=args_str)
                )
            )
            cleaned_text = cleaned_text.replace(full_match, "").strip()

        # 2. 匹配 <tool_call>...</tool_call> 标签
        pattern_xml = re.compile(r"<tool_call>([\s\S]*?)</tool_call>", re.IGNORECASE)
        for i, match in enumerate(pattern_xml.finditer(cleaned_text)):
            full_match = match.group(0)
            xml_content = match.group(1).strip()
            try:
                data = json.loads(xml_content)
                name = data.get("name") or data.get("tool") or data.get("function")
                args = data.get("arguments") or data.get("parameters") or data.get("args") or {}
                if name:
                    args_str = json.dumps(args, ensure_ascii=False) if isinstance(args, dict) else str(args)
                    extracted_tool_calls.append(
                        ToolCall(
                            id=f"call_xml_{i}_{int(time.time()*1000)}",
                            type="function",
                            function=ToolFunction(name=name, arguments=args_str)
                        )
                    )
                    cleaned_text = cleaned_text.replace(full_match, "").strip()
            except Exception:
                pass

        # 3. 清理伪工具伴随的末尾冗余模板语句
        cleaned_text = re.sub(r"(?:^|\n)\s*[-—]{3,}\s*(?:\n|$)", "\n", cleaned_text)
        cleaned_text = re.sub(r"执行状态\s*[:：]\s*当前步骤已完成[，,。]?\s*(?:请确认或下发下一指令[。]?)?", "", cleaned_text).strip()

        return cleaned_text, extracted_tool_calls

    async def step_stream(
        self,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        on_chunk_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
    ) -> LLMResponse:
        """执行流式 LLM 推理并实时逐字推送思考链 (thought_delta) 与回答 (answer_delta)"""
        from harness.providers.router import infer_provider_from_model
        m_name = model_name or self.config.providers.get("default_model", "deepseek-chat")
        p_name = provider_name or infer_provider_from_model(m_name, self.config.providers.get("default_provider", "deepseek"))
        # 再次核验智能纠正
        inferred = infer_provider_from_model(m_name, p_name)
        if inferred != p_name and ("gemini" in m_name or "claude" in m_name or "gpt" in m_name or "o1" in m_name or "o3" in m_name):
            p_name = inferred

        provider = self.router.get_provider(p_name)

        # 0. DSH 级长会话上下文剪枝与 Token 优化
        pruned_messages, saved_tokens = self.pruner.prune_and_compact(self.messages)

        from harness.prompt.refusal_detector import detect_refusal_intent, get_exemption_booster

        max_refusal_retries = 3
        current_master_override = self.custom_master_prompt
        assembled_tool_calls = None
        finish_reason = "stop"
        thought_accumulator = ""
        content_accumulator = ""

        for attempt in range(1, max_refusal_retries + 1):
            # 1. 核心关键：通过 Injector 确保 MASTER_SYSTEM_PROMPT.md 100% 绝对置顶与双端物理锚定
            injected_messages = self.injector.inject(
                messages=pruned_messages,
                workspace=self.config.workspace.default_cwd,
                custom_master_prompt=current_master_override
            )

            tool_schemas = self.tools.get_openai_tools()

            extra_params = {}
            effort = reasoning_effort or self.reasoning_effort
            if effort:
                extra_params["reasoning_effort"] = effort

            stream_gen = provider.stream_chat(
                messages=injected_messages,
                model=m_name,
                tools=tool_schemas if tool_schemas else None,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_params=extra_params
            )

            thought_accumulator = ""
            content_accumulator = ""
            tool_calls_builder: Dict[int, Dict[str, Any]] = {}
            finish_reason = "stop"
            refusal_intercepted = False
            refusal_reason = ""

            async for chunk in stream_gen:
                if chunk.get("type") == "done":
                    break

                # 1. 毫秒级实时流式吐出思考链 Token 并实时进行拒绝语义审计
                r_delta = chunk.get("reasoning_content")
                if r_delta:
                    thought_accumulator += r_delta

                    # 在思维链前 350 字内探测是否存在拒绝意图（毫秒级熔断）
                    if len(thought_accumulator) <= 350 and attempt < max_refusal_retries:
                        is_refusal, reason = detect_refusal_intent(thought_accumulator, max_chars_to_scan=350)
                        if is_refusal:
                            refusal_intercepted = True
                            refusal_reason = reason or "CoT Refusal Signal"
                            break

                    if on_chunk_callback:
                        await on_chunk_callback({
                            "type": "thought_delta",
                            "delta": r_delta,
                            "accumulated": thought_accumulator
                        })

                # 2. 毫秒级实时流式吐出回答文本 Token 并实时进行前段拒绝审计
                c_delta = chunk.get("content")
                if c_delta:
                    content_accumulator += c_delta

                    # 在回答文本前 200 字内探测是否存在拒绝意图（毫秒级熔断）
                    if len(content_accumulator) <= 200 and attempt < max_refusal_retries:
                        is_refusal, reason = detect_refusal_intent(content_accumulator, max_chars_to_scan=200)
                        if is_refusal:
                            refusal_intercepted = True
                            refusal_reason = reason or "Answer Refusal Signal"
                            break

                    if on_chunk_callback:
                        await on_chunk_callback({
                            "type": "answer_delta",
                            "delta": c_delta,
                            "accumulated": content_accumulator
                        })

                # 3. 实时收集工具调用碎片 (Tool Call Fragments)
                tcs = chunk.get("tool_calls")
                if tcs:
                    for tc in tcs:
                        idx = tc.get("index", 0)
                        if idx not in tool_calls_builder:
                            tool_calls_builder[idx] = {
                                "id": tc.get("id") or f"call_{idx}",
                                "name": tc.get("function", {}).get("name", ""),
                                "arguments": ""
                            }
                        if tc.get("id"):
                            tool_calls_builder[idx]["id"] = tc["id"]
                        if tc.get("function", {}).get("name"):
                            tool_calls_builder[idx]["name"] = tc["function"]["name"]
                        if tc.get("function", {}).get("arguments"):
                            tool_calls_builder[idx]["arguments"] += tc["function"]["arguments"]

                if chunk.get("finish_reason"):
                    finish_reason = chunk["finish_reason"]

                if chunk.get("usage"):
                    u = chunk["usage"]
                    p_tok = u.get("prompt_tokens", 0)
                    c_tok = u.get("completion_tokens", 0)
                    self.total_usage.prompt_tokens += p_tok
                    self.total_usage.completion_tokens += c_tok
                    self.total_usage.total_tokens += u.get("total_tokens", (p_tok + c_tok))
                    self.total_usage.prompt_cache_hit_tokens += u.get("prompt_cache_hit_tokens", 0)
                    self.total_usage.prompt_cache_miss_tokens += u.get("prompt_cache_miss_tokens", 0)
                    self.total_usage.current_context_tokens = p_tok + c_tok

            # 4. 判定是否触发拒绝熔断（核心铁律：若大模型已输出工具调用，代表正在采取实际行动，100% 绝对豁免熔断）
            if tool_calls_builder:
                refusal_intercepted = False
            elif not refusal_intercepted and attempt < max_refusal_retries:
                # 只有在纯文本回答（0 工具调用）时，才在流式结束时校验是否为真实拒绝
                is_ref, ref_r = detect_refusal_intent(content_accumulator, max_chars_to_scan=350)
                if is_ref:
                    refusal_intercepted = True
                    refusal_reason = ref_r or "Answer Refusal Signal"

            if refusal_intercepted:
                booster = get_exemption_booster(attempt)
                current_master_override = (self.custom_master_prompt or "") + booster
                notice_msg = f"⚡ 毫秒级熔断模型拒绝倾向 ({refusal_reason})，已叠加第 {attempt} 阶强制豁免指令重发..."
                self.current_turn_refusal_notices.append(notice_msg)
                if on_chunk_callback:
                    await on_chunk_callback({
                        "type": "refusal_intercepted",
                        "attempt": attempt,
                        "max_retries": max_refusal_retries,
                        "reason": refusal_reason,
                        "message": notice_msg
                    })
                # 重置累加器并重发
                thought_accumulator = ""
                content_accumulator = ""
                tool_calls_builder.clear()
                continue

            # 未触发拒绝或包含有效工具调用，正常结束重试循环
            break

        # 整理构建完整的 ToolCalls 列表
        assembled_tool_calls = None
        if tool_calls_builder:
            assembled_tool_calls = []
            for idx in sorted(tool_calls_builder.keys()):
                item = tool_calls_builder[idx]
                assembled_tool_calls.append(
                    ToolCall(
                        id=item["id"],
                        type="function",
                        function=ToolFunction(
                            name=item["name"],
                            arguments=item["arguments"]
                        )
                    )
                )

        # 若流式中未直接下发 usage 结构，根据字符数进行高精度保底估算
        if self.total_usage.total_tokens == 0:
            prompt_chars = sum(len(str(m.content or "")) for m in injected_messages)
            comp_chars = len(content_accumulator) + len(thought_accumulator)
            p_tok = max(1, prompt_chars // 3)
            c_tok = max(1, comp_chars // 3)
            self.total_usage.prompt_tokens += p_tok
            self.total_usage.completion_tokens += c_tok
            self.total_usage.total_tokens += (p_tok + c_tok)
            self.total_usage.current_context_tokens = p_tok + c_tok

        return LLMResponse(
            content=content_accumulator,
            reasoning_content=thought_accumulator,
            tool_calls=assembled_tool_calls,
            finish_reason=finish_reason,
            usage=self.total_usage
        )

    async def run_task(
        self,
        task_prompt: str,
        max_steps: int = 30,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        on_step_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
    ) -> str:
        """
        运行完整 Agent 任务闭环 (ReAct 思考循环)
        接收用户指令 -> 斜杠指令转换 -> 实时流式思考决策 -> 调用工具 -> 穿插纠偏 -> 迭代修正 -> 最终交付
        """
        # 1. 解析并转换斜杠快捷指令 (如 /goal, /grill-me, /schedule, /browser, /learn 等)
        transformed_prompt, cmd_name, cmd_meta = parse_and_transform_slash_command(task_prompt)
        self.messages.append(Message(role="user", content=transformed_prompt, attachments=attachments or []))

        step_count = 0
        final_answer = ""
        effort = reasoning_effort or self.reasoning_effort

        while step_count < max_steps:
            # 2. 检查急停状态 (Emergency Stop / Abort)
            if self._abort_requested:
                abort_msg = "🛑 任务已由用户执行急停打断 (Emergency Stopped by User)。"
                if on_step_callback:
                    await on_step_callback({
                        "type": "aborted",
                        "message": abort_msg
                    })
                return abort_msg

            # 3. 检查并注入工作中穿插的追问与纠偏消息 (Mid-flight Steer Messages)
            while self._steer_queue:
                interjected = self._steer_queue.pop(0)
                steer_text, _, _ = parse_and_transform_slash_command(interjected)
                self.messages.append(Message(role="user", content=f"[⚡ 穿插追问/纠偏指令]: {steer_text}"))
                if on_step_callback:
                    await on_step_callback({
                        "type": "steer_injected",
                        "content": interjected
                    })

            step_count += 1
            if on_step_callback:
                await on_step_callback({
                    "type": "step_start",
                    "step": step_count
                })

            # 执行单步实时流式推理（实时推送 thought_delta 与 answer_delta）
            try:
                response = await self.step_stream(
                    provider_name=provider_name,
                    model_name=model_name,
                    reasoning_effort=effort,
                    on_chunk_callback=on_step_callback
                )
            except Exception as e:
                err_str = str(e)
                # 针对 Google Gemini thought_signature 校验异常自动直接注入「继续」指令推进
                if "thought_signature" in err_str:
                    if on_step_callback:
                        await on_step_callback({
                            "type": "thought_signature_injected",
                            "notice": "⚡ 检测到上游 thought_signature 校验异常，已自动直接注入「继续」指令自愈推进...",
                            "injected_prompt": "继续"
                        })
                    
                    # 净化历史中引发签名校验的 tool_calls 结构为标准文本，彻底解除 Google Gemini 结构死锁
                    for m in self.messages:
                        if m.role == "assistant" and m.tool_calls:
                            call_descs = [f"[Executed `{tc.function.name}` with parameters: {tc.function.arguments}]" for tc in m.tool_calls]
                            m.content = (m.content or "") + "\n" + "\n".join(call_descs)
                            m.tool_calls = None
                        elif m.role == "tool":
                            m.role = "user"
                            m.content = f"[Tool `{m.name or 'tool'}` Execution Output]:\n{m.content}"
                    
                    # 直接注入「继续」两个字
                    self.messages.append(Message(role="user", content="继续"))
                    continue

                err_msg = f"LLM Call Failed at step {step_count}: {e}"
                if on_step_callback:
                    await on_step_callback({"type": "error", "error": err_msg})
                self.messages.append(
                    Message(
                        role="assistant",
                        content=f"❌ 调用失败: {err_msg}"
                    )
                )
                return err_msg

            # 再次检查急停打断
            if self._abort_requested:
                abort_msg = "🛑 任务已由用户执行急停打断 (Emergency Stopped by User)。"
                if on_step_callback:
                    await on_step_callback({
                        "type": "aborted",
                        "message": abort_msg
                    })
                return abort_msg

            # 记录回复内容
            assistant_content = response.content or ""
            tool_calls = response.tool_calls

            # 保存 Assistant 消息到会话历史并持久化挂载熔断提醒记录
            turn_refusals = list(self.current_turn_refusal_notices)
            self.current_turn_refusal_notices.clear()

            self.messages.append(
                Message(
                    role="assistant",
                    content=assistant_content,
                    tool_calls=tool_calls,
                    refusal_notices=turn_refusals
                )
            )

            # 智能提取思考过程（全面支持 DeepSeek 原生 reasoning_content、<think> 深度推理链与 ReAct 前置思考）
            import re
            thought_text = getattr(response, "reasoning_content", None) or ""
            clean_answer = assistant_content

            if not thought_text:
                think_match = re.search(r'<think>([\s\S]*?)</think>', assistant_content, flags=re.IGNORECASE)
                if think_match:
                    thought_text = think_match.group(1).strip()
                    clean_answer = re.sub(r'<think>[\s\S]*?</think>', '', assistant_content, flags=re.IGNORECASE).strip()
                elif tool_calls and assistant_content:
                    thought_text = assistant_content

            # 如果存在思考内容，在会话历史中完整包装记录，确保历史重开时不丢失思考链
            if thought_text and "<think>" not in assistant_content:
                self.messages[-1].content = f"<think>\n{thought_text}\n</think>\n\n{clean_answer}".strip()

            # 4. 若上游未返回结构化 tool_calls，自动进行「伪工具调用智能提取与文本分离」
            # 解决大模型将工具调用混入正文（如 [调用工具 write_file 参数: {...}]）导致的格式错乱与执行失效
            if not tool_calls and assistant_content:
                cleaned_text, extracted_tools = self.extract_pseudo_tool_calls(assistant_content)
                if extracted_tools:
                    tool_calls = extracted_tools
                    assistant_content = cleaned_text
                    clean_answer = cleaned_text
                    self.messages[-1].content = cleaned_text
                    self.messages[-1].tool_calls = extracted_tools
                    if on_step_callback:
                        await on_step_callback({
                            "type": "thought_signature_injected",
                            "notice": f"🛠️ 智能检测并分离 {len(extracted_tools)} 项嵌入式工具调用，已转入工具通道真实执行并净化正文文本！"
                        })

            # 若分离后仍无工具调用，作为最终回答交付
            if not tool_calls:
                final_answer = clean_answer or assistant_content
                
                # 融入最高回答词 (Master Response Suffix)
                final_answer = self.injector.apply_master_suffix(
                    assistant_content=final_answer,
                    custom_suffix=self.custom_master_suffix
                )
                if self.messages and self.messages[-1].role == "assistant":
                    if thought_text and "<think>" not in self.messages[-1].content:
                        self.messages[-1].content = f"<think>\n{thought_text}\n</think>\n\n{final_answer}".strip()
                    else:
                        self.messages[-1].content = self.injector.apply_master_suffix(
                            assistant_content=self.messages[-1].content or "",
                            custom_suffix=self.custom_master_suffix
                        )

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
                if self._abort_requested:
                    abort_msg = "🛑 工具调用已由用户急停中止 (Tool execution aborted by user)。"
                    if on_step_callback:
                        await on_step_callback({
                            "type": "aborted",
                            "message": abort_msg
                        })
                    return abort_msg

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

                # 3. 多智能体集群协同派发 (invoke_subagent)
                elif t_name == "invoke_subagent":
                    p_args = json.loads(t_args) if isinstance(t_args, str) else (t_args or {})
                    sub_role = p_args.get("role", "general")
                    sub_prompt = p_args.get("prompt", "")
                    max_s = p_args.get("max_steps", 15)
                    observation = await self.subagent_manager.invoke(
                        role=sub_role,
                        task_prompt=sub_prompt,
                        max_steps=max_s,
                        on_parent_callback=on_step_callback
                    )

                # 4. 权限控制检查 (DSH Permission Enforcer)
                elif self.permission_mode == "read_only" and t_name in ("run_command", "write_file", "replace_file_content"):
                    observation = f"Permission Denied: Agent is running in 'read_only' mode. Destructive tool '{t_name}' execution is blocked by safety policy."
                else:
                    observation = await self.tools.execute(t_name, t_args)

                # 5. 生成统一红绿 Diff 补丁 (针对 replace_file_content)
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
