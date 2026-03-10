"""旧版 BaseCommand 抽象基类 (兼容层)

完整复刻旧版 src.plugin_system.base.base_command.BaseCommand 的接口和行为。
"""

import warnings
from abc import ABC, abstractmethod
from typing import Any

from maibot_sdk.compat.base.component_types import CommandInfo, ComponentType


class BaseCommand(ABC):
    """Command 组件基类

    Command 是插件的一种组件类型，用于处理命令请求。

    子类可以通过类属性定义命令模式：
    - command_pattern: 命令匹配的正则表达式
    """

    # ── 类属性 ────────────────────────────────────────────────
    command_name: str = ""
    command_description: str = ""
    command_pattern: str = r""

    def __init__(self, message: Any = None, plugin_config: dict[str, Any] | None = None, **kwargs: Any):
        """初始化 Command 组件

        Args:
            message: 接收到的消息对象 (SessionMessage)
            plugin_config: 插件配置字典
        """
        self.message = message
        self.matched_groups: dict[str, str] = {}
        self.plugin_config = plugin_config or {}
        self.log_prefix = "[Command]"

        # 运行时注入的 stream_id
        self._stream_id: str = ""

    def set_matched_groups(self, groups: dict[str, str]) -> None:
        """设置正则表达式匹配的命名组"""
        self.matched_groups = groups

    @abstractmethod
    async def execute(self) -> tuple[bool, str | None, int]:
        """执行 Command 的抽象方法，子类必须实现

        Returns:
            Tuple[bool, Optional[str], int]: (是否执行成功, 可选回复消息, 拦截力度 0/1/2)
        """
        ...

    # ── 配置访问 ──────────────────────────────────────────────

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取插件配置值，使用嵌套键访问"""
        if not self.plugin_config:
            return default
        keys = key.split(".")
        current: Any = self.plugin_config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    # ── 发送方法 (转发到 send_api 兼容模块) ─────────────────

    def _get_stream_id(self) -> str:
        """获取当前命令的目标 stream_id"""
        if self._stream_id:
            return self._stream_id
        if self.message and hasattr(self.message, "session_id"):
            return str(self.message.session_id)
        return ""

    async def send_text(
        self,
        content: str,
        set_reply: bool = False,
        reply_message: Any = None,
        storage_message: bool = True,
    ) -> bool:
        """发送回复消息"""
        warnings.warn("BaseCommand.send_text() 已弃用，请使用 self.ctx.send.text()", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self._get_stream_id()
        if not stream_id:
            return False
        return await send_api.text_to_stream(
            text=content,
            stream_id=stream_id,
            set_reply=set_reply,
            reply_message=reply_message,
            storage_message=storage_message,
        )

    async def send_image(
        self,
        image_base64: str,
        set_reply: bool = False,
        reply_message: Any = None,
        storage_message: bool = True,
    ) -> bool:
        """发送图片"""
        warnings.warn("BaseCommand.send_image() 已弃用，请使用 self.ctx.send.image()", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self._get_stream_id()
        if not stream_id:
            return False
        return await send_api.image_to_stream(
            image_base64=image_base64,
            stream_id=stream_id,
            set_reply=set_reply,
            reply_message=reply_message,
            storage_message=storage_message,
        )

    async def send_emoji(
        self,
        emoji_base64: str,
        set_reply: bool = False,
        reply_message: Any = None,
        storage_message: bool = True,
    ) -> bool:
        """发送表情包"""
        warnings.warn("BaseCommand.send_emoji() 已弃用，请使用 self.ctx.send.emoji()", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self._get_stream_id()
        if not stream_id:
            return False
        return await send_api.emoji_to_stream(
            emoji_base64=emoji_base64,
            stream_id=stream_id,
            set_reply=set_reply,
            reply_message=reply_message,
            storage_message=storage_message,
        )

    async def send_command(
        self,
        command_name: str,
        args: dict[str, Any] | None = None,
        display_message: str = "",
        storage_message: bool = True,
    ) -> bool:
        """发送命令消息"""
        warnings.warn(
            "BaseCommand.send_command() 已弃用，请使用 self.ctx.send.command()",
            DeprecationWarning,
            stacklevel=2,
        )
        from maibot_sdk.compat.apis import send_api

        stream_id = self._get_stream_id()
        if not stream_id:
            return False
        command_data = {"name": command_name, "args": args or {}}
        return await send_api.command_to_stream(
            command=command_data,
            stream_id=stream_id,
            storage_message=storage_message,
            display_message=display_message,
        )

    async def send_voice(self, voice_base64: str) -> bool:
        """发送语音消息"""
        warnings.warn("BaseCommand.send_voice() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self._get_stream_id()
        if not stream_id:
            return False
        return await send_api.custom_to_stream(
            message_type="voice",
            content=voice_base64,
            stream_id=stream_id,
            storage_message=False,
        )

    async def send_hybrid(
        self,
        message_tuple_list: list[tuple[Any, str]],
        typing: bool = False,
        set_reply: bool = False,
        reply_message: Any = None,
        storage_message: bool = True,
    ) -> bool:
        """发送混合类型消息"""
        warnings.warn("BaseCommand.send_hybrid() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self._get_stream_id()
        if not stream_id:
            return False
        return await send_api.custom_reply_set_to_stream(
            reply_set={"hybrid": message_tuple_list},
            stream_id=stream_id,
            typing=typing,
            set_reply=set_reply,
            reply_message=reply_message,
            storage_message=storage_message,
        )

    async def send_forward(
        self,
        messages_list: list[Any],
        storage_message: bool = True,
    ) -> bool:
        """转发消息"""
        warnings.warn("BaseCommand.send_forward() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self._get_stream_id()
        if not stream_id:
            return False
        return await send_api.custom_reply_set_to_stream(
            reply_set={"forward": messages_list},
            stream_id=stream_id,
            storage_message=storage_message,
        )

    async def send_custom(
        self,
        message_type: str,
        content: Any,
        display_message: str = "",
        typing: bool = False,
        set_reply: bool = False,
        reply_message: Any = None,
        storage_message: bool = True,
    ) -> bool:
        """发送自定义类型消息"""
        warnings.warn("BaseCommand.send_custom() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self._get_stream_id()
        if not stream_id:
            return False
        return await send_api.custom_to_stream(
            message_type=message_type,
            content=content,
            stream_id=stream_id,
            display_message=display_message,
            typing=typing,
            set_reply=set_reply,
            reply_message=reply_message,
            storage_message=storage_message,
        )

    # ── classmethod ───────────────────────────────────────────

    @classmethod
    def get_command_info(cls) -> CommandInfo:
        """从类属性生成 CommandInfo"""
        return CommandInfo(
            name=cls.command_name,
            component_type=ComponentType.COMMAND,
            description=cls.command_description,
            command_pattern=cls.command_pattern,
        )
