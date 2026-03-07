"""插件运行时上下文

为插件提供能力代理接口，所有能力调用通过上下文发起。
PluginContext 由 Runner SDK Runtime 在插件加载时注入。
"""

from collections.abc import Awaitable, Callable
from typing import Any

from maibot_sdk.capabilities.chat import ChatCapability
from maibot_sdk.capabilities.component import ComponentCapability
from maibot_sdk.capabilities.config import ConfigCapability
from maibot_sdk.capabilities.database import DatabaseCapability
from maibot_sdk.capabilities.emoji import EmojiCapability
from maibot_sdk.capabilities.frequency import FrequencyCapability
from maibot_sdk.capabilities.knowledge import KnowledgeCapability
from maibot_sdk.capabilities.llm import LLMCapability
from maibot_sdk.capabilities.logging import LoggingCapability
from maibot_sdk.capabilities.message import MessageCapability
from maibot_sdk.capabilities.person import PersonCapability
from maibot_sdk.capabilities.send import SendCapability
from maibot_sdk.capabilities.tool import ToolCapability

# RPC 调用函数类型: async (method, plugin_id, payload) -> result
RpcCallFn = Callable[..., Awaitable[Any]]


class PluginContext:
    """插件运行时上下文

    插件通过 self.ctx 访问此对象，获取所有能力代理。
    """

    def __init__(self, plugin_id: str, rpc_call: RpcCallFn | None = None) -> None:
        """
        Args:
            plugin_id: 当前插件 ID
            rpc_call: RPC 调用函数，由 Runner 注入
                      签名: async (method, plugin_id, payload) -> result
        """
        self._plugin_id: str = plugin_id
        self._rpc_call: RpcCallFn | None = rpc_call

        # 能力代理
        self.send: SendCapability = SendCapability(self)
        self.db: DatabaseCapability = DatabaseCapability(self)
        self.llm: LLMCapability = LLMCapability(self)
        self.config: ConfigCapability = ConfigCapability(self)
        self.emoji: EmojiCapability = EmojiCapability(self)
        self.message: MessageCapability = MessageCapability(self)
        self.frequency: FrequencyCapability = FrequencyCapability(self)
        self.component: ComponentCapability = ComponentCapability(self)
        self.chat: ChatCapability = ChatCapability(self)
        self.person: PersonCapability = PersonCapability(self)
        self.knowledge: KnowledgeCapability = KnowledgeCapability(self)
        self.tool: ToolCapability = ToolCapability(self)
        self.logging: LoggingCapability = LoggingCapability(self)

    @property
    def plugin_id(self) -> str:
        return self._plugin_id

    async def call_capability(self, capability: str, **kwargs: Any) -> Any:
        """调用一项能力（底层统一转发为 RPC）

        Args:
            capability: 能力名称，如 "send.text", "db.query"
            **kwargs: 能力参数

        Returns:
            能力调用结果
        """
        if self._rpc_call is None:
            raise RuntimeError("PluginContext 尚未初始化 RPC 连接")

        return await self._rpc_call(
            method="cap.request",
            plugin_id=self._plugin_id,
            payload={
                "capability": capability,
                "args": kwargs,
            },
        )
