"""旧版 tool_api 兼容层

复刻旧版 src.plugin_system.apis.tool_api 的公开函数签名。
"""

import logging
import warnings
from typing import Any, List, Optional, Tuple

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.tool_api")


def _get_tool():
    ctx = get_context()
    return ctx.tool if ctx else None


def get_tool_instance(tool_name: str, chat_stream: Any = None) -> Any:
    """获取公开工具实例 (同步，兼容层下返回 None)"""
    warnings.warn("tool_api.get_tool_instance() 已弃用", DeprecationWarning, stacklevel=2)
    return None


def get_llm_available_tool_definitions() -> List[Tuple[str, Any]]:
    """获取 LLM 可用的工具定义列表 (同步，兼容层下返回空)"""
    warnings.warn("tool_api.get_llm_available_tool_definitions() 已弃用", DeprecationWarning, stacklevel=2)
    return []


async def async_get_tool_definitions() -> Any:
    """异步获取工具定义"""
    tool = _get_tool()
    if tool is None:
        return []
    try:
        return await tool.get_definitions()
    except Exception as e:
        logger.error(f"tool_api.async_get_tool_definitions 失败: {e}")
        return []
