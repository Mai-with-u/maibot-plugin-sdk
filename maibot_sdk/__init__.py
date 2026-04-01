"""MaiBot Plugin SDK

插件开发的唯一依赖入口。插件不得导入 src.*，只能通过本 SDK 获取能力。

核心导出：
- MaiBotPlugin: 插件基类
- Tool, API, Command, EventHandler, HookHandler, MessageGateway: 组件声明装饰器
- Action: 兼容旧插件的装饰器别名，内部会自动转换为 Tool 声明
- PluginContext: 插件运行时上下文（提供能力代理）
"""

from .components import API, Action, Command, EventHandler, HookHandler, MessageGateway, Tool, WorkflowStep
from .config import Field, PluginConfigBase
from .context import PluginContext
from .plugin import MaiBotPlugin
from .types import CONFIG_RELOAD_SCOPE_SELF, ON_BOT_CONFIG_RELOAD, ON_MODEL_CONFIG_RELOAD

__version__ = "2.2.0"

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
    "PluginConfigBase",
    "Field",
    "PluginContext",
    "CONFIG_RELOAD_SCOPE_SELF",
    "ON_BOT_CONFIG_RELOAD",
    "ON_MODEL_CONFIG_RELOAD",
]
