"""兼容层集成测试

验证 import hook、基类、API 模块等所有兼容层组件能正常工作。
"""

import sys
import warnings

# ==================================================================
# 1. 安装 import hook
# ==================================================================
from maibot_sdk.compat._import_hook import install_hook

install_hook()
print("[PASS] import hook 安装成功")

# ==================================================================
# 2. 验证旧版导入路径全部可用
# ==================================================================
old_imports = [
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

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    for mod_path in old_imports:
        try:
            __import__(mod_path)
            assert mod_path in sys.modules, f"{mod_path} not in sys.modules"
        except Exception as e:
            print(f"[FAIL] import {mod_path}: {e}")
            sys.exit(1)

print(f"[PASS] 全部 {len(old_imports)} 个旧版导入路径可用")

# ==================================================================
# 3. 验证 from ... import ... 风格
# ==================================================================
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)

    from src.plugin_system import (
        PROJECT_ROOT,
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

    # 直接从子模块 import

print("[PASS] from ... import ... 风格全部通过")

# ==================================================================
# 4. 验证基类签名
# ==================================================================

# --- BaseAction ---
class _TestAction(BaseAction):
    action_name = "test_action"
    action_description = "A test action"
    activation_type = ActionActivationType.KEYWORD
    activation_keywords = ["hello"]
    action_parameters = {"param1": "desc1"}

    async def execute(self):
        return True, "ok"

action = _TestAction(
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
assert action.get_config("section.key") == "value"
assert action.get_config("missing.key", "default") == "default"
print("[PASS] BaseAction __init__ 签名和 get_config 正确")

# --- BaseAction classmethod ---
info = _TestAction.get_action_info()
assert info.name == "test_action"
assert info.activation_type == ActionActivationType.KEYWORD
assert info.activation_keywords == ["hello"]
print("[PASS] BaseAction.get_action_info() 正确")

# --- BaseCommand ---
class _TestCommand(BaseCommand):
    command_name = "test_cmd"
    command_description = "A test command"
    command_pattern = r"/test (?P<arg>\w+)"

    async def execute(self):
        return True, "ok", 0

cmd = _TestCommand(message=None, plugin_config={"a": {"b": 1}})
assert cmd.plugin_config == {"a": {"b": 1}}
assert cmd.get_config("a.b") == 1
cmd.set_matched_groups({"arg": "hello"})
assert cmd.matched_groups == {"arg": "hello"}
cmd_info = _TestCommand.get_command_info()
assert cmd_info.name == "test_cmd"
assert cmd_info.command_pattern == r"/test (?P<arg>\w+)"
print("[PASS] BaseCommand 签名和方法正确")

# --- BaseEventHandler ---
class _TestHandler(BaseEventHandler):
    event_type = EventType.ON_MESSAGE
    handler_name = "test_handler"
    handler_description = "A test handler"
    weight = 10
    intercept_message = False

    async def execute(self, message):
        return True, False, None, None, None

handler = _TestHandler()
handler.set_plugin_config({"x": 1})
handler.set_plugin_name("my_plugin")
assert handler.plugin_config == {"x": 1}
assert handler.plugin_name == "my_plugin"
assert handler.get_config("x") == 1
handler_info = _TestHandler.get_handler_info()
assert handler_info.name == "test_handler"
assert handler_info.weight == 10
print("[PASS] BaseEventHandler 签名和方法正确")

# --- BaseTool ---
class _TestTool(BaseTool):
    name = "test_tool"
    description = "A test tool"
    parameters = [
        ("query", ToolParamType.STRING, "Search query", True, None),
        ("limit", ToolParamType.INTEGER, "Max results", False, None),
    ]

    async def execute(self, function_args):
        return {"name": self.name, "content": "result"}

tool = _TestTool(plugin_config={"p": 1}, chat_stream=None)
assert tool.plugin_config == {"p": 1}
assert tool.get_config("p") == 1
tool_def = _TestTool.get_tool_definition()
assert tool_def["function"]["name"] == "test_tool"
assert "query" in tool_def["function"]["parameters"]["properties"]
assert "query" in tool_def["function"]["parameters"]["required"]
assert "limit" not in tool_def["function"]["parameters"]["required"]
tool_info = _TestTool.get_tool_info()
assert tool_info.name == "test_tool"
assert len(tool_info.tool_parameters) == 2
print("[PASS] BaseTool 签名和方法正确")

# ==================================================================
# 5. 验证 API 模块有正确的函数/属性
# ==================================================================

# send_api
assert callable(send_api.text_to_stream)
assert callable(send_api.emoji_to_stream)
assert callable(send_api.image_to_stream)
assert callable(send_api.command_to_stream)
assert callable(send_api.custom_to_stream)
assert callable(send_api.custom_reply_set_to_stream)
assert callable(send_api.custom_message)
print("[PASS] send_api 函数签名完整")

# config_api
assert callable(config_api.get_global_config)
assert callable(config_api.get_plugin_config)
assert callable(config_api.set_config_cache)
print("[PASS] config_api 函数签名完整")

# message_api
assert callable(message_api.count_new_messages)
assert callable(message_api.get_messages_by_time)
assert callable(message_api.async_get_messages_by_time)
print("[PASS] message_api 函数签名完整")

# database_api
assert callable(database_api.db_query)
assert callable(database_api.store_action_info)
print("[PASS] database_api 函数签名完整")

# llm_api
assert callable(llm_api.get_available_models)
assert callable(llm_api.generate_with_model)
print("[PASS] llm_api 函数签名完整")

# emoji_api
assert callable(emoji_api.get_by_description)
assert callable(emoji_api.get_random)
assert callable(emoji_api.get_count)
print("[PASS] emoji_api 函数签名完整")

# person_api
assert callable(person_api.get_person_id)
assert callable(person_api.get_person_value)
print("[PASS] person_api 函数签名完整")

# chat_api
assert hasattr(chat_api, "ChatManager")
print("[PASS] chat_api 属性完整")

# tool_api
assert callable(tool_api.get_tool_instance)
assert callable(tool_api.get_llm_available_tool_definitions)
print("[PASS] tool_api 函数签名完整")

# frequency_api
assert callable(frequency_api.get_current_talk_value)
assert callable(frequency_api.set_talk_frequency_adjust)
print("[PASS] frequency_api 函数签名完整")

# generator_api
assert callable(generator_api.get_replyer)
assert callable(generator_api.generate_reply)
print("[PASS] generator_api 函数签名完整")

# component_manage_api
assert callable(component_manage_api.get_all_plugin_info)
assert callable(component_manage_api.get_plugin_info)
print("[PASS] component_manage_api 函数签名完整")

# plugin_manage_api
assert callable(plugin_manage_api.list_loaded_plugins)
assert callable(plugin_manage_api.reload_plugin)
print("[PASS] plugin_manage_api 函数签名完整")

# plugin_service_api
assert callable(plugin_service_api.register_service)
assert callable(plugin_service_api.call_service)
print("[PASS] plugin_service_api 函数签名完整")

# workflow_api
assert callable(workflow_api.register_workflow_step)
assert callable(workflow_api.publish_event)
print("[PASS] workflow_api 函数签名完整")

# constants
from src.plugin_system.apis.constants import PROJECT_ROOT

assert isinstance(PROJECT_ROOT, str) or PROJECT_ROOT is not None
print("[PASS] constants 完整")

# ==================================================================
# 6. 验证 config_api 同步调用
# ==================================================================
config_api.set_config_cache(
    global_cfg={"bot": {"name": "MaiBot", "admin_id": "12345"}},
    plugin_cfg={"section": {"key": "value"}},
)
assert config_api.get_global_config("bot.name") == "MaiBot"
assert config_api.get_global_config("bot.admin_id") == "12345"
assert config_api.get_global_config("missing", "fallback") == "fallback"
assert config_api.get_plugin_config({"section": {"key": "value"}}, "section.key") == "value"
print("[PASS] config_api 同步调用正确")

# ==================================================================
# 7. 验证 LegacyPluginAdapter 基本流程
# ==================================================================
from maibot_sdk.compat.legacy_adapter import LegacyPluginAdapter


class _TestPlugin(BasePlugin):
    def get_plugin_components(self):
        return [
            (_TestAction.get_action_info(), _TestAction),
            (_TestCommand.get_command_info(), _TestCommand),
            (_TestHandler.get_handler_info(), _TestHandler),
            (_TestTool.get_tool_info(), _TestTool),
        ]

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    adapter = LegacyPluginAdapter(_TestPlugin())

# get_components 需要组件 info 有 enabled 属性
# ComponentInfo 基类有 enabled=True
components = adapter.get_components()
assert len(components) == 4, f"期望 4 个组件，实际 {len(components)}: {[c['name'] for c in components]}"
types_found = {c["type"] for c in components}
assert types_found == {"action", "command", "event_handler", "tool"}, f"类型不完整: {types_found}"
print("[PASS] LegacyPluginAdapter.get_components() 返回正确")

# 验证 set_plugin_config
adapter.set_plugin_config({"test_key": "test_val"})
assert adapter._plugin_config == {"test_key": "test_val"}
print("[PASS] LegacyPluginAdapter.set_plugin_config() 正确")

# ==================================================================
# 8. 验证 register_plugin 装饰器
# ==================================================================
@register_plugin(
    name="test_compat_plugin",
    description="测试兼容性",
    version="1.0.0",
    author="test",
)
class _TestRegisteredPlugin(BasePlugin):
    def get_plugin_components(self):
        return []

assert hasattr(_TestRegisteredPlugin, "_plugin_meta")
assert _TestRegisteredPlugin._plugin_meta["name"] == "test_compat_plugin"
print("[PASS] @register_plugin 装饰器正确")

# ==================================================================
# 9. 验证 get_logger
# ==================================================================
import logging

test_logger = get_logger("test_plugin")
assert isinstance(test_logger, logging.Logger)
print("[PASS] get_logger 返回正确")

# ==================================================================
print()
print("========================================")
print("  全部测试通过！兼容层完整性验证成功。  ")
print("========================================")
