"""组件声明装饰器

用于在插件类中声明 Action/Command/Tool/EventHandler/HookHandler/MessageGateway 组件。
装饰器将组件元数据附加到方法或类上，Runner 在加载时收集。
"""

from collections.abc import Callable
from typing import Any

from maibot_sdk.types import (
    ActionComponentInfo,
    ActivationType,
    APIComponentInfo,
    ChatMode,
    CommandComponentInfo,
    ErrorPolicy,
    EventHandlerComponentInfo,
    EventType,
    HookHandlerComponentInfo,
    MessageGatewayComponentInfo,
    MessageGatewayRouteType,
    ToolComponentInfo,
    ToolParameterInfo,
    WorkflowStage,
)

# 装饰器签名: 接受函数返回函数
_Decorator = Callable[[Callable[..., Any]], Callable[..., Any]]

# 标记属性名，用于在方法上附加组件信息
_COMPONENT_INFO_ATTR = "__maibot_component_info__"


def Action(
    name: str,
    description: str = "",
    activation_type: ActivationType = ActivationType.ALWAYS,
    activation_keywords: list[str] | None = None,
    activation_probability: float = 1.0,
    chat_mode: ChatMode = ChatMode.NORMAL,
    action_parameters: dict[str, Any] | None = None,
    action_require: list[str] | None = None,
    associated_types: list[str] | None = None,
    parallel_action: bool = False,
    action_prompt: str = "",
    **metadata: Any,
) -> _Decorator:
    """Action 组件装饰器

    用法：
        @Action("my_action", description="做某事", activation_type=ActivationType.KEYWORD,
                activation_keywords=["你好"], action_require=["send"])
        async def handle_my_action(self, **kwargs):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """将 Action 元数据附着到目标函数。

        Args:
            func: 被声明为 Action 的方法。

        Returns:
            Callable[..., Any]: 原始函数对象。
        """
        info = ActionComponentInfo(
            name=name,
            description=description,
            activation_type=activation_type,
            activation_keywords=activation_keywords or [],
            activation_probability=activation_probability,
            chat_mode=chat_mode,
            action_parameters=action_parameters or {},
            action_require=action_require or [],
            associated_types=associated_types or [],
            parallel_action=parallel_action,
            action_prompt=action_prompt,
            metadata=metadata,
        )
        setattr(func, _COMPONENT_INFO_ATTR, info)
        return func

    return decorator


def Command(
    name: str,
    description: str = "",
    pattern: str = "",
    aliases: list[str] | None = None,
    **metadata: Any,
) -> _Decorator:
    """Command 组件装饰器

    用法：
        @Command("hello", description="打招呼", pattern=r"^/hello")
        async def handle_hello(self, **kwargs):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """将 Command 元数据附着到目标函数。

        Args:
            func: 被声明为 Command 的方法。

        Returns:
            Callable[..., Any]: 原始函数对象。
        """
        info = CommandComponentInfo(
            name=name,
            description=description,
            command_pattern=pattern,
            aliases=aliases or [],
            metadata=metadata,
        )
        setattr(func, _COMPONENT_INFO_ATTR, info)
        return func

    return decorator


def API(
    name: str,
    description: str = "",
    version: str = "1",
    public: bool = False,
    **metadata: Any,
) -> _Decorator:
    """API 组件装饰器。

    用法：
        @API("render_html", description="渲染 HTML", version="1", public=True)
        async def handle_render_html(self, html: str):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """将 API 元数据附着到目标函数。

        Args:
            func: 被声明为 API 的方法。

        Returns:
            Callable[..., Any]: 原始函数对象。
        """

        info = APIComponentInfo(
            name=name,
            description=description,
            version=str(version or "1").strip() or "1",
            public=bool(public),
            metadata=metadata,
        )
        setattr(func, _COMPONENT_INFO_ATTR, info)
        return func

    return decorator


def Tool(
    name: str,
    description: str = "",
    parameters: list[ToolParameterInfo] | dict[str, Any] | None = None,
    **metadata: Any,
) -> _Decorator:
    """Tool 组件装饰器

    用法（结构化参数）：
        @Tool("search", description="搜索", parameters=[
            ToolParameterInfo(name="query", param_type=ToolParamType.STRING, description="搜索内容"),
        ])
        async def handle_search(self, query: str, **kwargs):
            ...

    用法（dict 参数，兼容旧式声明）：
        @Tool("search", description="搜索", parameters={"query": {"type": "string"}})
        async def handle_search(self, query: str, **kwargs):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """将 Tool 元数据附着到目标函数。

        Args:
            func: 被声明为 Tool 的方法。

        Returns:
            Callable[..., Any]: 原始函数对象。
        """
        typed_params: list[ToolParameterInfo] = []
        raw_params: dict[str, Any] = {}
        if isinstance(parameters, list):
            typed_params = parameters
        elif isinstance(parameters, dict):
            raw_params = parameters

        info = ToolComponentInfo(
            name=name,
            description=description,
            parameters=typed_params,
            parameters_raw=raw_params,
            metadata=metadata,
        )
        setattr(func, _COMPONENT_INFO_ATTR, info)
        return func

    return decorator


def EventHandler(
    name: str,
    description: str = "",
    event_type: EventType = EventType.ON_MESSAGE,
    intercept_message: bool = False,
    weight: int = 0,
    **metadata: Any,
) -> _Decorator:
    """EventHandler 组件装饰器

    Args:
        intercept_message: 为 True 时阻塞消息链（同步等待返回），为 False 时异步 fire-and-forget。
        weight: 权重越高越先执行，与旧系统的 weight 语义一致。

    用法：
        @EventHandler("on_start", event_type=EventType.ON_START)
        async def handle_start(self, **kwargs):
            ...

        @EventHandler("msg_filter", event_type=EventType.ON_MESSAGE_PRE_PROCESS,
                       intercept_message=True, weight=100)
        async def filter_message(self, message, **kwargs):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """将 EventHandler 元数据附着到目标函数。

        Args:
            func: 被声明为 EventHandler 的方法。

        Returns:
            Callable[..., Any]: 原始函数对象。
        """
        info = EventHandlerComponentInfo(
            name=name,
            description=description,
            event_type=event_type,
            intercept_message=intercept_message,
            weight=weight,
            metadata=metadata,
        )
        setattr(func, _COMPONENT_INFO_ATTR, info)
        return func

    return decorator


def HookHandler(
    name: str,
    stage: WorkflowStage,
    description: str = "",
    priority: int = 0,
    timeout_ms: int = 0,
    blocking: bool = True,
    error_policy: ErrorPolicy = ErrorPolicy.ABORT,
    filter: dict[str, Any] | None = None,
    **metadata: Any,
) -> _Decorator:
    """HookHandler 组件装饰器

    Args:
        name: 组件名称
        stage: 所属 workflow 阶段
        priority: 阶段内优先级（越高越先执行）
        timeout_ms: 超时(ms)，0=不限时
        blocking: True=串行可修改消息, False=并发只读
        error_policy: 异常处理策略 (abort/skip/log)
        filter: 前置过滤条件 dict，Host 端预过滤不满足条件的调用

    用法：
        @HookHandler("my_ingress", stage=WorkflowStage.INGRESS, priority=10)
        async def handle_ingress(self, context, message, **kwargs):
            return {"hook_result": "continue", "modified_message": {...}}

        @HookHandler("observer", stage=WorkflowStage.PRE_PROCESS, blocking=False)
        async def observe(self, context, message, **kwargs):
            # 只读观察者，并发执行
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """将 HookHandler 元数据附着到目标函数。

        Args:
            func: 被声明为 HookHandler 的方法。

        Returns:
            Callable[..., Any]: 原始函数对象。
        """
        info = HookHandlerComponentInfo(
            name=name,
            stage=stage,
            description=description,
            priority=priority,
            timeout_ms=timeout_ms,
            blocking=blocking,
            error_policy=error_policy,
            filter=filter or {},
            metadata=metadata,
        )
        setattr(func, _COMPONENT_INFO_ATTR, info)
        return func

    return decorator


def WorkflowStep(*args: Any, **kwargs: Any) -> _Decorator:
    """已移除的旧装饰器入口。

    `WorkflowStep` 在 SDK 2.0 中被 `HookHandler` 取代。这里保留同名入口，
    仅用于在旧代码仍尝试使用时给出明确错误信息，而不是静默兼容。
    """

    raise RuntimeError("`WorkflowStep` 已移除，请改用 `HookHandler`。这是一个不向后兼容更改。")


def _normalize_message_gateway_route_type(route_type: str) -> MessageGatewayRouteType:
    """规范化消息网关路由类型字符串。

    Args:
        route_type: 用户声明的路由类型字符串。

    Returns:
        MessageGatewayRouteType: 归一化后的路由类型枚举。

    Raises:
        ValueError: 当输入值不是支持的路由类型时抛出。
    """

    normalized_route_type = str(route_type or "").strip().lower()
    alias_map = {
        "recv": MessageGatewayRouteType.RECEIVE,
        "receive": MessageGatewayRouteType.RECEIVE,
        "recive": MessageGatewayRouteType.RECEIVE,
        "send": MessageGatewayRouteType.SEND,
        "duplex": MessageGatewayRouteType.DUPLEX,
    }
    resolved_route_type = alias_map.get(normalized_route_type)
    if resolved_route_type is None:
        raise ValueError(f"不支持的消息网关路由类型: {route_type}")
    return resolved_route_type


def MessageGateway(
    route_type: str,
    *,
    name: str = "",
    description: str = "",
    platform: str = "",
    protocol: str = "",
    account_id: str = "",
    scope: str = "",
    **metadata: Any,
) -> _Decorator:
    """声明消息网关组件。

    Args:
        route_type: 网关路由类型，支持 ``send``、``receive``、``duplex``。
        name: 可选的组件名；留空时默认使用方法名。
        description: 组件描述。
        platform: 可选的平台名称；为空时允许运行时动态上报。
        protocol: 可选的协议或实现名称。
        account_id: 可选的账号 ID 或 ``self_id``。
        scope: 可选的路由作用域。
        **metadata: 额外元数据。

    Returns:
        _Decorator: 用于修饰插件方法的装饰器。
    """

    normalized_route_type = _normalize_message_gateway_route_type(route_type)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """将 MessageGateway 元数据附着到目标函数。

        Args:
            func: 被声明为消息网关的插件方法。

        Returns:
            Callable[..., Any]: 原始函数对象。
        """

        component_name = name or func.__name__
        info = MessageGatewayComponentInfo(
            name=component_name,
            description=description,
            route_type=normalized_route_type,
            platform=str(platform or "").strip(),
            protocol=str(protocol or "").strip(),
            account_id=str(account_id or "").strip(),
            scope=str(scope or "").strip(),
            metadata=metadata,
        )
        setattr(func, _COMPONENT_INFO_ATTR, info)
        return func

    return decorator


def collect_components(instance: object) -> list[dict[str, Any]]:
    """从插件实例中收集所有被装饰器标记的组件信息

    Runner 在加载插件后调用此函数。

    Returns:
        组件信息字典列表，每个字典可直接序列化为 ComponentDeclaration
    """
    components = []
    for attr_name in dir(instance):
        try:
            attr = getattr(instance, attr_name)
        except Exception:
            continue
        if callable(attr) and hasattr(attr, _COMPONENT_INFO_ATTR):
            info = getattr(attr, _COMPONENT_INFO_ATTR)
            component_metadata = info.model_dump(exclude={"name", "type"})
            component_metadata.setdefault("handler_name", attr_name)
            components.append(
                {
                    "name": info.name,
                    "type": info.type.value,
                    "metadata": component_metadata,
                }
            )
    return components
