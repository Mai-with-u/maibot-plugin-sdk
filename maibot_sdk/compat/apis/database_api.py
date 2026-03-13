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
        model_name = model_class if isinstance(model_class, str) else getattr(model_class, "__name__", str(model_class))

        if query_type == "get":
            result = await db.query(
                model_name=model_name,
                query_type="get",
                filters=filters or data or {},
                order_by=order_by,
                limit=1 if single_result and limit is None else limit,
                single_result=single_result,
            )
            return result

        if query_type == "count":
            return await db.count(
                model_name=model_name,
                filters=filters or data or {},
            )

        if query_type == "delete":
            return await db.delete(
                model_name=model_name,
                filters=filters or data or {},
            )

        if query_type in {"save", "insert", "update"}:
            payload = data or {}
            if not isinstance(payload, dict):
                logger.error("database_api.db_query 失败: save/update 查询要求 data 为 dict")
                return None if single_result else []
            if query_type == "update":
                return await db.query(
                    model_name=model_name,
                    query_type="update",
                    data=payload,
                    filters=filters or {},
                )
            return await db.save(model_name=model_name, data=payload)

        logger.error(f"database_api.db_query 失败: 不支持的 query_type={query_type}")
        return None if single_result else []
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
            model_name="ActionRecord",
            data={
                "action_id": thinking_id,
                "session_id": getattr(chat_stream, "session_id", ""),
                "action_data": action_data if isinstance(action_data, str) else str(action_data),
                "action_name": action_name,
                "action_reasoning": action_reasoning,
                "action_builtin_prompt": str(action_build_into_prompt),
                "action_display_prompt": action_prompt_display,
                **kwargs,
            },
        )
    except Exception as e:
        logger.error(f"database_api.store_action_info 失败: {e}")
