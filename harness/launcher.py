"""
Omni Agent Harness - Cross-Platform Native Python Launcher
跨平台统一启动引导器：解决 Windows CMD 批处理编码缺陷、依赖自愈与防闪退保护。
"""

import os
import sys
import time
import shutil
import threading
import subprocess
import webbrowser
import traceback
from pathlib import Path

# 确保在 Windows 终端下 UTF-8 正常输出
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def print_banner():
    print("=" * 64)
    print("      Omni Agent Harness (Codex-DSH 架构) - 启动器")
    print("=" * 64)
    print()


def ensure_env_file():
    env_file = BASE_DIR / ".env"
    env_example = BASE_DIR / ".env.example"
    if not env_file.exists() and env_example.exists():
        try:
            shutil.copy(env_example, env_file)
            print("[提示] 已根据模板自动创建本地 .env 配置文件。")
        except Exception as e:
            print(f"[警告] 创建 .env 失败: {e}")


def check_and_fix_dependencies(install_only: bool = False):
    print("[1/3] 正在检查运行环境与核心依赖库...")
    need_install = False

    try:
        import pydantic
        import pydantic_core
        import fastapi
        import uvicorn
        import jinja2
        import httpx
        import yaml
        import dotenv
    except (ImportError, Exception) as e:
        need_install = True
        print(f"[提示] 检测到依赖库未安装或动态链接库需要配置 ({e})，正在自动安装修复...")

    if need_install or install_only:
        req_file = BASE_DIR / "requirements.txt"
        pip_cmd = [
            sys.executable, "-m", "pip", "install",
            "-r", str(req_file),
            "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
            "--upgrade"
        ]
        try:
            subprocess.check_call(pip_cmd)
            # 二次验证 pydantic_core 动态库
            try:
                import pydantic_core
            except Exception:
                print("[自动修复] 正在为当前 Python 环境重新拉取匹配的 pydantic-core...")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install",
                    "--upgrade", "--force-reinstall", "--no-cache-dir",
                    "pydantic", "pydantic-core",
                    "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
                ])
            print("  ✓ 所有依赖库已安装并校验完毕！")
        except subprocess.CalledProcessError as err:
            print(f"[警告] pip 安装遇到问题: {err}，将尝试以现有环境继续启动。")

    if install_only:
        print("\n[完成] 依赖安装完成！您可以运行 start_windows.bat 启动服务。")
        sys.exit(0)


def open_browser_delayed(url: str, delay_seconds: float = 1.5):
    def _open():
        time.sleep(delay_seconds)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    t = threading.Thread(target=_open, daemon=True)
    t.start()


def main():
    print_banner()
    ensure_env_file()

    install_only = "--install-only" in sys.argv
    check_and_fix_dependencies(install_only=install_only)

    host = "127.0.0.1"
    port = 7890
    url = f"http://{host}:{port}"

    print("[2/3] 正在启动 Web 控制台...")
    open_browser_delayed(url, 1.5)

    print("[3/3] Omni Agent Harness 服务已就绪！")
    print("=" * 64)
    print(f"  浏览器访问地址: {url}")
    print("  如需停止运行，请按 Ctrl + C 或直接关闭本窗口。")
    print("=" * 64)
    print()

    # 启动 Uvicorn 服务 (使用标准的 factory 字符串格式)
    try:
        import uvicorn
        uvicorn.run(
            "harness.ui.app:create_app",
            factory=True,
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n[退出] 服务已停止。")
    except Exception as e:
        print(f"\n[错误] 服务启动异常: {e}")
        traceback.print_exc()
        print("\n" + "=" * 64)
        print("[启动异常排查指引]")
        print("若提示 DLL load failed，通常是由于缺少微软 Visual C++ 运行库。")
        print("解决方案：")
        print("1. 下载安装微软官方 VC++ 2015-2022 x64 运行库:")
        print("   https://aka.ms/vs/17/release/vc_redist.x64.exe")
        print("2. 或推荐安装 Python 3.11 或 3.12 长期稳定版。")
        print("=" * 64)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        traceback.print_exc()
        print("\n================================================================")
        print(f"[严重异常] 启动器遇到错误: {ex}")
        print("================================================================")
        try:
            input("\n按回车键退出...")
        except Exception:
            pass
        sys.exit(1)
