"""旧版插件系统导入钩子

通过 ``sys.meta_path`` 拦截 ``from src.plugin_system import ...``，
将其透明重定向到 ``maibot_sdk.compat``，无需物理存在 ``src/plugin_system/`` 目录。

## 用法

在加载旧版插件 **之前** 调用::

    from maibot_sdk.compat._import_hook import install_hook
    install_hook()

之后所有 ``from src.plugin_system import X`` 的导入都会被重定向。
"""

from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Optional, Sequence

import importlib
import importlib.abc
import logging
import sys
import warnings

from maibot_sdk.compat._warnings import show_banner_once

logger = logging.getLogger("maibot_sdk.compat.import_hook")


class _AliasLoader(importlib.abc.Loader):
    """将模块别名指向 sys.modules 中已加载的真实模块。"""

    def __init__(self, real_module: ModuleType):
        self._real_module = real_module

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        return self._real_module

    def exec_module(self, module: ModuleType) -> None:
        if module is not self._real_module:
            # 如果 Python 传入了不同的模块对象，将真实模块的内容复制过去
            module.__dict__.update(self._real_module.__dict__)
        pass

# 旧模块路径 → 新模块路径 的映射
_MODULE_MAP: dict[str, str] = {
    "src.plugin_system": "maibot_sdk.compat",
    "src.plugin_system.base": "maibot_sdk.compat.base",
    "src.plugin_system.base.component_types": "maibot_sdk.compat.base.component_types",
    "src.plugin_system.base.config_types": "maibot_sdk.compat.base.config_types",
    "src.plugin_system.base.base_plugin": "maibot_sdk.compat.base.base_plugin",
    "src.plugin_system.base.base_action": "maibot_sdk.compat.base.base_action",
    "src.plugin_system.base.base_command": "maibot_sdk.compat.base.base_command",
    "src.plugin_system.base.base_tool": "maibot_sdk.compat.base.base_tool",
    "src.plugin_system.base.base_events_handler": "maibot_sdk.compat.base.base_events_handler",
    "src.plugin_system.base.service_types": "maibot_sdk.compat.base.service_types",
    "src.plugin_system.base.workflow_types": "maibot_sdk.compat.base.workflow_types",
    "src.plugin_system.base.workflow_errors": "maibot_sdk.compat.base.workflow_errors",
    # API 模块
    "src.plugin_system.apis": "maibot_sdk.compat.apis",
    "src.plugin_system.apis.send_api": "maibot_sdk.compat.apis.send_api",
    "src.plugin_system.apis.database_api": "maibot_sdk.compat.apis.database_api",
    "src.plugin_system.apis.config_api": "maibot_sdk.compat.apis.config_api",
    "src.plugin_system.apis.message_api": "maibot_sdk.compat.apis.message_api",
    "src.plugin_system.apis.llm_api": "maibot_sdk.compat.apis.llm_api",
    "src.plugin_system.apis.emoji_api": "maibot_sdk.compat.apis.emoji_api",
    "src.plugin_system.apis.person_api": "maibot_sdk.compat.apis.person_api",
    "src.plugin_system.apis.chat_api": "maibot_sdk.compat.apis.chat_api",
    "src.plugin_system.apis.tool_api": "maibot_sdk.compat.apis.tool_api",
    "src.plugin_system.apis.frequency_api": "maibot_sdk.compat.apis.frequency_api",
    "src.plugin_system.apis.generator_api": "maibot_sdk.compat.apis.generator_api",
    "src.plugin_system.apis.component_manage_api": "maibot_sdk.compat.apis.component_manage_api",
    "src.plugin_system.apis.plugin_manage_api": "maibot_sdk.compat.apis.plugin_manage_api",
    "src.plugin_system.apis.plugin_service_api": "maibot_sdk.compat.apis.plugin_service_api",
    "src.plugin_system.apis.workflow_api": "maibot_sdk.compat.apis.workflow_api",
    "src.plugin_system.apis.constants": "maibot_sdk.compat.apis.constants",
    "src.plugin_system.apis.logging_api": "maibot_sdk.compat.apis.logging_api",
    "src.plugin_system.apis.plugin_register_api": "maibot_sdk.compat.apis.plugin_register_api",
    # core / utils
    "src.plugin_system.core": "maibot_sdk.compat.core",
    "src.plugin_system.core.component_registry": "maibot_sdk.compat.core.component_registry",
    "src.plugin_system.core.plugin_manager": "maibot_sdk.compat.core.plugin_manager",
    "src.plugin_system.utils": "maibot_sdk.compat.utils",
}

_hook_installed = False


class _LegacyPluginSystemFinder(MetaPathFinder):
    """在 sys.meta_path 中拦截 src.plugin_system.* 导入

    使用 _AliasLoader 在 create_module 阶段直接返回已加载的真实模块对象，
    避免 Python 的 _load_unlocked 用新建的空模块覆盖 sys.modules。
    """

    def find_spec(
        self,
        fullname: str,
        path: Optional[Sequence[str]],
        target: Optional[ModuleType] = None,
    ) -> Optional[ModuleSpec]:
        # 对 bare "src" 创建命名空间占位包
        if fullname == "src":
            if fullname in sys.modules:
                return ModuleSpec(fullname, _AliasLoader(sys.modules[fullname]), is_package=True)
            placeholder = ModuleType(fullname)
            placeholder.__path__ = []  # type: ignore[attr-defined]
            placeholder.__package__ = fullname
            sys.modules[fullname] = placeholder
            return ModuleSpec(fullname, _AliasLoader(placeholder), is_package=True)

        if fullname not in _MODULE_MAP and not fullname.startswith("src.plugin_system."):
            return None

        # 已加载的直接返回
        if fullname in sys.modules:
            mod = sys.modules[fullname]
            return ModuleSpec(
                fullname,
                _AliasLoader(mod),
                is_package=_is_package(mod),
            )

        # 首次命中时显示大横幅
        show_banner_once()
        warnings.warn(
            f"导入 '{fullname}' 来自已弃用的旧版插件系统，请迁移到 maibot_sdk",
            DeprecationWarning,
            stacklevel=2,
        )

        # 确定目标模块路径
        new_name = _MODULE_MAP.get(fullname)
        if new_name is None:
            suffix = fullname[len("src.plugin_system."):]
            new_name = f"maibot_sdk.compat.{suffix}"

        # 从 sys.modules 获取已加载模块，避免重复加载导致类标识不同
        real_module = sys.modules.get(new_name)
        if real_module is None:
            try:
                real_module = importlib.import_module(new_name)
            except ImportError:
                logger.debug(f"兼容层无法映射 '{fullname}' → '{new_name}'，跳过")
                return None

        # 注册旧路径到 sys.modules
        sys.modules[fullname] = real_module

        # 确保父路径也已注册
        _ensure_parent_modules(fullname)

        # 返回 spec，使用 _AliasLoader 确保 create_module 返回真实模块
        return ModuleSpec(
            fullname,
            _AliasLoader(real_module),
            origin=new_name,
            is_package=_is_package(real_module),
        )


def _ensure_parent_modules(fullname: str) -> None:
    """确保 fullname 的每个父级都在 sys.modules 中。

    例如 ``src.plugin_system.base.component_types`` 需要
    ``src``、``src.plugin_system``、``src.plugin_system.base`` 都存在。
    """
    parts = fullname.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            if target := _MODULE_MAP.get(parent):
                try:
                    sys.modules[parent] = sys.modules.get(target) or importlib.import_module(target)
                except ImportError:
                    # 创建空的包占位，防止 ImportError
                    placeholder = ModuleType(parent)
                    placeholder.__path__ = []  # type: ignore[attr-defined]
                    placeholder.__package__ = parent
                    sys.modules[parent] = placeholder
            else:
                # 对于 'src' 本身，如果尚不存在就创建占位
                if parent not in sys.modules:
                    placeholder = ModuleType(parent)
                    placeholder.__path__ = []  # type: ignore[attr-defined]
                    placeholder.__package__ = parent
                    sys.modules[parent] = placeholder


def _is_package(module: ModuleType) -> bool:
    return hasattr(module, "__path__")


def install_hook() -> None:
    """安装导入钩子（幂等，多次调用安全）"""
    global _hook_installed
    if _hook_installed:
        return
    _hook_installed = True
    finder = _LegacyPluginSystemFinder()
    sys.meta_path.insert(0, finder)
    logger.debug("旧版插件系统导入钩子已安装")


def uninstall_hook() -> None:
    """移除导入钩子"""
    global _hook_installed
    sys.meta_path[:] = [f for f in sys.meta_path if not isinstance(f, _LegacyPluginSystemFinder)]
    _hook_installed = False

    # 清理 sys.modules 中的虚拟条目
    to_remove = [k for k in sys.modules if k.startswith("src.plugin_system")]
    for k in to_remove:
        del sys.modules[k]
