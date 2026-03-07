"""LLM 能力代理

对应旧系统的 llm_api，所有方法底层转发为 cap.request RPC。
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext


class LLMCapability:
    """LLM 调用能力"""

    def __init__(self, ctx: "PluginContext"):
        self._ctx = ctx

    async def generate(
        self,
        prompt: str | list[dict[str, str]],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """生成文本

        Args:
            prompt: 提示文本或消息列表
            model: 模型名称（空字符串使用默认模型）
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            {"success": bool, "response": str, "reasoning": str, "model": str}
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
            return result
        return {"success": False, "response": "", "reasoning": "", "model": ""}

    async def generate_with_tools(
        self,
        prompt: str | list[dict[str, str]],
        tools: list[dict[str, Any]],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """带工具调用的生成

        Args:
            prompt: 提示文本或消息列表
            tools: 工具定义列表
            model: 模型名称
            temperature: 温度
            max_tokens: 最大 token 数

        Returns:
            {"success": bool, "response": str, "reasoning": str, "model": str, "tool_calls": list}
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
            return result
        return {"success": False, "response": "", "reasoning": "", "model": "", "tool_calls": []}

    async def get_available_models(self) -> list[str]:
        """获取可用模型列表"""
        result = await self._ctx.call_capability("llm.get_models")
        if isinstance(result, list):
            return result
        return []
