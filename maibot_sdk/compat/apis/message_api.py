"""旧版 message_api 兼容层

复刻旧版 src.plugin_system.apis.message_api 的公开函数签名。
注意：旧版很多方法是 **同步** 的（直接查数据库），新版需要 RPC，因此
这里的同步签名保持兼容但实际功能受限 —— 在同步上下文中返回空结果。
若在异步上下文中调用，请改用 await 版本或迁移到新版 SDK。
"""

import logging
import warnings
from typing import Any

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.message_api")


def _get_message():
    ctx = get_context()
    return ctx.message if ctx else None


# ===========================================================================
# 同步方法 (旧版签名，新架构下功能受限)
# ===========================================================================

def get_messages_by_time(
    start_time: float,
    end_time: float,
    limit: int = 0,
    limit_mode: str = "latest",
    filter_mai: bool = False,
) -> list[Any]:
    """获取时间范围内的消息 (同步，兼容层下返回空列表)"""
    warnings.warn(
        "message_api.get_messages_by_time() 已弃用且在新架构下为异步，请使用 await self.ctx.message.get_by_time()",
        DeprecationWarning, stacklevel=2,
    )
    return []


def get_messages_by_time_in_chat(
    chat_id: str,
    start_time: float,
    end_time: float,
    limit: int = 0,
    limit_mode: str = "latest",
    filter_mai: bool = False,
    filter_command: bool = False,
    filter_intercept_message_level: int | None = None,
) -> list[Any]:
    """获取指定聊天中时间范围内的消息"""
    warnings.warn(
        "message_api.get_messages_by_time_in_chat() 已弃用，请使用 await self.ctx.message.get_by_time_in_chat()",
        DeprecationWarning, stacklevel=2,
    )
    return []


def count_new_messages(chat_id: str, start_time: float, end_time: float) -> int:
    """计算新消息数量"""
    warnings.warn(
        "message_api.count_new_messages() 已弃用，请使用 await self.ctx.message.count_new()",
        DeprecationWarning, stacklevel=2,
    )
    return 0


def build_readable_messages(messages: Any, **kwargs: Any) -> str:
    """将消息列表构建成可读文本"""
    warnings.warn("message_api.build_readable_messages() 已弃用", DeprecationWarning, stacklevel=2)
    return ""


def build_readable_messages_with_list(messages: Any, **kwargs: Any) -> list[str]:
    """将消息列表构建为可读文本列表"""
    warnings.warn("message_api.build_readable_messages_with_list() 已弃用", DeprecationWarning, stacklevel=2)
    return []


def get_person_id_list(chat_id: str, **kwargs: Any) -> list[str]:
    """获取聊天中的用户 ID 列表"""
    warnings.warn("message_api.get_person_id_list() 已弃用", DeprecationWarning, stacklevel=2)
    return []


def filter_mai_messages(messages: list[Any]) -> list[Any]:
    """过滤掉机器人自身消息"""
    warnings.warn("message_api.filter_mai_messages() 已弃用", DeprecationWarning, stacklevel=2)
    return messages


# ===========================================================================
# 异步版本 (新增，供有能力迁移的插件使用)
# ===========================================================================

async def async_get_messages_by_time(
    start_time: float, end_time: float, **kwargs: Any
) -> list[Any]:
    """异步版获取时间范围内的消息"""
    msg = _get_message()
    if msg is None:
        return []
    try:
        return await msg.get_by_time(
            start_time=str(start_time), end_time=str(end_time), **kwargs
        )
    except Exception as e:
        logger.error(f"async_get_messages_by_time 失败: {e}")
        return []


async def async_get_messages_by_time_in_chat(
    chat_id: str, start_time: float, end_time: float, **kwargs: Any
) -> list[Any]:
    """异步版获取指定聊天中的消息"""
    msg = _get_message()
    if msg is None:
        return []
    try:
        return await msg.get_by_time_in_chat(
            chat_id=chat_id,
            start_time=str(start_time), end_time=str(end_time), **kwargs
        )
    except Exception as e:
        logger.error(f"async_get_messages_by_time_in_chat 失败: {e}")
        return []


async def async_count_new_messages(chat_id: str, since: float) -> int:
    """异步版计算新消息数量"""
    msg = _get_message()
    if msg is None:
        return 0
    try:
        return await msg.count_new(chat_id=chat_id, since=str(since))
    except Exception as e:
        logger.error(f"async_count_new_messages 失败: {e}")
        return 0
