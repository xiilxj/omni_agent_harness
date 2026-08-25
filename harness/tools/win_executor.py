"""
Windows PowerShell / CMD Executor
支持 Windows 环境下的异步 PowerShell 与 CMD 执行
"""

import asyncio
import os
from typing import Optional


async def run_powershell_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 120,
    max_output_length: int = 20000
) -> str:
    """在 Windows 环境下执行 PowerShell 命令并返回结果"""
    working_dir = cwd or os.getcwd()
    try:
        # 使用 powershell.exe -NoProfile -ExecutionPolicy Bypass -Command
        ps_cmd = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "{command}"'
        process = await asyncio.create_subprocess_shell(
            ps_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            return f"Error: PowerShell command timed out after {timeout} seconds."

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
            result = f"[PowerShell finished with exit code {exit_code} and no output]"
        elif exit_code != 0:
            result = f"[Exit Code: {exit_code}]\n{result}"

        if len(result) > max_output_length:
            half = max_output_length // 2
            result = result[:half] + f"\n\n... [Truncated {len(result) - max_output_length} characters] ...\n\n" + result[-half:]

        return result
    except Exception as e:
        return f"Error executing PowerShell command: {e}"
