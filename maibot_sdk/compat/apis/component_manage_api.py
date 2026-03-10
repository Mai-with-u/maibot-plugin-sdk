"""旧版 component_manage_api 兼容层

复刻旧版 src.plugin_system.apis.component_manage_api 的公开函数签名。
"""

import logging
import warnings
from typing import Any, Dict, Optional, Union

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.component_manage_api")


def _get_component():
    ctx = get_context()
    return ctx.component if ctx else None


def get_all_plugin_info() -> Dict[str, Any]:
    """获取所有插件信息 (同步，兼容层下返回空)"""
    warnings.warn("component_manage_api.get_all_plugin_info() 已弃用", DeprecationWarning, stacklevel=2)
    return {}


def get_plugin_info(plugin_name: str) -> Any:
    """获取指定插件信息 (同步，兼容层下返回 None)"""
    warnings.warn("component_manage_api.get_plugin_info() 已弃用", DeprecationWarning, stacklevel=2)
    return None


def get_component_info(component_name: str, component_type: Any) -> Any:
    """获取指定组件信息"""
    warnings.warn("component_manage_api.get_component_info() 已弃用", DeprecationWarning, stacklevel=2)
    return None


def get_components_info_by_type(component_type: Any) -> Dict[str, Any]:
    """获取指定类型所有组件信息"""
    warnings.warn("component_manage_api.get_components_info_by_type() 已弃用", DeprecationWarning, stacklevel=2)
    return {}


def get_enabled_components_info_by_type(component_type: Any) -> Dict[str, Any]:
    """获取指定类型所有启用的组件信息"""
    warnings.warn("component_manage_api.get_enabled_components_info_by_type() 已弃用", DeprecationWarning, stacklevel=2)
    return {}


# 异步版本
async def async_get_all_plugins() -> Any:
    comp = _get_component()
    if comp is None:
        return {}
    try:
        return await comp.get_all_plugins()
    except Exception as e:
        logger.error(f"component_manage_api.async_get_all_plugins 失败: {e}")
        return {}


async def async_get_plugin_info(plugin_name: str) -> Any:
    comp = _get_component()
    if comp is None:
        return None
    try:
        return await comp.get_plugin_info(plugin_name=plugin_name)
    except Exception as e:
        logger.error(f"component_manage_api.async_get_plugin_info 失败: {e}")
        return None
