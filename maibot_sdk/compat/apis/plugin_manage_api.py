"""旧版 plugin_manage_api 兼容层

复刻旧版 src.plugin_system.apis.plugin_manage_api 的公开函数签名。
"""

import logging
import warnings
from typing import Any

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.plugin_manage_api")


def _get_component() -> Any:
    ctx = get_context()
    return ctx.component if ctx else None


def list_loaded_plugins() -> list[str]:
    """列出已加载的插件 (同步，返回最近一次拉取到的运行时快照)。"""
    warnings.warn("plugin_manage_api.list_loaded_plugins() 已弃用", DeprecationWarning, stacklevel=2)
    try:
        from maibot_sdk.compat.apis import component_manage_api

        return list(component_manage_api.get_all_plugin_info().keys())
    except Exception:
        return []


def list_registered_plugins() -> list[str]:
    """列出已注册的插件 (同步，返回最近一次拉取到的运行时快照)。"""
    warnings.warn("plugin_manage_api.list_registered_plugins() 已弃用", DeprecationWarning, stacklevel=2)
    try:
        from maibot_sdk.compat.apis import component_manage_api

        return list(component_manage_api.get_all_plugin_info().keys())
    except Exception:
        return []


def get_plugin_path(plugin_name: str) -> str:
    """获取插件路径 (同步，兼容层下抛出 ValueError)"""
    warnings.warn("plugin_manage_api.get_plugin_path() 已弃用", DeprecationWarning, stacklevel=2)
    raise ValueError(f"插件 '{plugin_name}' 路径在兼容层下不可用")


async def remove_plugin(plugin_name: str) -> bool:
    """卸载插件"""
    warnings.warn("plugin_manage_api.remove_plugin() 已弃用", DeprecationWarning, stacklevel=2)
    comp = _get_component()
    if comp is None:
        return False
    try:
        result = await comp.unload_plugin(plugin_name=plugin_name)
        if isinstance(result, dict):
            return bool(result.get("success"))
        return bool(result)
    except Exception as e:
        logger.error(f"plugin_manage_api.remove_plugin 失败: {e}")
        return False


async def reload_plugin(plugin_name: str) -> bool:
    """重新加载插件"""
    warnings.warn("plugin_manage_api.reload_plugin() 已弃用", DeprecationWarning, stacklevel=2)
    comp = _get_component()
    if comp is None:
        return False
    try:
        result = await comp.reload_plugin(plugin_name=plugin_name)
        if isinstance(result, dict):
            return bool(result.get("success"))
        return bool(result)
    except Exception as e:
        logger.error(f"plugin_manage_api.reload_plugin 失败: {e}")
        return False
