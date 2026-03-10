"""旧版 generator_api 兼容层

复刻旧版 src.plugin_system.apis.generator_api 的公开函数签名。
"""

import logging
import warnings
from typing import Any

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.generator_api")


def _get_llm():
    ctx = get_context()
    return ctx.llm if ctx else None


def get_replyer(
    chat_stream: Any = None,
    chat_id: str | None = None,
    request_type: str = "replyer",
) -> Any:
    """获取回复器对象 (同步，兼容层下返回 None)

    新版 SDK 中回复器概念不再独立暴露给插件。
    """
    warnings.warn(
        "generator_api.get_replyer() 已弃用，新版 SDK 不再暴露回复器对象",
        DeprecationWarning, stacklevel=2,
    )
    return None


async def generate_reply(
    chat_stream: Any = None,
    action_data: Any = None,
    reasoning: str = "",
    **kwargs: Any,
) -> tuple[bool, Any, Any]:
    """生成回复

    Returns:
        (是否成功, ReplySetModel, 额外数据)
    """
    warnings.warn(
        "generator_api.generate_reply() 已弃用，请使用 self.ctx.llm.generate()",
        DeprecationWarning,
        stacklevel=2,
    )
    llm = _get_llm()
    if llm is None:
        return False, None, None
    try:
        result = await llm.generate(prompt=reasoning or "", **kwargs)
        return True, result, None
    except Exception as e:
        logger.error(f"generator_api.generate_reply 失败: {e}")
        return False, None, None
