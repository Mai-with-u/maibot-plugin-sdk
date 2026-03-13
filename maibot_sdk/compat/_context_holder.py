"""兼容层上下文持有者

在旧版插件运行期间，按 plugin_id 存储各自的 PluginContext 引用，
使旧版基类方法和 API 桩能访问新版能力代理。

支持同一 Runner 进程加载多个旧版插件，每个插件持有独立的上下文。
使用 contextvars 追踪当前正在执行的插件 ID，确保 API 桩获取正确的上下文。
"""

from __future__ import annotations

import contextvars
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext

# 按 plugin_id 存储的上下文映射
_contexts: dict[str, PluginContext] = {}
# 最近设置的上下文（兜底，兼容只有单插件的场景和不传 plugin_id 的 API 调用）
_current_ctx: PluginContext | None = None
_lock = threading.Lock()

# 追踪当前正在执行的旧版插件 ID（asyncio Task 级隔离）
_active_plugin_id: contextvars.ContextVar[str] = contextvars.ContextVar("_active_plugin_id", default="")


def set_context(ctx: PluginContext) -> None:
    """由 LegacyPluginAdapter 在收到上下文注入时调用"""
    global _current_ctx
    with _lock:
        _contexts[ctx.plugin_id] = ctx
        _current_ctx = ctx


def activate_plugin(plugin_id: str) -> contextvars.Token[str]:
    """标记当前 async 任务正在执行指定插件的组件。

    由 LegacyPluginAdapter.invoke_component 在入口处调用，
    确保该调用链内的 get_context() 返回正确的插件上下文。

    Returns:
        contextvars Token，可用于 reset 恢复。
    """
    return _active_plugin_id.set(plugin_id)


def deactivate_plugin(token: contextvars.Token[str]) -> None:
    """恢复之前的活跃插件 ID。"""
    _active_plugin_id.reset(token)


def get_context(plugin_id: str = "") -> PluginContext | None:
    """获取指定插件的上下文。

    优先级：
    1. 显式传入的 plugin_id
    2. contextvars 中当前活跃的 plugin_id（由 invoke_component 设置）
    3. 最近设置的 _current_ctx（兜底）
    """
    with _lock:
        if plugin_id and plugin_id in _contexts:
            return _contexts[plugin_id]
        # 从 contextvars 获取当前活跃的插件 ID
        active_id = _active_plugin_id.get()
        if active_id and active_id in _contexts:
            return _contexts[active_id]
        return _current_ctx


def require_context(plugin_id: str = "") -> PluginContext:
    """获取上下文，不存在时抛出 RuntimeError"""
    ctx = get_context(plugin_id)
    if ctx is None:
        raise RuntimeError(
            "旧版插件兼容层: PluginContext 尚未注入。确保插件在 Runner 环境中运行且 LegacyPluginAdapter 已初始化。"
        )
    return ctx
