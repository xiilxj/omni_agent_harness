"""
Omni Background Task & Daemon Manager (DSH 后台常驻任务与进程管理系统)
支持启动、监控、日志捕获与终止后台常驻支持进程（如 Dev Server、编译监听器、后台抓取或分析任务），
避免阻塞前台 ReAct 对话与工具调度。
"""

import asyncio
import os
import signal
import time
from pathlib import Path
from typing import Dict, List, Optional


class BackgroundTask:
    def __init__(self, task_id: str, command: str, process: asyncio.subprocess.Process, log_file: Path, cwd: str):
        self.task_id = task_id
        self.command = command
        self.process = process
        self.log_file = log_file
        self.cwd = cwd
        self.start_time = time.time()

    @property
    def is_running(self) -> bool:
        return self.process.returncode is None

    def get_logs(self, max_lines: int = 50) -> str:
        if not self.log_file.exists():
            return "(No logs generated yet)"
        try:
            with open(self.log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            return "".join(lines[-max_lines:])
        except Exception as e:
            return f"(Error reading log file: {e})"


class BackgroundTaskManager:
    """后台常驻任务管理器"""

    def __init__(self, log_dir: str = "/tmp/omni_tasks"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._tasks: Dict[str, BackgroundTask] = {}
        self._counter = 0

    async def start_task(self, command: str, cwd: Optional[str] = None) -> str:
        """启动后台常驻进程并重定向输出至日志"""
        self._counter += 1
        task_id = f"task-{self._counter:03d}"
        log_file = self.log_dir / f"{task_id}.log"
        work_dir = cwd or os.getcwd()

        with open(log_file, "w", encoding="utf-8") as out:
            out.write(f"=== Omni Background Task [{task_id}] Started at {time.ctime()} ===\n")
            out.write(f"Command: {command}\nCwd: {work_dir}\n\n")

        # 启动异步子进程
        log_handle = open(log_file, "a", encoding="utf-8")
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=work_dir,
            stdout=log_handle,
            stderr=asyncio.subprocess.STDOUT
        )

        task = BackgroundTask(
            task_id=task_id,
            command=command,
            process=process,
            log_file=log_file,
            cwd=work_dir
        )
        self._tasks[task_id] = task

        return (
            f"✅ Background task [{task_id}] started successfully!\n"
            f"- PID: {process.pid}\n"
            f"- Command: {command}\n"
            f"- Log File: {log_file}\n"
            f"Use 'manage_task(action=\"status\", task_id=\"{task_id}\")' to inspect output or 'manage_task(action=\"kill\", task_id=\"{task_id}\")' to terminate."
        )

    def get_status(self, task_id: str) -> str:
        """获取指定后台任务状态与最新日志"""
        task = self._tasks.get(task_id)
        if not task:
            return f"Error: Task ID '{task_id}' not found."

        elapsed = time.time() - task.start_time
        status_str = "RUNNING 🟢" if task.is_running else f"STOPPED (Exit Code: {task.process.returncode}) ⚪"
        logs = task.get_logs(max_lines=30)

        return (
            f"=== Task [{task_id}] Status: {status_str} ===\n"
            f"- Command: {task.command}\n"
            f"- Runtime: {elapsed:.1f}s\n"
            f"- PID: {task.process.pid}\n\n"
            f"--- Latest Logs (tail 30 lines) ---\n{logs}"
        )

    async def kill_task(self, task_id: str) -> str:
        """终止指定的后台任务"""
        task = self._tasks.get(task_id)
        if not task:
            return f"Error: Task ID '{task_id}' not found."

        if not task.is_running:
            return f"Task [{task_id}] is already stopped."

        try:
            task.process.terminate()
            try:
                await asyncio.wait_for(task.process.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                task.process.kill()
            return f"Task [{task_id}] (PID {task.process.pid}) has been terminated."
        except Exception as e:
            return f"Failed to kill task [{task_id}]: {e}"

    def list_tasks(self) -> str:
        """列出所有后台任务"""
        if not self._tasks:
            return "No background tasks currently running or registered."

        lines = ["=== Omni Registered Background Tasks ==="]
        for tid, t in self._tasks.items():
            status = "RUNNING 🟢" if t.is_running else f"STOPPED ({t.process.returncode})"
            lines.append(f"- [{tid}] PID={t.process.pid} | Status={status} | Cmd='{t.command[:50]}'")
        return "\n".join(lines)


# 全局后台任务管理器单例
global_task_manager = BackgroundTaskManager()
