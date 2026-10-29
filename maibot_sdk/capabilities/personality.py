"""全局备选人设：查询与持久化切换，需要支持 personality.* 的 Host。"""

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext


class PersonalityCapability:
    def __init__(self, ctx: "PluginContext") -> None:
        self._ctx = ctx

    async def list(self) -> dict[str, Any]:
        """返回 {profiles: [...]}；需 personality.list 权限。"""
        return cast(dict[str, Any], await self._ctx.call_capability("personality.list"))

    async def get_current(self) -> dict[str, Any]:
        """返回当前 name 与五个人设字段；未命名时 name 为空。需 personality.get_current。"""
        return cast(dict[str, Any], await self._ctx.call_capability("personality.get_current"))

    async def switch(self, name: str) -> dict[str, Any]:
        """按名称精确匹配，保存并热重载，返回 {changed, current}。需 personality.switch。

        作用于所有会话；保留切换前编辑，同名切换不覆盖当前编辑。
        未找到人设、无权限或热重载失败时抛出能力调用异常。
        """
        return cast(dict[str, Any], await self._ctx.call_capability("personality.switch", name=name))
