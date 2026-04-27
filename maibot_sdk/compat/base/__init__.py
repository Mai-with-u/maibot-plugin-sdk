"""旧版 base 模块 (兼容层)

re-export 所有 base 子模块的公开名称，
使 ``from src.plugin_system.base import *`` 继续工作。
"""

from maibot_sdk.compat.base.base_action import BaseAction
from maibot_sdk.compat.base.base_command import BaseCommand
from maibot_sdk.compat.base.base_events_handler import BaseEventHandler
from maibot_sdk.compat.base.base_plugin import BasePlugin
from maibot_sdk.compat.base.base_tool import BaseTool
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
from maibot_sdk.compat.base.config_types import (
    ConfigField,
    ConfigLayout,
    ConfigSection,
    ConfigTab,
    section_meta,
)
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
    # 配置类型
    "ConfigField",
    "ConfigSection",
    "ConfigLayout",
    "ConfigTab",
    "section_meta",
    # 服务
    "PluginServiceInfo",
    # 工作流
    "WorkflowStage",
    "WorkflowStepInfo",
    "WorkflowStepResult",
    "WorkflowMessage",
    "WorkflowContext",
    "WorkflowErrorCode",
]
