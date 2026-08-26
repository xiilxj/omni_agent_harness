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


class SuffixPresetManager:
    """最高回答词预设与随机号池管理器：支持固定选定与多预设随机号池轮换"""

    def __init__(self, custom_file: Optional[Path] = None):
        self.custom_file = custom_file or (Path.home() / ".harness" / "suffix_presets.json")
        self.custom_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_defaults()

    def _ensure_defaults(self):
        """确保初始包含基础实用模板"""
        if not self.custom_file.exists():
            default_data = {
                "mode": "fixed",  # "fixed" | "random"
                "active_preset_id": "suffix_status_1",
                "enabled_pool_ids": ["suffix_status_1", "suffix_norm_2", "suffix_next_3"],
                "presets": [
                    {
                        "id": "suffix_status_1",
                        "name": "📋 执行状态签结",
                        "content": "\n\n---\n**执行状态**：当前步骤已完成，请确认或下发下一指令。",
                        "description": "标准工程执行签结"
                    },
                    {
                        "id": "suffix_norm_2",
                        "name": "🔒 规范核验标识",
                        "content": "\n\n[回答规范已核验完成，各项输出符合约束要求]",
                        "description": "输出格式约束与合规戳"
                    },
                    {
                        "id": "suffix_next_3",
                        "name": "⚡ 下一步建议",
                        "content": "\n\n---\n**下一步建议**：如有需要可随时下发延伸指令。",
                        "description": "延伸任务引导提示"
                    }
                ]
            }
            try:
                with open(self.custom_file, "w", encoding="utf-8") as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _load_data(self) -> Dict[str, Any]:
        if not self.custom_file.exists():
            self._ensure_defaults()
        try:
            with open(self.custom_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    data = {"mode": "fixed", "active_preset_id": None, "enabled_pool_ids": [], "presets": data}
                return data
        except Exception:
            return {"mode": "fixed", "active_preset_id": None, "enabled_pool_ids": [], "presets": []}

    def _save_data(self, data: Dict[str, Any]):
        try:
            with open(self.custom_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_state(self) -> Dict[str, Any]:
        """获取当前回答词预设库与模式状态"""
        return self._load_data()

    def list_presets(self) -> List[Dict[str, Any]]:
        """获取所有预设列表"""
        return self._load_data().get("presets", [])

    def save_preset(
        self,
        name: str,
        content: str,
        description: str = "",
        preset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """保存或覆盖回答词预设"""
        data = self._load_data()
        presets = data.get("presets", [])
        import uuid

        if preset_id:
            existing = next((p for p in presets if p["id"] == preset_id), None)
            if existing:
                existing["content"] = content.strip()
                if name and name.strip():
                    existing["name"] = name.strip()
                if description and description.strip():
                    existing["description"] = description.strip()
                self._save_data(data)
                return existing

        existing = next((p for p in presets if p["name"] == name.strip()), None)
        if existing:
            existing["content"] = content.strip()
            if description and description.strip():
                existing["description"] = description.strip()
            self._save_data(data)
            return existing

        new_id = preset_id or f"suffix_{str(uuid.uuid4())[:6]}"
        item = {
            "id": new_id,
            "name": name.strip() or "Custom Suffix",
            "description": description.strip() or "User saved suffix preset",
            "content": content.strip()
        }
        presets.append(item)
        data["presets"] = presets
        if not data.get("active_preset_id"):
            data["active_preset_id"] = new_id
        if new_id not in data.get("enabled_pool_ids", []):
            data.setdefault("enabled_pool_ids", []).append(new_id)
        self._save_data(data)
        return item

    def delete_preset(self, preset_id: str) -> bool:
        """删除回答词预设"""
        data = self._load_data()
        presets = data.get("presets", [])
        initial_len = len(presets)
        presets = [p for p in presets if p["id"] != preset_id]
        if len(presets) < initial_len:
            data["presets"] = presets
            if data.get("active_preset_id") == preset_id:
                data["active_preset_id"] = presets[0]["id"] if presets else None
            data["enabled_pool_ids"] = [pid for pid in data.get("enabled_pool_ids", []) if pid != preset_id]
            self._save_data(data)
            return True
        return False

    def update_settings(
        self,
        mode: Optional[str] = None,
        active_preset_id: Optional[str] = None,
        enabled_pool_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """更新模式 (fixed / random) 与激活状态"""
        data = self._load_data()
        if mode in ("fixed", "random"):
            data["mode"] = mode
        if active_preset_id is not None:
            data["active_preset_id"] = active_preset_id
        if enabled_pool_ids is not None:
            data["enabled_pool_ids"] = enabled_pool_ids
        self._save_data(data)
        return data

    def get_effective_suffix(self) -> str:
        """根据当前模式获取最终注入的最高回答词（支持固定与随机号池模式）"""
        import random
        data = self._load_data()
        mode = data.get("mode", "fixed")
        presets = data.get("presets", [])
        if not presets:
            return ""

        if mode == "random":
            pool_ids = data.get("enabled_pool_ids", [])
            valid_pool = [p for p in presets if p["id"] in pool_ids] if pool_ids else presets
            if not valid_pool:
                valid_pool = presets
            chosen = random.choice(valid_pool)
            return chosen.get("content", "")
        else:
            active_id = data.get("active_preset_id")
            matched = next((p for p in presets if p["id"] == active_id), None) if active_id else presets[0]
            if matched:
                return matched.get("content", "")
            return presets[0].get("content", "")
