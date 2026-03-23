"""SDK 类型定义

定义插件开发中使用的公共类型。
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

_COMPONENT_TYPE_ALIASES: dict[str, str] = {
    "ACTION": "ACTION",
    "API": "API",
    "COMMAND": "COMMAND",
    "EVENT_HANDLER": "EVENT_HANDLER",
    "HOOK_HANDLER": "HOOK_HANDLER",
    "MESSAGE_GATEWAY": "MESSAGE_GATEWAY",
    "TOOL": "TOOL",
    "action": "ACTION",
    "api": "API",
    "command": "COMMAND",
    "event_handler": "EVENT_HANDLER",
    "hook_handler": "HOOK_HANDLER",
    "message_gateway": "MESSAGE_GATEWAY",
    "tool": "TOOL",
}
_REMOVED_COMPONENT_TYPE_ALIASES = {"WORKFLOW_STEP", "workflow_step"}


def normalize_component_type_name(component_type: Any) -> str:
    """将组件类型归一化为协议层使用的大写字符串。

    SDK 2.0 起，组件协议值统一为大写。为降低迁移成本，仍接受大小写不同但
    语义相同的写法，例如 ``action`` / ``ACTION``。

    `WorkflowStep` 已被 `HookHandler` 替代，属于明确的 breaking change，
    因此这里不会再把 ``workflow_step`` 静默映射为 ``HOOK_HANDLER``。
    """

    value = getattr(component_type, "value", component_type)
    normalized_value = str(value or "").strip()
    if not normalized_value:
        raise ValueError("组件类型不能为空")
    if normalized_value in _REMOVED_COMPONENT_TYPE_ALIASES:
        raise ValueError("`WorkflowStep` 已移除，请改用 `HookHandler` / `HOOK_HANDLER`。")
    normalized_name = _COMPONENT_TYPE_ALIASES.get(normalized_value)
    if normalized_name is None:
        raise ValueError(f"不支持的组件类型: {normalized_value}")
    return normalized_name


# ─── 枚举类型 ──────────────────────────────────────────────────────


class ComponentType(str, Enum):
    """组件类型"""

    ACTION = "ACTION"
    API = "API"
    COMMAND = "COMMAND"
    TOOL = "TOOL"
    EVENT_HANDLER = "EVENT_HANDLER"
    HOOK_HANDLER = "HOOK_HANDLER"
    MESSAGE_GATEWAY = "MESSAGE_GATEWAY"

    @classmethod
    def from_value(cls, component_type: Any) -> "ComponentType":
        """从大小写兼容的输入值恢复为 SDK 组件类型枚举。"""

        return cls(normalize_component_type_name(component_type))


class ActivationType(str, Enum):
    """Action 激活类型"""

    NEVER = "never"
    ALWAYS = "always"
    RANDOM = "random"
    KEYWORD = "keyword"


class ChatMode(str, Enum):
    """聊天模式"""

    FOCUS = "focus"
    NORMAL = "normal"
    PRIORITY = "priority"
    ALL = "all"


class EventType(str, Enum):
    """事件类型 — 与旧系统完全对齐"""

    UNKNOWN = "unknown"
    ON_START = "on_start"
    ON_STOP = "on_stop"
    ON_MESSAGE_PRE_PROCESS = "on_message_pre_process"
    ON_MESSAGE = "on_message"
    ON_PLAN = "on_plan"
    POST_LLM = "post_llm"
    AFTER_LLM = "after_llm"
    POST_SEND_PRE_PROCESS = "post_send_pre_process"
    POST_SEND = "post_send"
    AFTER_SEND = "after_send"


class ToolParamType(str, Enum):
    """工具参数类型"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class MessageGatewayRouteType(str, Enum):
    """消息网关路由类型。"""

    SEND = "send"
    RECEIVE = "receive"
    DUPLEX = "duplex"


class WorkflowStage(str, Enum):
    """Workflow 阶段"""

    INGRESS = "ingress"
    PRE_PROCESS = "pre_process"
    PLAN = "plan"
    TOOL_EXECUTE = "tool_execute"
    POST_PROCESS = "post_process"
    EGRESS = "egress"


class ModifyFlag(str, Enum):
    """消息可修改标志"""

    CAN_MODIFY_PROMPT = "can_modify_prompt"
    CAN_MODIFY_RESPONSE = "can_modify_response"
    CAN_MODIFY_MESSAGE = "can_modify_message"


class HookResult(str, Enum):
    """Workflow hook 返回值语义"""

    CONTINUE = "continue"  # 继续当前 stage 的下一个 hook
    SKIP_STAGE = "skip_stage"  # 跳过当前 stage 剩余 hook，进入下一个 stage
    ABORT = "abort"  # 终止整个 pipeline


class ErrorPolicy(str, Enum):
    """Hook 异常处理策略"""

    ABORT = "abort"  # 异常终止 pipeline（默认）
    SKIP = "skip"  # 记录日志，跳过此 hook 继续
    LOG = "log"  # 记录日志，将异常传给后续 hook


# ─── 工具参数定义 ──────────────────────────────────────────────────


class ToolParameterInfo(BaseModel):
    """工具参数定义"""

    name: str = Field(description="参数名称")
    param_type: ToolParamType = Field(default=ToolParamType.STRING, description="参数类型")
    description: str = Field(default="", description="参数描述")
    required: bool = Field(default=True, description="是否必需")
    default: Any = Field(default=None, description="默认值")


# ─── 组件信息 ──────────────────────────────────────────────────────


class ComponentInfo(BaseModel):
    """组件信息（SDK 侧声明）"""

    name: str = Field(description="组件名称")
    type: ComponentType = Field(description="组件类型")
    description: str = Field(default="", description="组件描述")
    enabled: bool = Field(default=True, description="组件是否启用")
    metadata: dict[str, Any] = Field(default_factory=dict, description="组件元数据")


class ActionComponentInfo(ComponentInfo):
    """Action 组件信息"""

    type: ComponentType = ComponentType.ACTION
    activation_type: ActivationType = ActivationType.ALWAYS
    activation_keywords: list[str] = Field(default_factory=list)
    activation_probability: float = 1.0
    chat_mode: ChatMode = ChatMode.NORMAL
    action_parameters: dict[str, Any] = Field(default_factory=dict, description="Action 参数定义")
    action_require: list[str] = Field(default_factory=list, description="Action 前置需求")
    associated_types: list[str] = Field(default_factory=list, description="关联消息类型")
    parallel_action: bool = Field(default=False, description="是否可并行执行")
    action_prompt: str = Field(default="", description="Action 的 LLM 提示语")


class APIComponentInfo(ComponentInfo):
    """API 组件信息"""

    type: ComponentType = ComponentType.API
    version: str = Field(default="1", description="API 版本")
    public: bool = Field(default=False, description="是否允许其他插件调用")


class CommandComponentInfo(ComponentInfo):
    """Command 组件信息"""

    type: ComponentType = ComponentType.COMMAND
    command_pattern: str = Field(default="", description="命令正则模式")
    aliases: list[str] = Field(default_factory=list, description="命令别名")


class ToolComponentInfo(ComponentInfo):
    """Tool 组件信息"""

    type: ComponentType = ComponentType.TOOL
    parameters: list[ToolParameterInfo] = Field(default_factory=list, description="结构化参数定义")
    parameters_raw: dict[str, Any] = Field(default_factory=dict, description="原始参数 schema（兼容 dict 声明）")


class EventHandlerComponentInfo(ComponentInfo):
    """EventHandler 组件信息"""

    type: ComponentType = ComponentType.EVENT_HANDLER
    event_type: EventType = EventType.ON_MESSAGE
    intercept_message: bool = Field(default=False, description="是否阻塞消息链")
    weight: int = Field(default=0, description="权重/优先级（越高越先执行）")


class HookHandlerComponentInfo(ComponentInfo):
    """HookHandler 组件信息"""

    type: ComponentType = ComponentType.HOOK_HANDLER
    stage: WorkflowStage = Field(description="所属 workflow 阶段")
    priority: int = Field(default=0, description="阶段内优先级（越高越先执行）")
    timeout_ms: int = Field(default=0, description="超时(ms)，0=不限时")
    blocking: bool = Field(default=True, description="True=串行可修改消息, False=并发只读")
    error_policy: ErrorPolicy = Field(default=ErrorPolicy.ABORT, description="异常处理策略")
    filter: dict[str, Any] = Field(default_factory=dict, description="前置过滤条件，Host 预过滤不走 IPC")


class MessageGatewayComponentInfo(ComponentInfo):
    """消息网关组件信息。"""

    type: ComponentType = ComponentType.MESSAGE_GATEWAY
    route_type: MessageGatewayRouteType = Field(description="消息网关路由类型")
    platform: str = Field(default="", description="可选的平台名称，允许在运行时动态上报")
    protocol: str = Field(default="", description="可选的协议或接入方言名称")
    account_id: str = Field(default="", description="可选的账号 ID 或 self_id")
    scope: str = Field(default="", description="可选的路由作用域")


# ─── 通用响应 ──────────────────────────────────────────────────────


class CapabilityResult(BaseModel):
    """能力调用结果"""

    success: bool
    result: Any = None
    error: str = ""
