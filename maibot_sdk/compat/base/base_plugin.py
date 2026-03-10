"""旧版 BasePlugin 抽象基类 (兼容层)

旧版插件通过继承 BasePlugin 声明自身。
兼容层保留接口签名，但 get_plugin_components() 返回的组件
会由 LegacyPluginAdapter 桥接到新版 SDK。
"""

import warnings
from abc import ABC, abstractmethod
from typing import Any

from maibot_sdk.compat.base.component_types import ComponentInfo


class BasePlugin(ABC):
    """旧版插件基类 (已弃用)

    请迁移到 ``maibot_sdk.MaiBotPlugin``。
    """

    plugin_name: str = ""
    enable_plugin: bool = True
    dependencies: list[str] = []
    python_dependencies: list[str] = []
    config_file_name: str = "config.toml"
    config_schema: dict[str, Any] = {}
    config_section_descriptions: dict[str, Any] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        warnings.warn(
            "BasePlugin 已弃用，请使用 maibot_sdk.MaiBotPlugin",
            DeprecationWarning,
            stacklevel=2,
        )

    @abstractmethod
    def get_plugin_components(self) -> list[tuple[ComponentInfo, type]]:
        """声明插件包含的组件列表

        Returns:
            (ComponentInfo, 组件实现类) 元组列表
        """
        ...

    async def on_load(self) -> None:  # noqa: B027
        """插件加载后回调（可选覆盖）"""

    async def on_unload(self) -> None:  # noqa: B027
        """插件卸载前回调（可选覆盖）"""
