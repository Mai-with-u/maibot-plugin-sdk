"""
旧版组件类型定义 (兼容层)

提供与旧版 src.plugin_system.base.component_types 一致的类型。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ─── 枚举类型 ──────────────────────────────────────────────────────


class ComponentType(Enum):
    ACTION = "action"
    COMMAND = "command"
    TOOL = "tool"
    SCHEDULER = "scheduler"
    EVENT_HANDLER = "event_handler"

    def __str__(self) -> str:
        return self.value


class ActionActivationType(Enum):
    NEVER = "never"
    ALWAYS = "always"
    RANDOM = "random"
    KEYWORD = "keyword"

    def __str__(self) -> str:
        return self.value


class ChatMode(Enum):
    FOCUS = "focus"
    NORMAL = "normal"
    PRIORITY = "priority"
    ALL = "all"

    def __str__(self) -> str:
        return self.value


class EventType(Enum):
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
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value


class ToolParamType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"

    def __str__(self) -> str:
        return self.value


class ReplyContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    EMOJI = "emoji"
    FORWARD = "forward"
    HYBRID = "hybrid"


# ─── 数据类 ──────────────────────────────────────────────────────


@dataclass
class ComponentInfo:
    name: str
    component_type: ComponentType
    description: str = ""
    enabled: bool = True
    plugin_name: str = ""
    is_built_in: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionInfo(ComponentInfo):
    action_parameters: dict[str, str] = field(default_factory=dict)
    action_require: list[str] = field(default_factory=list)
    associated_types: list[str] = field(default_factory=list)
    focus_activation_type: ActionActivationType = ActionActivationType.ALWAYS
    normal_activation_type: ActionActivationType = ActionActivationType.ALWAYS
    activation_type: ActionActivationType = ActionActivationType.ALWAYS
    random_activation_probability: float = 0.0
    activation_keywords: list[str] = field(default_factory=list)
    keyword_case_sensitive: bool = False
    parallel_action: bool = False

    def __post_init__(self) -> None:
        self.component_type = ComponentType.ACTION


@dataclass
class CommandInfo(ComponentInfo):
    command_pattern: str = ""

    def __post_init__(self) -> None:
        self.component_type = ComponentType.COMMAND


@dataclass
class ToolInfo(ComponentInfo):
    tool_parameters: list[tuple[str, ToolParamType, str, bool, list[str] | None]] = field(
        default_factory=list
    )
    tool_description: str = ""

    def __post_init__(self) -> None:
        self.component_type = ComponentType.TOOL


@dataclass
class EventHandlerInfo(ComponentInfo):
    event_type: "EventType | str" = EventType.ON_MESSAGE
    intercept_message: bool = False
    weight: int = 0

    def __post_init__(self) -> None:
        self.component_type = ComponentType.EVENT_HANDLER


@dataclass
class PythonDependency:
    package_name: str
    version: str = ""
    optional: bool = False
    description: str = ""
    install_name: str = ""

    def __post_init__(self) -> None:
        if not self.install_name:
            self.install_name = self.package_name

    def get_pip_requirement(self) -> str:
        if self.version:
            return f"{self.install_name}{self.version}"
        return self.install_name


@dataclass
class PluginInfo:
    display_name: str = ""
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    enabled: bool = True
    is_built_in: bool = False
    components: list[ComponentInfo] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    python_dependencies: list[PythonDependency] = field(default_factory=list)
    config_file: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    manifest_data: dict[str, Any] = field(default_factory=dict)
    license: str = ""
    homepage_url: str = ""
    repository_url: str = ""
    keywords: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    min_host_version: str = ""
    max_host_version: str = ""


@dataclass
class ModifyFlag:
    modify_message_segments: bool = False
    modify_plain_text: bool = False
    modify_llm_prompt: bool = False
    modify_llm_response_content: bool = False
    modify_llm_response_reasoning: bool = False


@dataclass
class ToolCall:
    name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    id: str = ""


@dataclass
class MaiMessages:
    """MaiM 插件消息 (兼容层)"""

    message_segments: list[Any] = field(default_factory=list)
    message_base_info: dict[str, Any] = field(default_factory=dict)
    plain_text: str = ""
    raw_message: str | None = None
    is_group_message: bool = False
    is_private_message: bool = False
    stream_id: str | None = None
    llm_prompt: str | None = None
    llm_response_content: str | None = None
    llm_response_reasoning: str | None = None
    llm_response_model: str | None = None
    llm_response_tool_call: list[ToolCall] | None = None
    action_usage: list[str] | None = None
    additional_data: dict[Any, Any] = field(default_factory=dict)
    _modify_flags: ModifyFlag = field(default_factory=ModifyFlag)

    def deepcopy(self) -> "MaiMessages":
        import copy
        return copy.deepcopy(self)

    def modify_message_segments(self, new_segments: list[Any], suppress_warning: bool = False) -> None:
        self.message_segments = new_segments
        self._modify_flags.modify_message_segments = True

    def modify_llm_prompt(self, new_prompt: str, suppress_warning: bool = False) -> None:
        self.llm_prompt = new_prompt
        self._modify_flags.modify_llm_prompt = True

    def modify_plain_text(self, new_text: str, suppress_warning: bool = False) -> None:
        self.plain_text = new_text
        self._modify_flags.modify_plain_text = True

    def modify_llm_response_content(self, new_content: str, suppress_warning: bool = False) -> None:
        self.llm_response_content = new_content
        self._modify_flags.modify_llm_response_content = True

    def modify_llm_response_reasoning(self, new_reasoning: str, suppress_warning: bool = False) -> None:
        self.llm_response_reasoning = new_reasoning
        self._modify_flags.modify_llm_response_reasoning = True


@dataclass
class CustomEventHandlerResult:
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReplyContent:
    content_type: ReplyContentType = ReplyContentType.TEXT
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ForwardNode:
    sender_name: str = ""
    sender_id: str = ""
    content: str = ""
    timestamp: int = 0


@dataclass
class ReplySetModel:
    contents: list[ReplyContent] = field(default_factory=list)
    forward_nodes: list[ForwardNode] = field(default_factory=list)
