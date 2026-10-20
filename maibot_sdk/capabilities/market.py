"""插件市场只读能力，统一使用 Host 配置的信息源和缓存。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext

MarketSort = Literal[
    "name",
    "downloads",
    "likes",
    "rating",
    "downloads_growth_7d",
    "likes_growth_7d",
    "downloads_growth_30d",
    "likes_growth_30d",
]


class MarketCapability:
    """需要在 manifest 中分别声明 market.search/get_detail/get_readme。"""

    def __init__(self, ctx: PluginContext) -> None:
        self._ctx = ctx

    async def _call(self, capability: str, **kwargs: Any) -> dict[str, Any]:
        result = await self._ctx.call_capability(capability, **kwargs)
        if not isinstance(result, dict):
            raise TypeError(f"Host 能力 {capability} 返回了非字典结果")
        return result

    async def search(
        self,
        query: str = "",
        *,
        category: str = "",
        page: int = 1,
        limit: int = 20,
        sort_by: MarketSort = "name",
        compatible_only: bool = False,
        include_manifest: bool = False,
        include_stats: bool = False,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """搜索市场，返回 plugins、分页、source、features 和 cache。

        统计排序需要所选信息源支持统计；网络、数据和能力不支持错误直接抛出。
        id 为 manifest ID，marketplace_id 为市场登记 ID。每页最多 50 项。
        """
        return await self._call(
            "market.search",
            query=query,
            category=category,
            page=page,
            limit=limit,
            sort_by=sort_by,
            compatible_only=compatible_only,
            include_manifest=include_manifest,
            include_stats=include_stats,
            force_refresh=force_refresh,
        )

    async def get_detail(self, plugin_id: str, *, force_refresh: bool = False) -> dict[str, Any]:
        """获取 plugin、releases 及兼容性；支持准确 ID、名称或已登记仓库地址。"""
        return await self._call("market.get_detail", plugin_id=plugin_id, force_refresh=force_refresh)

    async def get_readme(
        self,
        plugin_id: str,
        *,
        max_chars: int = 8000,
        prefer_local: bool = True,
        branch: str = "main",
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """读取 README，先查本地再按需访问市场登记仓库；返回截断标记及来源。

        max_chars 范围 500～20000；远程只读取指定分支的 README.md，不轮询镜像或分支。
        """
        return await self._call(
            "market.get_readme",
            plugin_id=plugin_id,
            max_chars=max_chars,
            prefer_local=prefer_local,
            branch=branch,
            force_refresh=force_refresh,
        )
