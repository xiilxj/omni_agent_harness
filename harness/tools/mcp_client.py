"""
Model Context Protocol (MCP) Client Integrator
为 Omni Agent Harness 提供标准 MCP 插件生态支持 (STDIO & SSE 客户端)
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("omni.mcp")


class MCPServerConnection:
    """单个 STDIO MCP Server 连接与工具代理"""

    def __init__(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        self.name = name
        self.command = command
        self.args = args or []
        self.env = {**os.environ, **(env or {})}
        self.process: Optional[asyncio.subprocess.Process] = None
        self.tools: List[Dict[str, Any]] = []
        self._request_id = 0

    async def connect(self):
        """启动 MCP Server 子进程并通过 STDIO 建立 JSON-RPC 握手"""
        try:
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.env
            )
            # 发送 MCP Initialize 请求
            init_res = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "omni-agent-harness", "version": "1.0.0"}
            })
            # 发送 initialized 通知
            await self._send_notification("notifications/initialized", {})
            # 获取工具列表
            list_res = await self._send_request("tools/list", {})
            if list_res and "tools" in list_res:
                self.tools = list_res["tools"]
                logger.info(f"MCP Server '{self.name}' initialized with {len(self.tools)} tools.")
        except Exception as e:
            logger.warning(f"Failed to connect to MCP server '{self.name}': {e}")

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """发送 JSON-RPC 请求并等待响应"""
        if not self.process or not self.process.stdin or not self.process.stdout:
            return None
        self._request_id += 1
        req_id = self._request_id
        req = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }
        line = json.dumps(req) + "\n"
        self.process.stdin.write(line.encode("utf-8"))
        await self.process.stdin.drain()

        # 读取响应
        while True:
            line_bytes = await self.process.stdout.readline()
            if not line_bytes:
                break
            try:
                resp = json.loads(line_bytes.decode("utf-8").strip())
                if resp.get("id") == req_id:
                    return resp.get("result")
            except Exception:
                continue
        return None

    async def _send_notification(self, method: str, params: Dict[str, Any]):
        """发送无需等待返回的通知"""
        if not self.process or not self.process.stdin:
            return
        notif = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        line = json.dumps(notif) + "\n"
        self.process.stdin.write(line.encode("utf-8"))
        await self.process.stdin.drain()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """调用 MCP 工具"""
        res = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        if not res:
            return f"Error: No response from MCP tool '{tool_name}'."
        content_items = res.get("content", [])
        text_outputs = []
        for item in content_items:
            if isinstance(item, dict) and item.get("type") == "text":
                text_outputs.append(item.get("text", ""))
            else:
                text_outputs.append(str(item))
        return "\n".join(text_outputs) if text_outputs else json.dumps(res, ensure_ascii=False)


class MCPManager:
    """全局 MCP 服务器管理器"""

    def __init__(self):
        self.servers: Dict[str, MCPServerConnection] = {}

    async def load_from_config(self, mcp_config: Dict[str, Any], registry: Any):
        """从配置字典加载并注册所有 MCP 服务器中的工具"""
        for s_name, s_cfg in mcp_config.items():
            cmd = s_cfg.get("command")
            args = s_cfg.get("args", [])
            env = s_cfg.get("env", {})
            if cmd:
                conn = MCPServerConnection(s_name, cmd, args, env)
                await conn.connect()
                self.servers[s_name] = conn

                # 动态注册工具到 ToolRegistry
                for t in conn.tools:
                    full_name = f"mcp__{s_name}__{t['name']}"
                    schema = t.get("inputSchema", {"type": "object", "properties": {}})
                    desc = f"[MCP: {s_name}] {t.get('description', '')}"

                    # 闭包绑定当前工具调用
                    def make_handler(c: MCPServerConnection, raw_name: str):
                        async def handler(**kwargs):
                            return await c.call_tool(raw_name, kwargs)
                        return handler

                    registry.register_raw(
                        name=full_name,
                        description=desc,
                        parameters=schema,
                        func=make_handler(conn, t['name']),
                        is_async=True
                    )


global_mcp_manager = MCPManager()
