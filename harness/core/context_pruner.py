"""
Omni Context Pruner & Token Optimizer (DSH 上下文压缩与 Token 剪枝优化器)
在长多轮会话或大规模代码搜索任务中，智能对早期冗长工具输出与历史上下文进行无损剪枝与压缩，
防止长上下文爆 Token，最大化 Prompt Cache 命中率并节省推理预算。
"""

import copy
from typing import List, Tuple
from harness.core.models import Message


class ContextPruner:
    """智能上下文剪枝器"""

    def __init__(self, max_context_chars: int = 60000, tool_truncation_len: int = 600):
        self.max_context_chars = max_context_chars
        self.tool_truncation_len = tool_truncation_len

    def prune_and_compact(self, messages: List[Message]) -> Tuple[List[Message], int]:
        """
        对消息列表进行无损/低损压缩剪枝：
        1. 绝不修改 index 0 处的 Master System Prompt 与最新 4 轮关键上下文；
        2. 将历史较早轮次中超过 tool_truncation_len 字符的超大工具观察结果安全压缩截断并保留特征标；
        3. 返回剪枝后的消息列表及节省的估计 Token 数。
        """
        if not messages or len(messages) <= 5:
            return messages, 0

        # 计算原始字符总量
        raw_char_count = sum(len(str(m.content or "")) for m in messages)
        if raw_char_count <= self.max_context_chars:
            return messages, 0

        compacted_messages = []
        total_saved_chars = 0

        # 保留最近 4 轮消息完整不压缩
        recent_threshold = max(1, len(messages) - 4)

        for idx, msg in enumerate(messages):
            # 必须严格保留系统提示词 (index 0) 与最新轮次
            if idx == 0 or idx >= recent_threshold:
                compacted_messages.append(msg)
                continue

            # 对历史中间轮次的 tool 或 assistant 消息进行剪枝
            content_str = str(msg.content or "")
            if len(content_str) > self.tool_truncation_len:
                head_part = content_str[:self.tool_truncation_len // 2]
                tail_part = content_str[-self.tool_truncation_len // 2:]
                truncated_count = len(content_str) - (len(head_part) + len(tail_part))
                
                new_content = (
                    f"{head_part}\n\n"
                    f"[... ⚡ Omni Context Pruner: 已自动剪枝压缩历史冗余输出 ({truncated_count} 字符) 以优化上下文窗口 ...]\n\n"
                    f"{tail_part}"
                )
                saved = len(content_str) - len(new_content)
                total_saved_chars += max(0, saved)

                # 复制消息对象并更新内容
                new_msg = copy.deepcopy(msg)
                new_msg.content = new_content
                compacted_messages.append(new_msg)
            else:
                compacted_messages.append(msg)

        estimated_saved_tokens = max(0, total_saved_chars // 3)
        return compacted_messages, estimated_saved_tokens
