"""数据库能力代理

对应旧系统的 database_api，所有方法底层转发为 cap.request RPC。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext


class DatabaseCapability:
    """数据库操作能力"""

    def __init__(self, ctx: PluginContext):
        self._ctx = ctx

    async def query(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
        order_by: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Any:
        """查询数据

        Args:
            table: 表名
            filters: 过滤条件
            order_by: 排序字段
            limit: 返回条数限制
            offset: 偏移量
        """
        return await self._ctx.call_capability(
            "db.query",
            table=table,
            filters=filters or {},
            order_by=order_by or [],
            limit=limit,
            offset=offset,
        )

    async def save(
        self,
        table: str,
        data: dict[str, Any],
        key_field: str = "id",
        key_value: Any = None,
    ) -> Any:
        """保存数据（插入或更新）

        Args:
            table: 表名
            data: 要保存的数据
            key_field: 主键字段名
            key_value: 主键值（为 None 时表示插入）
        """
        return await self._ctx.call_capability(
            "db.save",
            table=table,
            data=data,
            key_field=key_field,
            key_value=key_value,
        )

    async def delete(
        self,
        table: str,
        filters: dict[str, Any],
    ) -> Any:
        """删除数据

        Args:
            table: 表名
            filters: 过滤条件
        """
        return await self._ctx.call_capability(
            "db.delete",
            table=table,
            filters=filters,
        )

    async def count(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
    ) -> int:
        """计数

        Args:
            table: 表名
            filters: 过滤条件
        """
        result = await self._ctx.call_capability(
            "db.count",
            table=table,
            filters=filters or {},
        )
        return int(result) if result is not None else 0
