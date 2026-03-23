"""MaiBot 插件基类

所有 SDK 插件必须继承此基类。
插件通过装饰器声明组件，通过 self.ctx 访问能力代理。
"""

from typing import Any

from maibot_sdk.components import collect_components
from maibot_sdk.context import PluginContext


class MaiBotPlugin:
    """SDK 插件基类

    用法示例：

        from maibot_sdk import MaiBotPlugin, Action, Command

        class MyPlugin(MaiBotPlugin):
            @Action("greet", description="打招呼")
            async def handle_greet(self, **kwargs):
                await self.ctx.send.text("你好！", kwargs["stream_id"])
                return True, "已回复"

            @Command("hello", pattern=r"^/hello")
            async def handle_hello(self, **kwargs):
                await self.ctx.send.text("Hello!", kwargs["stream_id"])
                return True, "Hello!", 2

        def create_plugin():
            return MyPlugin()
    """

    def __init__(self) -> None:
        """初始化插件基类状态。"""
        self._ctx: PluginContext | None = None

    @property
    def ctx(self) -> PluginContext:
        """返回插件运行时上下文。

        Returns:
            PluginContext: 由 Runner 注入的上下文对象。

        Raises:
            RuntimeError: 当前插件尚未注入上下文时抛出。
        """
        if self._ctx is None:
            raise RuntimeError("插件上下文尚未初始化，确保在 Runner 环境中运行")
        return self._ctx

    def _set_context(self, ctx: PluginContext) -> None:
        """由 Runner 注入上下文对象。

        Args:
            ctx: 当前插件对应的运行时上下文。
        """
        self._ctx = ctx

    def get_components(self) -> list[dict[str, Any]]:
        """收集所有被装饰器标记的组件信息

        由 Runner 自动调用，无需手动覆盖。
        """
        return collect_components(self)

    async def on_load(self) -> None:
        """插件加载完成后的回调。

        该方法为可选覆盖点，默认不执行任何逻辑。
        """
        pass

    async def on_unload(self) -> None:
        """插件卸载前的回调。

        该方法为可选覆盖点，默认不执行任何逻辑。
        """
        pass

    async def on_config_update(self, new_config: dict[str, Any], version: str) -> None:
        """配置热更新回调。

        Args:
            new_config: 新配置数据。
            version: 配置版本号。
        """
        pass
