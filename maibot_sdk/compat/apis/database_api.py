"""旧版 database_api 兼容层

复刻旧版 src.plugin_system.apis.database_api 的公开函数签名。
"""

import logging
import warnings
from typing import Any

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.database_api")


def _get_db() -> Any:
    ctx = get_context()
    return ctx.db if ctx else None


async def db_query(
    model_class: Any,
    data: dict[str, Any] | None = None,
    query_type: str = "get",
    filters: dict[str, Any] | None = None,
    limit: int | None = None,
    order_by: list[str] | None = None,
    single_result: bool = False,
) -> Any:
    """通用数据库查询 (兼容层经由 ctx.db.query 转发)"""
    warnings.warn("database_api.db_query() 已弃用，请使用 self.ctx.db.query()", DeprecationWarning, stacklevel=2)
    db = _get_db()
    if db is None:
        return None if single_result else []
    try:
        return await db.query(
            model=str(model_class) if not isinstance(model_class, str) else model_class,
            query_type=query_type,
            data=data,
            filters=filters,
            limit=limit,
            order_by=order_by,
            single_result=single_result,
        )
    except Exception as e:
        logger.error(f"database_api.db_query 失败: {e}")
        return None if single_result else []


async def store_action_info(
    chat_stream: Any = None,
    action_build_into_prompt: bool = False,
    action_prompt_display: str = "",
    action_done: bool = True,
    thinking_id: str = "",
    action_data: Any = None,
    action_name: str = "",
    action_reasoning: str = "",
    **kwargs: Any,
) -> None:
    """存储动作信息 (兼容层经由 ctx.db.save 转发)"""
    warnings.warn("database_api.store_action_info() 已弃用", DeprecationWarning, stacklevel=2)
    db = _get_db()
    if db is None:
        return
    try:
        await db.save(
            table="action_info",
            data={
                "action_build_into_prompt": action_build_into_prompt,
                "action_prompt_display": action_prompt_display,
                "action_done": action_done,
                "thinking_id": thinking_id,
                "action_data": action_data,
                "action_name": action_name,
                "action_reasoning": action_reasoning,
                **kwargs,
            },
        )
    except Exception as e:
        logger.error(f"database_api.store_action_info 失败: {e}")
