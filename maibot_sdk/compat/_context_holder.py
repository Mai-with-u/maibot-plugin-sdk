"""兼容层上下文持有者

在旧版插件运行期间，存储当前 PluginContext 引用，
使旧版基类方法和 API 桩能访问新版能力代理。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext

_current_ctx: PluginContext | None = None


def set_context(ctx: PluginContext) -> None:
    """由 LegacyPluginAdapter 在收到上下文注入时调用"""
    global _current_ctx
    _current_ctx = ctx


def get_context() -> PluginContext | None:
    """获取当前上下文（可能为 None）"""
    return _current_ctx


def require_context() -> PluginContext:
    """获取当前上下文，不存在时抛出 RuntimeError"""
    if _current_ctx is None:
        raise RuntimeError(
            "旧版插件兼容层: PluginContext 尚未注入。"
            "确保插件在 Runner 环境中运行且 LegacyPluginAdapter 已初始化。"
        )
    return _current_ctx
