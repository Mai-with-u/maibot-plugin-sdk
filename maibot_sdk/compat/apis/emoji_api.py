"""旧版 emoji_api 兼容层

复刻旧版 src.plugin_system.apis.emoji_api 的公开函数签名。
"""

import logging
import warnings

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.emoji_api")


def _get_emoji():
    ctx = get_context()
    return ctx.emoji if ctx else None


async def get_by_description(description: str) -> tuple[str, str, str] | None:
    """根据描述获取表情包

    Returns:
        (base64编码, 描述, 情感标签) 或 None
    """
    warnings.warn("emoji_api.get_by_description() 已弃用，请使用 self.ctx.emoji.get_by_description()", DeprecationWarning, stacklevel=2)
    emoji = _get_emoji()
    if emoji is None:
        return None
    try:
        result = await emoji.get_by_description(description=description)
        if isinstance(result, (tuple, list)) and len(result) >= 3:
            return (result[0], result[1], result[2])
        return result
    except Exception as e:
        logger.error(f"emoji_api.get_by_description 失败: {e}")
        return None


async def get_random(count: int | None = 1) -> list[tuple[str, str, str]]:
    """随机获取表情包"""
    warnings.warn("emoji_api.get_random() 已弃用，请使用 self.ctx.emoji.get_random()", DeprecationWarning, stacklevel=2)
    emoji = _get_emoji()
    if emoji is None:
        return []
    try:
        return await emoji.get_random(count=count or 1)
    except Exception as e:
        logger.error(f"emoji_api.get_random 失败: {e}")
        return []


def get_count() -> int:
    """获取表情数量 (同步，兼容层下返回 0)"""
    warnings.warn("emoji_api.get_count() 已弃用", DeprecationWarning, stacklevel=2)
    return 0


async def async_get_count() -> int:
    """异步获取表情数量"""
    emoji = _get_emoji()
    if emoji is None:
        return 0
    try:
        return await emoji.get_count()
    except Exception as e:
        logger.error(f"emoji_api.async_get_count 失败: {e}")
        return 0
