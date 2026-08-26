"""
Harness Web UI Backend Application (FastAPI)
提供最高指令实时控制台、多会话持久化管理、工作区文件树、动态模型探测、Telemetry 仪表盘与 Agent 流式交互 API
"""

import asyncio
import json
import os
import time
import httpx
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from harness.core.config import AppConfig, load_config, get_os_type, MODEL_TIERS, PERMISSION_MODES, REASONING_EFFORT_TIERS
from harness.core.models import Message, UsageStats
from harness.core.agent import OmniAgent
from harness.core.session import SessionManager, SessionItem, TelemetryData, auto_generate_title, global_session_manager
from harness.core.workspace import WorkspaceManager, global_workspace_manager
from harness.prompt.master_injector import MasterPromptInjector
from harness.tools.registry import global_tools
from harness.tools.default_tools import register_default_tools


def create_app(config_path: Optional[str] = None) -> FastAPI:
    """创建并配置 FastAPI 应用实例"""
    config = load_config(config_path)
    tools = register_default_tools(global_tools)
    injector = MasterPromptInjector(config)
    session_mgr = global_session_manager
    workspace_mgr = global_workspace_manager

    # 默认包含全部最新 DeepSeek 模型
    if "deepseek" in config.providers and isinstance(config.providers["deepseek"], dict):
        current_models = config.providers["deepseek"].get("models", [])
        standard_v4_models = [
            "deepseek-v4-pro",
            "deepseek-v4-flash",
            "deepseek-chat",
            "deepseek-reasoner",
            "deepseek-v4-flash-vision-exp"
        ]
        merged = list(dict.fromkeys(standard_v4_models + current_models))
        config.providers["deepseek"]["models"] = merged

    app = FastAPI(
        title="Omni Agent Harness",
        version="1.0.0",
        description="Omni Agent Harness - 工业级智能体底座与最高层级系统指令控制台"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    templates_dir = Path(__file__).resolve().parent / "templates"

    @app.get("/", response_class=HTMLResponse)
    async def index_page():
        """渲染主控制台页面"""
        html_file = templates_dir / "index.html"
        if not html_file.exists():
            return HTMLResponse("<h1>Omni Agent Harness</h1><p>index.html not found</p>")
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content)

    # ==================== 会话管理 API ====================

    @app.get("/api/sessions")
    async def list_sessions():
        """获取所有历史会话列表"""
        return {"sessions": session_mgr.list_sessions()}

    class CreateSessionRequest(BaseModel):
        title: Optional[str] = "New Task Session"
        workspace: Optional[str] = None
        provider: Optional[str] = "deepseek"
        model: Optional[str] = "deepseek-chat"

    @app.post("/api/sessions")
    async def create_session(req: CreateSessionRequest):
        """创建全新会话"""
        session = SessionItem(
            title=req.title or "New Task Session",
            workspace=req.workspace or str(workspace_mgr.cwd),
            provider=req.provider or "deepseek",
            model=req.model or "deepseek-chat"
        )
        session_mgr.save_session(session)
        return {"status": "success", "session": session.model_dump()}

    @app.get("/api/sessions/{session_id}")
    async def get_session_detail(session_id: str):
        """获取特定会话的全部历史数据与遥测状态"""
        session = session_mgr.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"session": session.model_dump()}

    @app.delete("/api/sessions/{session_id}")
    async def delete_session(session_id: str):
        """删除指定会话"""
        success = session_mgr.delete_session(session_id)
        return {"status": "success" if success else "failed"}

    @app.post("/api/sessions/{session_id}/archive")
    async def toggle_session_archive(session_id: str):
        """切换会话的归档状态"""
        is_archived = session_mgr.toggle_archive(session_id)
        if is_archived is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "success", "is_archived": is_archived}

    # ==================== 工作区与文件管理 API ====================

    @app.get("/api/workspace/tree")
    async def get_workspace_tree():
        """获取当前工作区目录树"""
        return {"tree": workspace_mgr.list_tree(), "cwd": str(workspace_mgr.cwd)}

    class WorkspaceOpRequest(BaseModel):
        path: str
        content: Optional[str] = ""

    @app.post("/api/workspace/mkdir")
    async def create_directory(req: WorkspaceOpRequest):
        """在工作区创建新目录"""
        try:
            created = workspace_mgr.create_directory(req.path)
            return {"status": "success", "path": created}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/workspace/touch")
    async def create_file(req: WorkspaceOpRequest):
        """在工作区创建新文件"""
        try:
            created = workspace_mgr.create_file(req.path, req.content or "")
            return {"status": "success", "path": created}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/workspace/set-cwd")
    async def set_workspace_cwd(req: WorkspaceOpRequest):
        """动态切换工作区路径"""
        try:
            new_cwd = workspace_mgr.set_cwd(req.path)
            return {"status": "success", "cwd": str(new_cwd)}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    class RenameSessionRequest(BaseModel):
        title: str

    @app.post("/api/sessions/{session_id}/rename")
    async def rename_session(session_id: str, req: RenameSessionRequest):
        """用户自主修改会话标题"""
        success = session_mgr.rename_session(session_id, req.title)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "success", "title": req.title.strip()}

    # ==================== Master Prompt 物理注入与预设切换 API ====================

    from harness.prompt.presets import PresetManager
    preset_mgr = PresetManager()

    @app.get("/api/master-prompt/presets")
    async def list_prompt_presets():
        """获取所有系统提示词预设（内置 + 用户自定义）"""
        return {"presets": preset_mgr.list_presets()}

    class SavePresetRequest(BaseModel):
        name: Optional[str] = ""
        content: str
        description: Optional[str] = ""
        preset_id: Optional[str] = None

    @app.post("/api/master-prompt/presets")
    async def save_custom_preset(req: SavePresetRequest):
        """保存或覆盖自定义系统提示词预设"""
        item = preset_mgr.save_custom_preset(
            name=req.name or "",
            content=req.content,
            description=req.description or "",
            preset_id=req.preset_id
        )
        return {"status": "success", "preset": item}

    @app.delete("/api/master-prompt/presets/{preset_id}")
    async def delete_custom_preset(preset_id: str):
        """删除用户自定义预设"""
        success = preset_mgr.delete_custom_preset(preset_id)
        return {"status": "success" if success else "failed"}

    @app.get("/api/master-prompt")
    async def get_master_prompt():
        """获取当前 MASTER_SYSTEM_PROMPT.md 物理文件内容与路径"""
        prompt_path = injector.resolve_master_prompt_path()
        content = injector.read_master_prompt(force_reload=True)
        rendered = injector.render_prompt(raw_prompt=content, workspace=str(workspace_mgr.cwd))
        cleaned = injector.clean_zero_token_waste(rendered)
        return {
            "path": str(prompt_path),
            "content": content,
            "rendered": rendered,
            "cleaned": cleaned,
            "char_count": len(content)
        }

    class UpdatePromptRequest(BaseModel):
        content: str

    @app.post("/api/master-prompt")
    async def update_master_prompt(req: UpdatePromptRequest):
        """保存并更新 MASTER_SYSTEM_PROMPT.md 物理文件，实现全局同源热生效"""
        prompt_path = injector.resolve_master_prompt_path()
        try:
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(req.content)
            
            # 同步全局 ~/.config/dsh/ 目录
            global_path = Path.home() / ".config" / "dsh" / "MASTER_SYSTEM_PROMPT.md"
            if prompt_path != global_path:
                try:
                    global_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(global_path, "w", encoding="utf-8") as f:
                        f.write(req.content)
                except Exception:
                    pass

            injector.read_master_prompt(force_reload=True)
            return {"status": "success", "message": "Master System Prompt updated and synchronized successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write prompt file: {e}")

    # ==================== 系统与模型提供商 API ====================

    @app.get("/api/system-info")
    async def get_system_info():
        """获取系统状态、提供商及模型列表"""
        providers_meta = {}
        for p_name, p_data in config.providers.items():
            if isinstance(p_data, dict):
                raw_key = os.environ.get(f"{p_name.upper()}_API_KEY") or p_data.get("api_key", "")
                masked_key = (raw_key[:7] + "..." + raw_key[-4:]) if len(raw_key) > 12 else ("*" * len(raw_key))
                providers_meta[p_name] = {
                    "type": p_data.get("type", "openai_compatible"),
                    "base_url": p_data.get("base_url", ""),
                    "models": p_data.get("models", []),
                    "has_key": bool(raw_key and raw_key != "EMPTY"),
                    "masked_key": masked_key
                }

        return {
            "name": "Omni Agent Harness",
            "os_type": get_os_type(),
            "cwd": str(workspace_mgr.cwd),
            "providers": providers_meta,
            "default_provider": config.providers.get("default_provider", "deepseek"),
            "default_model": config.providers.get("default_model", "deepseek-chat"),
            "model_tier": config.model_tier,
            "permission_mode": config.permission_mode,
            "reasoning_effort": getattr(config, "reasoning_effort", "medium"),
            "model_tiers": MODEL_TIERS,
            "permission_modes": PERMISSION_MODES,
            "reasoning_effort_tiers": REASONING_EFFORT_TIERS,
            "tools_count": len(tools.get_openai_tools())
        }

    class UpdateModesRequest(BaseModel):
        model_tier: Optional[str] = None
        permission_mode: Optional[str] = None
        reasoning_effort: Optional[str] = None

    @app.get("/api/modes")
    async def get_modes():
        """获取当前模型档位、权限模式与推理强度"""
        return {
            "model_tier": config.model_tier,
            "permission_mode": config.permission_mode,
            "reasoning_effort": getattr(config, "reasoning_effort", "medium"),
            "model_tiers": MODEL_TIERS,
            "permission_modes": PERMISSION_MODES,
            "reasoning_effort_tiers": REASONING_EFFORT_TIERS
        }

    @app.post("/api/modes")
    async def set_modes(req: UpdateModesRequest):
        """动态切换模型档位、权限模式或推理强度"""
        if req.model_tier and req.model_tier in MODEL_TIERS:
            config.model_tier = req.model_tier
            # 自动联动默认模型
            tier_info = MODEL_TIERS[req.model_tier]
            if "model" in tier_info:
                config.providers["default_model"] = tier_info["model"]
        if req.permission_mode and req.permission_mode in PERMISSION_MODES:
            config.permission_mode = req.permission_mode
        if req.reasoning_effort and req.reasoning_effort in REASONING_EFFORT_TIERS:
            config.reasoning_effort = req.reasoning_effort
        return {
            "status": "success",
            "model_tier": config.model_tier,
            "permission_mode": config.permission_mode,
            "reasoning_effort": getattr(config, "reasoning_effort", "medium")
        }

    @app.get("/api/user/balance")
    async def get_user_balance():
        """从上游官方 API 获取用户账户实际余额"""
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            return {"is_available": False, "total_balance": "0.00", "currency": "CNY", "message": "No API Key"}

        url = "https://api.deepseek.com/user/balance"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    balance_infos = data.get("balance_infos", [])
                    if balance_infos:
                        b = balance_infos[0]
                        return {
                            "is_available": data.get("is_available", True),
                            "currency": b.get("currency", "CNY"),
                            "total_balance": b.get("total_balance", "0.00"),
                            "granted_balance": b.get("granted_balance", "0.00"),
                            "topped_up_balance": b.get("topped_up_balance", "0.00")
                        }
                    return {"is_available": True, "currency": "CNY", "total_balance": "0.00"}
                else:
                    return {"is_available": False, "error": f"HTTP {resp.status_code}", "total_balance": "--"}
        except Exception as e:
            return {"is_available": False, "error": str(e), "total_balance": "--"}

    class TestAndFetchModelsRequest(BaseModel):
        provider_name: str = "deepseek"
        base_url: str
        api_key: str

    @app.post("/api/providers/test-and-fetch-models")
    async def test_and_fetch_models(req: TestAndFetchModelsRequest):
        """向上游 API 发起真实连通性测试并动态获取可用模型列表"""
        base_url = req.base_url.rstrip("/")
        api_key = req.api_key.strip()
        if not api_key:
            api_key = os.environ.get(f"{req.provider_name.upper()}_API_KEY", "")

        if not api_key:
            raise HTTPException(status_code=400, detail="API Key is required to test and fetch models.")

        url = f"{base_url}/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=headers)
                latency = int((time.time() - start_time) * 1000)

                if resp.status_code == 200:
                    data = resp.json()
                    model_list = []
                    if "data" in data and isinstance(data["data"], list):
                        for item in data["data"]:
                            if "id" in item:
                                model_list.append(item["id"])
                    
                    if not model_list:
                        if "deepseek" in req.provider_name.lower():
                            model_list = [
                                "deepseek-v4-pro",
                                "deepseek-v4-flash",
                                "deepseek-chat",
                                "deepseek-reasoner",
                                "deepseek-v4-flash-vision-exp"
                            ]
                        else:
                            model_list = ["default-model"]

                    # 更新到运行配置
                    if req.provider_name.lower() in config.providers:
                        config.providers[req.provider_name.lower()]["models"] = model_list

                    return {
                        "status": "success",
                        "latency_ms": latency,
                        "models": sorted(model_list),
                        "message": f"Successfully connected! Found {len(model_list)} models."
                    }
                else:
                    raise HTTPException(
                        status_code=resp.status_code,
                        detail=f"API connection failed ({resp.status_code}): {resp.text}"
                    )
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Network error connecting to {url}: {e}")

    class UpdateProviderConfigRequest(BaseModel):
        provider_name: str
        base_url: str
        api_key: Optional[str] = None
        models: Optional[List[str]] = None
        default_model: Optional[str] = None

    @app.post("/api/config/update-provider")
    async def update_provider_config(req: UpdateProviderConfigRequest):
        """更新 Provider 配置并持久化到私有环境变量"""
        p_name = req.provider_name.lower()
        if req.api_key and req.api_key.strip():
            env_var = f"{p_name.upper()}_API_KEY"
            os.environ[env_var] = req.api_key.strip()
            env_file = Path(__file__).resolve().parent.parent.parent / ".env"
            try:
                lines = []
                found = False
                if env_file.exists():
                    with open(env_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                
                new_lines = []
                for line in lines:
                    if line.startswith(f"{env_var}="):
                        new_lines.append(f"{env_var}={req.api_key.strip()}\n")
                        found = True
                    else:
                        new_lines.append(line)
                if not found:
                    new_lines.append(f"{env_var}={req.api_key.strip()}\n")

                with open(env_file, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            except Exception as e:
                print(f"Warning writing .env: {e}")

        if p_name in config.providers and isinstance(config.providers[p_name], dict):
            config.providers[p_name]["base_url"] = req.base_url
            if req.models:
                config.providers[p_name]["models"] = req.models
        if req.default_model:
            config.providers["default_model"] = req.default_model

        return {"status": "success", "message": f"Provider '{p_name}' configuration updated."}

    @app.get("/api/tools")
    async def get_tools():
        """获取所有可用 Agent 工具定义列表"""
        return {"tools": tools.get_openai_tools()}

    # ==================== Agent 流式交互与 Telemetry 收集 API ====================

    class RunTaskRequest(BaseModel):
        session_id: Optional[str] = None
        prompt: str
        provider: Optional[str] = None
        model: Optional[str] = None
        permission_mode: Optional[str] = None
        reasoning_effort: Optional[str] = None
        custom_master_prompt: Optional[str] = None

    @app.post("/api/agent/stream")
    async def run_agent_stream(req: RunTaskRequest):
        """以细粒度 SSE 格式执行任务，实时推送思考链、工具调用与 Telemetry 遥测数据"""
        # 加载或创建会话
        session = None
        if req.session_id:
            session = session_mgr.get_session(req.session_id)
        if not session:
            session = SessionItem(
                title=auto_generate_title(req.prompt),
                workspace=str(workspace_mgr.cwd),
                provider=req.provider or "deepseek",
                model=req.model or "deepseek-chat"
            )
        elif session.title in ("New Task Session", "Untitled Session") or len(session.messages) <= 1:
            session.title = auto_generate_title(req.prompt)

        agent = OmniAgent(
            config=config,
            tools=tools,
            custom_master_prompt=req.custom_master_prompt,
            permission_mode=req.permission_mode or config.permission_mode,
            reasoning_effort=req.reasoning_effort or getattr(config, "reasoning_effort", "medium")
        )

        # 挂载历史消息以继续对话
        for m in session.messages:
            if m.get("role") in ["user", "assistant", "tool"]:
                agent.messages.append(Message(**m))

        # 绑定 ask_user 异步交互等待 Future 解析器
        active_questions: Dict[str, asyncio.Future] = getattr(app.state, "active_questions", {})
        app.state.active_questions = active_questions

        async def ask_user_resolver(tool_id: str, parsed_args: Dict[str, Any]):
            fut = asyncio.get_running_loop().create_future()
            active_questions[tool_id] = fut
            try:
                # 阻塞等待用户在 Web 界面选择提交（默认 5 分钟超时）
                res = await asyncio.wait_for(fut, timeout=300)
                return res
            except asyncio.TimeoutError:
                opts = parsed_args.get("options", [])
                default_choice = opts[0] if opts else "Proceed"
                return f"User confirmation timed out. Automatically chose: {default_choice}"
            finally:
                active_questions.pop(tool_id, None)

        agent.ask_user_resolver = ask_user_resolver

        start_time = time.time()

        async def event_generator():
            queue = asyncio.Queue()

            async def step_callback(event: Dict[str, Any]):
                await queue.put(event)

            task = asyncio.create_task(
                agent.run_task(
                    task_prompt=req.prompt,
                    provider_name=req.provider or session.provider,
                    model_name=req.model or session.model,
                    reasoning_effort=req.reasoning_effort or getattr(config, "reasoning_effort", "medium"),
                    on_step_callback=step_callback
                )
            )

            prompt_preview = agent.injector.inject(
                messages=[Message(role="user", content=req.prompt)],
                custom_master_prompt=req.custom_master_prompt,
                workspace=str(workspace_mgr.cwd)
            )
            yield f"data: {json.dumps({'type': 'init', 'session_id': session.id, 'master_prompt': prompt_preview[0].content}, ensure_ascii=False)}\n\n"

            while not task.done() or not queue.empty():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.2)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    continue

            total_duration = time.time() - start_time
            try:
                res = await task
                # 采用大模型返回的 100% 真实 Token 统计与缓存命中数据
                p_tokens = agent.total_usage.prompt_tokens
                c_tokens = agent.total_usage.completion_tokens
                t_tokens = agent.total_usage.total_tokens or (p_tokens + c_tokens)
                tps = round(c_tokens / max(total_duration, 0.1), 1)
                cache_tokens = agent.total_usage.prompt_cache_hit_tokens
                cache_ratio = round((cache_tokens / max(p_tokens, 1)) * 100, 1) if cache_tokens else 0.0

                telemetry = TelemetryData(
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                    total_tokens=t_tokens,
                    latency_ms=int(total_duration * 1000),
                    tokens_per_sec=tps,
                    cache_hit_tokens=cache_tokens,
                    cache_hit_ratio=cache_ratio
                )

                # 会话持久化记录
                session.messages = [m.model_dump() for m in agent.messages]
                session.telemetry = telemetry
                session_mgr.save_session(session)

                yield f"data: {json.dumps({'type': 'complete', 'session_id': session.id, 'result': res, 'telemetry': telemetry.model_dump()}, ensure_ascii=False)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    class UserResponseRequest(BaseModel):
        tool_id: str
        selected_options: List[str] = []
        custom_input: Optional[str] = None

    @app.post("/api/agent/user-response")
    async def handle_user_response(req: UserResponseRequest):
        """处理前端用户对 ask_user 交互提问的提交并唤醒 Agent 思考流"""
        active_questions: Dict[str, asyncio.Future] = getattr(app.state, "active_questions", {})
        fut = active_questions.get(req.tool_id)
        if not fut or fut.done():
            return {"status": "error", "message": "未找到待确认的提问或该提问已超时处理。"}

        parts = []
        if req.selected_options:
            parts.append(f"用户选择了: {', '.join(req.selected_options)}")
        if req.custom_input:
            parts.append(f"补充说明: {req.custom_input}")
        ans_text = " | ".join(parts) if parts else "用户已确认。"
        fut.set_result(ans_text)
        return {"status": "success", "message": "选项已成功同步给 Agent，正在继续执行！"}

    class RollbackRequest(BaseModel):
        message_index: int

    @app.post("/api/sessions/{session_id}/rollback")
    async def rollback_session(session_id: str, req: RollbackRequest):
        """会话时间旅行：回退到指定历史步骤并裁剪后续上下文"""
        session = session_mgr.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if 0 <= req.message_index < len(session.messages):
            session.messages = session.messages[:req.message_index + 1]
            session_mgr.save_session(session)
            return {"status": "success", "session": session}
        return {"status": "error", "message": "Invalid message index"}

    from harness.tools.mcp_client import global_mcp_manager

    @app.get("/api/mcp/servers")
    async def get_mcp_servers():
        """获取当前已挂载的 MCP 服务器列表与工具"""
        res = {}
        for s_name, conn in global_mcp_manager.servers.items():
            res[s_name] = {
                "name": s_name,
                "command": conn.command,
                "tools_count": len(conn.tools),
                "tools": [t.get("name") for t in conn.tools]
            }
        return {"mcp_servers": res}

    return app
