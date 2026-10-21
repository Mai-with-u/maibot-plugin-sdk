"""Maisaka 能力代理。

提供上下文消息、图片读取、长文生成和主动任务能力。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext


class MaisakaContextCapability:
    """Maisaka 上下文能力。"""

    def __init__(self, ctx: PluginContext) -> None:
        self._ctx = ctx

    async def resolve_image(self, stream_id: str, source_id: str, index: int = 0) -> Any:
        """读取现有聊天上下文中的图片。

        Args:
            stream_id: 已存在的真实聊天流 ID，不会创建新的运行上下文。
            source_id: 上下文消息编号（支持短别名）或 tool_result:<call_id>:<item_index>。
            index: 消息内图片序号，从 0 开始；工具媒体引用通常使用 0。

        Returns:
            成功时返回 success 和 image（binary_data_base64、binary_hash）；失败时返回 error。
        """
        return await self._ctx.call_capability(
            "maisaka.context.resolve_image",
            stream_id=stream_id,
            source_id=source_id,
            index=index,
        )

    async def append(
        self,
        stream_id: str,
        segments: list[dict[str, Any]],
        *,
        visible_text: str = "",
        source_kind: str = "",
        message_id: str = "",
        replyable: bool = False,
        user_info: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """向指定聊天流的 Maisaka 上下文追加一条图文消息。

        Args:
            stream_id: 目标聊天流 ID。
            segments: 消息段列表。
            visible_text: 可选的可见文本摘要。
            source_kind: 可选的消息来源标识。
            message_id: 可选的消息 ID；replyable=True 时必须提供真实消息 ID。
            replyable: 是否作为可回复的用户消息加入历史，不会自动触发回复。
            user_info: replyable=True 时必须提供真实作者信息。
            **kwargs: Host 支持的额外参数。
        """

        return await self._ctx.call_capability(
            "maisaka.context.append",
            stream_id=stream_id,
            segments=segments,
            visible_text=visible_text,
            source_kind=source_kind,
            message_id=message_id,
            replyable=replyable,
            user_info=user_info,
            **kwargs,
        )


class MaisakaReplyCapability:
    """生成符合会话人格的长文，仅返回文本，不自动发送。"""

    def __init__(self, ctx: PluginContext) -> None:
        self._ctx = ctx

    async def generate(
        self,
        stream_id: str,
        reference: str,
        *,
        format_instruction: str = "",
        model_name: str = "",
        timeout_ms: int | None = None,
    ) -> Any:
        """基于材料生成长文，复用 Host 的人格、表达选择与回复 Hook。

        Args:
            stream_id: Host 中已存在的真实聊天流 ID。
            reference: 非空写作材料，最多 500000 字符。
            format_instruction: 可选写作要求，最多 8000 字符。
            model_name: 可选 Host 模型名称，留空沿用会话配置。
            timeout_ms: 本次 RPC 超时毫秒数；长文生成可按需增加。

        Returns:
            成功返回 success、text 和 selected_expression_ids，失败返回 success=False 与 error。
        """
        return await self._ctx.call_capability(
            "maisaka.reply.generate",
            stream_id=stream_id,
            reference=reference,
            format_instruction=format_instruction,
            model_name=model_name,
            timeout_ms=timeout_ms,
        )


class MaisakaProactiveCapability:
    """Maisaka 主动任务能力。"""

    def __init__(self, ctx: PluginContext) -> None:
        self._ctx = ctx

    async def trigger(
        self,
        stream_id: str,
        intent: str,
        *,
        reason: str = "",
        priority: str = "",
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """请求 Maisaka 基于指定聊天流主动处理一轮对话。

        Args:
            stream_id: 目标聊天流 ID，必须是 Host 中已存在的聊天流。
            intent: 主动任务意图。
            reason: 可选的触发原因。
            priority: 可选的优先级。
            metadata: 可选的任务元数据。
            **kwargs: Host 支持的额外参数。
        """

        return await self._ctx.call_capability(
            "maisaka.proactive.trigger",
            stream_id=stream_id,
            intent=intent,
            reason=reason,
            priority=priority,
            metadata=metadata or {},
            **kwargs,
        )


class MaisakaCapability:
    """Maisaka 能力入口。"""

    def __init__(self, ctx: PluginContext) -> None:
        self._ctx = ctx
        self.reply = MaisakaReplyCapability(ctx)
        self.context = MaisakaContextCapability(ctx)
        self.proactive = MaisakaProactiveCapability(ctx)

    async def append_context(
        self,
        stream_id: str,
        segments: list[dict[str, Any]],
        **kwargs: Any,
    ) -> Any:
        """向 Maisaka 上下文追加消息。"""

        return await self.context.append(stream_id, segments, **kwargs)

    async def trigger_proactive(
        self,
        stream_id: str,
        intent: str,
        **kwargs: Any,
    ) -> Any:
        """触发 Maisaka 主动任务。"""

        return await self.proactive.trigger(stream_id, intent, **kwargs)
