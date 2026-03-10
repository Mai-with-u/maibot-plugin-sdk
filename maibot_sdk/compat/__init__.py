"""旧版插件系统兼容层 (maibot_sdk.compat)

此包提供与已删除的 ``src.plugin_system`` 完全兼容的接口。
配合 ``_import_hook`` 模块，旧版插件的 ``from src.plugin_system import ...``
导入将被透明重定向到此处，同时发出弃用警告。

⚠️  此兼容层将在未来版本中移除，请尽快迁移到新版 maibot_sdk。
"""

# ── 基类 ───────────────────────────────────────────────────────
# ── API 占位 ──────────────────────────────────────────────────
from maibot_sdk.compat.apis import (
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
    send_api,
    tool_api,
    workflow_api,
)
from maibot_sdk.compat.apis.constants import (
    BOT_CONFIG_PATH,
    CONFIG_DIR,
    INTERNAL_PLUGINS_DIR,
    MODEL_CONFIG_PATH,
    PLUGINS_DIR,
    PROJECT_ROOT,
)

# ── 注册装饰器 ────────────────────────────────────────────────
from maibot_sdk.compat.apis.plugin_register_api import register_plugin
from maibot_sdk.compat.base.base_action import BaseAction
from maibot_sdk.compat.base.base_command import BaseCommand
from maibot_sdk.compat.base.base_events_handler import BaseEventHandler
from maibot_sdk.compat.base.base_plugin import BasePlugin
from maibot_sdk.compat.base.base_tool import BaseTool

# ── 组件类型 ───────────────────────────────────────────────────
from maibot_sdk.compat.base.component_types import (
    ActionActivationType,
    ActionInfo,
    ChatMode,
    CommandInfo,
    ComponentInfo,
    ComponentType,
    CustomEventHandlerResult,
    EventHandlerInfo,
    EventType,
    ForwardNode,
    MaiMessages,
    ModifyFlag,
    PluginInfo,
    PythonDependency,
    ReplyContent,
    ReplyContentType,
    ReplySetModel,
    ToolCall,
    ToolInfo,
    ToolParamType,
)

# ── 配置类型 ───────────────────────────────────────────────────
from maibot_sdk.compat.base.config_types import (
    ConfigField,
    ConfigLayout,
    ConfigSection,
    ConfigTab,
    section_meta,
)

# ── 服务/工作流类型 ───────────────────────────────────────────
from maibot_sdk.compat.base.service_types import PluginServiceInfo
from maibot_sdk.compat.base.workflow_errors import WorkflowErrorCode
from maibot_sdk.compat.base.workflow_types import (
    WorkflowContext,
    WorkflowMessage,
    WorkflowStage,
    WorkflowStepInfo,
    WorkflowStepResult,
)

__all__ = [
    # 基类
    "BasePlugin",
    "BaseAction",
    "BaseCommand",
    "BaseTool",
    "BaseEventHandler",
    # 组件类型
    "ComponentType",
    "ActionActivationType",
    "ChatMode",
    "EventType",
    "ToolParamType",
    "ReplyContentType",
    "ComponentInfo",
    "ActionInfo",
    "CommandInfo",
    "ToolInfo",
    "EventHandlerInfo",
    "PluginInfo",
    "PythonDependency",
    "MaiMessages",
    "ToolCall",
    "ModifyFlag",
    "CustomEventHandlerResult",
    "ReplyContent",
    "ForwardNode",
    "ReplySetModel",
    # 配置
    "ConfigField",
    "ConfigSection",
    "ConfigLayout",
    "ConfigTab",
    "section_meta",
    # 服务/工作流
    "PluginServiceInfo",
    "WorkflowStage",
    "WorkflowStepInfo",
    "WorkflowStepResult",
    "WorkflowMessage",
    "WorkflowContext",
    "WorkflowErrorCode",
    # API
    "send_api",
    "llm_api",
    "database_api",
    "config_api",
    "message_api",
    "emoji_api",
    "person_api",
    "chat_api",
    "tool_api",
    "frequency_api",
    "generator_api",
    "component_manage_api",
    "plugin_manage_api",
    "plugin_service_api",
    "workflow_api",
    "get_logger",
    # 常量
    "PROJECT_ROOT",
    "CONFIG_DIR",
    "BOT_CONFIG_PATH",
    "MODEL_CONFIG_PATH",
    "PLUGINS_DIR",
    "INTERNAL_PLUGINS_DIR",
    # 装饰器
    "register_plugin",
]
