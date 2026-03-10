"""旧版 BaseEventHandler 抽象基类 (兼容层)

完整复刻旧版 src.plugin_system.base.base_events_handler.BaseEventHandler 的接口和行为。
EventHandler 的 send 方法与 Action/Command 不同：stream_id 是第一个参数，
因为 EventHandler 可以在不同的聊天流中发送消息。
"""

import warnings
from abc import ABC, abstractmethod
from typing import Any

from maibot_sdk.compat.base.component_types import ComponentType, EventHandlerInfo, EventType


class BaseEventHandler(ABC):
    """EventHandler 组件基类

    EventHandler 用于监听和处理系统事件（消息到达、定时器等）。

    与 Action/Command 不同，EventHandler 的 send 方法需要显式提供 stream_id，
    因为事件处理器可能需要向不同的聊天流发送消息。
    """

    # ── 类属性 ────────────────────────────────────────────────
    event_type: EventType = EventType.ON_MESSAGE
    handler_name: str = ""
    handler_description: str = ""
    weight: int = 0
    intercept_message: bool = False

    def __init__(self) -> None:
        self.plugin_config: dict[str, Any] = {}
        self.plugin_name: str = ""
        self.log_prefix: str = "[EventHandler]"

    def set_plugin_config(self, config: dict[str, Any]) -> None:
        """由框架注入插件配置"""
        self.plugin_config = config or {}

    def set_plugin_name(self, name: str) -> None:
        """由框架注入插件名称"""
        self.plugin_name = name

    @abstractmethod
    async def execute(self, message: Any) -> tuple[bool, bool, str | None, None, None]:
        """处理事件

        Args:
            message: MaiMessages 对象

        Returns:
            Tuple[bool, bool, Optional[str], None, None]:
                (是否处理, 是否拦截, 可选回复, None, None)
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

    # ── 发送方法 (stream_id 作为第一参数) ─────────────────────

    async def send_text(
        self,
        stream_id: str,
        content: str,
        set_reply: bool = False,
        reply_message: Any = None,
        typing: bool = False,
        storage_message: bool = True,
    ) -> bool:
        """发送文本消息到指定聊天流"""
        warnings.warn("BaseEventHandler.send_text() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        if not stream_id:
            return False
        return await send_api.text_to_stream(
            text=content,
            stream_id=stream_id,
            set_reply=set_reply,
            reply_message=reply_message,
            typing=typing,
            storage_message=storage_message,
        )

    async def send_image(
        self,
        stream_id: str,
        image_base64: str,
        set_reply: bool = False,
        reply_message: Any = None,
        storage_message: bool = True,
    ) -> bool:
        """发送图片到指定聊天流"""
        warnings.warn("BaseEventHandler.send_image() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

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
        stream_id: str,
        emoji_base64: str,
        set_reply: bool = False,
        reply_message: Any = None,
        storage_message: bool = True,
    ) -> bool:
        """发送表情包到指定聊天流"""
        warnings.warn("BaseEventHandler.send_emoji() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        if not stream_id:
            return False
        return await send_api.emoji_to_stream(
            emoji_base64=emoji_base64,
            stream_id=stream_id,
            set_reply=set_reply,
            reply_message=reply_message,
            storage_message=storage_message,
        )

    async def send_voice(
        self,
        stream_id: str,
        voice_base64: str,
    ) -> bool:
        """发送语音消息到指定聊天流"""
        warnings.warn("BaseEventHandler.send_voice() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        if not stream_id:
            return False
        return await send_api.custom_to_stream(
            message_type="voice",
            content=voice_base64,
            stream_id=stream_id,
            storage_message=False,
        )

    async def send_command(
        self,
        stream_id: str,
        command_name: str,
        args: dict[str, Any] | None = None,
        display_message: str = "",
        storage_message: bool = True,
    ) -> bool:
        """发送命令消息到指定聊天流"""
        warnings.warn("BaseEventHandler.send_command() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        if not stream_id:
            return False
        command_data = {"name": command_name, "args": args or {}}
        return await send_api.command_to_stream(
            command=command_data,
            stream_id=stream_id,
            storage_message=storage_message,
            display_message=display_message,
        )

    async def send_custom(
        self,
        stream_id: str,
        message_type: str,
        content: Any,
        display_message: str = "",
        typing: bool = False,
        set_reply: bool = False,
        reply_message: Any = None,
        storage_message: bool = True,
    ) -> bool:
        """发送自定义类型消息到指定聊天流"""
        warnings.warn("BaseEventHandler.send_custom() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

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

    async def send_hybrid(
        self,
        stream_id: str,
        message_tuple_list: list[tuple[Any, str]],
        typing: bool = False,
        set_reply: bool = False,
        reply_message: Any = None,
        storage_message: bool = True,
    ) -> bool:
        """发送混合类型消息到指定聊天流"""
        warnings.warn("BaseEventHandler.send_hybrid() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

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
        stream_id: str,
        messages_list: list[Any],
        storage_message: bool = True,
    ) -> bool:
        """转发消息到指定聊天流"""
        warnings.warn("BaseEventHandler.send_forward() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        if not stream_id:
            return False
        return await send_api.custom_reply_set_to_stream(
            reply_set={"forward": messages_list},
            stream_id=stream_id,
            storage_message=storage_message,
        )

    # ── classmethod ───────────────────────────────────────────

    @classmethod
    def get_handler_info(cls) -> EventHandlerInfo:
        """从类属性生成 EventHandlerInfo"""
        return EventHandlerInfo(
            name=cls.handler_name,
            component_type=ComponentType.EVENT_HANDLER,
            description=cls.handler_description,
            event_type=cls.event_type,
            weight=cls.weight,
            intercept_message=cls.intercept_message,
        )
