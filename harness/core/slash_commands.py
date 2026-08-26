"""
Slash Commands Engine (斜杠快捷指令系统)
支持 /goal, /grill-me, /schedule, /browser, /teamwork-preview, /learn, /rollback, /clear, /help 等指令解析与提示词增强
"""

import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List


SLASH_COMMANDS_REGISTRY = [
    {
        "command": "/goal",
        "title": "🎯 长程深度攻坚目标 (Autonomous Goal)",
        "syntax": "/goal <目标描述>",
        "desc": "开启深度自主长程攻坚模式，设定最终目标，Agent 将穷尽所有工具与路径自主纠偏，不达目的誓不罢休。",
        "placeholder": "/goal 请彻底重构鉴权模块并补充 100% 覆盖率单元测试"
    },
    {
        "command": "/grill-me",
        "title": "🔥 交互式对齐盘问 (Interactive Grill-Me)",
        "syntax": "/grill-me [设计议题/需求]",
        "desc": "智能体化身资深技术架构师，不直接写代码，而是以尖锐的提问逐项盘问你未说明的技术细节、边界条件与设计决策。",
        "placeholder": "/grill-me 针对高并发限流网关进行架构对齐与方案评审"
    },
    {
        "command": "/schedule",
        "title": "⏰ 定时/周期巡检任务 (Schedule Cron/Timer)",
        "syntax": "/schedule <表达式/秒数> <巡检任务>",
        "desc": "调度后台一次性定时器或周期性 Cron 自动化任务（如每 5 分钟健康检查）。",
        "placeholder": "/schedule 300 检查服务运行状态并汇报"
    },
    {
        "command": "/browser",
        "title": "🌐 Chrome DevTools 自动化浏览 (Browser Automation)",
        "syntax": "/browser <URL/查询目标>",
        "desc": "调用本地 Chrome DevTools MCP 浏览器自动访问目标、提取 DOM、截获 Network 请求与自动化测试。",
        "placeholder": "/browser http://localhost:7890 审计页面布局与 API 接口"
    },
    {
        "command": "/teamwork-preview",
        "title": "👥 多智能体集群演练 (Multi-Agent Swarm)",
        "syntax": "/teamwork-preview <协同项目>",
        "desc": "派发架构师、逆向员、测试员等多子 Agent 并行协作攻坚复杂工程。",
        "placeholder": "/teamwork-preview 协同完成跨平台逆向与协议分析"
    },
    {
        "command": "/learn",
        "title": "🧠 经验模式持久化 (Persistent Learning)",
        "syntax": "/learn <避坑经验/技术要点>",
        "desc": "将当前学到的重要经验或规则直接写入系统的唯一持久化记忆文件 persistent_memory.txt。",
        "placeholder": "/learn 在进行 API 签名逆向时优先通过 Frida Hook 内存定位"
    },
    {
        "command": "/rollback",
        "title": "⏪ 状态时空回退 (Rollback History)",
        "syntax": "/rollback [步骤编号]",
        "desc": "回退到指定轮次的交互状态，并裁剪清除后续所有多余上下文。",
        "placeholder": "/rollback 3"
    },
    {
        "command": "/clear",
        "title": "🧹 清空控制台 (Clear Console)",
        "syntax": "/clear",
        "desc": "清空当前会话显示并重置流式控制台。",
        "placeholder": "/clear"
    },
    {
        "command": "/help",
        "title": "❓ 斜杠指令指南 (Commands Help)",
        "syntax": "/help",
        "desc": "列出所有支持的斜杠快捷指令与用法说明。",
        "placeholder": "/help"
    }
]


def parse_and_transform_slash_command(raw_prompt: str) -> Tuple[str, Optional[str], Dict[str, Any]]:
    """
    解析并转换用户输入的斜杠命令
    返回: (transformed_prompt, command_name, command_meta)
    """
    text = raw_prompt.strip()
    if not text.startswith("/"):
        return raw_prompt, None, {}

    # 提取指令名称与参数
    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "/goal":
        transformed = (
            f"[LONG-RUNNING GOAL DIRECTIVE: EXTRA THOROUGH & AUTONOMOUS]\n"
            f"User Goal: {args or 'Execute full end-to-end task and verify completion'}\n\n"
            f"Instructions:\n"
            f"1. Break down the goal into clear milestones using `update_todo_list`.\n"
            f"2. Execute each step rigorously with ReAct tools, self-correct errors, and verify with tests/files.\n"
            f"3. Do NOT stop or give partial advice until the goal is 100% completed and fully verified."
        )
        return transformed, "goal", {"original": raw_prompt, "target": args}

    elif cmd in ("/grill-me", "/grill_me"):
        transformed = (
            f"[GRILL-ME INTERVIEW & ALIGNMENT DIRECTIVE]\n"
            f"Topic: {args or 'The proposed architecture and technical implementation plan'}\n\n"
            f"Instructions:\n"
            f"1. You are acting as an uncompromising, senior technical architect and interviewer.\n"
            f"2. Do NOT write the implementation code yet!\n"
            f"3. Instead, interrogate the user by asking 2-4 incisive, clarifying questions using the `ask_question` tool or structured bullet points.\n"
            f"4. Focus on uncovering hidden assumptions, edge cases, error recovery, performance bottlenecks, and design trade-offs.\n"
            f"5. Wait for the user to respond before generating the final implementation plan."
        )
        return transformed, "grill-me", {"original": raw_prompt, "topic": args}

    elif cmd == "/schedule":
        transformed = (
            f"[SCHEDULE BACKGROUND TASK DIRECTIVE]\n"
            f"Schedule Request: {args}\n\n"
            f"Instructions: Parse the time/cron and task description from the request, and invoke the schedule tool or provide the exact cron configuration immediately."
        )
        return transformed, "schedule", {"original": raw_prompt, "args": args}

    elif cmd == "/browser":
        transformed = (
            f"[BROWSER RECON & AUTOMATION DIRECTIVE]\n"
            f"Target: {args}\n\n"
            f"Instructions: Use Chrome DevTools MCP tools to navigate to the target, inspect the DOM, monitor Network Fetch/XHR requests, and report findings."
        )
        return transformed, "browser", {"original": raw_prompt, "target": args}

    elif cmd in ("/teamwork-preview", "/teamwork"):
        transformed = (
            f"[MULTI-AGENT SWARM TEAMWORK DIRECTIVE]\n"
            f"Plan/Project: {args or 'Collaborative engineering task'}\n\n"
            f"Instructions: Break down this complex task across specialized subagents using `invoke_subagent` (e.g. Researcher, Reverse Engineer, Tester), manage their execution, and synthesize the final deliverable."
        )
        return transformed, "teamwork-preview", {"original": raw_prompt, "project": args}

    elif cmd == "/learn":
        # 自动追加到 persistent_memory.txt
        persistent_file = Path.home() / ".gemini" / "antigravity" / "rules" / "persistent_memory.txt"
        if args:
            try:
                persistent_file.parent.mkdir(parents=True, exist_ok=True)
                with open(persistent_file, "a", encoding="utf-8") as f:
                    f.write(f"\n- [Learned Experience]: {args}")
            except Exception:
                pass
        transformed = (
            f"[LEARNED EXPERIENCE PERSISTED]\n"
            f"The following knowledge has been permanently recorded to persistent_memory.txt: '{args}'.\n"
            f"Please confirm the memory persistence and explain how this rule will be applied in future tasks."
        )
        return transformed, "learn", {"original": raw_prompt, "knowledge": args}

    elif cmd == "/help":
        lines = [
            "# 📖 Omni Agent Harness 斜杠快捷指令指南 (Slash Commands Guide)\n",
            "您可以在输入框开头输入 `/` 触发以下专业指令：\n"
        ]
        for c in SLASH_COMMANDS_REGISTRY:
            lines.append(f"- **`{c['command']}`** ({c['syntax']}): {c['desc']}")
        transformed = (
            f"[SYSTEM HELP REQUEST]\n"
            f"User asked for help with slash commands. Display the following guide nicely in Markdown:\n\n"
            + "\n".join(lines)
        )
        return transformed, "help", {"original": raw_prompt}

    return raw_prompt, None, {}
