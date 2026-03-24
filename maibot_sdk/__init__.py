"""MaiBot Plugin SDK

插件开发的唯一依赖入口。插件不得导入 src.*，只能通过本 SDK 获取能力。

核心导出：
- MaiBotPlugin: 插件基类
- Action, API, Command, Tool, EventHandler, HookHandler, MessageGateway: 组件声明装饰器
- PluginContext: 插件运行时上下文（提供能力代理）
"""

from maibot_sdk.components import API, Action, Command, EventHandler, HookHandler, MessageGateway, Tool, WorkflowStep
from maibot_sdk.context import PluginContext
from maibot_sdk.plugin import MaiBotPlugin
from maibot_sdk.types import CONFIG_RELOAD_SCOPE_SELF, ON_BOT_CONFIG_RELOAD, ON_MODEL_CONFIG_RELOAD

__version__ = "2.1.0"

__all__ = [
    "MaiBotPlugin",
    "API",
    "Action",
    "Command",
    "Tool",
    "EventHandler",
    "HookHandler",
    "MessageGateway",
    "WorkflowStep",
    "PluginContext",
    "CONFIG_RELOAD_SCOPE_SELF",
    "ON_BOT_CONFIG_RELOAD",
    "ON_MODEL_CONFIG_RELOAD",
]
