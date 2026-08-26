"""
Omni Subagent Swarm Delegation Engine (DSH 智能体集群与子 Agent 协同派发引擎)
支持主智能体将高复杂度、深层搜索或代码审计子任务异步派发给专精子智能体 (Subagent)，
子智能体拥有独立的思考上下文与沙箱内存，完成后向主智能体提交结构化交付报告。
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional
from harness.core.config import AppConfig

logger = logging.getLogger("SubagentSwarm")


class SubagentManager:
    """子智能体派发生命周期管理器"""

    SUBAGENT_ROLES = {
        "researcher": "你是一名资深深度调研与代码库探索专家 (Codebase Researcher)。专注于全面检索代码结构、依赖与协议定义，输出清晰紧凑的调研总结，绝不修改破坏业务代码。",
        "code_auditor": "你是一名资深代码与安全审计专家 (Code & Security Auditor)。专注于静态分析语法、逻辑缺陷、越权漏洞与反编译逻辑，输出精准修复建议与缺陷定位。",
        "exploit_analyst": "你是一名资深协议逆向与攻防分析专家 (Reverse & Security Analyst)。专注于解构数据封包、加解密算法与逻辑绕过验证，输出精准的技术验证结论与 PoC 流程。",
        "general": "你是一名全能高执行力工程师 (Autonomous Operator)。直接专注于交付指定的子任务目标，输出具体执行结果。"
    }

    def __init__(self, parent_config: AppConfig, parent_tools: Any):
        self.parent_config = parent_config
        self.parent_tools = parent_tools

    async def invoke(
        self,
        role: str,
        task_prompt: str,
        max_steps: int = 15,
        on_parent_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
    ) -> str:
        """派发并运行子智能体，返回结构化执行报告"""
        from harness.core.agent import OmniAgent
        from harness.tools.registry import ToolRegistry
        from harness.tools.default_tools import register_default_tools

        sub_role = role.lower().strip()
        role_prompt = self.SUBAGENT_ROLES.get(sub_role, self.SUBAGENT_ROLES["general"])

        # 为子智能体组装独立沙箱工具集
        sub_tools = ToolRegistry()
        register_default_tools(sub_tools)

        # 构建子智能体
        child_agent = OmniAgent(
            config=self.parent_config,
            tools=sub_tools,
            custom_master_prompt=role_prompt
        )

        subagent_id = f"subagent-{sub_role}-{id(child_agent) % 10000}"

        if on_parent_callback:
            await on_parent_callback({
                "type": "subagent_event",
                "action": "spawned",
                "subagent_id": subagent_id,
                "role": sub_role,
                "prompt": task_prompt
            })

        async def subagent_step_relay(ev: Dict[str, Any]):
            """将子智能体的思考与工具执行流式中继给父通道"""
            if on_parent_callback:
                await on_parent_callback({
                    "type": "subagent_event",
                    "action": "step",
                    "subagent_id": subagent_id,
                    "role": sub_role,
                    "sub_event": ev
                })

        try:
            result = await child_agent.run_task(
                task_prompt=task_prompt,
                max_steps=max_steps,
                on_step_callback=subagent_step_relay
            )

            if on_parent_callback:
                await on_parent_callback({
                    "type": "subagent_event",
                    "action": "completed",
                    "subagent_id": subagent_id,
                    "role": sub_role,
                    "summary": result[:200] + "..." if len(result) > 200 else result
                })

            return f"=== Subagent [{sub_role}:{subagent_id}] Output Report ===\n\n{result}"
        except Exception as e:
            err_msg = f"Subagent [{subagent_id}] failed with error: {e}"
            logger.error(err_msg)
            return err_msg
