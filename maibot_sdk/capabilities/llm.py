"""LLM 能力代理

对应旧系统的 llm_api，所有方法底层转发为 cap.call RPC。
"""
# ruff: noqa: UP006,UP035

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext


def _normalize_llm_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """统一补齐兼容字段。

    Args:
        result: 原始能力返回结果。

    Returns:
        Dict[str, Any]: 规范化后的结果字典。
    """
    if "model" not in result and "model_name" in result:
        result["model"] = result["model_name"]
    return result


class LLMCapability:
    """LLM 调用能力。"""

    def __init__(self, ctx: PluginContext):
        """初始化 LLM 能力代理。

        Args:
            ctx: 当前插件上下文。
        """
        self._ctx = ctx

    async def generate(
        self,
        prompt: str | List[Dict[str, Any]],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """生成文本。

        Args:
            prompt: 提示文本或消息列表。
            model: 模型名称；空字符串表示使用默认模型。
            temperature: 温度参数。
            max_tokens: 最大 token 数。

        Returns:
            Dict[str, Any]: 统一的 LLM 响应字典。
        """
        result = await self._ctx.call_capability(
            "llm.generate",
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        if isinstance(result, dict):
            return _normalize_llm_result(result)
        return {"success": False, "response": "", "reasoning": "", "model": ""}

    async def generate_with_tools(
        self,
        prompt: str | List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """执行带工具调用的文本生成。

        Args:
            prompt: 提示文本或消息列表。
            tools: 工具定义列表。
            model: 模型名称。
            temperature: 温度参数。
            max_tokens: 最大 token 数。

        Returns:
            Dict[str, Any]: 统一的 LLM 响应字典。
        """
        result = await self._ctx.call_capability(
            "llm.generate_with_tools",
            prompt=prompt,
            tools=tools,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        if isinstance(result, dict):
            return _normalize_llm_result(result)
        return {"success": False, "response": "", "reasoning": "", "model": "", "tool_calls": []}

    async def get_available_models(self) -> List[str]:
        """获取可用模型列表。

        Returns:
            List[str]: 当前宿主可见的模型任务名列表。
        """
        result = await self._ctx.call_capability("llm.get_available_models")
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            models = result.get("models")
            if isinstance(models, list):
                return models
        return []
