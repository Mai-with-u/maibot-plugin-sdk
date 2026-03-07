"""聊天流能力代理

提供聊天流发现与查询功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext


class ChatCapability:
    """聊天流管理能力"""

    def __init__(self, ctx: PluginContext):
        self._ctx = ctx

    async def get_all_streams(self) -> Any:
        """获取所有活跃的聊天流"""
        return await self._ctx.call_capability("chat.get_all_streams")

    async def get_group_streams(self) -> Any:
        """获取所有群聊流"""
        return await self._ctx.call_capability("chat.get_group_streams")

    async def get_private_streams(self) -> Any:
        """获取所有私聊流"""
        return await self._ctx.call_capability("chat.get_private_streams")

    async def get_stream_by_group_id(self, group_id: str) -> Any:
        """根据群组 ID 查找聊天流

        Args:
            group_id: 群组 ID
        """
        return await self._ctx.call_capability(
            "chat.get_stream_by_group_id",
            group_id=group_id,
        )

    async def get_stream_by_user_id(self, user_id: str) -> Any:
        """根据用户 ID 查找聊天流

        Args:
            user_id: 用户 ID
        """
        return await self._ctx.call_capability(
            "chat.get_stream_by_user_id",
            user_id=user_id,
        )
