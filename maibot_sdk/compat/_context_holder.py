"""兼容层上下文持有者

在旧版插件运行期间，按 plugin_id 存储各自的 PluginContext 引用，
使旧版基类方法和 API 桩能访问新版能力代理。

支持同一 Runner 进程加载多个旧版插件，每个插件持有独立的上下文。
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext

# 按 plugin_id 存储的上下文映射
_contexts: dict[str, PluginContext] = {}
# 最近设置的上下文（兜底，兼容只有单插件的场景和不传 plugin_id 的 API 调用）
_current_ctx: Optional[PluginContext] = None
_lock = threading.Lock()


def set_context(ctx: PluginContext) -> None:
    """由 LegacyPluginAdapter 在收到上下文注入时调用"""
    global _current_ctx
    with _lock:
        _contexts[ctx.plugin_id] = ctx
        _current_ctx = ctx


def get_context(plugin_id: str = "") -> Optional[PluginContext]:
    """获取指定插件的上下文，未指定时返回最近设置的"""
    with _lock:
        if plugin_id and plugin_id in _contexts:
            return _contexts[plugin_id]
        return _current_ctx


def require_context(plugin_id: str = "") -> PluginContext:
    """获取上下文，不存在时抛出 RuntimeError"""
    ctx = get_context(plugin_id)
    if ctx is None:
        raise RuntimeError(
            "旧版插件兼容层: PluginContext 尚未注入。确保插件在 Runner 环境中运行且 LegacyPluginAdapter 已初始化。"
        )
    return ctx
