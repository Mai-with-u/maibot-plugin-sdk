"""旧版 BasePlugin 抽象基类 (兼容层)

旧版插件通过继承 BasePlugin 声明自身。
兼容层保留接口签名，但 get_plugin_components() 返回的组件
会由 LegacyPluginAdapter 桥接到新版 SDK。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Type

import warnings

from maibot_sdk.compat.base.component_types import ComponentInfo


class BasePlugin(ABC):
    """旧版插件基类 (已弃用)

    请迁移到 ``maibot_sdk.MaiBotPlugin``。
    """

    plugin_name: str = ""
    enable_plugin: bool = True
    dependencies: List[str] = []
    python_dependencies: List[str] = []
    config_file_name: str = "config.toml"
    config_schema: Dict[str, Any] = {}
    config_section_descriptions: Dict[str, Any] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        warnings.warn(
            "BasePlugin 已弃用，请使用 maibot_sdk.MaiBotPlugin",
            DeprecationWarning,
            stacklevel=2,
        )

    @abstractmethod
    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        """声明插件包含的组件列表

        Returns:
            (ComponentInfo, 组件实现类) 元组列表
        """
        ...

    async def on_load(self) -> None:
        """插件加载后回调（可选覆盖）"""
        pass

    async def on_unload(self) -> None:
        """插件卸载前回调（可选覆盖）"""
        pass
