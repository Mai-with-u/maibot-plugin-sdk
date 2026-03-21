"""MaiBot Plugin SDK

插件开发的唯一依赖入口。插件不得导入 src.*，只能通过本 SDK 获取能力。

核心导出：
- MaiBotPlugin: 插件基类
- Action, Command, Tool, EventHandler, HookHandler: 组件声明装饰器
- Adapter: 适配器角色声明装饰器
- PluginContext: 插件运行时上下文（提供能力代理）
"""

from maibot_sdk.components import Action, Adapter, Command, EventHandler, HookHandler, Tool, WorkflowStep
from maibot_sdk.context import PluginContext
from maibot_sdk.plugin import MaiBotPlugin

__version__ = "2.0.1"

__all__ = [
    "MaiBotPlugin",
    "Action",
    "Adapter",
    "Command",
    "Tool",
    "EventHandler",
    "HookHandler",
    "WorkflowStep",
    "PluginContext",
]
