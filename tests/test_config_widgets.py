"""运行时控件必须与持久化配置隔离。"""

import pytest

from maibot_sdk import ConfigWidget, ConfigWidgetState, Field, MaiBotPlugin, PluginConfigBase


class Settings(PluginConfigBase):
    address: str = Field(default="localhost")


class Adapter(MaiBotPlugin):
    config_model = Settings
    config_widgets = [ConfigWidget(id="login", kind="qrcode", label="登录")]

    async def get_config_widget_state(self):
        return {"login": ConfigWidgetState(text="等待扫码", image="data:image/png;base64,AAAA")}


@pytest.mark.asyncio
async def test_runtime_values_never_enter_config():
    plugin = Adapter()
    defaults = plugin.get_default_config()
    schema = plugin.get_webui_config_schema(plugin_id="test.adapter")
    assert schema["runtime_widgets"][0]["id"] == "login"
    assert "login" not in schema["sections"].get("general", {}).get("fields", {})
    states = await plugin.get_config_widget_state()
    assert states["login"].image
    assert plugin.get_default_config() == defaults
    assert "runtime_widgets" not in defaults
    assert "login" not in defaults


def test_old_plugin_schema_unchanged():
    assert "runtime_widgets" not in MaiBotPlugin().get_webui_config_schema()


def test_widgets_without_config_model():
    class WidgetOnly(MaiBotPlugin):
        config_widgets = [ConfigWidget(id="status", kind="status", label="连接状态")]

    schema = WidgetOnly().get_webui_config_schema(plugin_id="widget.only")
    assert schema["sections"] == {}
    assert schema["runtime_widgets"][0]["kind"] == "status"
