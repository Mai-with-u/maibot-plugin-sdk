"""旧版 component_manage_api 兼容层

复刻旧版 src.plugin_system.apis.component_manage_api 的公开函数签名。
"""

import copy
import logging
import warnings
from typing import Any

from maibot_sdk.compat._context_holder import get_context
from maibot_sdk.types import normalize_component_type_name

logger = logging.getLogger("legacy_plugin.component_manage_api")

_plugins_cache: dict[str, Any] = {}


def _set_plugins_cache(plugins: Any) -> None:
    global _plugins_cache
    _plugins_cache = dict(plugins) if isinstance(plugins, dict) else {}


def _normalize_component_type(component_type: Any) -> str:
    return normalize_component_type_name(component_type)


def _iter_cached_components() -> list[dict[str, Any]]:
    components: list[dict[str, Any]] = []
    for plugin_info in _plugins_cache.values():
        if not isinstance(plugin_info, dict):
            continue
        plugin_components = plugin_info.get("components", [])
        if isinstance(plugin_components, list):
            components.extend(c for c in plugin_components if isinstance(c, dict))
    return components


def _get_component() -> Any:
    ctx = get_context()
    return ctx.component if ctx else None


def get_all_plugin_info() -> dict[str, Any]:
    """获取所有插件信息 (同步，返回最近一次拉取到的运行时快照)。"""
    warnings.warn("component_manage_api.get_all_plugin_info() 已弃用", DeprecationWarning, stacklevel=2)
    return copy.deepcopy(_plugins_cache)


def get_plugin_info(plugin_name: str) -> Any:
    """获取指定插件信息 (同步，返回最近一次拉取到的运行时快照)。"""
    warnings.warn("component_manage_api.get_plugin_info() 已弃用", DeprecationWarning, stacklevel=2)
    plugin_info = _plugins_cache.get(plugin_name)
    return copy.deepcopy(plugin_info) if isinstance(plugin_info, dict) else None


def get_component_info(component_name: str, component_type: Any) -> Any:
    """获取指定组件信息。"""
    warnings.warn("component_manage_api.get_component_info() 已弃用", DeprecationWarning, stacklevel=2)
    normalized_type = _normalize_component_type(component_type)
    for component_info in _iter_cached_components():
        try:
            cached_type = _normalize_component_type(component_info.get("type"))
        except ValueError:
            continue
        if cached_type != normalized_type:
            continue
        if component_info.get("full_name") == component_name or component_info.get("name") == component_name:
            return copy.deepcopy(component_info)
    return None


def get_components_info_by_type(component_type: Any) -> dict[str, Any]:
    """获取指定类型所有组件信息。"""
    warnings.warn("component_manage_api.get_components_info_by_type() 已弃用", DeprecationWarning, stacklevel=2)
    normalized_type = _normalize_component_type(component_type)
    result: dict[str, Any] = {}
    for component_info in _iter_cached_components():
        try:
            cached_type = _normalize_component_type(component_info.get("type"))
        except ValueError:
            continue
        if cached_type != normalized_type:
            continue
        key = str(component_info.get("full_name") or component_info.get("name") or "")
        if key:
            result[key] = copy.deepcopy(component_info)
    return result


def get_enabled_components_info_by_type(component_type: Any) -> dict[str, Any]:
    """获取指定类型所有启用的组件信息。"""
    warnings.warn("component_manage_api.get_enabled_components_info_by_type() 已弃用", DeprecationWarning, stacklevel=2)
    result = get_components_info_by_type(component_type)
    return {name: info for name, info in result.items() if info.get("enabled", True)}


# 异步版本
async def async_get_all_plugins() -> Any:
    comp = _get_component()
    if comp is None:
        _set_plugins_cache({})
        return {}
    try:
        plugins = await comp.get_all_plugins()
        _set_plugins_cache(plugins)
        return plugins
    except Exception as e:
        logger.error(f"component_manage_api.async_get_all_plugins 失败: {e}")
        return {}


async def async_get_plugin_info(plugin_name: str) -> Any:
    comp = _get_component()
    if comp is None:
        return None
    try:
        plugin_info = await comp.get_plugin_info(plugin_name=plugin_name)
        if isinstance(plugin_info, dict):
            _plugins_cache[plugin_name] = copy.deepcopy(plugin_info)
        return plugin_info
    except Exception as e:
        logger.error(f"component_manage_api.async_get_plugin_info 失败: {e}")
        return None
