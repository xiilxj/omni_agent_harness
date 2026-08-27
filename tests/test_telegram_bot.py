"""
Unit Test for Telegram Bot Remote Control Bridge
"""

import pytest
from unittest.mock import AsyncMock, patch
from harness.bot.telegram_bot import TelegramBotBridge
from harness.core.config import load_config


@pytest.mark.asyncio
async def test_telegram_bot_auth_and_whitelist():
    """测试 Telegram Bot 白名单权限校验"""
    config = load_config()
    # 限制仅允许用户 1001 与 1002
    bot = TelegramBotBridge(token="TEST_TOKEN", allowed_users=[1001, 1002], config=config)
    
    assert bot.is_user_authorized(1001) is True
    assert bot.is_user_authorized(1002) is True
    assert bot.is_user_authorized(9999) is False

    # 空白名单允许所有人
    bot_open = TelegramBotBridge(token="TEST_TOKEN", allowed_users=[], config=config)
    assert bot_open.is_user_authorized(9999) is True


@pytest.mark.asyncio
async def test_telegram_bot_menus_and_callback_queries():
    """测试 Telegram Bot 模型、厂商与强度菜单及按钮回调"""
    config = load_config()
    bot = TelegramBotBridge(token="TEST_TOKEN", allowed_users=[1001], config=config)

    # Mock API 发送与回调应答
    bot._send_api = AsyncMock(return_value={"ok": True, "result": {"message_id": 42}})

    # 1. 测试 /start
    await bot.handle_start(chat_id=123, user_id=1001)
    bot._send_api.assert_called()
    last_call = bot._send_api.call_args[0]
    assert last_call[0] == "sendMessage"
    assert "Omni Agent Harness Pro" in last_call[1]["text"]
    assert "inline_keyboard" in last_call[1]["reply_markup"]

    # 2. 测试切换模型回调 query
    cb_update = {
        "callback_query": {
            "id": "query_01",
            "from": {"id": 1001},
            "data": "set_model:models/gemini-3.5-flash-lite",
            "message": {"chat": {"id": 123}, "message_id": 42}
        }
    }
    await bot.handle_update(cb_update)
    state = bot.get_user_state(1001)
    assert state["model"] == "models/gemini-3.5-flash-lite"
    assert state["provider"] == "gemini"

    # 3. 测试切换推理强度回调 query
    cb_effort = {
        "callback_query": {
            "id": "query_02",
            "from": {"id": 1001},
            "data": "set_effort:high",
            "message": {"chat": {"id": 123}, "message_id": 42}
        }
    }
    await bot.handle_update(cb_effort)
    assert state["reasoning_effort"] == "high"

    # 4. 测试未授权用户点击按钮拦截
    unauth_cb = {
        "callback_query": {
            "id": "query_03",
            "from": {"id": 8888},
            "data": "menu_model",
            "message": {"chat": {"id": 123}, "message_id": 42}
        }
    }
    await bot.handle_update(unauth_cb)
    last_call = bot._send_api.call_args[0]
    assert last_call[0] == "answerCallbackQuery"
    assert "权限不足" in last_call[1]["text"]


@pytest.mark.asyncio
async def test_telegram_bot_message_dispatch_and_execution():
    """测试 Telegram 文本指令接收与 Agent 任务派发"""
    config = load_config()
    bot = TelegramBotBridge(token="TEST_TOKEN", allowed_users=[1001], config=config)
    bot._send_api = AsyncMock(return_value={"ok": True, "result": {"message_id": 100}})

    # Mock OmniAgent
    with patch("harness.bot.telegram_bot.OmniAgent") as mock_agent_cls:
        mock_instance = AsyncMock()
        mock_instance.messages = []
        mock_instance.run_task.return_value = "这是 Telegram 远程执行完成的答案。"
        mock_agent_cls.return_value = mock_instance

        # 模拟收到用户任务消息
        msg_update = {
            "message": {
                "message_id": 1,
                "chat": {"id": 123},
                "from": {"id": 1001},
                "text": "帮我查看当前目录"
            }
        }
        await bot.handle_update(msg_update)
        
        # 等待后台任务执行完成
        if 1001 in bot.active_tasks:
            await bot.active_tasks[1001]

        # 验证是否成功调用 run_task 并发送最终结果
        mock_instance.run_task.assert_called_once()
        sent_texts = [call[0][1]["text"] for call in bot._send_api.call_args_list if call[0][0] == "sendMessage"]
        assert any("这是 Telegram 远程执行完成的答案。" in t for t in sent_texts)
