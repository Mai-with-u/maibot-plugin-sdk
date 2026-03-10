"""旧版 plugin_service_api 兼容层

复刻旧版 src.plugin_system.apis.plugin_service_api 的公开函数签名。
跨插件服务注册/调用在新版 IPC 架构中不再直接支持。
"""

import logging
import warnings
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("legacy_plugin.plugin_service_api")

# 本地注册表 (仅同一进程内有效)
_local_services: Dict[str, Any] = {}
_local_handlers: Dict[str, Callable[..., Any]] = {}


def register_service(service_info: Any, service_handler: Callable[..., Any]) -> bool:
    """注册插件服务 (兼容层下仅在进程内有效)"""
    warnings.warn("plugin_service_api.register_service() 已弃用，新版 IPC 架构不支持跨进程服务", DeprecationWarning, stacklevel=2)
    key = getattr(service_info, "service_name", str(service_info))
    _local_services[key] = service_info
    _local_handlers[key] = service_handler
    return True


def get_service(service_name: str, plugin_name: Optional[str] = None) -> Any:
    """获取服务元信息"""
    warnings.warn("plugin_service_api.get_service() 已弃用", DeprecationWarning, stacklevel=2)
    return _local_services.get(service_name)


def get_service_handler(service_name: str, plugin_name: Optional[str] = None) -> Optional[Callable[..., Any]]:
    """获取服务处理函数"""
    warnings.warn("plugin_service_api.get_service_handler() 已弃用", DeprecationWarning, stacklevel=2)
    return _local_handlers.get(service_name)


def list_services(plugin_name: Optional[str] = None, enabled_only: bool = False) -> Dict[str, Any]:
    """列出服务"""
    warnings.warn("plugin_service_api.list_services() 已弃用", DeprecationWarning, stacklevel=2)
    return dict(_local_services)


def enable_service(service_name: str, plugin_name: Optional[str] = None) -> bool:
    warnings.warn("plugin_service_api.enable_service() 已弃用", DeprecationWarning, stacklevel=2)
    return service_name in _local_services


def disable_service(service_name: str, plugin_name: Optional[str] = None) -> bool:
    warnings.warn("plugin_service_api.disable_service() 已弃用", DeprecationWarning, stacklevel=2)
    return service_name in _local_services


def unregister_service(service_name: str, plugin_name: Optional[str] = None) -> bool:
    warnings.warn("plugin_service_api.unregister_service() 已弃用", DeprecationWarning, stacklevel=2)
    return _local_services.pop(service_name, None) is not None


async def call_service(
    service_name: str,
    *args: Any,
    plugin_name: Optional[str] = None,
    caller_plugin: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """调用插件服务 (仅进程内)"""
    warnings.warn("plugin_service_api.call_service() 已弃用", DeprecationWarning, stacklevel=2)
    handler = _local_handlers.get(service_name)
    if handler is None:
        raise KeyError(f"服务 '{service_name}' 不存在")
    return await handler(*args, **kwargs) if callable(handler) else None
