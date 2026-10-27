"""Bot 内部统一聊天：主人与麦麦唯一固定的私聊聊天流，网页聊天室与插件界面共用（host >= 1.3.16）。"""

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext


class InternalChatCapability:
    def __init__(self, ctx: "PluginContext") -> None:
        self._ctx = ctx

    async def identity(self) -> dict[str, Any]:
        """返回内部统一聊天的 platform=internal 与主人 user_id=owner。

        Requires manifest capability internal_chat.identity. 麦麦发给主人的消息可在 send_service.after_send
        中按 message["platform"] 等于 platform、message_info.additional_config.platform_io_target_user_id
        等于 user_id 识别；聊天流可用 ctx.chat.get_all_streams(platform=...) 按 user_id 找到。
        """
        return cast(dict[str, Any], await self._ctx.call_capability("internal_chat.identity"))

    async def send(self, text: str) -> dict[str, Any]:
        """代主人向内部统一聊天说一句话，返回 message_id；在线的网页聊天室会同步显示。

        Requires manifest capability internal_chat.send. text 去除首尾空白后 1～2000 字符。
        称呼使用网页聊天室设置的共享昵称，插件不能另行指定。消息记录本插件为来源，不具备受保护命令权限。
        """
        return cast(
            dict[str, Any],
            await self._ctx.call_capability("internal_chat.send", text=text),
        )
