"""旧版 config_api 兼容层

复刻旧版 src.plugin_system.apis.config_api 的公开函数签名。
注意：旧版 get_global_config / get_plugin_config 均为同步函数。
兼容层中它们也保持同步 —— 通过缓存或返回 default 实现。
"""

import logging
import warnings
from typing import Any

logger = logging.getLogger("legacy_plugin.config_api")

# 全局配置缓存，由 LegacyPluginAdapter 在加载时注入
_global_config_cache: dict[str, Any] = {}
_plugin_config_cache: dict[str, Any] = {}


def set_config_cache(global_cfg: dict[str, Any], plugin_cfg: dict[str, Any]) -> None:
    """由适配器调用，注入配置缓存 (内部使用)"""
    global _global_config_cache, _plugin_config_cache
    _global_config_cache = global_cfg
    _plugin_config_cache = plugin_cfg


def get_global_config(key: str, default: Any = None) -> Any:
    """从全局配置中获取值 (同步)

    Args:
        key: 嵌套键名，如 "section.subsection.key"
        default: 默认值
    """
    warnings.warn(
        "config_api.get_global_config() 已弃用，请使用 self.ctx.config.get()",
        DeprecationWarning,
        stacklevel=2,
    )
    return _nested_get(_global_config_cache, key, default)


def get_plugin_config(plugin_config: dict, key: str, default: Any = None) -> Any:
    """从插件配置字典中获取值 (同步)

    Args:
        plugin_config: 插件配置字典
        key: 嵌套键名
        default: 默认值
    """
    warnings.warn("config_api.get_plugin_config() 已弃用", DeprecationWarning, stacklevel=2)
    return _nested_get(plugin_config, key, default)


def _nested_get(data: Any, key: str, default: Any = None) -> Any:
    """嵌套键访问辅助"""
    if not data:
        return default
    keys = key.split(".")
    current = data
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        elif hasattr(current, k):
            current = getattr(current, k)
        else:
            return default
    return current
