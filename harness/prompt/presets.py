"""
Master System Prompt Presets Manager
提供工业级内置预设库与用户自定义预设持久化管理
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# 所有内置预设已全部移除，纯净模式：100% 由用户自主编写、保存与管理
BUILTIN_PRESETS: List[Dict[str, Any]] = []


class PresetManager:
    """预设管理器：纯净由用户自主保存、命名、管理与热切换的自定义预设库"""

    def __init__(self, custom_file: Optional[Path] = None):
        self.custom_file = custom_file or (Path.home() / ".harness" / "prompt_presets.json")
        self.custom_file.parent.mkdir(parents=True, exist_ok=True)

    def list_presets(self) -> List[Dict[str, Any]]:
        """获取用户自主保存的所有自定义预设列表"""
        return self._load_custom()

    def _load_custom(self) -> List[Dict[str, Any]]:
        if not self.custom_file.exists():
            return []
        try:
            with open(self.custom_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_custom_preset(
        self,
        name: str,
        content: str,
        description: str = "",
        preset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """保存或覆盖更新用户自定义预设"""
        presets = self._load_custom()
        import uuid
        
        # 1. 若显式指定了 preset_id，优先按 ID 覆盖
        if preset_id:
            existing = next((p for p in presets if p["id"] == preset_id), None)
            if existing:
                existing["content"] = content.strip()
                if name and name.strip():
                    existing["name"] = name.strip()
                if description and description.strip():
                    existing["description"] = description.strip()
                with open(self.custom_file, "w", encoding="utf-8") as f:
                    json.dump(presets, f, ensure_ascii=False, indent=2)
                return existing

        # 2. 若无 ID 但同名，覆盖同名项
        existing = next((p for p in presets if p["name"] == name.strip()), None)
        if existing:
            existing["content"] = content.strip()
            if description and description.strip():
                existing["description"] = description.strip()
            with open(self.custom_file, "w", encoding="utf-8") as f:
                json.dump(presets, f, ensure_ascii=False, indent=2)
            return existing

        # 3. 创建新预设
        new_id = preset_id or f"custom_{str(uuid.uuid4())[:6]}"
        item = {
            "id": new_id,
            "name": name.strip() or "Custom Preset",
            "tag": "Custom",
            "description": description.strip() or "User saved custom preset",
            "content": content.strip()
        }
        presets.append(item)

        with open(self.custom_file, "w", encoding="utf-8") as f:
            json.dump(presets, f, ensure_ascii=False, indent=2)
        return item

    def delete_custom_preset(self, preset_id: str) -> bool:
        """删除用户自定义预设"""
        presets = self._load_custom()
        initial_len = len(presets)
        presets = [p for p in presets if p["id"] != preset_id]
        if len(presets) < initial_len:
            with open(self.custom_file, "w", encoding="utf-8") as f:
                json.dump(presets, f, ensure_ascii=False, indent=2)
            return True
        return False
