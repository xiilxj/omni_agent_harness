import pytest
from harness.core.slash_commands import parse_and_transform_slash_command, SLASH_COMMANDS_REGISTRY
from harness.core.config import load_config
from harness.core.agent import OmniAgent
from harness.core.models import LLMResponse, UsageStats


def test_slash_command_parsing():
    # 1. /goal 测试
    transformed, cmd, meta = parse_and_transform_slash_command("/goal 优化所有接口并发性能")
    assert cmd == "goal"
    assert "LONG-RUNNING GOAL DIRECTIVE" in transformed
    assert "优化所有接口并发性能" in transformed

    # 2. /grill-me 测试
    transformed, cmd, meta = parse_and_transform_slash_command("/grill-me 限流算法设计方案")
    assert cmd == "grill-me"
    assert "GRILL-ME INTERVIEW" in transformed
    assert "限流算法设计方案" in transformed

    # 3. /schedule 测试
    transformed, cmd, meta = parse_and_transform_slash_command("/schedule 300 检查服务")
    assert cmd == "schedule"
    assert "SCHEDULE BACKGROUND TASK DIRECTIVE" in transformed

    # 4. /browser 测试
    transformed, cmd, meta = parse_and_transform_slash_command("/browser https://example.com")
    assert cmd == "browser"
    assert "BROWSER RECON & AUTOMATION DIRECTIVE" in transformed

    # 5. /learn 测试
    transformed, cmd, meta = parse_and_transform_slash_command("/learn 测试经验规则")
    assert cmd == "learn"
    assert "LEARNED EXPERIENCE PERSISTED" in transformed

    # 6. /help 测试
    transformed, cmd, meta = parse_and_transform_slash_command("/help")
    assert cmd == "help"
    assert "SYSTEM HELP REQUEST" in transformed


def test_agent_abort_and_steer_mechanisms():
    config = load_config()
    agent = OmniAgent(config=config)

    # 初始状态
    assert agent._abort_requested is False
    assert len(agent._steer_queue) == 0

    # 穿插消息注入
    agent.steer_message("请先停下当前步骤，改用轻量级算法")
    assert len(agent._steer_queue) == 1
    assert agent._steer_queue[0] == "请先停下当前步骤，改用轻量级算法"

    # 急停打断
    agent.request_abort()
    assert agent._abort_requested is True

    # 重置
    agent.reset_conversation()
    assert agent._abort_requested is False
    assert len(agent._steer_queue) == 0
