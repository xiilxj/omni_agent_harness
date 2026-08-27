"""
Unit Test for Embedded Telegram Bot Lifecycle & Web API
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from harness.ui.app import create_app


def test_telegram_api_status_and_config():
    """测试 Web UI 嵌入的 Telegram 状态查询与配置热保存接口"""
    app = create_app()
    client = TestClient(app)

    # 1. 查询初始状态
    res = client.get("/api/telegram/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "running" in data
    assert "has_token" in data

    # 2. 模拟在 Web UI 保存 Telegram 配置
    with patch("harness.bot.telegram_bot.TelegramBotBridge.start_polling", new_callable=AsyncMock):
        save_res = client.post(
            "/api/telegram/config",
            json={
                "bot_token": "123456:TEST_MOCK_TOKEN_ABCDEF",
                "allowed_users": "1001, 1002"
            }
        )
        assert save_res.status_code == 200
        save_data = save_res.json()
        assert save_data["status"] == "success"

        # 再次获取状态，验证 token_masked 与 allowed_users
        st_res = client.get("/api/telegram/status")
        st_data = st_res.json()
        assert st_data["has_token"] is True
        assert "123456" in st_data["token_masked"]
        assert 1001 in st_data["allowed_users"]
        assert 1002 in st_data["allowed_users"]


def test_telegram_api_toggle():
    """测试 Telegram Bot 手动启停接口"""
    app = create_app()
    client = TestClient(app)

    with patch("harness.bot.telegram_bot.TelegramBotBridge.start_polling", new_callable=AsyncMock), \
         patch("harness.bot.telegram_bot.TelegramBotBridge.stop", new_callable=AsyncMock):
        
        # 停止
        stop_res = client.post("/api/telegram/toggle", json={"action": "stop"})
        assert stop_res.status_code == 200
        assert stop_res.json()["status"] == "success"

        # 启动
        start_res = client.post("/api/telegram/toggle", json={"action": "start"})
        assert start_res.status_code == 200
        assert start_res.json()["status"] == "success"
