"""旧版 person_api 兼容层

复刻旧版 src.plugin_system.apis.person_api 的公开函数签名。
"""

import logging
import warnings
from typing import Any

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.person_api")


def _get_person() -> Any:
    ctx = get_context()
    return ctx.person if ctx else None


def get_person_id(platform: str, user_id: Any) -> str:
    """根据平台和用户 ID 获取 person_id (同步，兼容层下返回空)"""
    warnings.warn(
        "person_api.get_person_id() 已弃用，请使用 await self.ctx.person.get_id()",
        DeprecationWarning,
        stacklevel=2,
    )
    return ""


async def async_get_person_id(platform: str, user_id: Any) -> str:
    """异步版获取 person_id"""
    person = _get_person()
    if person is None:
        return ""
    try:
        return await person.get_id(platform=platform, user_id=str(user_id))
    except Exception as e:
        logger.error(f"person_api.async_get_person_id 失败: {e}")
        return ""


async def get_person_value(person_id: str, field_name: str, default: Any = None) -> Any:
    """获取用户信息字段"""
    warnings.warn(
        "person_api.get_person_value() 已弃用，请使用 self.ctx.person.get_value()",
        DeprecationWarning,
        stacklevel=2,
    )
    person = _get_person()
    if person is None:
        return default
    try:
        result = await person.get_value(person_id=person_id, field_name=field_name)
        return result if result is not None else default
    except Exception as e:
        logger.error(f"person_api.get_person_value 失败: {e}")
        return default


def get_person_id_by_name(person_name: str) -> str:
    """根据用户名获取 person_id (同步，兼容层下返回空)"""
    warnings.warn("person_api.get_person_id_by_name() 已弃用", DeprecationWarning, stacklevel=2)
    return ""


async def async_get_person_id_by_name(person_name: str) -> str:
    """异步版根据用户名获取 person_id"""
    person = _get_person()
    if person is None:
        return ""
    try:
        return await person.get_id_by_name(person_name=person_name)
    except Exception as e:
        logger.error(f"person_api.async_get_person_id_by_name 失败: {e}")
        return ""
