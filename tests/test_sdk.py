"""maibot-plugin-sdk 基础测试"""

from maibot_sdk import Action, Command, EventHandler, MaiBotPlugin, Tool
from maibot_sdk.messages import MaiMessages
from maibot_sdk.types import (
    ActivationType,
    ComponentType,
    EventType,
    ModifyFlag,
    ToolParameterInfo,
    ToolParamType,
)


class SamplePlugin(MaiBotPlugin):
    @Action("test_action", description="测试动作", activation_type=ActivationType.KEYWORD, activation_keywords=["你好"])
    async def handle_action(self, **kwargs):
        return True, "ok"

    @Command("test_cmd", pattern=r"^/test")
    async def handle_cmd(self, **kwargs):
        return True, "done", 2

    @Tool("test_tool", parameters=[ToolParameterInfo(name="q", param_type=ToolParamType.STRING)])
    async def handle_tool(self, **kwargs):
        return "result"

    @EventHandler("test_event", event_type=EventType.ON_MESSAGE)
    async def handle_event(self, **kwargs):
        pass


def test_plugin_instantiation():
    plugin = SamplePlugin()
    assert isinstance(plugin, MaiBotPlugin)


def test_collect_components():
    plugin = SamplePlugin()
    components = plugin.get_components()
    names = {c["name"] for c in components}
    assert "test_action" in names
    assert "test_cmd" in names
    assert "test_tool" in names
    assert "test_event" in names


def test_component_types():
    plugin = SamplePlugin()
    components = plugin.get_components()
    type_map = {c["name"]: c["type"] for c in components}
    assert type_map["test_action"] == ComponentType.ACTION.value
    assert type_map["test_cmd"] == ComponentType.COMMAND.value
    assert type_map["test_tool"] == ComponentType.TOOL.value
    assert type_map["test_event"] == ComponentType.EVENT_HANDLER.value


def test_messages_modify():
    msg = MaiMessages(plain_text="原始文本")
    assert msg.can_modify(ModifyFlag.CAN_MODIFY_MESSAGE)
    assert msg.modify_plain_text("新文本")
    assert msg.plain_text == "新文本"


def test_messages_modify_blocked():
    msg = MaiMessages(plain_text="原始文本")
    msg.set_modify_flag(ModifyFlag.CAN_MODIFY_MESSAGE, False)
    assert not msg.modify_plain_text("新文本")
    assert msg.plain_text == "原始文本"


def test_messages_serialization():
    msg = MaiMessages(plain_text="test", stream_id="s1")
    data = msg.to_rpc_dict()
    restored = MaiMessages.from_rpc_dict(data)
    assert restored.plain_text == "test"
    assert restored.stream_id == "s1"


def test_context_raises_without_rpc():
    plugin = SamplePlugin()
    try:
        _ = plugin.ctx
        raise AssertionError("应该抛出 RuntimeError")
    except RuntimeError:
        pass


def test_version():
    import maibot_sdk

    assert maibot_sdk.__version__ == "1.0.0"
