"""
Omni Agent Harness - Telegram Bot Remote Control Bridge
提供全功能 Telegram 机器人远程控制终端，支持模型切换、厂商选择、推理强度配置、任务下发、多模态图文与文件收发及实时进度推送。
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import httpx

from harness.core.config import AppConfig, load_config
from harness.core.models import Message
from harness.core.agent import OmniAgent
from harness.core.session import global_session_manager, SessionItem, auto_generate_title
from harness.core.workspace import global_workspace_manager
from harness.providers.manager import global_provider_manager
from harness.providers.router import infer_provider_from_model
from harness.tools.registry import global_tools
from harness.tools.default_tools import register_default_tools
from harness.tools.uploader import save_upload_bytes, is_image_file

logger = logging.getLogger("OmniTelegramBot")


def escape_tg_markdown(text: str) -> str:
    """对 Telegram Markdown 特殊字符做基础兼容过滤"""
    if not text:
        return ""
    # 简单过滤或原样返回，避免格式解析失败
    return text


class TelegramBotBridge:
    """Telegram Bot 远程控制器核心桥接引擎"""

    def __init__(
        self,
        token: Optional[str] = None,
        allowed_users: Optional[List[int]] = None,
        config: Optional[AppConfig] = None,
        tools: Optional[Any] = None
    ):
        self.config = config or load_config()
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN") or self.config.telegram.bot_token
        
        # 白名单处理 (显式参数优先，其次环境变量，最后配置文件)
        if allowed_users is not None:
            self.allowed_users = allowed_users
        else:
            env_allowed = os.environ.get("TELEGRAM_ALLOWED_USERS", "")
            if env_allowed:
                parsed_users = []
                for u in env_allowed.split(","):
                    u_str = u.strip()
                    if u_str.isdigit():
                        parsed_users.append(int(u_str))
                self.allowed_users = parsed_users
            else:
                self.allowed_users = self.config.telegram.allowed_users

        self.tools = tools or register_default_tools(global_tools)
        self.session_mgr = global_session_manager
        self.workspace_mgr = global_workspace_manager
        self.provider_mgr = global_provider_manager

        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.http_client: Optional[httpx.AsyncClient] = None
        self._running = False
        self._last_update_id = 0

        # 用户交互状态存储: user_id -> state dict
        self.user_states: Dict[int, Dict[str, Any]] = {}
        self.active_agents: Dict[int, OmniAgent] = {}
        self.active_tasks: Dict[int, asyncio.Task] = {}

    def is_user_authorized(self, user_id: int) -> bool:
        """校验用户是否在白名单中（若白名单为空则允许所有人，若配置了白名单则严格校验）"""
        if not self.allowed_users:
            return True
        return user_id in self.allowed_users

    def get_user_state(self, user_id: int) -> Dict[str, Any]:
        """获取或初始化用户的独立会话与模型状态"""
        if user_id not in self.user_states:
            active_p = self.provider_mgr.get_active_provider_id() or "deepseek"
            p_info = self.provider_mgr.get_provider_info(active_p) or {}
            models = p_info.get("models", ["deepseek-chat"])
            def_model = p_info.get("default_model") or (models[0] if models else "deepseek-chat")

            self.user_states[user_id] = {
                "session_id": None,
                "provider": active_p,
                "model": def_model,
                "reasoning_effort": "medium",
                "permission_mode": "unrestricted",
                "staged_attachments": []
            }
        return self.user_states[user_id]

    async def _send_api(self, method: str, data: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """向 Telegram Bot API 发送 HTTP 请求"""
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=60.0)
        url = f"{self.base_url}/{method}"
        try:
            if files:
                res = await self.http_client.post(url, data=data, files=files)
            else:
                res = await self.http_client.post(url, json=data)
            return res.json()
        except Exception as e:
            logger.error(f"Telegram API request failed ({method}): {e}")
            return {"ok": False, "description": str(e)}

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """发送文本消息（自动处理 4096 字符分片）"""
        if len(text) > 4000:
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            last_res = {"ok": True}
            for idx, c in enumerate(chunks):
                markup = reply_markup if idx == len(chunks) - 1 else None
                payload = {
                    "chat_id": chat_id,
                    "text": c,
                    "reply_markup": markup
                }
                if parse_mode:
                    payload["parse_mode"] = parse_mode
                last_res = await self._send_api("sendMessage", payload)
            return last_res
        else:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": reply_markup
            }
            if parse_mode:
                payload["parse_mode"] = parse_mode
            res = await self._send_api("sendMessage", payload)
            if not res.get("ok") and parse_mode:
                # 若 Markdown 格式解析失败，降级为纯文本重发
                payload.pop("parse_mode", None)
                res = await self._send_api("sendMessage", payload)
            return res

    async def edit_message(
        self,
        chat_id: Union[int, str],
        message_id: int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """编辑已发送的文本消息"""
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text[:4000],
            "reply_markup": reply_markup
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        res = await self._send_api("editMessageText", payload)
        if not res.get("ok") and parse_mode:
            payload.pop("parse_mode", None)
            res = await self._send_api("editMessageText", payload)
        return res

    async def send_chat_action(self, chat_id: Union[int, str], action: str = "typing") -> None:
        """发送状态动作 (typing / upload_document 等)"""
        await self._send_api("sendChatAction", {"chat_id": chat_id, "action": action})

    async def answer_callback_query(self, query_id: str, text: Optional[str] = None, show_alert: bool = False) -> None:
        """响应内联按钮点击"""
        payload = {"callback_query_id": query_id, "show_alert": show_alert}
        if text:
            payload["text"] = text
        await self._send_api("answerCallbackQuery", payload)

    async def download_file_by_id(self, file_id: str, filename: str, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """从 Telegram 服务器下载文件并持久化归档到工作区"""
        res = await self._send_api("getFile", {"file_id": file_id})
        if not res.get("ok"):
            return None
        file_path = res.get("result", {}).get("file_path")
        if not file_path:
            return None

        download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
        try:
            if not self.http_client:
                self.http_client = httpx.AsyncClient(timeout=60.0)
            f_resp = await self.http_client.get(download_url)
            file_bytes = f_resp.content
            return save_upload_bytes(
                file_bytes=file_bytes,
                filename=filename,
                workspace_dir=self.workspace_mgr.cwd,
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"Download file from Telegram failed: {e}")
            return None

    # ==================== 指令与交互处理器 ====================

    async def handle_start(self, chat_id: int, user_id: int) -> None:
        """处理 /start 与 /help 指令"""
        state = self.get_user_state(user_id)
        msg = (
            "🤖 *Omni Agent Harness Pro · Telegram 远程控制终端*\n\n"
            f"📍 *当前工作区*: `{self.workspace_mgr.cwd}`\n"
            f"🏢 *当前厂商*: `{state['provider']}`\n"
            f"🧠 *当前模型*: `{state['model']}`\n"
            f"⚡ *推理强度*: `{state['reasoning_effort']}`\n"
            f"🛡️ *权限模式*: `{state['permission_mode']}`\n\n"
            "📋 *支持的远程控制指令*:\n"
            "• `/model` - 自选可用模型列表 (Inline 按钮)\n"
            "• `/provider` - 切换上游厂商 (DeepSeek / Gemini / OpenAI)\n"
            "• `/effort` - 调节思考强度 (Off / Low / Med / High / Max)\n"
            "• `/auth` - 调节执行权限模式 (Full / Ask / Read)\n"
            "• `/balance` - 查询 DeepSeek 官方账户可用余额\n"
            "• `/status` - 查看当前连接与环境状态\n"
            "• `/abort` - 紧急中止正在执行的任务\n"
            "• `/clear` - 清空历史开启新任务\n"
            "• `/help` - 查看此帮助面板\n\n"
            "💡 *使用方法*: 直接发送文字或图片/文档，Agent 将全自动规划与调用工具执行！"
        )
        markup = {
            "inline_keyboard": [
                [
                    {"text": "🧠 选择模型", "callback_data": "menu_model"},
                    {"text": "🏢 切换厂商", "callback_data": "menu_provider"}
                ],
                [
                    {"text": "⚡ 推理强度", "callback_data": "menu_effort"},
                    {"text": "🛡️ 权限模式", "callback_data": "menu_auth"}
                ],
                [
                    {"text": "💰 账户余额", "callback_data": "cmd_balance"},
                    {"text": "🧹 清空会话", "callback_data": "cmd_clear"}
                ]
            ]
        }
        await self.send_message(chat_id, msg, reply_markup=markup, parse_mode="Markdown")

    async def handle_model_menu(self, chat_id: int, user_id: int, message_id: Optional[int] = None) -> None:
        """弹出模型自选菜单 (Inline Keyboard)"""
        state = self.get_user_state(user_id)
        current_p = state["provider"]
        p_info = self.provider_mgr.get_provider_info(current_p) or {}
        models = p_info.get("models", [])
        if not models:
            models = ["deepseek-chat", "deepseek-reasoner"]

        keyboard = []
        for m in models:
            is_cur = (m == state["model"])
            btn_text = f"✅ {m}" if is_cur else m
            keyboard.append([{"text": btn_text, "callback_data": f"set_model:{m}"}])

        keyboard.append([{"text": "🔙 返回主菜单", "callback_data": "menu_main"}])

        text = f"🧠 *选择当前厂商 (`{current_p}`) 的可用模型*:\n当前选中: `{state['model']}`"
        markup = {"inline_keyboard": keyboard}

        if message_id:
            await self.edit_message(chat_id, message_id, text, reply_markup=markup, parse_mode="Markdown")
        else:
            await self.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    async def handle_provider_menu(self, chat_id: int, user_id: int, message_id: Optional[int] = None) -> None:
        """弹出厂商切换菜单"""
        state = self.get_user_state(user_id)
        providers = self.provider_mgr.get_all_providers()
        keyboard = []
        for p in providers:
            p_id = p["id"]
            p_name = p.get("name", p_id)
            is_cur = (p_id == state["provider"])
            btn_text = f"✅ {p_name}" if is_cur else p_name
            keyboard.append([{"text": btn_text, "callback_data": f"set_provider:{p_id}"}])

        keyboard.append([{"text": "🔙 返回主菜单", "callback_data": "menu_main"}])
        text = f"🏢 *选择上游供应商*:\n当前厂商: `{state['provider']}`"
        markup = {"inline_keyboard": keyboard}

        if message_id:
            await self.edit_message(chat_id, message_id, text, reply_markup=markup, parse_mode="Markdown")
        else:
            await self.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    async def handle_effort_menu(self, chat_id: int, user_id: int, message_id: Optional[int] = None) -> None:
        """弹出推理强度切换菜单"""
        state = self.get_user_state(user_id)
        efforts = [
            ("none", "Off (零思考/极速直出)"),
            ("low", "Low (轻量思考 2K)"),
            ("medium", "Med (标准平衡 8K - 推荐)"),
            ("high", "High (深度推演 16K)"),
            ("max", "Max (极限推理 32K)")
        ]
        keyboard = []
        for val, label in efforts:
            is_cur = (val == state["reasoning_effort"])
            btn_text = f"✅ {label}" if is_cur else label
            keyboard.append([{"text": btn_text, "callback_data": f"set_effort:{val}"}])

        keyboard.append([{"text": "🔙 返回主菜单", "callback_data": "menu_main"}])
        text = f"⚡ *调节 Reasoning Effort (推理思考预算)*:\n当前档位: `{state['reasoning_effort']}`"
        markup = {"inline_keyboard": keyboard}

        if message_id:
            await self.edit_message(chat_id, message_id, text, reply_markup=markup, parse_mode="Markdown")
        else:
            await self.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    async def handle_auth_menu(self, chat_id: int, user_id: int, message_id: Optional[int] = None) -> None:
        """弹出权限模式切换菜单"""
        state = self.get_user_state(user_id)
        modes = [
            ("unrestricted", "Full (完全自主执行)"),
            ("ask_confirmation", "Ask (关键破坏操作需确认)"),
            ("read_only", "Read (仅只读分析)")
        ]
        keyboard = []
        for val, label in modes:
            is_cur = (val == state["permission_mode"])
            btn_text = f"✅ {label}" if is_cur else label
            keyboard.append([{"text": btn_text, "callback_data": f"set_auth:{val}"}])

        keyboard.append([{"text": "🔙 返回主菜单", "callback_data": "menu_main"}])
        text = f"🛡️ *调节工具执行权限模式*:\n当前模式: `{state['permission_mode']}`"
        markup = {"inline_keyboard": keyboard}

        if message_id:
            await self.edit_message(chat_id, message_id, text, reply_markup=markup, parse_mode="Markdown")
        else:
            await self.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    async def handle_balance_query(self, chat_id: int, user_id: int) -> None:
        """查询余额并回复"""
        p_info = self.provider_mgr.get_provider_info("deepseek") or {}
        api_key = p_info.get("api_key") or os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            await self.send_message(chat_id, "⚠️ DeepSeek API Key 未配置，无法查询官方余额。")
            return

        try:
            if not self.http_client:
                self.http_client = httpx.AsyncClient(timeout=30.0)
            res = await self.http_client.get(
                "https://api.deepseek.com/user/balance",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            data = res.json()
            if data.get("is_available"):
                balances = data.get("balance_infos", [])
                cny_b = next((b.get("total_balance") for b in balances if b.get("currency") == "CNY"), "0.00")
                await self.send_message(chat_id, f"💰 *DeepSeek 官方账户可用余额*: `¥{cny_b}`", parse_mode="Markdown")
            else:
                await self.send_message(chat_id, f"⚠️ 查询失败: {data}")
        except Exception as e:
            await self.send_message(chat_id, f"⚠️ 查询余额网络异常: {e}")

    async def handle_abort(self, chat_id: int, user_id: int) -> None:
        """急停打断当前任务"""
        if user_id in self.active_agents:
            self.active_agents[user_id].request_abort()
            await self.send_message(chat_id, "🛑 已下发紧急急停指令，正在中止当前任务与工具调用...")
        else:
            await self.send_message(chat_id, "ℹ️ 当前没有正在运行的后台任务。")

    async def handle_clear(self, chat_id: int, user_id: int) -> None:
        """重置用户会话"""
        state = self.get_user_state(user_id)
        state["session_id"] = None
        state["staged_attachments"] = []
        await self.send_message(chat_id, "🧹 会话上下文与暂存附件已清空，可直接发送新指令开始！")

    # ==================== 任务分发与流式执行 ====================

    async def execute_task_for_user(self, chat_id: int, user_id: int, prompt_text: str) -> None:
        """为指定 Telegram 用户运行完整 Agent 任务闭环并流式推送进度"""
        state = self.get_user_state(user_id)

        # 检查是否已在运行中
        if user_id in self.active_tasks and not self.active_tasks[user_id].done():
            # 穿插纠偏
            if user_id in self.active_agents:
                self.active_agents[user_id].interject_steer(prompt_text)
                await self.send_message(chat_id, f"⚡ 穿插追问已注入运行中的 Agent: `{prompt_text}`", parse_mode="Markdown")
                return

        # 创建或加载会话
        session_id = state.get("session_id")
        session = self.session_mgr.get_session(session_id) if session_id else None
        if not session:
            session = SessionItem(
                title=auto_generate_title(prompt_text),
                workspace=str(self.workspace_mgr.cwd),
                provider=state["provider"],
                model=state["model"]
            )
            state["session_id"] = session.id
        else:
            session.provider = state["provider"]
            session.model = state["model"]

        # 发送初始进度消息卡片
        status_msg = await self.send_message(
            chat_id,
            f"🚀 *Agent 任务启动*\n🧠 模型: `{state['model']}`\n📝 任务: `{prompt_text[:100]}...`\n⏳ 正在思考规划中...",
            parse_mode="Markdown"
        )
        status_msg_id = status_msg.get("result", {}).get("message_id")

        agent = OmniAgent(
            config=self.config,
            tools=self.tools,
            permission_mode=state["permission_mode"],
            reasoning_effort=state["reasoning_effort"]
        )

        # 挂载历史
        from harness.prompt.refusal_detector import sanitize_messages_history
        sanitized_history = sanitize_messages_history(session.messages)
        for m in sanitized_history:
            if m.get("role") in ["user", "assistant", "tool"]:
                agent.messages.append(Message(**m))

        self.active_agents[user_id] = agent
        attachments = list(state.get("staged_attachments", []))
        state["staged_attachments"] = []  # 清空暂存

        last_edit_time = 0.0
        current_thought_preview = ""
        current_tool_preview = ""

        async def step_callback(ev: Dict[str, Any]):
            nonlocal last_edit_time, current_thought_preview, current_tool_preview
            ev_type = ev.get("type")
            now = time.time()

            if ev_type == "thought_delta":
                current_thought_preview = (ev.get("accumulated") or "")[:250]
            elif ev_type == "tool_executing":
                t_name = ev.get("tool_name")
                current_tool_preview = f"🛠️ 正在调用工具: `{t_name}`"
            elif ev_type == "tool_result":
                current_tool_preview = f"✅ 工具执行完毕: `{ev.get('tool_id')}`"
            elif ev_type == "thought_signature_injected":
                current_tool_preview = "⚡ 已自动注入「继续」指令推进执行..."

            # 控制编辑频率（至少间隔 1.5 秒更新一次 Telegram 消息）
            if status_msg_id and (now - last_edit_time > 1.5 or ev_type in ("tool_executing", "task_completed")):
                last_edit_time = now
                live_text = (
                    f"🚀 *Agent 执行中...*\n"
                    f"🧠 模型: `{state['model']}`\n"
                    f"{current_tool_preview}\n\n"
                    f"💭 *思考链*: \n`{current_thought_preview}...`"
                )
                try:
                    await self.edit_message(chat_id, status_msg_id, live_text, parse_mode="Markdown")
                except Exception:
                    pass

        async def run_coro():
            try:
                target_model = state["model"]
                target_provider = infer_provider_from_model(target_model, state["provider"])
                
                res = await agent.run_task(
                    task_prompt=prompt_text,
                    provider_name=target_provider,
                    model_name=target_model,
                    reasoning_effort=state["reasoning_effort"],
                    attachments=attachments,
                    on_step_callback=step_callback
                )

                # 持久化保存会话
                session.messages = [m.model_dump() for m in agent.messages]
                self.session_mgr.save_session(session)

                # 发送最终交付答复
                final_header = f"🏁 *Agent 任务完成* (`{target_model}`)\n\n"
                await self.send_message(chat_id, final_header + res, parse_mode="Markdown")

            except Exception as e:
                logger.error(f"Telegram task failed: {e}")
                await self.send_message(chat_id, f"❌ *执行失败*: `{e}`", parse_mode="Markdown")
            finally:
                self.active_agents.pop(user_id, None)
                self.active_tasks.pop(user_id, None)

        task = asyncio.create_task(run_coro())
        self.active_tasks[user_id] = task

    # ==================== Update 分发中心 ====================

    async def handle_update(self, update: Dict[str, Any]) -> None:
        """处理单条 Telegram Update 事件"""
        # 1. 响应 Inline Keyboard 按钮点击 (Callback Query)
        if "callback_query" in update:
            cb = update["callback_query"]
            cb_id = cb["id"]
            user_id = cb["from"]["id"]
            data = cb.get("data", "")
            msg = cb.get("message", {})
            chat_id = msg.get("chat", {}).get("id")
            msg_id = msg.get("message_id")

            if not self.is_user_authorized(user_id):
                await self.answer_callback_query(cb_id, "⛔ 权限不足：您未在允许的用户白名单中。", show_alert=True)
                return

            state = self.get_user_state(user_id)

            if data == "menu_main":
                await self.handle_start(chat_id, user_id)
                await self.answer_callback_query(cb_id)
            elif data == "menu_model":
                await self.handle_model_menu(chat_id, user_id, msg_id)
                await self.answer_callback_query(cb_id)
            elif data == "menu_provider":
                await self.handle_provider_menu(chat_id, user_id, msg_id)
                await self.answer_callback_query(cb_id)
            elif data == "menu_effort":
                await self.handle_effort_menu(chat_id, user_id, msg_id)
                await self.answer_callback_query(cb_id)
            elif data == "menu_auth":
                await self.handle_auth_menu(chat_id, user_id, msg_id)
                await self.answer_callback_query(cb_id)
            elif data == "cmd_balance":
                await self.answer_callback_query(cb_id)
                await self.handle_balance_query(chat_id, user_id)
            elif data == "cmd_clear":
                await self.answer_callback_query(cb_id, "已重置会话")
                await self.handle_clear(chat_id, user_id)
            elif data.startswith("set_model:"):
                chosen_m = data.split(":", 1)[1]
                state["model"] = chosen_m
                # 自动推导厂商
                state["provider"] = infer_provider_from_model(chosen_m, state["provider"])
                await self.answer_callback_query(cb_id, f"已切换模型为: {chosen_m}")
                await self.handle_model_menu(chat_id, user_id, msg_id)
            elif data.startswith("set_provider:"):
                chosen_p = data.split(":", 1)[1]
                state["provider"] = chosen_p
                p_info = self.provider_mgr.get_provider_info(chosen_p) or {}
                models = p_info.get("models", [])
                if models:
                    state["model"] = p_info.get("default_model") or models[0]
                await self.answer_callback_query(cb_id, f"已切换厂商为: {chosen_p}")
                await self.handle_provider_menu(chat_id, user_id, msg_id)
            elif data.startswith("set_effort:"):
                chosen_e = data.split(":", 1)[1]
                state["reasoning_effort"] = chosen_e
                await self.answer_callback_query(cb_id, f"推理强度已设置为: {chosen_e}")
                await self.handle_effort_menu(chat_id, user_id, msg_id)
            elif data.startswith("set_auth:"):
                chosen_a = data.split(":", 1)[1]
                state["permission_mode"] = chosen_a
                await self.answer_callback_query(cb_id, f"权限模式已设置为: {chosen_a}")
                await self.handle_auth_menu(chat_id, user_id, msg_id)
            return

        # 2. 处理普通消息 (Message)
        if "message" in update:
            msg = update["message"]
            chat_id = msg["chat"]["id"]
            user = msg.get("from", {})
            user_id = user.get("id")

            if not user_id or not self.is_user_authorized(user_id):
                await self.send_message(chat_id, f"⛔ *未授权访问*: 您的 User ID (`{user_id}`) 未在系统白名单中。")
                return

            text = msg.get("text", "").strip()

            # 指令路由
            if text in ("/start", "/help"):
                await self.handle_start(chat_id, user_id)
                return
            elif text == "/model":
                await self.handle_model_menu(chat_id, user_id)
                return
            elif text == "/provider":
                await self.handle_provider_menu(chat_id, user_id)
                return
            elif text == "/effort":
                await self.handle_effort_menu(chat_id, user_id)
                return
            elif text == "/auth":
                await self.handle_auth_menu(chat_id, user_id)
                return
            elif text == "/balance":
                await self.handle_balance_query(chat_id, user_id)
                return
            elif text == "/abort":
                await self.handle_abort(chat_id, user_id)
                return
            elif text == "/clear":
                await self.handle_clear(chat_id, user_id)
                return
            elif text == "/status":
                state = self.get_user_state(user_id)
                status_text = (
                    f"📊 *Omni Agent Harness 状态报告*\n"
                    f"🏢 供应商: `{state['provider']}`\n"
                    f"🧠 模型: `{state['model']}`\n"
                    f"⚡ 推理强度: `{state['reasoning_effort']}`\n"
                    f"🛡️ 权限: `{state['permission_mode']}`\n"
                    f"📂 工作区: `{self.workspace_mgr.cwd}`\n"
                    f"📁 暂存附件数: `{len(state.get('staged_attachments', []))}`"
                )
                await self.send_message(chat_id, status_text, parse_mode="Markdown")
                return

            # 处理附件：照片 (Photo)
            if "photo" in msg:
                photos = msg["photo"]
                best_photo = photos[-1]  # 取最大分辨率
                file_id = best_photo["file_id"]
                fname = f"tg_photo_{int(time.time())}.jpg"
                state = self.get_user_state(user_id)
                f_meta = await self.download_file_by_id(file_id, fname, session_id=state.get("session_id"))
                if f_meta:
                    state["staged_attachments"].append(f_meta)
                    caption = msg.get("caption", "").strip() or "请帮我分析这张图片"
                    await self.send_message(chat_id, f"📷 *图片已暂存并挂载*: `{f_meta['name']}` ({round(f_meta['size']/1024, 1)} KB)\n正在启动 Vision 视觉多模态分析...", parse_mode="Markdown")
                    await self.execute_task_for_user(chat_id, user_id, caption)
                else:
                    await self.send_message(chat_id, "⚠️ 下载图片失败，请重试。")
                return

            # 处理附件：文档 (Document)
            if "document" in msg:
                doc = msg["document"]
                file_id = doc["file_id"]
                orig_name = doc.get("file_name", f"tg_doc_{int(time.time())}.dat")
                state = self.get_user_state(user_id)
                f_meta = await self.download_file_by_id(file_id, orig_name, session_id=state.get("session_id"))
                if f_meta:
                    state["staged_attachments"].append(f_meta)
                    caption = msg.get("caption", "").strip() or f"请分析挂载的文件 {orig_name}"
                    await self.send_message(chat_id, f"📎 *文件已归档至工作区*: `{f_meta['name']}` ({round(f_meta['size']/1024, 1)} KB)\n正在注入 Agent 上下文进行处理...", parse_mode="Markdown")
                    await self.execute_task_for_user(chat_id, user_id, caption)
                else:
                    await self.send_message(chat_id, "⚠️ 下载文档失败，请重试。")
                return

            # 普通文本任务下发
            if text:
                await self.execute_task_for_user(chat_id, user_id, text)

    # ==================== Polling 主循环 ====================

    async def start_polling(self, poll_interval: float = 1.0) -> None:
        """启动 Telegram Long-Polling 异步监听循环"""
        if not self.token:
            logger.warning("Telegram Bot Token 未配置，跳过 Telegram 服务启动。")
            return

        self._running = True
        logger.info(f"Telegram Bot 正在启动... Base API: {self.base_url}")
        
        # 校验 Token 有效性
        me_res = await self._send_api("getMe")
        if not me_res.get("ok"):
            logger.error(f"Telegram getMe 校验失败: {me_res}")
            return
        bot_user = me_res.get("result", {})
        print(f"✓ Telegram Bot 已成功连接: @{bot_user.get('username')} ({bot_user.get('first_name')})")

        # 向已配置白名单的管理员发送上线就绪广播通知
        if self.allowed_users:
            for admin_uid in self.allowed_users[:3]:
                try:
                    await self.send_message(
                        admin_uid,
                        f"🚀 *Omni Agent Harness Pro 已成功在主机上线启动！*\n\n"
                        f"📍 *当前工作区*: `{self.workspace_mgr.cwd}`\n"
                        f"🏢 *激活厂商*: `{self.provider_mgr.get_active_provider_id() or 'deepseek'}`\n"
                        f"🤖 Telegram 远程控制已就绪，发送 `/help` 或 `/model` 开始远程操控！",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning(f"发送上线通知到用户 {admin_uid} 失败: {e}")

        while self._running:
            try:
                updates_res = await self._send_api(
                    "getUpdates",
                    {"offset": self._last_update_id + 1, "timeout": 25}
                )
                if updates_res.get("ok"):
                    updates = updates_res.get("result", [])
                    for u in updates:
                        u_id = u["update_id"]
                        self._last_update_id = max(self._last_update_id, u_id)
                        asyncio.create_task(self.handle_update(u))
                await asyncio.sleep(poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Telegram Polling loop error: {e}")
                await asyncio.sleep(3.0)

    async def stop(self) -> None:
        """优雅停止 Bot"""
        self._running = False
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
