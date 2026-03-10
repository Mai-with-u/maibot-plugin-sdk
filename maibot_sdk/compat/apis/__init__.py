"""旧版 API 模块 (兼容层)

每个 API 子模块均为独立文件，复刻旧版 src.plugin_system.apis 的结构。
旧版插件通过 ``from src.plugin_system.apis import send_api`` 等方式使用。
"""

from maibot_sdk.compat.apis import (
    chat_api,
    component_manage_api,
    config_api,
    database_api,
    emoji_api,
    frequency_api,
    generator_api,
    llm_api,
    message_api,
    person_api,
    plugin_manage_api,
    plugin_service_api,
    send_api,
    tool_api,
    workflow_api,
)
from maibot_sdk.compat.apis.logging_api import get_logger
from maibot_sdk.compat.apis.plugin_register_api import register_plugin

__all__ = [
    "chat_api",
    "component_manage_api",
    "config_api",
    "database_api",
    "emoji_api",
    "frequency_api",
    "generator_api",
    "llm_api",
    "message_api",
    "person_api",
    "plugin_manage_api",
    "plugin_service_api",
    "send_api",
    "tool_api",
    "frequency_api",
    "workflow_api",
    "get_logger",
    "register_plugin",
]
