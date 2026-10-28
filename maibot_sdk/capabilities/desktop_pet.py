"""控制主程序内置桌宠（MaiBot 1.3.16+，仅 Windows）。"""

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext


class DesktopPetCapability:
    def __init__(self, ctx: "PluginContext") -> None:
        self._ctx = ctx

    async def status(self) -> dict[str, Any]:
        """查询 enabled/supported/running/ready/visible/error。需要 desktop_pet.status。"""
        return cast(dict[str, Any], await self._ctx.call_capability("desktop_pet.status"))

    async def show(self) -> dict[str, Any]:
        """显示已启用并就绪的桌宠，不更改启用配置。需要 desktop_pet.show。"""
        return cast(dict[str, Any], await self._ctx.call_capability("desktop_pet.show"))

    async def hide(self) -> dict[str, Any]:
        """隐藏窗口，保留进程、待办和聊天连接。需要 desktop_pet.hide。"""
        return cast(dict[str, Any], await self._ctx.call_capability("desktop_pet.hide"))

    async def say(self, text: str) -> dict[str, Any]:
        """显示 1～2000 字符的纯文本气泡，不写聊天历史/记忆，不自动显示隐藏的窗口。

        需要 desktop_pet.say。只有窗口确认显示指令后才返回；内容作为文本渲染，不能运行脚本。
        """
        return cast(dict[str, Any], await self._ctx.call_capability("desktop_pet.say", text=text))

    async def set_thinking(self, active: bool) -> dict[str, Any]:
        """开启/结束思考动画；聊天回复也会更新动画。需要 desktop_pet.set_thinking。"""
        return cast(dict[str, Any], await self._ctx.call_capability("desktop_pet.set_thinking", active=active))

    async def get_skin(self) -> dict[str, Any]:
        """查询当前皮肤 ID、名称和版本。"""
        return cast(dict[str, Any], await self._ctx.call_capability("desktop_pet.get_skin"))

    async def list_animations(self) -> dict[str, Any]:
        """返回当前皮肤的动画列表及标准事件映射。"""
        return cast(dict[str, Any], await self._ctx.call_capability("desktop_pet.list_animations"))

    async def play_animation(self, name: str, repeat: int = 1) -> dict[str, Any]:
        """播放有限次数的动作，总时长最多 30 秒；返回播放 ID，不代表播放结束。"""
        return cast(
            dict[str, Any],
            await self._ctx.call_capability("desktop_pet.play_animation", name=name, repeat=repeat),
        )

    async def play_event(self, event: str) -> dict[str, Any]:
        """播放 click/happy/error/greeting 标准事件，具体动作由当前皮肤决定。"""
        return cast(dict[str, Any], await self._ctx.call_capability("desktop_pet.play_event", event=event))

    async def stop_animation(self, playback_id: str) -> dict[str, Any]:
        """停止本插件发起的动画。"""
        return cast(
            dict[str, Any],
            await self._ctx.call_capability("desktop_pet.stop_animation", playback_id=playback_id),
        )

    async def animation_status(self, playback_id: str) -> dict[str, Any]:
        """查询本插件的播放记录；窗口最多保留 128 条已结束记录。"""
        return cast(
            dict[str, Any],
            await self._ctx.call_capability("desktop_pet.animation_status", playback_id=playback_id),
        )
