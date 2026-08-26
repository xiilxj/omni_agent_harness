"""
Session Management & Persistence Engine
支持多会话独立持久化存储、会话切换、历史消息与 Telemetry 状态恢复
"""

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from harness.core.models import Message, UsageStats


class TelemetryData(BaseModel):
    """遥测与计量数据 (DSH 对齐)"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    tokens_per_sec: float = 0.0
    cache_hit_tokens: int = 0
    cache_hit_ratio: float = 0.0
    prompt_cache_miss_tokens: int = 0
    turn_cost_cny: float = 0.0
    session_cost_cny: float = 0.0
    formatted_cost: str = "¥0.00000"
    model_name: str = "deepseek-chat"
    pricing_breakdown: Dict[str, Any] = Field(default_factory=dict)


class SessionItem(BaseModel):
    """会话对象定义"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = "New Task Session"
    is_archived: bool = False
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    workspace: str = Field(default_factory=os.getcwd)
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    telemetry: TelemetryData = Field(default_factory=TelemetryData)
    accumulated_cost_cny: float = 0.0


def auto_generate_title(prompt: str) -> str:
    """基于首条用户提示词智能提取高可读性会话简短标题"""
    cleaned = prompt.strip().replace("\n", " ")
    # 移除常见的起手词以获得精炼核心词
    for prefix in ["帮我", "请帮我", "请", "能否", "帮我看下", "分析一下", "执行", "运行", "编写", "创建"]:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            break
    if len(cleaned) > 20:
        cleaned = cleaned[:20] + "..."
    return cleaned or "Task Session"


class SessionManager:
    """会话管理器，负责磁盘 JSON 序列化与读写缓存"""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or (Path.home() / ".harness" / "sessions")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, session_id: str) -> Path:
        return self.storage_dir / f"{session_id}.json"

    def list_sessions(self) -> List[Dict[str, Any]]:
        """获取所有已保存会话的元数据列表（按更新时间倒序）"""
        sessions = []
        for file in self.storage_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append({
                        "id": data.get("id"),
                        "title": data.get("title", "Untitled Session"),
                        "is_archived": bool(data.get("is_archived", False)),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                        "message_count": len(data.get("messages", [])),
                        "model": data.get("model", "deepseek-chat"),
                        "workspace": data.get("workspace", "")
                    })
            except Exception:
                continue

        sessions.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        return sessions

    def get_session(self, session_id: str) -> Optional[SessionItem]:
        """获取指定 ID 的完整会话对象"""
        p = self._get_session_path(session_id)
        if not p.exists():
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                return SessionItem(**data)
        except Exception:
            return None

    def save_session(self, session: SessionItem):
        """保存或更新会话到磁盘"""
        session.updated_at = time.time()
        p = self._get_session_path(session.id)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(session.model_dump(), f, ensure_ascii=False, indent=2)

    def toggle_archive(self, session_id: str) -> Optional[bool]:
        """切换会话归档状态"""
        session = self.get_session(session_id)
        if not session:
            return None
        session.is_archived = not session.is_archived
        self.save_session(session)
        return session.is_archived

    def rename_session(self, session_id: str, new_title: str) -> bool:
        """用户自主重命名会话标题"""
        session = self.get_session(session_id)
        if not session:
            return False
        session.title = new_title.strip() or "Untitled Session"
        self.save_session(session)
        return True

    def delete_session(self, session_id: str) -> bool:
        """删除指定会话"""
        p = self._get_session_path(session_id)
        if p.exists():
            p.unlink()
            return True
        return False


# 全局单例
global_session_manager = SessionManager()
