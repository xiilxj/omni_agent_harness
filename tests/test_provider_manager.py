import pytest
import os
import tempfile
from pathlib import Path
from harness.providers.manager import ProviderManager, mask_key, BUILTIN_PROVIDER_TEMPLATES
from harness.providers.router import ProviderRouter
from harness.core.config import AppConfig


def test_mask_key():
    assert mask_key("") == "未配置"
    assert mask_key("EMPTY") == "未配置"
    assert mask_key("short") == "******"
    assert mask_key("AQ.MOCK_SAMPLE_KEY_1234567890_TEST") == "AQ.M...TEST"
    assert mask_key("sk-1234567890abcdef") == "sk-1...cdef"


def test_provider_manager_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mgr = ProviderManager(config_dir=tmp_path, env_file=tmp_path / ".env")

        # 1. 验证内置厂商列表已初始化
        providers = mgr.list_providers()
        assert len(providers) >= 6
        provider_ids = [p["id"] for p in providers]
        assert "deepseek" in provider_ids
        assert "gemini" in provider_ids
        assert "openai" in provider_ids

        # 2. 新增自定义厂商，不影响其他厂商
        saved = mgr.save_provider(
            provider_id="my_proxy",
            name="My Custom Proxy",
            base_url="https://api.myproxy.com/v1",
            api_key="sk-test-secret-key-123456",
            models=["gpt-4o-custom", "claude-custom"],
            default_model="gpt-4o-custom"
        )
        assert saved["id"] == "my_proxy"
        assert saved["name"] == "My Custom Proxy"

        # 3. 验证独立并存
        p_info = mgr.get_provider_info("my_proxy")
        assert p_info is not None
        assert p_info["base_url"] == "https://api.myproxy.com/v1"
        assert "gpt-4o-custom" in p_info["models"]

        deepseek_info = mgr.get_provider_info("deepseek")
        assert deepseek_info["base_url"] == "https://api.deepseek.com/v1"

        # 4. 切换激活状态
        assert mgr.set_active_provider("gemini") is True
        assert mgr.get_active_provider_id() == "gemini"

        # 5. 更新 Gemini 配置，验证不覆盖其他厂商
        mgr.save_provider(
            provider_id="gemini",
            name="Google Gemini 官方",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key="AQ.MOCK_SAMPLE_KEY_ABCDEF1234_TEST",
            models=["gemini-2.5-pro", "gemini-2.5-flash"],
            default_model="gemini-2.5-pro"
        )

        gemini_p = mgr.get_provider_info("gemini")
        assert gemini_p["models"] == ["gemini-2.5-pro", "gemini-2.5-flash"]
        assert gemini_p["default_model"] == "gemini-2.5-pro"

        # 验证 DeepSeek 仍然完好无损
        deepseek_p = mgr.get_provider_info("deepseek")
        assert "deepseek-chat" in deepseek_p["models"]

        # 6. 删除自定义厂商
        assert mgr.delete_provider("my_proxy") is True
        assert mgr.get_provider_info("my_proxy") is None


def test_provider_router_dynamic_switch(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AQ.TESTKEY1234567890")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mgr = ProviderManager(config_dir=tmp_path, env_file=tmp_path / ".env")
        mgr.save_provider(
            provider_id="gemini",
            name="Google Gemini",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            models=["gemini-2.5-flash", "gemini-2.5-pro"]
        )

        app_config = AppConfig()
        router = ProviderRouter(config=app_config)

        # 获取 deepseek provider
        ds_provider = router.get_provider("deepseek")
        assert ds_provider.name == "deepseek"
        assert "deepseek.com" in ds_provider.base_url

        # 获取 gemini provider
        gemini_provider = router.get_provider("gemini")
        assert gemini_provider.name == "gemini"
        assert "generativelanguage.googleapis.com" in gemini_provider.base_url
        assert gemini_provider.name == "gemini"
        assert "generativelanguage.googleapis.com" in gemini_provider.base_url
