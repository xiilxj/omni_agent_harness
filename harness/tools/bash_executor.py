"""
Linux Shell / Bash Executor
支持异步子进程执行、超时保护与输出截断
"""

import asyncio
import os
from typing import Optional


async def run_shell_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 120,
    max_output_length: int = 20000
) -> str:
    """在当前 Linux/macOS 环境执行 shell 命令并返回结果"""
    working_dir = cwd or os.getcwd()
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            return f"Error: Command timed out after {timeout} seconds."

        out_str = stdout.decode("utf-8", errors="replace")
        err_str = stderr.decode("utf-8", errors="replace")
        exit_code = process.returncode

        result = ""
        if out_str:
            result += out_str
        if err_str:
            if result:
                result += "\n"
            result += f"[stderr]\n{err_str}"

        if not result.strip():
            result = f"[Command finished with exit code {exit_code} and no output]"
        elif exit_code != 0:
            result = f"[Exit Code: {exit_code}]\n{result}"

        # 输出长度截断保护
        if len(result) > max_output_length:
            half = max_output_length // 2
            result = result[:half] + f"\n\n... [Truncated {len(result) - max_output_length} characters] ...\n\n" + result[-half:]

        return result
    except Exception as e:
        return f"Error executing shell command: {e}"
