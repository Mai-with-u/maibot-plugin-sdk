"""MaiBot 插件基类

所有 SDK 插件必须继承此基类。
插件通过装饰器声明组件，通过 self.ctx 访问能力代理。
"""

from collections.abc import Callable, Iterable
from inspect import isawaitable, iscoroutinefunction
from typing import Any, ClassVar

from maibot_sdk.components import collect_components
from maibot_sdk.context import PluginContext
from maibot_sdk.types import normalize_config_reload_subscription


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

    config_reload_subscriptions: ClassVar[Iterable[str]] = ()
    """插件订阅的全局配置热重载范围。

    仅支持订阅 ``bot`` 和 ``model`` 两类全局配置广播。插件自身的
    ``config.toml`` 变化不通过该字段声明，而是固定通过
    :meth:`on_config_update` 接收。
    """

    def __init__(self) -> None:
        """初始化插件基类状态。"""
        self._ctx: PluginContext | None = None
        self._dynamic_api_components: dict[str, dict[str, Any]] = {}
        self._dynamic_api_handlers: dict[str, Callable[..., Any]] = {}

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
        components = collect_components(self)
        components.extend(self.get_dynamic_api_components())
        return components

    @staticmethod
    def _build_dynamic_api_key(name: str, version: str) -> str:
        """构造动态 API 的稳定键。"""

        normalized_name = str(name or "").strip()
        normalized_version = str(version or "1").strip() or "1"
        return f"{normalized_name}@{normalized_version}"

    def register_dynamic_api(
        self,
        name: str,
        handler: Callable[..., Any],
        *,
        description: str = "",
        version: str = "1",
        public: bool = False,
        handler_name: str = "",
        **metadata: Any,
    ) -> dict[str, Any]:
        """注册一个动态 API 定义。

        Args:
            name: 对外暴露的 API 名称。
            handler: 当前 API 对应的处理函数。
            description: API 描述。
            version: API 版本。
            public: 是否允许其他插件调用。
            handler_name: 可选的内部处理器名称；留空时自动生成。
            **metadata: 额外元数据。

        Returns:
            dict[str, Any]: 可直接同步到 Host 的组件声明。
        """

        normalized_name = str(name or "").strip()
        if not normalized_name:
            raise ValueError("动态 API 名称不能为空")
        normalized_version = str(version or "1").strip() or "1"
        resolved_handler_name = str(handler_name or f"dynamic_api__{normalized_name}__{normalized_version}").strip()
        if not resolved_handler_name:
            raise ValueError("动态 API handler_name 不能为空")

        component_metadata: dict[str, Any] = {
            "description": description,
            "version": normalized_version,
            "public": bool(public),
            "dynamic": True,
            "handler_name": resolved_handler_name,
            **metadata,
        }
        component: dict[str, Any] = {
            "name": normalized_name,
            "type": "API",
            "metadata": component_metadata,
        }
        self._dynamic_api_components[self._build_dynamic_api_key(normalized_name, normalized_version)] = component
        self._dynamic_api_handlers[resolved_handler_name] = handler
        return {
            "name": component["name"],
            "type": component["type"],
            "metadata": dict(component_metadata),
        }

    def unregister_dynamic_api(self, name: str, *, version: str = "1") -> bool:
        """注销一个动态 API 定义。"""

        api_key = self._build_dynamic_api_key(name, version)
        component = self._dynamic_api_components.pop(api_key, None)
        if component is None:
            return False

        handler_name = str(component["metadata"].get("handler_name", "") or "").strip()
        if handler_name:
            handler_still_used = any(
                str(candidate["metadata"].get("handler_name", "") or "").strip() == handler_name
                for candidate in self._dynamic_api_components.values()
            )
            if not handler_still_used:
                self._dynamic_api_handlers.pop(handler_name, None)
        return True

    def clear_dynamic_apis(self) -> None:
        """清空当前插件维护的全部动态 API。"""

        self._dynamic_api_components.clear()
        self._dynamic_api_handlers.clear()

    def get_dynamic_api_components(self) -> list[dict[str, Any]]:
        """返回当前插件维护的动态 API 组件声明。"""

        return [
            {
                "name": component["name"],
                "type": component["type"],
                "metadata": dict(component["metadata"]),
            }
            for component in self._dynamic_api_components.values()
        ]

    async def sync_dynamic_apis(self, *, offline_reason: str = "动态 API 已下线") -> bool:
        """将当前动态 API 集合同步到 Host。"""

        return await self.ctx.api.replace_dynamic_apis(
            self.get_dynamic_api_components(),
            offline_reason=offline_reason,
        )

    async def invoke_component(self, component_name: str, **kwargs: Any) -> Any:
        """为动态 API 提供默认的组件调用分发。"""

        handler = self._dynamic_api_handlers.get(component_name)
        if handler is None:
            raise AttributeError(f"插件未注册动态组件处理器: {component_name}")

        if iscoroutinefunction(handler):
            return await handler(**kwargs)

        result = handler(**kwargs)
        if isawaitable(result):
            return await result
        return result

    def get_config_reload_subscriptions(self) -> list[str]:
        """返回当前插件订阅的全局配置热重载范围。

        Returns:
            list[str]: 归一化后的订阅范围列表，仅包含 ``bot`` 和 ``model``。

        Raises:
            TypeError: 当 ``config_reload_subscriptions`` 不是可迭代对象时抛出。
            ValueError: 当订阅值不受支持时抛出。
        """

        raw_subscriptions = type(self).config_reload_subscriptions
        if isinstance(raw_subscriptions, str):
            raise TypeError("config_reload_subscriptions 必须是可迭代集合，不能直接使用字符串")
        if not isinstance(raw_subscriptions, Iterable):
            raise TypeError("config_reload_subscriptions 必须是可迭代集合")

        normalized_subscriptions: set[str] = set()
        for subscription in raw_subscriptions:
            normalized_subscriptions.add(normalize_config_reload_subscription(subscription))
        return sorted(normalized_subscriptions)

    async def on_load(self) -> None:
        """插件加载完成后的回调。

        Raises:
            NotImplementedError: 子类未覆盖该生命周期方法时抛出。
        """
        raise NotImplementedError("插件必须实现 on_load() 来处理加载生命周期")

    async def on_unload(self) -> None:
        """插件卸载前的回调。

        Raises:
            NotImplementedError: 子类未覆盖该生命周期方法时抛出。
        """
        raise NotImplementedError("插件必须实现 on_unload() 来处理卸载生命周期")

    async def on_config_update(self, scope: str, config_data: dict[str, Any], version: str) -> None:
        """处理配置热更新事件。

        Args:
            scope: 配置变更范围，取值为 ``self``、``bot``、``model``。
            config_data: 当前范围对应的最新配置数据。
            version: 配置版本号。

        Raises:
            NotImplementedError: 子类未覆盖该生命周期方法时抛出。
        """
        raise NotImplementedError("插件必须实现 on_config_update() 来处理配置热重载")
