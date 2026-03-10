"""旧版 frequency_api 兼容层

复刻旧版 src.plugin_system.apis.frequency_api 的公开函数签名。
"""

import logging
import warnings
from typing import Any

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.frequency_api")


def _get_frequency():
    ctx = get_context()
    return ctx.frequency if ctx else None


def get_current_talk_value(chat_id: str) -> float:
    """获取当前聊天话题值 (同步，兼容层下返回 0.0)"""
    warnings.warn(
        "frequency_api.get_current_talk_value() 已弃用，请使用 await self.ctx.frequency.get_current_talk_value()",
        DeprecationWarning, stacklevel=2,
    )
    return 0.0


def set_talk_frequency_adjust(chat_id: str, talk_frequency_adjust: float) -> None:
    """设置说话频率调整 (同步，兼容层下为空操作)"""
    warnings.warn("frequency_api.set_talk_frequency_adjust() 已弃用", DeprecationWarning, stacklevel=2)


def get_talk_frequency_adjust(chat_id: str) -> float:
    """获取说话频率调整 (同步，兼容层下返回 1.0)"""
    warnings.warn("frequency_api.get_talk_frequency_adjust() 已弃用", DeprecationWarning, stacklevel=2)
    return 1.0


# 异步版本
async def async_get_current_talk_value(chat_id: str) -> float:
    freq = _get_frequency()
    if freq is None:
        return 0.0
    try:
        return await freq.get_current_talk_value(chat_id=chat_id)
    except Exception as e:
        logger.error(f"frequency_api.async_get_current_talk_value 失败: {e}")
        return 0.0


async def async_set_adjust(chat_id: str, value: float) -> Any:
    freq = _get_frequency()
    if freq is None:
        return None
    try:
        return await freq.set_adjust(chat_id=chat_id, value=value)
    except Exception as e:
        logger.error(f"frequency_api.async_set_adjust 失败: {e}")
        return None


async def async_get_adjust(chat_id: str) -> float:
    freq = _get_frequency()
    if freq is None:
        return 1.0
    try:
        return await freq.get_adjust(chat_id=chat_id)
    except Exception as e:
        logger.error(f"frequency_api.async_get_adjust 失败: {e}")
        return 1.0
