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
