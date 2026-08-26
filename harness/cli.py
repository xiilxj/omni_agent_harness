"""
Omni Agent Harness CLI Entrypoint
统一命令行入口：支持交互式 REPL、单任务模式 (-p/--prompt) 与 Web UI 服务启动 (--ui/--web)
"""

import argparse
import asyncio
import os
import sys
import webbrowser
from pathlib import Path

# 确保工程根目录加入 sys.path，支持在任意路径下直接运行
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from harness.core.config import load_config, get_os_type
from harness.core.agent import OmniAgent
from harness.prompt.master_injector import MasterPromptInjector


def parse_args():
    parser = argparse.ArgumentParser(
        description="Omni Agent Harness (Codex-DSH Core) - 100% 绝对系统提示词注入智能体底座"
    )
    parser.add_argument(
        "-p", "--prompt",
        type=str,
        help="直接运行单次 Agent 任务指令并退出"
    )
    parser.add_argument(
        "--ui", "--web",
        action="store_true",
        help="启动 Web UI 可视化控制台 (Dashboard)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Web UI 监听 Host (默认: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7890,
        help="Web UI 监听端口 (默认: 7890)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="指定使用的 LLM Provider (deepseek, openai, anthropic, local_vllm)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="指定使用的模型名称"
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="启用 Web UI 与 API 访问 Token 认证密码 (防止公网无鉴权暴露)"
    )
    return parser.parse_args()


async def run_single_task(args, config):
    """运行单次命令行任务"""
    agent = OmniAgent(config=config)
    print(f"\n[Omni Harness] 正在执行任务 (操作系统: {get_os_type()} | 工作目录: {os.getcwd()})")
    print(f"[Omni Harness] 100% 绝对最高指令注入生效中: {agent.injector.resolve_master_prompt_path()}\n")

    async def step_callback(ev):
        ev_type = ev.get("type")
        if ev_type == "assistant_thought":
            print(f"\n[Agent 思考]\n{ev.get('content')}")
        elif ev_type == "tool_executing":
            print(f"\n⚙️ [调用工具] {ev.get('tool_name')}({ev.get('tool_args')})")
        elif ev_type == "tool_result":
            obs = str(ev.get('observation', ''))
            if len(obs) > 300:
                obs = obs[:150] + " ... [省略] ... " + obs[-150:]
            print(f"✔️ [工具输出] {obs}")

    res = await agent.run_task(
        task_prompt=args.prompt,
        provider_name=args.provider,
        model_name=args.model,
        on_step_callback=step_callback
    )
    print(f"\n==================== [任务完成] ====================")
    print(res)
    print(f"====================================================\n")


async def run_repl(config):
    """运行交互式终端 REPL"""
    agent = OmniAgent(config=config)
    print("=" * 65)
    print("  Omni Agent Harness (Codex-DSH Core) - 交互式智能体终端")
    print(f"  OS: {get_os_type()} | Workspace: {os.getcwd()}")
    print(f"  最高领导指令: {agent.injector.resolve_master_prompt_path()}")
    print("  输入任务开始执行，输入 'exit' 或 'quit' 退出")
    print("=" * 65)

    while True:
        try:
            user_input = input("\n[User] > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("退出 Harness。")
                break

            async def step_callback(ev):
                if ev.get("type") == "assistant_thought":
                    print(f"\n[Agent 思考]\n{ev.get('content')}")
                elif ev.get("type") == "tool_executing":
                    print(f"\n⚙️ [调用工具] {ev.get('tool_name')}({ev.get('tool_args')})")
                elif ev.get("type") == "tool_result":
                    obs = str(ev.get('observation', ''))
                    if len(obs) > 300:
                        obs = obs[:150] + " ... [省略] ... " + obs[-150:]
                    print(f"✔️ [工具输出] {obs}")

            res = await agent.run_task(task_prompt=user_input, on_step_callback=step_callback)
            print(f"\n[Agent 结论]\n{res}")
        except (KeyboardInterrupt, EOFError):
            print("\n已中断。")
            break


def start_web_ui(host: str, port: int, token: str = None, config_path: str = None):
    """启动 Web UI 服务"""
    import uvicorn

    if token:
        os.environ["HARNESS_AUTH_TOKEN"] = token

    auth_active = bool(os.getenv("HARNESS_AUTH_TOKEN"))

    # 安全审计告警
    if host in ("0.0.0.0", "::") and not auth_active:
        print("\n" + "!" * 64)
        print("  [⚠️ 安全风险告警] 服务监听地址为 0.0.0.0 且未启用 Token 访问鉴权！")
        print("  局域网或公网用户均可直接访问您的 Web UI 并执行任意文件读写或终端命令。")
        print("  强烈建议：")
        print("    1. 本地安全使用：使用默认 host (127.0.0.1)")
        print("    2. 远程网络访问：启动时添加 --token <SECRET_TOKEN> 或配置 HARNESS_AUTH_TOKEN")
        print("!" * 64 + "\n")

    from harness.ui.app import create_app
    app = create_app(config_path)

    browser_url = f"http://127.0.0.1:{port}" if host in ("0.0.0.0", "127.0.0.1") else f"http://{host}:{port}"
    if auth_active:
        browser_url += f"/?token={os.getenv('HARNESS_AUTH_TOKEN')}"

    print(f"\n=======================================================")
    print(f"  Omni Agent Harness - Master Dashboard Web UI 已启动!")
    print(f"  浏览器访问地址: {browser_url}")
    if auth_active:
        print(f"  🔒 安全鉴权模式: 已启用 (Token 保护中)")
    else:
        print(f"  🔓 安全鉴权模式: 本地单机模式 (127.0.0.1)")
    print(f"  最高领导指令编辑中心已就绪，100% 绝对置顶注入生效中")
    print(f"=======================================================\n")

    uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    args = parse_args()
    config = load_config()

    if args.ui:
        start_web_ui(args.host, args.port, token=args.token)
    elif args.prompt:
        asyncio.run(run_single_task(args, config))
    else:
        asyncio.run(run_repl(config))


if __name__ == "__main__":
    main()
