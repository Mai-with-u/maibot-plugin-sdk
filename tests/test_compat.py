"""兼容层集成测试

验证 import hook、基类、API 模块等所有兼容层组件能正常工作。
"""

from __future__ import annotations

import asyncio
import importlib
import json
import logging
import sys
import types
import warnings
from pathlib import Path

import pytest

from maibot_sdk.compat._import_hook import install_hook, uninstall_hook

# ── 全局前置：安装 import hook ──────────────────────────────────────

install_hook()


def teardown_module(module) -> None:
    uninstall_hook()


# ── 旧版导入路径列表 ───────────────────────────────────────────────

OLD_IMPORTS = [
    "src.plugin_system",
    "src.plugin_system.base",
    "src.plugin_system.base.base_action",
    "src.plugin_system.base.base_command",
    "src.plugin_system.base.base_events_handler",
    "src.plugin_system.base.base_tool",
    "src.plugin_system.base.base_plugin",
    "src.plugin_system.base.component_types",
    "src.plugin_system.base.config_types",
    "src.plugin_system.base.service_types",
    "src.plugin_system.base.workflow_types",
    "src.plugin_system.base.workflow_errors",
    "src.plugin_system.apis",
    "src.plugin_system.apis.send_api",
    "src.plugin_system.apis.database_api",
    "src.plugin_system.apis.config_api",
    "src.plugin_system.apis.message_api",
    "src.plugin_system.apis.llm_api",
    "src.plugin_system.apis.emoji_api",
    "src.plugin_system.apis.person_api",
    "src.plugin_system.apis.chat_api",
    "src.plugin_system.apis.tool_api",
    "src.plugin_system.apis.frequency_api",
    "src.plugin_system.apis.generator_api",
    "src.plugin_system.apis.component_manage_api",
    "src.plugin_system.apis.plugin_manage_api",
    "src.plugin_system.apis.plugin_service_api",
    "src.plugin_system.apis.workflow_api",
    "src.plugin_system.apis.constants",
    "src.plugin_system.apis.logging_api",
    "src.plugin_system.apis.plugin_register_api",
    "src.plugin_system.core",
    "src.plugin_system.utils",
]


# ── 静默导入旧版模块供后续测试使用 ─────────────────────────────────

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from src.plugin_system import (  # type: ignore[import-untyped]
        ActionActivationType,
        BaseAction,
        BaseCommand,
        BaseEventHandler,
        BasePlugin,
        BaseTool,
        EventType,
        ToolParamType,
        chat_api,
        component_manage_api,
        config_api,
        database_api,
        emoji_api,
        frequency_api,
        generator_api,
        get_logger,
        llm_api,
        message_api,
        person_api,
        plugin_manage_api,
        plugin_service_api,
        register_plugin,
        send_api,
        tool_api,
        workflow_api,
    )


# ═══════════════════════════════════════════════════════════════════
#  1. Import hook
# ═══════════════════════════════════════════════════════════════════


class TestImportHook:
    @pytest.mark.parametrize("mod_path", OLD_IMPORTS)
    def test_old_import_path_available(self, mod_path: str):
        """每个旧版导入路径都能成功 import 并注册到 sys.modules"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            importlib.import_module(mod_path)
        assert mod_path in sys.modules

    def test_from_import_style(self):
        """from src.plugin_system import ... 风格导入正常"""
        assert BaseAction is not None
        assert BaseCommand is not None
        assert BaseEventHandler is not None
        assert BaseTool is not None
        assert BasePlugin is not None
        assert callable(register_plugin)
        assert callable(get_logger)

    def test_hook_does_not_shadow_real_src_package(self, tmp_path: Path) -> None:
        """安装兼容 hook 后，真实 src.* 模块仍应可导入。"""
        src_root = tmp_path / "src"
        protocol_root = src_root / "plugin_runtime" / "protocol"
        protocol_root.mkdir(parents=True)

        for package_dir in (src_root, src_root / "plugin_runtime", protocol_root):
            (package_dir / "__init__.py").write_text("", encoding="utf-8")

        (protocol_root / "envelope.py").write_text("class Envelope:\n    pass\n", encoding="utf-8")

        module_names = [
            "src",
            "src.plugin_runtime",
            "src.plugin_runtime.protocol",
            "src.plugin_runtime.protocol.envelope",
        ]
        original_modules = {name: sys.modules.pop(name, None) for name in module_names}

        sys.path.insert(0, str(tmp_path))
        importlib.invalidate_caches()
        try:
            module = importlib.import_module("src.plugin_runtime.protocol.envelope")
            assert hasattr(module, "Envelope")
            assert module.Envelope.__module__ == "src.plugin_runtime.protocol.envelope"
        finally:
            sys.path.remove(str(tmp_path))
            importlib.invalidate_caches()
            for name in module_names:
                sys.modules.pop(name, None)
            for name, module in original_modules.items():
                if module is not None:
                    sys.modules[name] = module


# ═══════════════════════════════════════════════════════════════════
#  2. 基类签名
# ═══════════════════════════════════════════════════════════════════


class _StubAction(BaseAction):
    action_name = "test_action"
    action_description = "A test action"
    activation_type = ActionActivationType.KEYWORD
    activation_keywords = ["hello"]
    action_parameters = {"param1": "desc1"}

    async def execute(self):
        return True, "ok"


class _StubCommand(BaseCommand):
    command_name = "test_cmd"
    command_description = "A test command"
    command_pattern = r"/test (?P<arg>\w+)"

    async def execute(self):
        return True, "ok", 0


class _StubHandler(BaseEventHandler):
    event_type = EventType.ON_MESSAGE
    handler_name = "test_handler"
    handler_description = "A test handler"
    weight = 10
    intercept_message = False

    async def execute(self, message):
        return True, False, None, None, None


class _StubTool(BaseTool):
    name = "test_tool"
    description = "A test tool"
    parameters = [
        ("query", ToolParamType.STRING, "Search query", True, None),
        ("limit", ToolParamType.INTEGER, "Max results", False, None),
    ]

    async def execute(self, function_args):
        return {"name": self.name, "content": "result"}


class TestBaseAction:
    def test_init_signature(self):
        action = _StubAction(
            action_data={"key": "val"},
            action_reasoning="test reason",
            cycle_timers={},
            thinking_id="tid-123",
            chat_stream=None,
            plugin_config={"section": {"key": "value"}},
            action_message=None,
        )
        assert action.action_data == {"key": "val"}
        assert action.action_reasoning == "test reason"
        assert action.thinking_id == "tid-123"
        assert action.plugin_config == {"section": {"key": "value"}}

    def test_get_config(self):
        action = _StubAction(plugin_config={"section": {"key": "value"}})
        assert action.get_config("section.key") == "value"
        assert action.get_config("missing.key", "default") == "default"

    def test_get_action_info(self):
        info = _StubAction.get_action_info()
        assert info.name == "test_action"
        assert info.activation_type == ActionActivationType.KEYWORD
        assert info.activation_keywords == ["hello"]


class TestBaseCommand:
    def test_init_and_config(self):
        cmd = _StubCommand(message=None, plugin_config={"a": {"b": 1}})
        assert cmd.plugin_config == {"a": {"b": 1}}
        assert cmd.get_config("a.b") == 1

    def test_set_matched_groups(self):
        cmd = _StubCommand()
        cmd.set_matched_groups({"arg": "hello"})
        assert cmd.matched_groups == {"arg": "hello"}

    def test_get_command_info(self):
        info = _StubCommand.get_command_info()
        assert info.name == "test_cmd"
        assert info.command_pattern == r"/test (?P<arg>\w+)"


class TestBaseEventHandler:
    def test_init_and_injection(self):
        handler = _StubHandler()
        handler.set_plugin_config({"x": 1})
        handler.set_plugin_name("my_plugin")
        assert handler.plugin_config == {"x": 1}
        assert handler.plugin_name == "my_plugin"
        assert handler.get_config("x") == 1

    def test_get_handler_info(self):
        info = _StubHandler.get_handler_info()
        assert info.name == "test_handler"
        assert info.weight == 10


class TestBaseTool:
    def test_init_and_config(self):
        tool = _StubTool(plugin_config={"p": 1}, chat_stream=None)
        assert tool.plugin_config == {"p": 1}
        assert tool.get_config("p") == 1

    def test_get_tool_definition(self):
        defn = _StubTool.get_tool_definition()
        func = defn["function"]
        assert func["name"] == "test_tool"
        assert "query" in func["parameters"]["properties"]
        assert "query" in func["parameters"]["required"]
        assert "limit" not in func["parameters"]["required"]

    def test_get_tool_info(self):
        info = _StubTool.get_tool_info()
        assert info.name == "test_tool"
        assert len(info.tool_parameters) == 2


# ═══════════════════════════════════════════════════════════════════
#  3. API 模块签名
# ═══════════════════════════════════════════════════════════════════


class TestApiModules:
    def test_send_api(self):
        for fn in (
            "text_to_stream",
            "emoji_to_stream",
            "image_to_stream",
            "command_to_stream",
            "custom_to_stream",
            "custom_reply_set_to_stream",
            "custom_message",
        ):
            assert callable(getattr(send_api, fn)), f"send_api.{fn} 不可调用"

    def test_config_api(self):
        for fn in ("get_global_config", "get_plugin_config", "set_config_cache"):
            assert callable(getattr(config_api, fn))

    def test_message_api(self):
        for fn in ("count_new_messages", "get_messages_by_time", "async_get_messages_by_time"):
            assert callable(getattr(message_api, fn))

    def test_database_api(self):
        for fn in ("db_query", "store_action_info"):
            assert callable(getattr(database_api, fn))

    def test_llm_api(self):
        for fn in ("get_available_models", "generate_with_model"):
            assert callable(getattr(llm_api, fn))

    def test_emoji_api(self):
        for fn in ("get_by_description", "get_random", "get_count"):
            assert callable(getattr(emoji_api, fn))

    def test_person_api(self):
        for fn in ("get_person_id", "get_person_value"):
            assert callable(getattr(person_api, fn))

    def test_chat_api(self):
        assert hasattr(chat_api, "ChatManager")

    def test_tool_api(self):
        for fn in ("get_tool_instance", "get_llm_available_tool_definitions"):
            assert callable(getattr(tool_api, fn))

    def test_frequency_api(self):
        for fn in ("get_current_talk_value", "set_talk_frequency_adjust"):
            assert callable(getattr(frequency_api, fn))

    def test_generator_api(self):
        for fn in ("get_replyer", "generate_reply"):
            assert callable(getattr(generator_api, fn))

    def test_component_manage_api(self):
        for fn in ("get_all_plugin_info", "get_plugin_info"):
            assert callable(getattr(component_manage_api, fn))

    def test_plugin_manage_api(self):
        for fn in ("list_loaded_plugins", "reload_plugin"):
            assert callable(getattr(plugin_manage_api, fn))

    def test_plugin_service_api(self):
        for fn in ("register_service", "call_service"):
            assert callable(getattr(plugin_service_api, fn))

    def test_workflow_api(self):
        for fn in ("register_workflow_step", "publish_event"):
            assert callable(getattr(workflow_api, fn))

    def test_constants(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from src.plugin_system.apis.constants import PROJECT_ROOT  # type: ignore[import-untyped]
        assert PROJECT_ROOT is not None

    def test_async_compat_apis_receive_normalized_results(self):
        from maibot_sdk.compat._context_holder import set_context
        from maibot_sdk.context import PluginContext

        async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
            assert method == "cap.call"
            assert payload is not None
            capability = payload["capability"]
            return {
                "chat.get_all_streams": {"success": True, "streams": [{"session_id": "s1"}]},
                "person.get_id": {"success": True, "person_id": "person-1"},
                "frequency.get_current_talk_value": {"success": True, "value": 0.5},
                "message.get_by_time": {"success": True, "messages": [{"id": 1}]},
            }[capability]

        async def main():
            ctx = PluginContext(plugin_id="legacy-demo", rpc_call=fake_rpc_call)
            set_context(ctx)
            streams = await chat_api.async_get_all_streams()
            person_id = await person_api.async_get_person_id("qq", "123")
            talk_value = await frequency_api.async_get_current_talk_value("chat-1")
            messages = await message_api.async_get_messages_by_time(1.0, 2.0)
            return streams, person_id, talk_value, messages

        streams, person_id, talk_value, messages = asyncio.run(main())

        assert streams == [{"session_id": "s1"}]
        assert person_id == "person-1"
        assert talk_value == 0.5
        assert messages == [{"id": 1}]


# ═══════════════════════════════════════════════════════════════════
#  4. config_api 同步调用
# ═══════════════════════════════════════════════════════════════════


class TestConfigApiSync:
    def test_set_and_get(self):
        config_api.set_config_cache(
            global_cfg={"bot": {"name": "MaiBot", "admin_id": "12345"}},
            plugin_cfg={"section": {"key": "value"}},
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            assert config_api.get_global_config("bot.name") == "MaiBot"
            assert config_api.get_global_config("bot.admin_id") == "12345"
            assert config_api.get_global_config("missing", "fallback") == "fallback"
            assert (
                config_api.get_plugin_config(
                    {"section": {"key": "value"}},
                    "section.key",
                )
                == "value"
            )


# ═══════════════════════════════════════════════════════════════════
#  5. LegacyPluginAdapter
# ═══════════════════════════════════════════════════════════════════


class _StubPlugin(BasePlugin):
    def get_plugin_components(self):
        return [
            (_StubAction.get_action_info(), _StubAction),
            (_StubCommand.get_command_info(), _StubCommand),
            (_StubHandler.get_handler_info(), _StubHandler),
            (_StubTool.get_tool_info(), _StubTool),
        ]


class TestLegacyPluginAdapter:
    def test_get_components(self):
        from maibot_sdk.compat.legacy_adapter import LegacyPluginAdapter

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            adapter = LegacyPluginAdapter(_StubPlugin())

        components = adapter.get_components()
        assert len(components) == 4
        types_found = {c["type"] for c in components}
        assert types_found == {"ACTION", "COMMAND", "EVENT_HANDLER", "TOOL"}

    def test_set_plugin_config(self):
        from maibot_sdk.compat.legacy_adapter import LegacyPluginAdapter

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            adapter = LegacyPluginAdapter(_StubPlugin())

        adapter.set_plugin_config({"test_key": "test_val"})
        assert adapter._plugin_config == {"test_key": "test_val"}

    def test_set_plugin_config_seeds_global_config_cache(self, monkeypatch):
        from maibot_sdk.compat.legacy_adapter import LegacyPluginAdapter

        class _DummyGlobalConfig:
            def model_dump(self) -> dict[str, object]:
                return {"bot": {"name": "MaiBot", "admin_id": "12345"}}

        src_module = types.ModuleType("src")
        config_package = types.ModuleType("src.config")
        runtime_config = types.ModuleType("src.config.config")
        runtime_config.global_config = _DummyGlobalConfig()

        monkeypatch.setitem(sys.modules, "src", src_module)
        monkeypatch.setitem(sys.modules, "src.config", config_package)
        monkeypatch.setitem(sys.modules, "src.config.config", runtime_config)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            adapter = LegacyPluginAdapter(_StubPlugin())
            adapter.set_plugin_config({"section": {"key": "value"}})
            assert config_api.get_global_config("bot.name") == "MaiBot"
            assert config_api.get_global_config("bot.admin_id") == "12345"

    def test_get_config_reload_subscriptions(self):
        from maibot_sdk.compat.legacy_adapter import LegacyPluginAdapter

        class _ScopedPlugin(_StubPlugin):
            config_reload_subscriptions = ["model", "bot", "ignored", "bot"]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            adapter = LegacyPluginAdapter(_ScopedPlugin())

        assert adapter.get_config_reload_subscriptions() == ["bot", "model"]

    def test_on_config_update_accepts_scope_and_refreshes_global_cache(self, monkeypatch):
        from maibot_sdk.compat.legacy_adapter import LegacyPluginAdapter

        monkeypatch.setenv(
            "MAIBOT_GLOBAL_CONFIG_SNAPSHOT",
            json.dumps({"bot": {"name": "MaiBot"}, "model": {"models": [{"name": "old"}]}}),
        )

        class _ScopedPlugin(_StubPlugin):
            def __init__(self):
                self.updates: list[tuple[str, dict[str, object], str]] = []

            async def on_config_update(self, scope: str, config: dict[str, object], version: str) -> None:
                self.updates.append((scope, config, version))

        legacy_plugin = _ScopedPlugin()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            adapter = LegacyPluginAdapter(legacy_plugin)

        asyncio.run(adapter.on_config_update("model", {"models": [{"name": "new"}]}, "v2"))

        assert legacy_plugin.updates == [("model", {"models": [{"name": "new"}]}, "v2")]
        assert config_api.get_global_config("model.models")[0]["name"] == "new"

    def test_on_config_update_preserves_two_argument_legacy_signature(self):
        from maibot_sdk.compat.legacy_adapter import LegacyPluginAdapter

        class _TwoArgPlugin(_StubPlugin):
            def __init__(self):
                self.updates: list[tuple[dict[str, object], str]] = []

            def on_config_update(self, config: dict[str, object], version: str) -> None:
                self.updates.append((config, version))

        legacy_plugin = _TwoArgPlugin()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            adapter = LegacyPluginAdapter(legacy_plugin)

        asyncio.run(adapter.on_config_update("self", {"enabled": True}, "v1"))

        assert legacy_plugin.updates == [({"enabled": True}, "v1")]


# ═══════════════════════════════════════════════════════════════════
#  6. register_plugin 装饰器
# ═══════════════════════════════════════════════════════════════════


class TestRegisterPlugin:
    def test_with_kwargs(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            @register_plugin(
                name="test_compat_plugin",
                description="测试兼容性",
                version="1.0.0",
                author="test",
            )
            class _Registered(BasePlugin):
                def get_plugin_components(self):
                    return []

        assert hasattr(_Registered, "_plugin_meta")
        assert _Registered._plugin_meta["name"] == "test_compat_plugin"

    def test_bare_decorator(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            @register_plugin
            class _Registered(BasePlugin):
                def get_plugin_components(self):
                    return []

        assert hasattr(_Registered, "_is_legacy_registered")
        assert _Registered._is_legacy_registered is True


# ═══════════════════════════════════════════════════════════════════
#  7. get_logger
# ═══════════════════════════════════════════════════════════════════


class TestGetLogger:
    def test_returns_logger(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            logger = get_logger("test_plugin")
        assert isinstance(logger, logging.Logger)


class TestCompatRuntimeContracts:
    def test_send_api_propagates_false_result(self):
        from maibot_sdk.compat._context_holder import set_context
        from maibot_sdk.context import PluginContext

        async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
            assert method == "cap.call"
            assert payload is not None
            assert payload["capability"] == "send.text"
            return {"success": False, "error": "denied"}

        async def main() -> bool:
            ctx = PluginContext(plugin_id="legacy-demo", rpc_call=fake_rpc_call)
            set_context(ctx)
            return await send_api.text_to_stream("hello", "stream-1")

        assert asyncio.run(main()) is False

    def test_llm_api_reads_response_field(self):
        from maibot_sdk.compat._context_holder import set_context
        from maibot_sdk.context import PluginContext

        async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
            assert method == "cap.call"
            assert payload is not None
            capability = payload["capability"]
            return {
                "llm.generate": {
                    "success": True,
                    "response": "hello",
                    "reasoning": "chain",
                    "model_name": "model-a",
                },
                "llm.generate_with_tools": {
                    "success": True,
                    "response": "tool-result",
                    "reasoning": "tool-chain",
                    "model_name": "model-b",
                    "tool_calls": [{"id": "call-1"}],
                },
            }[capability]

        async def main():
            ctx = PluginContext(plugin_id="legacy-demo", rpc_call=fake_rpc_call)
            set_context(ctx)
            plain = await llm_api.generate_with_model("prompt")
            with_tools = await llm_api.generate_with_tools("prompt")
            return plain, with_tools

        plain, with_tools = asyncio.run(main())

        assert plain == (True, "hello", "chain", "model-a")
        assert with_tools == (True, "tool-result", "tool-chain", "model-b", [{"id": "call-1"}])

    def test_plugin_manage_api_normalizes_success_flag(self):
        from maibot_sdk.compat._context_holder import set_context
        from maibot_sdk.context import PluginContext

        async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
            assert method == "cap.call"
            assert payload is not None
            capability = payload["capability"]
            return {
                "component.reload_plugin": {"success": False, "error": "missing"},
                "component.unload_plugin": {"success": False, "error": "unsupported"},
            }[capability]

        async def main():
            ctx = PluginContext(plugin_id="legacy-demo", rpc_call=fake_rpc_call)
            set_context(ctx)
            reloaded = await plugin_manage_api.reload_plugin("missing")
            removed = await plugin_manage_api.remove_plugin("missing")
            return reloaded, removed

        reloaded, removed = asyncio.run(main())

        assert reloaded is False
        assert removed is False

    def test_database_api_maps_to_new_sdk_signature(self):
        from maibot_sdk.compat._context_holder import set_context
        from maibot_sdk.context import PluginContext

        captured: dict[str, object] = {}

        async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
            assert method == "cap.call"
            assert payload is not None
            captured["capability"] = payload["capability"]
            captured["args"] = payload["args"]
            return {"success": True, "result": [{"id": 1, "value": "ok"}]}

        async def main():
            ctx = PluginContext(plugin_id="legacy-demo", rpc_call=fake_rpc_call)
            set_context(ctx)
            return await database_api.db_query("DemoTable", filters={"id": 1}, single_result=True)

        result = asyncio.run(main())

        assert result == {"id": 1, "value": "ok"}
        assert captured["capability"] == "database.query"
        assert captured["args"] == {
            "model_name": "DemoTable",
            "query_type": "get",
            "data": None,
            "filters": {"id": 1},
            "order_by": [],
            "limit": 1,
            "single_result": True,
        }

    def test_emoji_api_returns_normalized_dict_payloads(self):
        from maibot_sdk.compat._context_holder import set_context
        from maibot_sdk.context import PluginContext

        async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
            assert method == "cap.call"
            assert payload is not None
            capability = payload["capability"]
            return {
                "emoji.get_random": {
                    "success": True,
                    "emojis": [{"base64": "img-1", "description": "smile", "emotion": "happy"}],
                },
                "emoji.get_by_description": {
                    "success": True,
                    "emoji": {"base64": "img-2", "description": "wink", "emotion": "playful"},
                },
            }[capability]

        async def main():
            ctx = PluginContext(plugin_id="legacy-demo", rpc_call=fake_rpc_call)
            set_context(ctx)
            random_result = await emoji_api.get_random(1)
            search_result = await emoji_api.get_by_description("wink")
            return random_result, search_result

        random_result, search_result = asyncio.run(main())

        assert random_result == [{"base64": "img-1", "description": "smile", "emotion": "happy"}]
        assert search_result == {"base64": "img-2", "description": "wink", "emotion": "playful"}

    def test_sync_manage_apis_return_cached_runtime_snapshot(self):
        from maibot_sdk.compat.legacy_adapter import LegacyPluginAdapter
        from maibot_sdk.context import PluginContext

        plugins_snapshot = {
            "demo_plugin": {
                "name": "demo_plugin",
                "version": "1.0.0",
                "enabled": True,
                "components": [
                    {
                        "name": "demo_action",
                        "full_name": "demo_plugin.demo_action",
                        "type": "action",
                        "enabled": True,
                        "metadata": {"legacy": True},
                    }
                ],
            }
        }

        async def fake_rpc_call(method: str, plugin_id: str = "", payload: dict | None = None):
            assert method == "cap.call"
            assert payload is not None
            capability = payload["capability"]
            return {
                "component.get_all_plugins": {"success": True, "plugins": plugins_snapshot},
            }[capability]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            adapter = LegacyPluginAdapter(_StubPlugin())

        adapter._set_context(PluginContext(plugin_id="legacy-demo", rpc_call=fake_rpc_call))
        asyncio.run(adapter.on_load())

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            all_plugins = component_manage_api.get_all_plugin_info()
            plugin_info = component_manage_api.get_plugin_info("demo_plugin")
            component_info = component_manage_api.get_component_info("demo_action", "action")
            components_by_type = component_manage_api.get_components_info_by_type("action")
            enabled_components = component_manage_api.get_enabled_components_info_by_type("action")
            loaded_plugins = plugin_manage_api.list_loaded_plugins()
            registered_plugins = plugin_manage_api.list_registered_plugins()

        assert all_plugins == plugins_snapshot
        assert plugin_info == plugins_snapshot["demo_plugin"]
        assert component_info == plugins_snapshot["demo_plugin"]["components"][0]
        assert components_by_type == {"demo_plugin.demo_action": plugins_snapshot["demo_plugin"]["components"][0]}
        assert enabled_components == {"demo_plugin.demo_action": plugins_snapshot["demo_plugin"]["components"][0]}
        assert loaded_plugins == ["demo_plugin"]
        assert registered_plugins == ["demo_plugin"]
