"""适配器专用能力代理。

为声明了 ``@Adapter`` 的插件提供插件到 Host 的专用通道。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext


class AdapterCapability:
    """适配器插件能力代理。"""

    def __init__(self, ctx: PluginContext) -> None:
        """初始化适配器能力代理。

        Args:
            ctx: 当前插件对应的上下文对象。
        """

        self._ctx = ctx

    async def receive_external_message(
        self,
        message: dict[str, Any],
        *,
        route_metadata: dict[str, Any] | None = None,
        external_message_id: str = "",
        dedupe_key: str = "",
    ) -> bool:
        """将外部平台消息注入 Host 主消息链。

        Args:
            message: 适配器转换后的标准 ``MessageDict``。
            route_metadata: 可选的路由辅助元数据，例如 ``self_id`` 或连接实例标识。
            external_message_id: 可选的外部平台消息 ID，用于去重和观测。
            dedupe_key: 可选的显式去重键，适用于外部平台没有稳定消息 ID 的场景。

        Returns:
            bool: Host 是否接受了本次外部消息注入。
        """

        result = await self._ctx.call_host_method(
            "host.receive_external_message",
            payload={
                "message": message,
                "route_metadata": route_metadata or {},
                "external_message_id": external_message_id,
                "dedupe_key": dedupe_key,
            },
        )
        if not isinstance(result, dict):
            return False
        return bool(result.get("accepted", False))

    async def update_runtime_state(
        self,
        *,
        connected: bool,
        account_id: str = "",
        scope: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """向 Host 上报适配器运行时状态。

        Args:
            connected: 当前适配器连接是否已经就绪，可安全接管平台路由。
            account_id: 当前连接对应的账号 ID 或 ``self_id``。
            scope: 当前连接对应的可选路由作用域，例如连接实例名。
            metadata: 可选的运行时状态元数据。

        Returns:
            bool: Host 是否接受了本次状态更新。
        """

        result = await self._ctx.call_host_method(
            "host.update_adapter_state",
            payload={
                "connected": connected,
                "account_id": account_id,
                "scope": scope,
                "metadata": metadata or {},
            },
        )
        if not isinstance(result, dict):
            return False
        return bool(result.get("accepted", False))
