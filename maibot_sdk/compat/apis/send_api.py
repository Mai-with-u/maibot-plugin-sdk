"""旧版 send_api 兼容层

复刻旧版 src.plugin_system.apis.send_api 的所有公开函数签名，
内部通过 PluginContext 的 send 能力代理进行转发。
"""

import logging
import warnings
from typing import Any

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.send_api")


def _get_send():
    ctx = get_context()
    if ctx is None:
        return None
    return ctx.send


# ===========================================================================
# text_to_stream / text_to_group / text_to_user
# ===========================================================================

async def text_to_stream(
    text: str,
    stream_id: str,
    set_reply: bool = False,
    reply_message: Any = None,
    typing: bool = False,
    storage_message: bool = True,
    **kwargs: Any,
) -> bool:
    """发送文本消息到指定聊天流"""
    warnings.warn("send_api.text_to_stream() 已弃用，请使用 self.ctx.send.text()", DeprecationWarning, stacklevel=2)
    send = _get_send()
    if send is None:
        logger.warning("send_api: PluginContext 未注入，无法发送消息")
        return False
    try:
        await send.text(
            text=text, stream_id=stream_id,
            set_reply=set_reply, reply_message=reply_message,
            typing=typing, storage_message=storage_message,
            **kwargs,
        )
        return True
    except Exception as e:
        logger.error(f"send_api.text_to_stream 失败: {e}")
        return False


async def text_to_group(text: str, group_id: str, **kwargs: Any) -> bool:
    """发送文本到群聊 (旧版兼容)"""
    warnings.warn("send_api.text_to_group() 已弃用", DeprecationWarning, stacklevel=2)
    return await text_to_stream(text=text, stream_id=group_id, **kwargs)


async def text_to_user(text: str, user_id: str, **kwargs: Any) -> bool:
    """发送文本到私聊 (旧版兼容)"""
    warnings.warn("send_api.text_to_user() 已弃用", DeprecationWarning, stacklevel=2)
    return await text_to_stream(text=text, stream_id=user_id, **kwargs)


# ===========================================================================
# emoji_to_stream
# ===========================================================================

async def emoji_to_stream(
    emoji_base64: str,
    stream_id: str,
    set_reply: bool = False,
    reply_message: Any = None,
    storage_message: bool = True,
    **kwargs: Any,
) -> bool:
    """发送表情到指定聊天流"""
    warnings.warn("send_api.emoji_to_stream() 已弃用，请使用 self.ctx.send.emoji()", DeprecationWarning, stacklevel=2)
    send = _get_send()
    if send is None:
        return False
    try:
        await send.emoji(
            emoji_data=emoji_base64, stream_id=stream_id,
            set_reply=set_reply, reply_message=reply_message,
            storage_message=storage_message, **kwargs,
        )
        return True
    except Exception as e:
        logger.error(f"send_api.emoji_to_stream 失败: {e}")
        return False


# ===========================================================================
# image_to_stream
# ===========================================================================

async def image_to_stream(
    image_base64: str,
    stream_id: str,
    set_reply: bool = False,
    reply_message: Any = None,
    storage_message: bool = True,
    **kwargs: Any,
) -> bool:
    """发送图片到指定聊天流"""
    warnings.warn("send_api.image_to_stream() 已弃用，请使用 self.ctx.send.image()", DeprecationWarning, stacklevel=2)
    send = _get_send()
    if send is None:
        return False
    try:
        await send.image(
            image_data=image_base64, stream_id=stream_id,
            set_reply=set_reply, reply_message=reply_message,
            storage_message=storage_message, **kwargs,
        )
        return True
    except Exception as e:
        logger.error(f"send_api.image_to_stream 失败: {e}")
        return False


# ===========================================================================
# command_to_stream
# ===========================================================================

async def command_to_stream(
    command: Any,
    stream_id: str,
    storage_message: bool = True,
    display_message: str = "",
    **kwargs: Any,
) -> bool:
    """发送命令到指定聊天流"""
    warnings.warn(
        "send_api.command_to_stream() 已弃用，请使用 self.ctx.send.command()",
        DeprecationWarning,
        stacklevel=2,
    )
    send = _get_send()
    if send is None:
        return False
    try:
        # 旧版 command 可能是 dict，新版接收 str
        cmd_str = command if isinstance(command, str) else str(command)
        await send.command(
            command=cmd_str, stream_id=stream_id,
            storage_message=storage_message, display_message=display_message,
            **kwargs,
        )
        return True
    except Exception as e:
        logger.error(f"send_api.command_to_stream 失败: {e}")
        return False


# ===========================================================================
# custom_to_stream
# ===========================================================================

async def custom_to_stream(
    message_type: str,
    content: Any,
    stream_id: str,
    display_message: str = "",
    typing: bool = False,
    set_reply: bool = False,
    reply_message: Any = None,
    storage_message: bool = True,
    **kwargs: Any,
) -> bool:
    """发送自定义类型消息"""
    warnings.warn("send_api.custom_to_stream() 已弃用，请使用 self.ctx.send.custom()", DeprecationWarning, stacklevel=2)
    send = _get_send()
    if send is None:
        return False
    try:
        await send.custom(
            custom_type=message_type, data=content, stream_id=stream_id,
            display_message=display_message, typing=typing,
            set_reply=set_reply, reply_message=reply_message,
            storage_message=storage_message, **kwargs,
        )
        return True
    except Exception as e:
        logger.error(f"send_api.custom_to_stream 失败: {e}")
        return False


# ===========================================================================
# custom_reply_set_to_stream (ReplySetModel → custom)
# ===========================================================================

async def custom_reply_set_to_stream(
    reply_set: Any,
    stream_id: str,
    typing: bool = False,
    set_reply: bool = False,
    reply_message: Any = None,
    storage_message: bool = True,
    **kwargs: Any,
) -> bool:
    """发送 ReplySetModel 消息 (兼容层将其序列化为 custom 消息)"""
    warnings.warn("send_api.custom_reply_set_to_stream() 已弃用", DeprecationWarning, stacklevel=2)
    send = _get_send()
    if send is None:
        return False
    try:
        # 将 ReplySetModel 转为可序列化的 dict
        data = reply_set.to_dict() if hasattr(reply_set, "to_dict") else str(reply_set)
        await send.custom(
            custom_type="reply_set", data=data, stream_id=stream_id,
            typing=typing, set_reply=set_reply, reply_message=reply_message,
            storage_message=storage_message, **kwargs,
        )
        return True
    except Exception as e:
        logger.error(f"send_api.custom_reply_set_to_stream 失败: {e}")
        return False


# ===========================================================================
# custom_message (旧版通用发送)
# ===========================================================================

async def custom_message(
    message_type: str,
    content: Any,
    target_id: str,
    is_group: bool = True,
    **kwargs: Any,
) -> bool:
    """通用消息发送 (旧版兼容)"""
    warnings.warn("send_api.custom_message() 已弃用", DeprecationWarning, stacklevel=2)
    return await custom_to_stream(
        message_type=message_type, content=content,
        stream_id=target_id, **kwargs,
    )
