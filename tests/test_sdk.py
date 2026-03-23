"""maibot-plugin-sdk 基础测试"""

import asyncio

import pytest

from maibot_sdk import (
    API,
    Action,
    Command,
    EventHandler,
    HookHandler,
    MaiBotPlugin,
    MessageGateway,
    Tool,
    WorkflowStep,
)
from maibot_sdk.messages import MaiMessages
from maibot_sdk.types import (
    ActivationType,
    ComponentType,
    EventType,
    HookResult,
    ModifyFlag,
    ToolParameterInfo,
    ToolParamType,
    WorkflowStage,
)


class SamplePlugin(MaiBotPlugin):
    @Action("test_action", description="测试动作", activation_type=ActivationType.KEYWORD, activation_keywords=["你好"])
    async def handle_action(self, **kwargs):
        return True, "ok"

    @API("test_api", description="测试 API", version="1", public=True)
    async def handle_api(self, **kwargs):
        return {"ok": True}

    @Command("test_cmd", pattern=r"^/test")
    async def handle_cmd(self, **kwargs):
        return True, "done", 2

    @Tool("test_tool", parameters=[ToolParameterInfo(name="q", param_type=ToolParamType.STRING)])
    async def handle_tool(self, **kwargs):
        return "result"

    @EventHandler("test_event", event_type=EventType.ON_MESSAGE)
    async def handle_event(self, **kwargs):
        pass

    @HookHandler("test_hook", stage=WorkflowStage.INGRESS)
    async def handle_hook(self, **kwargs):
        return {"hook_result": HookResult.CONTINUE}


def test_plugin_instantiation():
    plugin = SamplePlugin()
    assert isinstance(plugin, MaiBotPlugin)


def test_collect_components():
    plugin = SamplePlugin()
    components = plugin.get_components()
    names = {c["name"] for c in components}
    assert "test_action" in names
    assert "test_api" in names
    assert "test_cmd" in names
    assert "test_tool" in names
    assert "test_event" in names
    assert "test_hook" in names


def test_component_types():
    plugin = SamplePlugin()
    components = plugin.get_components()
    type_map = {c["name"]: c["type"] for c in components}
    assert type_map["test_action"] == ComponentType.ACTION.value
    assert type_map["test_api"] == ComponentType.API.value
    assert type_map["test_cmd"] == ComponentType.COMMAND.value
    assert type_map["test_tool"] == ComponentType.TOOL.value
    assert type_map["test_event"] == ComponentType.EVENT_HANDLER.value
    assert type_map["test_hook"] == ComponentType.HOOK_HANDLER.value


def test_workflow_step_is_a_breaking_change():
    with pytest.raises(RuntimeError, match="HookHandler"):
        WorkflowStep("legacy_hook", stage=WorkflowStage.INGRESS)


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


def test_context_has_all_capabilities():
    """验证 PluginContext 暴露了全部能力代理和 logger 属性。"""
    from maibot_sdk.context import PluginContext

    ctx = PluginContext(plugin_id="__test__", rpc_call=None)

    expected = [
        "api",
        "gateway",
        "send",
        "db",
        "llm",
        "config",
        "emoji",
        "message",
        "frequency",
        "component",
        "chat",
        "person",
        "knowledge",
        "tool",
        "logger",
    ]
    for attr in expected:
        assert hasattr(ctx, attr), f"PluginContext 缺少能力代理: {attr}"

    # logger 应返回标准 logging.Logger 实例
    import logging

    assert isinstance(ctx.logger, logging.Logger)
    assert ctx.logger.name == "plugin.__test__"


class SampleGatewayPlugin(MaiBotPlugin):
    """用于验证消息网关组件收集的测试插件。"""

    @MessageGateway(route_type="send", platform="qq")
    async def outbound(self, **kwargs):
        """示例出站网关。"""

        return kwargs

    @MessageGateway(route_type="receive")
    async def inbound(self, **kwargs):
        """示例入站网关。"""

        return kwargs


def test_collect_message_gateway_components() -> None:
    """消息网关装饰器应被收集为标准组件声明。"""

    plugin = SampleGatewayPlugin()
    components = plugin.get_components()
    gateway_components = {
        component["name"]: component
        for component in components
        if component["type"] == "MESSAGE_GATEWAY"
    }

    assert gateway_components["outbound"]["metadata"]["route_type"] == "send"
    assert gateway_components["outbound"]["metadata"]["platform"] == "qq"
    assert gateway_components["inbound"]["metadata"]["route_type"] == "receive"


def test_collect_api_components() -> None:
    """API 装饰器应被收集为标准组件声明。"""

    plugin = SamplePlugin()
    components = plugin.get_components()
    api_components = {
        component["name"]: component
        for component in components
        if component["type"] == "API"
    }

    assert api_components["test_api"]["metadata"]["version"] == "1"
    assert api_components["test_api"]["metadata"]["public"] is True


def test_capability_classes_importable():
    """确保所有能力代理类可以正常 import"""
    from maibot_sdk.capabilities.api import APICapability
    from maibot_sdk.capabilities.chat import ChatCapability
    from maibot_sdk.capabilities.component import ComponentCapability
    from maibot_sdk.capabilities.config import ConfigCapability
    from maibot_sdk.capabilities.database import DatabaseCapability
    from maibot_sdk.capabilities.emoji import EmojiCapability
    from maibot_sdk.capabilities.frequency import FrequencyCapability
    from maibot_sdk.capabilities.gateway import GatewayCapability
    from maibot_sdk.capabilities.knowledge import KnowledgeCapability
    from maibot_sdk.capabilities.llm import LLMCapability
    from maibot_sdk.capabilities.message import MessageCapability
    from maibot_sdk.capabilities.person import PersonCapability
    from maibot_sdk.capabilities.send import SendCapability
    from maibot_sdk.capabilities.tool import ToolCapability

    # LoggingCapability 已移除，logging.py 模块仍可 import 但不再导出类

    assert all(
        [
            APICapability,
            ChatCapability,
            ComponentCapability,
            ConfigCapability,
            DatabaseCapability,
            EmojiCapability,
            FrequencyCapability,
            GatewayCapability,
            KnowledgeCapability,
            LLMCapability,
            MessageCapability,
            PersonCapability,
            SendCapability,
            ToolCapability,
        ]
    )


def test_version():
    import maibot_sdk

    assert maibot_sdk.__version__ == "2.0.1"


def test_component_capability_normalizes_lowercase_component_type():
    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        assert payload is not None
        captured.update(payload["args"])
        return {"success": True}

    async def main() -> None:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        await ctx.component.enable_component("demo.test", "event_handler")

    asyncio.run(main())

    assert captured["component_type"] == "EVENT_HANDLER"


def test_component_capability_rejects_workflow_step_name():
    from maibot_sdk.context import PluginContext

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        raise AssertionError("workflow_step 不应继续发起 RPC")

    async def main() -> None:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        with pytest.raises(ValueError, match="HookHandler"):
            await ctx.component.disable_component("demo.legacy", "workflow_step")

    asyncio.run(main())


def test_database_count_unwraps_host_dict_result():
    from maibot_sdk.context import PluginContext

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        assert payload is not None
        assert payload["capability"] == "database.count"
        return {"success": True, "count": 3}

    async def main() -> int:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        return await ctx.db.count("SomeTable")

    assert asyncio.run(main()) == 3


def test_database_query_uses_model_name_signature():
    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        assert payload is not None
        captured.update(payload["args"])
        return {"success": True, "result": []}

    async def main() -> None:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        await ctx.db.query(
            model_name="ChatHistory",
            query_type="update",
            data={"summary": "ok"},
            filters={"session_id": "s-1"},
            order_by=["-start_timestamp"],
            limit=5,
            single_result=False,
        )

    asyncio.run(main())

    assert captured == {
        "model_name": "ChatHistory",
        "query_type": "update",
        "data": {"summary": "ok"},
        "filters": {"session_id": "s-1"},
        "order_by": ["-start_timestamp"],
        "limit": 5,
        "single_result": False,
    }


def test_database_get_uses_filters_signature():
    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        assert payload is not None
        captured.update(payload["args"])
        return {"success": True, "result": None}

    async def main() -> None:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        await ctx.db.get(
            model_name="ActionRecord",
            filters={"action_id": "a-1"},
            limit=1,
            order_by="-timestamp",
            single_result=True,
        )

    asyncio.run(main())

    assert captured == {
        "model_name": "ActionRecord",
        "filters": {"action_id": "a-1"},
        "limit": 1,
        "order_by": "-timestamp",
        "single_result": True,
    }


def test_send_custom_sends_compat_field_aliases():
    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        assert payload is not None
        captured.update(payload["args"])
        return payload

    async def main() -> None:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        await ctx.send.custom("notice", {"x": 1}, "stream-1")

    asyncio.run(main())

    assert captured["custom_type"] == "notice"
    assert captured["data"] == {"x": 1}
    assert captured["message_type"] == "notice"
    assert captured["content"] == {"x": 1}


def test_chat_capability_passes_platform_argument():
    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        assert payload is not None
        captured.update(payload["args"])
        return {"success": True, "streams": []}

    async def main() -> None:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        await ctx.chat.get_group_streams(platform="discord")

    asyncio.run(main())
    assert captured["platform"] == "discord"


def test_llm_result_normalizes_model_alias():
    from maibot_sdk.context import PluginContext

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        return {
            "success": True,
            "response": "ok",
            "reasoning": "",
            "model_name": "gpt-like",
        }

    async def main() -> dict[str, object]:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        return await ctx.llm.generate("hello")

    result = asyncio.run(main())
    assert result["model"] == "gpt-like"
    assert result["model_name"] == "gpt-like"


def test_capabilities_unwrap_host_wrapper_results():
    from maibot_sdk.context import PluginContext

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        assert payload is not None
        capability = payload["capability"]
        return {
            "config.get": {"success": True, "value": 42},
            "chat.get_all_streams": {"success": True, "streams": [{"session_id": "s1"}]},
            "message.get_by_time": {"success": True, "messages": [{"id": 1}]},
            "person.get_id": {"success": True, "person_id": "person-1"},
            "frequency.get_current_talk_value": {"success": True, "value": 0.75},
            "tool.get_definitions": {"success": True, "tools": [{"name": "demo"}]},
            "send.text": {"success": True},
        }[capability]

    async def main() -> dict[str, object]:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        return {
            "config": await ctx.config.get("answer"),
            "streams": await ctx.chat.get_all_streams(),
            "messages": await ctx.message.get_by_time("1", "2"),
            "person_id": await ctx.person.get_id("qq", "123"),
            "talk_value": await ctx.frequency.get_current_talk_value("chat-1"),
            "tools": await ctx.tool.get_definitions(),
            "send_ok": await ctx.send.text("hello", "stream-1"),
        }

    result = asyncio.run(main())

    assert result["config"] == 42
    assert result["streams"] == [{"session_id": "s1"}]
    assert result["messages"] == [{"id": 1}]
    assert result["person_id"] == "person-1"
    assert result["talk_value"] == 0.75
    assert result["tools"] == [{"name": "demo"}]
    assert result["send_ok"] is True


def test_gateway_capability_calls_host_route_message():
    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "host.route_message"
        assert plugin_id == "demo"
        assert payload is not None
        captured.update(payload)
        return {"accepted": True}

    async def main() -> bool:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        return await ctx.gateway.route_message(
            gateway_name="napcat_gateway",
            message={
                "message_id": "msg-1",
                "platform": "qq",
                "message_info": {
                    "user_info": {"user_id": "u1", "user_nickname": "tester"},
                    "group_info": {"group_id": "g1", "group_name": "group"},
                    "additional_config": {},
                },
                "raw_message": [],
            },
            route_metadata={"self_id": "10001"},
            external_message_id="external-1",
            dedupe_key="dedupe-1",
        )

    assert asyncio.run(main()) is True
    assert captured["gateway_name"] == "napcat_gateway"
    assert captured["route_metadata"] == {"self_id": "10001"}
    assert captured["external_message_id"] == "external-1"
    assert captured["dedupe_key"] == "dedupe-1"


def test_gateway_capability_calls_host_update_state() -> None:
    """验证消息网关能力代理可以上报运行时状态。"""
    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}

    async def fake_rpc_call(
        method: str,
        plugin_id: str = "",
        payload: dict[str, object] | None = None,
    ) -> dict[str, bool]:
        """模拟 Host RPC 调用并捕获上报载荷。"""
        assert method == "host.update_message_gateway_state"
        assert plugin_id == "demo"
        assert payload is not None
        captured.update(payload)
        return {"accepted": True}

    async def main() -> bool:
        """执行一次消息网关状态上报调用。"""
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        return await ctx.gateway.update_state(
            gateway_name="napcat_gateway",
            ready=True,
            platform="qq",
            account_id="10001",
            scope="primary",
            metadata={"ws_url": "ws://127.0.0.1:3001"},
        )

    assert asyncio.run(main()) is True
    assert captured["gateway_name"] == "napcat_gateway"
    assert captured["ready"] is True
    assert captured["platform"] == "qq"
    assert captured["account_id"] == "10001"
    assert captured["scope"] == "primary"
    assert captured["metadata"] == {"ws_url": "ws://127.0.0.1:3001"}
