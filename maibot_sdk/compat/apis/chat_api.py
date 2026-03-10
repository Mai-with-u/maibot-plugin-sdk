"""旧版 chat_api 兼容层

复刻旧版 src.plugin_system.apis.chat_api 的公开接口。
旧版以 ChatManager 静态方法类 + 模块顶层函数两种用法暴露。
"""

import logging
import warnings
from enum import Enum
from typing import Any

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.chat_api")


def _get_chat():
    ctx = get_context()
    return ctx.chat if ctx else None


class SpecialTypes(Enum):
    """特殊枚举类型"""

    ALL_PLATFORMS = "all_platforms"


class ChatManager:
    """旧版 ChatManager 兼容类

    旧版插件通过 ``chat_api.ChatManager.get_all_streams()`` 调用。
    兼容层下同步方法返回空列表；请迁移到新版 SDK 的异步 chat 能力。
    """

    @staticmethod
    def get_all_streams(platform: str | None = "qq") -> list[Any]:
        warnings.warn("chat_api.ChatManager.get_all_streams() 已弃用", DeprecationWarning, stacklevel=2)
        return []

    @staticmethod
    def get_group_streams(platform: str | None = "qq") -> list[Any]:
        warnings.warn("chat_api.ChatManager.get_group_streams() 已弃用", DeprecationWarning, stacklevel=2)
        return []

    @staticmethod
    def get_private_streams(platform: str | None = "qq") -> list[Any]:
        warnings.warn("chat_api.ChatManager.get_private_streams() 已弃用", DeprecationWarning, stacklevel=2)
        return []


# 旧版模块级快捷函数
def get_all_streams(platform: str | None = "qq") -> list[Any]:
    return ChatManager.get_all_streams(platform)


def get_group_streams(platform: str | None = "qq") -> list[Any]:
    return ChatManager.get_group_streams(platform)


def get_all_group_streams(platform: str | None = "qq") -> list[Any]:
    return ChatManager.get_group_streams(platform)


# 异步版本
async def async_get_all_streams() -> list[Any]:
    """异步获取所有聊天流"""
    chat = _get_chat()
    if chat is None:
        return []
    try:
        return await chat.get_all_streams()
    except Exception as e:
        logger.error(f"chat_api.async_get_all_streams 失败: {e}")
        return []


async def async_get_group_streams() -> list[Any]:
    """异步获取所有群聊流"""
    chat = _get_chat()
    if chat is None:
        return []
    try:
        return await chat.get_group_streams()
    except Exception as e:
        logger.error(f"chat_api.async_get_group_streams 失败: {e}")
        return []
