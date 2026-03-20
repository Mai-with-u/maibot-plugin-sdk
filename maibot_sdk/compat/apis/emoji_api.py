"""旧版 emoji_api 兼容层

复刻旧版 src.plugin_system.apis.emoji_api 的公开函数签名。
"""

import logging
import warnings
from typing import Any

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.emoji_api")


def _get_emoji() -> Any:
    """获取当前上下文中的表情能力代理。

    Returns:
        Any: 兼容层中的 emoji 能力对象；若当前没有上下文则返回 ``None``。
    """
    ctx = get_context()
    return ctx.emoji if ctx else None


def _normalize_emoji_result(result: Any) -> dict[str, Any] | None:
    """将旧版或新版表情返回值归一化为字典。

    Args:
        result: 底层 emoji 能力返回的原始对象。

    Returns:
        dict[str, Any] | None: 归一化后的表情信息字典；若无法识别则返回 ``None``。
    """
    if isinstance(result, dict):
        return {str(key): value for key, value in result.items()}

    if isinstance(result, (tuple, list)) and len(result) >= 3:
        return {
            "base64": result[0],
            "description": result[1],
            "emotion": result[2],
        }

    if all(hasattr(result, field_name) for field_name in ("base64", "description", "emotion")):
        return {
            "base64": result.base64,
            "description": result.description,
            "emotion": result.emotion,
        }

    return None


async def get_by_description(description: str) -> dict[str, Any] | None:
    """根据描述获取表情包。

    Args:
        description: 用于检索表情包的描述文本。

    Returns:
        归一化后的表情包字典或 None。
        典型字段包括 ``base64``、``description``、``emotion``。
    """
    warnings.warn(
        "emoji_api.get_by_description() 已弃用，请使用 self.ctx.emoji.get_by_description()",
        DeprecationWarning,
        stacklevel=2,
    )
    emoji = _get_emoji()
    if emoji is None:
        return None
    try:
        result = await emoji.get_by_description(description=description)
        return _normalize_emoji_result(result)
    except Exception as e:
        logger.error(f"emoji_api.get_by_description 失败: {e}")
        return None


async def get_random(count: int | None = 1) -> list[dict[str, Any]]:
    """随机获取表情包。

    Returns:
        归一化后的表情包字典列表。
    """
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
