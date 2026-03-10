"""旧版 BaseAction 抽象基类 (兼容层)

完整复刻旧版 src.plugin_system.base.base_action.BaseAction 的接口和行为。
内部通过 send_api / database_api / message_api 兼容模块转发到新版能力。
"""

import asyncio
import time
import warnings
from abc import ABC, abstractmethod
from typing import Any

from maibot_sdk.compat.base.component_types import (
    ActionActivationType,
    ActionInfo,
    ComponentType,
)


class BaseAction(ABC):
    """Action 组件基类

    Action 是插件的一种组件类型，用于处理聊天中的动作逻辑。

    子类可以通过类属性定义激活条件：
    - activation_type: 激活类型
    - activation_keywords: 激活关键词列表
    - keyword_case_sensitive: 关键词是否区分大小写
    - parallel_action: 是否允许并行执行
    - random_activation_probability: 随机激活概率
    """

    # ── 类属性（子类可覆盖）──────────────────────────────────
    action_name: str = ""
    action_description: str = ""
    action_parameters: dict[str, str] = {}
    action_require: list[str] = []
    activation_type: ActionActivationType = ActionActivationType.ALWAYS
    focus_activation_type: ActionActivationType = ActionActivationType.ALWAYS
    normal_activation_type: ActionActivationType = ActionActivationType.ALWAYS
    random_activation_probability: float = 0.0
    activation_keywords: list[str] = []
    keyword_case_sensitive: bool = False
    parallel_action: bool = True
    associated_types: list[str] = []

    def __init__(
        self,
        action_data: dict | None = None,
        action_reasoning: str = "",
        cycle_timers: dict | None = None,
        thinking_id: str = "",
        chat_stream: Any = None,
        plugin_config: dict | None = None,
        action_message: Any = None,
        **kwargs: Any,
    ):
        """初始化 Action 组件

        Args:
            action_data: 动作数据
            action_reasoning: 执行该动作的理由
            cycle_timers: 计时器字典
            thinking_id: 思考 ID
            chat_stream: 聊天流对象
            plugin_config: 插件配置字典
            action_message: 消息数据
        """
        self.action_data = action_data or {}
        self.action_reasoning = action_reasoning
        self.reasoning = ""
        self.cycle_timers = cycle_timers or {}
        self.thinking_id = thinking_id
        self.plugin_config = plugin_config or {}

        # 设置动作基本信息
        self.action_name = getattr(self.__class__, "action_name", "") or self.__class__.__name__.lower().replace(
            "action", ""
        )
        self.action_description = getattr(self.__class__, "action_description", self.__doc__ or "Action组件")
        self.action_parameters = getattr(self.__class__, "action_parameters", {}).copy()
        self.action_require = getattr(self.__class__, "action_require", []).copy()
        self.activation_type = getattr(self.__class__, "activation_type", ActionActivationType.ALWAYS)
        self.random_activation_probability = getattr(self.__class__, "random_activation_probability", 0.0)
        self.activation_keywords = getattr(self.__class__, "activation_keywords", []).copy()
        self.keyword_case_sensitive = getattr(self.__class__, "keyword_case_sensitive", False)
        self.parallel_action = getattr(self.__class__, "parallel_action", True)
        self.associated_types = getattr(self.__class__, "associated_types", []).copy()

        # 聊天流信息
        self.chat_stream = chat_stream or kwargs.get("chat_stream")
        self.action_message = action_message

        # 便捷属性
        self.chat_id: str = ""
        self.platform: str | None = None
        self.group_id: str | None = None
        self.group_name: str | None = None
        self.user_id: str | None = None
        self.user_nickname: str | None = None
        self.is_group: bool = False
        self.target_id: str | None = None
        self.log_prefix: str = "[Action]"

        # 运行时注入的 stream_id
        self._stream_id: str = ""

        # 尝试从 chat_stream / action_message 提取信息
        if self.chat_stream:
            self.chat_id = getattr(self.chat_stream, "session_id", "")
            self.platform = getattr(self.chat_stream, "platform", None)

        if self.action_message:
            chat_info = getattr(self.action_message, "chat_info", None)
            user_info = getattr(self.action_message, "user_info", None)
            if chat_info:
                group_info = getattr(chat_info, "group_info", None)
                if group_info:
                    self.group_id = str(getattr(group_info, "group_id", ""))
                    self.group_name = getattr(group_info, "group_name", None)
            if user_info:
                self.user_id = str(getattr(user_info, "user_id", ""))
                self.user_nickname = getattr(user_info, "user_nickname", None)

            if self.group_id:
                self.is_group = True
                self.target_id = self.group_id
                self.log_prefix = f"[{self.group_name}]"
            else:
                self.is_group = False
                self.target_id = self.user_id
                self.log_prefix = f"[{self.user_nickname} 的 私聊]"

    @abstractmethod
    async def execute(self) -> tuple[bool, str]:
        """执行 Action 的抽象方法，子类必须实现

        Returns:
            Tuple[bool, str]: (是否执行成功, 回复文本)
        """
        ...

    # ── 发送方法 (转发到 send_api 兼容模块) ─────────────────

    async def send_text(
        self,
        content: str,
        set_reply: bool = False,
        reply_message: Any = None,
        typing: bool = False,
        storage_message: bool = True,
    ) -> bool:
        """发送文本消息"""
        warnings.warn("BaseAction.send_text() 已弃用，请使用 self.ctx.send.text()", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self.chat_id or self._stream_id
        if not stream_id:
            return False
        return await send_api.text_to_stream(
            text=content,
            stream_id=stream_id,
            set_reply=set_reply,
            reply_message=reply_message,
            typing=typing,
            storage_message=storage_message,
        )

    async def send_emoji(
        self,
        emoji_base64: str,
        set_reply: bool = False,
        reply_message: Any = None,
        storage_message: bool = True,
    ) -> bool:
        """发送表情包"""
        warnings.warn("BaseAction.send_emoji() 已弃用，请使用 self.ctx.send.emoji()", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self.chat_id or self._stream_id
        if not stream_id:
            return False
        return await send_api.emoji_to_stream(
            emoji_base64=emoji_base64,
            stream_id=stream_id,
            set_reply=set_reply,
            reply_message=reply_message,
            storage_message=storage_message,
        )

    async def send_image(
        self,
        image_base64: str,
        set_reply: bool = False,
        reply_message: Any = None,
        storage_message: bool = True,
    ) -> bool:
        """发送图片"""
        warnings.warn("BaseAction.send_image() 已弃用，请使用 self.ctx.send.image()", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self.chat_id or self._stream_id
        if not stream_id:
            return False
        return await send_api.image_to_stream(
            image_base64=image_base64,
            stream_id=stream_id,
            set_reply=set_reply,
            reply_message=reply_message,
            storage_message=storage_message,
        )

    async def send_command(
        self,
        command_name: str,
        args: dict | None = None,
        display_message: str = "",
        storage_message: bool = True,
    ) -> bool:
        """发送命令消息"""
        warnings.warn(
            "BaseAction.send_command() 已弃用，请使用 self.ctx.send.command()",
            DeprecationWarning,
            stacklevel=2,
        )
        from maibot_sdk.compat.apis import send_api

        stream_id = self.chat_id or self._stream_id
        if not stream_id:
            return False
        command_data = {"name": command_name, "args": args or {}}
        return await send_api.command_to_stream(
            command=command_data,
            stream_id=stream_id,
            storage_message=storage_message,
            display_message=display_message,
        )

    async def send_custom(
        self,
        message_type: str,
        content: Any,
        typing: bool = False,
        set_reply: bool = False,
        reply_message: Any = None,
        storage_message: bool = True,
    ) -> bool:
        """发送自定义类型消息"""
        warnings.warn("BaseAction.send_custom() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self.chat_id or self._stream_id
        if not stream_id:
            return False
        return await send_api.custom_to_stream(
            message_type=message_type,
            content=content,
            stream_id=stream_id,
            typing=typing,
            set_reply=set_reply,
            reply_message=reply_message,
            storage_message=storage_message,
        )

    async def send_forward(
        self,
        messages_list: list[Any],
        storage_message: bool = True,
    ) -> bool:
        """转发消息"""
        warnings.warn("BaseAction.send_forward() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self.chat_id or self._stream_id
        if not stream_id:
            return False
        return await send_api.custom_reply_set_to_stream(
            reply_set={"forward": messages_list},
            stream_id=stream_id,
            storage_message=storage_message,
        )

    async def send_voice(self, audio_base64: str) -> bool:
        """发送语音消息"""
        warnings.warn("BaseAction.send_voice() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import send_api

        stream_id = self.chat_id or self._stream_id
        if not stream_id:
            return False
        return await send_api.custom_to_stream(
            message_type="voice",
            content=audio_base64,
            stream_id=stream_id,
            storage_message=False,
        )

    # ── 数据库方法 ────────────────────────────────────────────

    async def store_action_info(
        self,
        action_build_into_prompt: bool = False,
        action_prompt_display: str = "",
        action_done: bool = True,
    ) -> None:
        """存储动作信息到数据库"""
        warnings.warn("BaseAction.store_action_info() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import database_api

        await database_api.store_action_info(
            chat_stream=self.chat_stream,
            action_build_into_prompt=action_build_into_prompt,
            action_prompt_display=action_prompt_display,
            action_done=action_done,
            thinking_id=self.thinking_id,
            action_data=self.action_data,
            action_name=self.action_name,
            action_reasoning=self.action_reasoning,
        )

    # ── 消息等待 ──────────────────────────────────────────────

    async def wait_for_new_message(self, timeout: int = 1200) -> tuple[bool, str]:
        """等待新消息或超时

        Args:
            timeout: 超时时间（秒），默认 1200 秒

        Returns:
            Tuple[bool, str]: (是否收到新消息, 空字符串)
        """
        warnings.warn("BaseAction.wait_for_new_message() 已弃用", DeprecationWarning, stacklevel=2)
        from maibot_sdk.compat.apis import message_api

        if not self.chat_id:
            return False, "没有有效的chat_id"

        loop_start_time = self.action_data.get("loop_start_time", time.time())
        wait_start_time = asyncio.get_event_loop().time()

        while True:
            current_time = time.time()
            new_count = message_api.count_new_messages(
                chat_id=self.chat_id,
                start_time=loop_start_time,
                end_time=current_time,
            )
            if new_count > 0:
                return True, ""

            elapsed = asyncio.get_event_loop().time() - wait_start_time
            if elapsed > timeout:
                return False, ""

            await asyncio.sleep(0.5)

    # ── 配置访问 ──────────────────────────────────────────────

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取插件配置值，使用嵌套键访问

        Args:
            key: 配置键名，如 "section.subsection.key"
            default: 默认值
        """
        if not self.plugin_config:
            return default
        keys = key.split(".")
        current: Any = self.plugin_config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    # ── classmethod ───────────────────────────────────────────

    @classmethod
    def get_action_info(cls) -> ActionInfo:
        """从类属性生成 ActionInfo"""
        name = getattr(cls, "action_name", "") or cls.__name__.lower().replace("action", "")
        activation_type = getattr(cls, "activation_type", ActionActivationType.ALWAYS)
        return ActionInfo(
            name=name,
            component_type=ComponentType.ACTION,
            description=getattr(cls, "action_description", "Action动作"),
            activation_type=activation_type,
            activation_keywords=getattr(cls, "activation_keywords", []).copy(),
            keyword_case_sensitive=getattr(cls, "keyword_case_sensitive", False),
            parallel_action=getattr(cls, "parallel_action", True),
            random_activation_probability=getattr(cls, "random_activation_probability", 0.0),
            action_parameters=getattr(cls, "action_parameters", {}).copy(),
            action_require=getattr(cls, "action_require", []).copy(),
            associated_types=getattr(cls, "associated_types", []).copy(),
        )
