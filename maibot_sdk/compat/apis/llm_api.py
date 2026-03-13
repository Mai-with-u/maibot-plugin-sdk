"""旧版 llm_api 兼容层

复刻旧版 src.plugin_system.apis.llm_api 的公开函数签名。
"""

import logging
import warnings
from typing import Any

from maibot_sdk.compat._context_holder import get_context

logger = logging.getLogger("legacy_plugin.llm_api")


def _coerce_bool(value: Any, default: bool = True) -> bool:
    return default if value is None else bool(value)


def _coerce_str(value: Any) -> str:
    return "" if value is None else str(value)


def _coerce_tool_calls(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _get_llm() -> Any:
    ctx = get_context()
    return ctx.llm if ctx else None


def get_available_models() -> dict[str, Any]:
    """获取可用模型配置 (同步，兼容层下功能受限)"""
    warnings.warn(
        "llm_api.get_available_models() 已弃用，请使用 await self.ctx.llm.get_available_models()",
        DeprecationWarning,
        stacklevel=2,
    )
    return {}


async def generate_with_model(
    prompt: str,
    model_config: Any = None,
    request_type: str = "plugin.generate",
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> tuple[bool, str, str, str]:
    """使用指定模型生成内容

    Returns:
        (是否成功, 生成内容, 推理过程, 模型名称)
    """
    warnings.warn(
        "llm_api.generate_with_model() 已弃用，请使用 self.ctx.llm.generate()",
        DeprecationWarning,
        stacklevel=2,
    )
    llm = _get_llm()
    if llm is None:
        return False, "", "", ""
    try:
        result = await llm.generate(
            prompt=prompt,
            request_type=request_type,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # 新版返回格式可能不同，尝试适配
        if isinstance(result, dict):
            return (
                _coerce_bool(result.get("success"), True),
                _coerce_str(result.get("response", result.get("content", ""))),
                _coerce_str(result.get("reasoning", "")),
                _coerce_str(result.get("model", result.get("model_name", ""))),
            )
        return True, str(result), "", ""
    except Exception as e:
        logger.error(f"llm_api.generate_with_model 失败: {e}")
        return False, "", "", ""


async def generate_with_tools(
    prompt: str,
    tools: list[Any] | None = None,
    model_config: Any = None,
    request_type: str = "plugin.tool_use",
    **kwargs: Any,
) -> tuple[bool, str, str, str, list[Any]]:
    """使用工具调用生成

    Returns:
        (是否成功, 生成内容, 推理过程, 模型名称, 工具调用列表)
    """
    warnings.warn("llm_api.generate_with_tools() 已弃用", DeprecationWarning, stacklevel=2)
    llm = _get_llm()
    if llm is None:
        return False, "", "", "", []
    try:
        result = await llm.generate_with_tools(
            prompt=prompt,
            tools=tools or [],
            request_type=request_type,
            **kwargs,
        )
        if isinstance(result, dict):
            return (
                _coerce_bool(result.get("success"), True),
                _coerce_str(result.get("response", result.get("content", ""))),
                _coerce_str(result.get("reasoning", "")),
                _coerce_str(result.get("model", result.get("model_name", ""))),
                _coerce_tool_calls(result.get("tool_calls", [])),
            )
        return True, str(result), "", "", []
    except Exception as e:
        logger.error(f"llm_api.generate_with_tools 失败: {e}")
        return False, "", "", "", []
