"""maibot-plugin-sdk 基础测试"""

# ruff: noqa: I001

from typing import Any, Literal, cast

import asyncio

import pytest

from maibot_sdk import (
    API,
    CONFIG_RELOAD_SCOPE_SELF,
    ON_MODEL_CONFIG_RELOAD,
    Action,
    Command,
    EventHandler,
    Field,
    HomeCard,
    HookHandler,
    LLMProvider,
    LLMProviderBase,
    MaiBotPlugin,
    MessageGateway,
    PluginConfigBase,
    PluginPaths,
    Tool,
    WorkflowStep,
)
from maibot_sdk.config import PluginConfigVersionError, generate_plugin_config_schema
from maibot_sdk.messages import MaiMessages
from maibot_sdk.types import (
    ActivationType,
    ComponentType,
    EventType,
    HookMode,
    HookOrder,
    ModifyFlag,
    ToolParameterInfo,
    ToolParamType,
)


class SamplePlugin(MaiBotPlugin):
    config_reload_subscriptions = {ON_MODEL_CONFIG_RELOAD}

    async def on_load(self) -> None:
        """处理插件加载。"""

        return None

    async def on_unload(self) -> None:
        """处理插件卸载。"""

        return None

    @Action("test_action", description="测试动作", activation_type=ActivationType.KEYWORD, activation_keywords=["你好"])
    async def handle_action(self, **kwargs: Any) -> tuple[bool, str]:
        """处理测试 Action。"""

        del kwargs
        return True, "ok"

    @API("test_api", description="测试 API", version="1", public=True)
    async def handle_api(self, **kwargs: Any) -> dict[str, bool]:
        """处理测试 API。"""

        del kwargs
        return {"ok": True}

    @Command("test_cmd", pattern=r"^/test")
    async def handle_cmd(self, **kwargs: Any) -> tuple[bool, str, int]:
        """处理测试命令。"""

        del kwargs
        return True, "done", 2

    @Tool(
        "test_tool",
        parameters=[ToolParameterInfo(name="q", param_type=ToolParamType.STRING)],
        core_tool=True,
        visibility="visible",
    )
    async def handle_tool(self, **kwargs: Any) -> str:
        """处理测试工具。"""

        del kwargs
        return "result"

    @EventHandler("test_event", event_type=EventType.ON_MESSAGE)
    async def handle_event(self, **kwargs: Any) -> None:
        """处理测试事件。"""

        del kwargs
        return None

    @HookHandler("demo.test_hook", name="test_hook", mode=HookMode.BLOCKING, order=HookOrder.NORMAL)
    async def handle_hook(self, **kwargs: Any) -> dict[str, str]:
        """处理测试 Hook。"""

        del kwargs
        return {"action": "continue"}

    @HomeCard(
        "status_card",
        title="状态卡片",
        content="**插件运行中**",
        link_url="/plugin-config?plugin=demo",
        link_label="打开配置",
        width="wide",
        order=20,
    )
    async def home_card_marker(self) -> None:
        """声明首页卡片。"""

        return None

    @LLMProvider("example.provider", name="Example Provider", description="测试 Provider")
    async def handle_llm_provider(self, operation: str, request: dict[str, Any]) -> dict[str, Any]:
        """处理测试 LLM Provider 请求。"""

        return {
            "content": f"{operation}:{request.get('prompt', '')}",
        }

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        """处理配置热重载事件。

        Args:
            scope: 配置作用域。
            config_data: 当前配置数据。
            version: 配置版本。
        """

        del scope
        del config_data
        del version


class DemoPluginSection(PluginConfigBase):
    """插件基础配置节。"""

    __ui_label__ = "插件设置"
    __ui_i18n__ = {
        "en_US": {
            "title": "Plugin Settings",
            "description": "Basic plugin settings.",
        }
    }

    config_version: str = Field(default="2.0.0", description="配置版本号")
    enabled: bool = Field(
        default=True,
        description="是否启用插件",
        json_schema_extra={
            "label": "启用插件",
            "hint": "关闭后插件不会执行主动功能。",
            "i18n": {
                "en_US": {
                    "label": "Enable plugin",
                    "hint": "When disabled, the plugin will not run proactive features.",
                },
                "ja_JP": {
                    "label": "プラグインを有効化",
                },
            },
        },
    )
    retry_count: int = Field(default=3, description="最大重试次数", ge=0)


class DemoFeatureSection(PluginConfigBase):
    """功能配置节。"""

    __ui_label__ = "功能设置"

    endpoint: str = Field(default="https://example.com", description="目标地址")
    tags: list[str] = Field(default_factory=lambda: ["demo"], description="标签列表")


class DemoPluginConfig(PluginConfigBase):
    """演示插件配置。"""

    plugin: DemoPluginSection = Field(default_factory=DemoPluginSection)
    feature: DemoFeatureSection = Field(default_factory=DemoFeatureSection)


class DemoObjectItemConfig(PluginConfigBase):
    """对象列表项配置。"""

    name: str = Field(
        default="demo",
        description="名称",
        json_schema_extra={
            "label": "名称",
            "placeholder": "请输入名称",
            "i18n": {
                "en_US": {
                    "label": "Name",
                    "placeholder": "Enter a name",
                }
            },
        },
    )


class DemoListPluginConfig(PluginConfigBase):
    """对象列表配置。"""

    items: list[DemoObjectItemConfig] = Field(default_factory=list)


class DemoMultiSelectItemConfig(PluginConfigBase):
    """带多选字段的对象列表项配置。"""

    push_format: list[Literal["image", "text"]] = Field(
        default_factory=list,
        description="推送格式",
        json_schema_extra={
            "label": "推送格式",
        },
    )


class DemoMultiSelectPluginConfig(PluginConfigBase):
    """带多选字段的配置。"""

    push_format: list[Literal["image", "text"]] = Field(
        default_factory=list,
        description="推送格式",
        json_schema_extra={
            "label": "推送格式",
        },
    )
    items: list[DemoMultiSelectItemConfig] = Field(default_factory=list)


class ConfigurablePlugin(MaiBotPlugin):
    """用于验证配置模型能力的测试插件。"""

    config_model = DemoPluginConfig

    async def on_load(self) -> None:
        """处理插件加载。"""

        return None

    async def on_unload(self) -> None:
        """处理插件卸载。"""

        return None

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        """处理配置热重载事件。"""

        del scope
        del config_data
        del version


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
    assert "status_card" in names

    tool_component = next(component for component in components if component["name"] == "test_tool")
    assert tool_component["metadata"]["core_tool"] is True
    assert tool_component["metadata"]["visibility"] == "visible"
    assert "metadata" not in tool_component["metadata"]


def test_collect_llm_providers():
    plugin = SamplePlugin()
    providers = plugin.get_llm_providers()

    assert len(providers) == 1
    assert providers[0]["client_type"] == "example.provider"
    assert providers[0]["name"] == "Example Provider"
    assert providers[0]["metadata"]["handler_name"] == "handle_llm_provider"


def test_llm_provider_base_dispatch():
    class DemoProvider(LLMProviderBase):
        async def get_response(self, request: dict[str, Any]) -> dict[str, Any]:
            """生成测试响应。"""

            return {"content": str(request.get("prompt", ""))}

    async def main() -> dict[str, Any]:
        provider = DemoProvider()
        return await provider.dispatch("response", {"prompt": "hello"})

    result = asyncio.run(main())

    assert result["content"] == "hello"


def test_component_types():
    plugin = SamplePlugin()
    components = plugin.get_components()
    component_map = {c["name"]: c for c in components}
    assert component_map["test_action"]["type"] == ComponentType.TOOL.value
    action_metadata = component_map["test_action"]["metadata"]
    assert action_metadata["legacy_action"] is True
    assert action_metadata["legacy_component_type"] == ComponentType.ACTION.value
    assert component_map["test_api"]["type"] == ComponentType.API.value
    assert component_map["test_cmd"]["type"] == ComponentType.COMMAND.value
    assert component_map["test_tool"]["type"] == ComponentType.TOOL.value
    assert component_map["test_event"]["type"] == ComponentType.EVENT_HANDLER.value
    assert component_map["test_hook"]["type"] == ComponentType.HOOK_HANDLER.value
    assert component_map["status_card"]["type"] == ComponentType.HOME_CARD.value
    assert component_map["status_card"]["metadata"]["title"] == "状态卡片"
    assert component_map["status_card"]["metadata"]["content"] == "**插件运行中**"
    assert component_map["status_card"]["metadata"]["link_url"] == "/plugin-config?plugin=demo"
    assert component_map["status_card"]["metadata"]["width"] == "wide"


def test_hook_handler_metadata():
    """HookHandler 应输出新的命名 Hook 元数据。"""

    plugin = SamplePlugin()
    components = plugin.get_components()
    hook_component = next(component for component in components if component["name"] == "test_hook")

    assert hook_component["metadata"]["hook"] == "demo.test_hook"
    assert hook_component["metadata"]["mode"] == HookMode.BLOCKING
    assert hook_component["metadata"]["order"] == HookOrder.NORMAL
    assert (
        getattr(hook_component["metadata"]["error_policy"], "value", hook_component["metadata"]["error_policy"])
        == "skip"
    )


def test_workflow_step_is_a_breaking_change():
    with pytest.raises(RuntimeError, match="HookHandler"):
        WorkflowStep("legacy_hook")


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
        "render",
        "knowledge",
        "tool",
        "statistics",
        "paths",
        "logger",
    ]
    for attr in expected:
        assert hasattr(ctx, attr), f"PluginContext 缺少能力代理: {attr}"

    # logger 应返回标准 logging.Logger 实例
    import logging

    assert isinstance(ctx.logger, logging.Logger)
    assert ctx.logger.name == "plugin.__test__"


def test_context_accepts_runtime_paths(tmp_path):
    """PluginContext 应暴露 Runner 授予的标准插件路径。"""
    from maibot_sdk.context import PluginContext

    paths = PluginPaths(
        data_dir=tmp_path / "data" / "plugins" / "demo.plugin",
        runtime_dir=tmp_path / "temp" / "plugins" / "demo.plugin",
    )
    ctx = PluginContext(plugin_id="demo.plugin", rpc_call=None, paths=paths)

    assert ctx.paths is paths
    assert ctx.paths.data_dir == paths.data_dir
    assert ctx.paths.runtime_dir == paths.runtime_dir


def test_plugin_default_config_generation() -> None:
    """声明了配置模型的插件应能生成默认配置。"""

    plugin = ConfigurablePlugin()

    assert plugin.get_default_config() == {
        "plugin": {"config_version": "2.0.0", "enabled": True, "retry_count": 3},
        "feature": {"endpoint": "https://example.com", "tags": ["demo"]},
    }


def test_plugin_config_schema_generation() -> None:
    """插件应能基于配置模型生成 WebUI Schema。"""

    plugin = ConfigurablePlugin()
    schema = plugin.get_webui_config_schema(
        plugin_id="demo.plugin",
        plugin_name="演示插件",
        plugin_version="1.2.3",
        plugin_description="用于测试 Schema 生成",
        plugin_author="MaiBot",
    )

    assert schema["plugin_id"] == "demo.plugin"
    assert schema["plugin_info"]["name"] == "演示插件"
    assert schema["sections"]["plugin"]["fields"]["enabled"]["type"] == "boolean"
    assert schema["sections"]["plugin"]["i18n"]["en_US"]["title"] == "Plugin Settings"
    assert schema["sections"]["plugin"]["fields"]["enabled"]["label"] == "启用插件"
    assert schema["sections"]["plugin"]["fields"]["enabled"]["hint"] == "关闭后插件不会执行主动功能。"
    assert schema["sections"]["plugin"]["fields"]["enabled"]["i18n"]["en_US"]["label"] == "Enable plugin"
    assert (
        schema["sections"]["plugin"]["fields"]["enabled"]["i18n"]["en_US"]["hint"]
        == "When disabled, the plugin will not run proactive features."
    )
    assert schema["sections"]["plugin"]["fields"]["enabled"]["i18n"]["ja_JP"]["label"] == "プラグインを有効化"
    assert schema["sections"]["feature"]["fields"]["tags"]["type"] == "array"


def test_plugin_config_schema_generation_preserves_list_item_i18n() -> None:
    """对象列表子字段的 WebUI 多语言元数据应保留。"""

    generated_schema = ConfigurablePlugin.build_config_schema()
    assert generated_schema["sections"]["plugin"]["fields"]["enabled"]["i18n"]["en_US"]["label"] == "Enable plugin"

    list_schema = generate_plugin_config_schema(
        DemoListPluginConfig,
        plugin_id="demo.list",
    )
    item_field = list_schema["sections"]["general"]["fields"]["items"]["item_fields"]["name"]
    assert item_field["label"] == "名称"
    assert item_field["placeholder"] == "请输入名称"
    assert item_field["i18n"]["en_US"]["label"] == "Name"
    assert item_field["i18n"]["en_US"]["placeholder"] == "Enter a name"


def test_plugin_config_schema_generation_supports_list_literal_multiselect() -> None:
    """list[Literal[...]] 应生成带 multiple 的 select 字段。"""

    schema = generate_plugin_config_schema(
        DemoMultiSelectPluginConfig,
        plugin_id="demo.multiselect",
    )

    field_schema = schema["sections"]["general"]["fields"]["push_format"]
    assert field_schema["type"] == "select"
    assert field_schema["choices"] == ["image", "text"]
    assert field_schema["multiple"] is True
    assert field_schema["default"] == []


def test_plugin_config_schema_generation_supports_list_literal_in_object_items() -> None:
    """对象数组子字段中的 list[Literal[...]] 应生成带 multiple 的 select 字段。"""

    schema = generate_plugin_config_schema(
        DemoMultiSelectPluginConfig,
        plugin_id="demo.multiselect",
    )

    item_field = schema["sections"]["general"]["fields"]["items"]["item_fields"]["push_format"]
    assert item_field["type"] == "select"
    assert item_field["choices"] == ["image", "text"]
    assert item_field["multiple"] is True
    assert item_field["default"] == []


def test_plugin_set_config_builds_typed_model() -> None:
    """设置配置后，插件应能暴露强类型配置对象。"""

    plugin = ConfigurablePlugin()
    plugin.set_plugin_config(
        {
            "plugin": {"config_version": "2.0.0", "enabled": False},
            "feature": {"endpoint": "https://maibot.io"},
        }
    )

    config = cast(DemoPluginConfig, plugin.config)
    assert config.plugin.config_version == "2.0.0"
    assert config.plugin.enabled is False
    assert config.plugin.retry_count == 3
    assert config.feature.endpoint == "https://maibot.io"
    assert config.feature.tags == ["demo"]


def test_plugin_set_config_requires_version() -> None:
    """声明式插件配置在存在内容时必须提供版本号。"""

    plugin = ConfigurablePlugin()

    with pytest.raises(PluginConfigVersionError, match="config_version"):
        plugin.set_plugin_config({"plugin": {"enabled": False}, "feature": {"endpoint": "https://maibot.io"}})


class SampleGatewayPlugin(MaiBotPlugin):
    """用于验证消息网关组件收集的测试插件。"""

    async def on_load(self) -> None:
        """处理插件加载。"""

        return None

    async def on_unload(self) -> None:
        """处理插件卸载。"""

        return None

    @MessageGateway(route_type="send", platform="qq")
    async def outbound(self, **kwargs: Any) -> dict[str, Any]:
        """示例出站网关。"""

        return kwargs

    @MessageGateway(route_type="receive")
    async def inbound(self, **kwargs: Any) -> dict[str, Any]:
        """示例入站网关。"""

        return kwargs

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        """处理配置热重载事件。"""

        del scope
        del config_data
        del version


def test_collect_message_gateway_components() -> None:
    """消息网关装饰器应被收集为标准组件声明。"""

    plugin = SampleGatewayPlugin()
    components = plugin.get_components()
    gateway_components = {
        component["name"]: component for component in components if component["type"] == "MESSAGE_GATEWAY"
    }

    assert gateway_components["outbound"]["metadata"]["route_type"] == "send"
    assert gateway_components["outbound"]["metadata"]["platform"] == "qq"
    assert gateway_components["inbound"]["metadata"]["route_type"] == "receive"


def test_collect_api_components() -> None:
    """API 装饰器应被收集为标准组件声明。"""

    plugin = SamplePlugin()
    components = plugin.get_components()
    api_components = {component["name"]: component for component in components if component["type"] == "API"}

    assert api_components["test_api"]["metadata"]["version"] == "1"
    assert api_components["test_api"]["metadata"]["public"] is True
    assert api_components["test_api"]["metadata"]["handler_name"] == "handle_api"


def test_collect_config_reload_subscriptions() -> None:
    """插件应能声明全局配置热重载订阅。"""

    plugin = SamplePlugin()

    assert plugin.get_config_reload_subscriptions() == [ON_MODEL_CONFIG_RELOAD]


@pytest.mark.asyncio
async def test_on_config_update_can_distinguish_scope() -> None:
    """插件可通过 scope 区分自配置与全局配置热重载。"""

    plugin = SamplePlugin()

    await plugin.on_config_update(CONFIG_RELOAD_SCOPE_SELF, {}, "")


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
    from maibot_sdk.capabilities.render import RenderCapability
    from maibot_sdk.capabilities.send import SendCapability
    from maibot_sdk.capabilities.statistics import StatisticsCapability
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
            RenderCapability,
            SendCapability,
            StatisticsCapability,
            ToolCapability,
        ]
    )


def test_version():
    import maibot_sdk

    assert maibot_sdk.__version__ == "2.7.1"


def test_llm_generate_omits_unset_generation_options():
    """省略生成参数时由 Host 使用模型配置。"""
    from maibot_sdk.context import PluginContext

    captured: list[tuple[str, dict[str, Any]]] = []

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        assert payload is not None
        captured.append((payload["capability"], dict(payload["args"])))
        return {"success": True, "response": "ok", "reasoning": "", "model_name": "m"}

    async def main() -> None:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        await ctx.llm.generate("hello", model="utils")
        await ctx.llm.generate("hello", model="utils", temperature=0.4, max_tokens=4096)
        await ctx.llm.generate_with_tools("hello", tools=[], model="utils")
        await ctx.llm.generate_with_tools("hello", tools=[], model="utils", temperature=0.4, max_tokens=4096)

    asyncio.run(main())

    assert captured[0] == (
        "llm.generate",
        {"prompt": "hello", "model": "utils"},
    )
    assert captured[1] == (
        "llm.generate",
        {"prompt": "hello", "model": "utils", "temperature": 0.4, "max_tokens": 4096},
    )
    assert captured[2] == (
        "llm.generate_with_tools",
        {"prompt": "hello", "tools": [], "model": "utils"},
    )
    assert captured[3] == (
        "llm.generate_with_tools",
        {"prompt": "hello", "tools": [], "model": "utils", "temperature": 0.4, "max_tokens": 4096},
    )


def test_llm_transcribe_audio_encodes_bytes():
    """ASR 便捷方法应支持直接传入音频字节。"""
    from maibot_sdk.context import PluginContext

    captured: list[tuple[str, dict[str, Any]]] = []

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        assert payload is not None
        captured.append((payload["capability"], dict(payload["args"])))
        return {"success": True, "text": "转写结果", "content": "转写结果"}

    async def main() -> None:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        result = await ctx.llm.transcribe_audio(b"voice-bytes")
        assert result["text"] == "转写结果"

    asyncio.run(main())

    assert captured == [
        (
            "llm.transcribe_audio",
            {
                "audio_base64": "dm9pY2UtYnl0ZXM=",
                "task_name": "voice",
                "model": "",
                "model_name": "",
            },
        )
    ]


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


def test_component_capability_forwards_api_version():
    """组件启停能力应透传 API 版本参数。"""
    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        assert payload is not None
        captured.update(payload["args"])
        return {"success": True}

    async def main() -> None:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        await ctx.component.disable_component("demo.test_api", "api", version="2")

    asyncio.run(main())

    assert captured["component_type"] == "API"
    assert captured["version"] == "2"


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


def test_render_capability_unwraps_result() -> None:
    """ctx.render.html2png 应自动解包 Host 返回的 result 字段。"""

    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        assert payload is not None
        captured.update(payload["args"])
        return {
            "success": True,
            "result": {
                "image_base64": "abc",
                "mime_type": "image/png",
                "width": 100,
                "height": 200,
            },
        }

    async def main() -> dict[str, object]:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        return await ctx.render.html2png(
            "<body><div id='card'>hello</div></body>",
            selector="#card",
            viewport={"width": 1200, "height": 800},
            device_scale_factor=1.5,
            allow_network=True,
        )

    result = asyncio.run(main())

    assert result == {
        "image_base64": "abc",
        "mime_type": "image/png",
        "width": 100,
        "height": 200,
    }
    assert captured["selector"] == "#card"
    assert captured["viewport"] == {"width": 1200, "height": 800}
    assert captured["device_scale_factor"] == 1.5
    assert captured["allow_network"] is True


def test_statistics_capability_forwards_arguments_and_unwraps_results() -> None:
    """ctx.statistics.local 应转发本机统计参数并自动解包 Host 返回字段。"""

    from maibot_sdk.context import PluginContext

    captured: list[tuple[str, dict[str, object]]] = []

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        assert method == "cap.call"
        assert plugin_id == "demo"
        assert payload is not None
        capability = payload["capability"]
        captured.append((capability, dict(payload["args"])))
        return {
            "statistics.local.models": {"success": True, "models": [{"model_name": "model-a"}]},
            "statistics.local.model_trend": {"success": True, "series": {"timestamps": ["2026-06-25"]}},
            "statistics.local.token_trend": {"success": True, "series": {"total": 10}},
            "statistics.local.token_distribution": {"success": True, "distribution": {"total": 10}},
            "statistics.local.message_trend": {"success": True, "series": {"total": 3}},
            "statistics.local.tool_trend": {"success": True, "series": {"total": 2}},
            "statistics.local.online_time_trend": {"success": True, "series": {"total": 1.5}},
        }[capability]

    async def main() -> dict[str, object]:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        return {
            "models": await ctx.statistics.local.models(days=7, limit=5),
            "model_trend": await ctx.statistics.local.model_trend(days=7, bucket="hour", top_models=5),
            "token_trend": await ctx.statistics.local.token_trend(days=7, group_by="model", top_items=5),
            "token_distribution": await ctx.statistics.local.token_distribution(days=7, group_by="model", top_items=5),
            "message_trend": await ctx.statistics.local.message_trend(days=7, top_chats=5),
            "tool_trend": await ctx.statistics.local.tool_trend(days=7, top_tools=5),
            "online_time_trend": await ctx.statistics.local.online_time_trend(days=7),
        }

    result = asyncio.run(main())

    assert result == {
        "models": [{"model_name": "model-a"}],
        "model_trend": {"timestamps": ["2026-06-25"]},
        "token_trend": {"total": 10},
        "token_distribution": {"total": 10},
        "message_trend": {"total": 3},
        "tool_trend": {"total": 2},
        "online_time_trend": {"total": 1.5},
    }
    assert captured == [
        ("statistics.local.models", {"days": 7, "limit": 5}),
        (
            "statistics.local.model_trend",
            {"days": 7, "bucket": "hour", "top_models": 5, "metric": "token", "module_name": ""},
        ),
        ("statistics.local.token_trend", {"days": 7, "bucket": "day", "group_by": "model", "top_items": 5}),
        ("statistics.local.token_distribution", {"days": 7, "group_by": "model", "top_items": 5}),
        ("statistics.local.message_trend", {"days": 7, "bucket": "day", "top_chats": 5}),
        ("statistics.local.tool_trend", {"days": 7, "bucket": "day", "top_tools": 5}),
        ("statistics.local.online_time_trend", {"days": 7, "bucket": "day"}),
    ]


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


def test_emoji_delete_forwards_keep_desc_argument():
    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}

    async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
        captured["method"] = method
        captured["plugin_id"] = plugin_id
        captured["payload"] = payload
        return {"success": True, "hash": "hash-demo", "keep_desc": False}

    async def main() -> object:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        return await ctx.emoji.delete_emoji("hash-demo", keep_desc=False)

    result = asyncio.run(main())

    assert result["keep_desc"] is False
    assert captured["method"] == "cap.call"
    assert captured["payload"] == {
        "capability": "emoji.delete",
        "args": {"emoji_hash": "hash-demo", "keep_desc": False},
    }


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


def test_context_blocks_internal_host_methods() -> None:
    """插件不应直接调用 Host 内部 RPC。"""
    from maibot_sdk.context import PluginContext

    async def fake_rpc_call(
        method: str,
        plugin_id: str = "",
        payload: dict[str, object] | None = None,
    ) -> dict[str, bool]:
        raise AssertionError(f"不应真正发起 RPC: {method} {plugin_id} {payload}")

    async def main() -> None:
        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        with pytest.raises(PermissionError, match="plugin.bootstrap"):
            await ctx.call_host_method("plugin.bootstrap")

    asyncio.run(main())


def test_call_capability_forwards_rpc_timeout_separately() -> None:
    """timeout_ms 应作为 RPC 超时传递，而不是进入能力参数。"""
    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}

    async def fake_rpc_call(
        method: str,
        plugin_id: str = "",
        payload: dict[str, object] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, object]:
        """捕获能力调用的 RPC 超时和业务载荷。"""

        captured["method"] = method
        captured["plugin_id"] = plugin_id
        captured["payload"] = payload
        captured["timeout_ms"] = timeout_ms
        return {"success": True, "value": "ok"}

    async def main() -> object:
        """发起一次带自定义 RPC 超时的能力调用。"""

        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        return await ctx.call_capability("config.get", key="name", timeout_ms=42000)

    assert asyncio.run(main()) == "ok"
    assert captured["method"] == "cap.call"
    assert captured["plugin_id"] == "demo"
    assert captured["timeout_ms"] == 42000
    assert captured["payload"] == {
        "capability": "config.get",
        "args": {"key": "name"},
    }


def test_render_timeout_uses_render_timeout_ms_argument() -> None:
    """render.html2png 的 render_timeout_ms 应作为渲染参数传给 Host。"""
    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}

    async def fake_rpc_call(
        method: str,
        plugin_id: str = "",
        payload: dict[str, object] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, object]:
        """捕获渲染能力调用。"""

        captured["method"] = method
        captured["plugin_id"] = plugin_id
        captured["payload"] = payload
        captured["timeout_ms"] = timeout_ms
        return {"success": True, "result": {"image_base64": "ok"}}

    async def main() -> object:
        """发起一次带业务超时的渲染调用。"""

        ctx = PluginContext(plugin_id="demo", rpc_call=fake_rpc_call)
        return await ctx.render.html2png("<div>ok</div>", render_timeout_ms=12000)

    assert asyncio.run(main()) == {"image_base64": "ok"}
    assert captured["method"] == "cap.call"
    assert captured["plugin_id"] == "demo"
    assert captured["timeout_ms"] is None
    assert captured["payload"] is not None
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["capability"] == "render.html2png"
    args = payload["args"]
    assert isinstance(args, dict)
    assert args["render_timeout_ms"] == 12000


def test_dynamic_api_helpers_can_sync_and_dispatch() -> None:
    """插件基类应能同步并分发动态 API。"""
    from maibot_sdk.context import PluginContext

    captured: dict[str, object] = {}
    plugin = SamplePlugin()

    async def fake_rpc_call(
        method: str,
        plugin_id: str = "",
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        assert method == "cap.call"
        assert plugin_id == "demo"
        assert payload is not None
        captured.update(payload["args"])
        return {"success": True, "count": 1, "offlined": 0}

    async def dynamic_handler(value: str) -> str:
        """测试动态 API 处理器。"""

        return f"echo:{value}"

    plugin._set_context(PluginContext(plugin_id="demo", rpc_call=fake_rpc_call))
    component = plugin.register_dynamic_api(
        "dynamic.echo",
        dynamic_handler,
        description="动态回显",
        version="2",
        public=True,
    )

    async def main() -> tuple[Any, bool]:
        result = await plugin.invoke_component(component["metadata"]["handler_name"], value="hello")
        synced = await plugin.sync_dynamic_apis(offline_reason="mcp server closed")
        return result, synced

    result, synced = asyncio.run(main())

    assert result == "echo:hello"
    assert synced is True
    assert captured["offline_reason"] == "mcp server closed"
    assert captured["apis"][0]["name"] == "dynamic.echo"
    assert captured["apis"][0]["metadata"]["version"] == "2"
