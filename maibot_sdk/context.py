"""插件运行时上下文

为插件提供能力代理接口，所有能力调用通过上下文发起。
PluginContext 由 Runner SDK Runtime 在插件加载时注入。
"""

import logging as stdlib_logging
from collections.abc import Awaitable, Callable
from typing import Any, Optional

from maibot_sdk.capabilities.chat import ChatCapability
from maibot_sdk.capabilities.component import ComponentCapability
from maibot_sdk.capabilities.config import ConfigCapability
from maibot_sdk.capabilities.database import DatabaseCapability
from maibot_sdk.capabilities.emoji import EmojiCapability
from maibot_sdk.capabilities.frequency import FrequencyCapability
from maibot_sdk.capabilities.knowledge import KnowledgeCapability
from maibot_sdk.capabilities.llm import LLMCapability
from maibot_sdk.capabilities.message import MessageCapability
from maibot_sdk.capabilities.person import PersonCapability
from maibot_sdk.capabilities.send import SendCapability
from maibot_sdk.capabilities.tool import ToolCapability

# RPC 调用函数类型: async (method, plugin_id, payload) -> result
RpcCallFn = Callable[..., Awaitable[Any]]


class PluginContext:
    """插件运行时上下文

    插件通过 self.ctx 访问此对象，获取所有能力代理。

    日志使用方式：

        # 推荐：直接使用 stdlib logging，日志自动通过 IPC 传输到主进程
        self.ctx.logger.info("插件已启动")

        # 或直接使用 logging.getLogger("插件名")
        import logging
        logger = logging.getLogger(__name__)   # 名称不以 plugin. 开头也能正常工作
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
        self._logger: Optional[stdlib_logging.Logger] = None

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

    @property
    def plugin_id(self) -> str:
        return self._plugin_id

    @property
    def logger(self) -> stdlib_logging.Logger:
        """返回属于本插件的标准 Logger。

        Logger 名称为 ``plugin.<plugin_id>``，在 Runner 进程中该
        Logger 的展示会被 :class:`RunnerIPCLogHandler` 自动
        技持到主进程。

        使用示例::

            self.ctx.logger.info("消息已处理")
            self.ctx.logger.error("出错了", exc_info=True)
        """
        if self._logger is None:
            self._logger = stdlib_logging.getLogger(f"plugin.{self._plugin_id}")
        return self._logger

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
