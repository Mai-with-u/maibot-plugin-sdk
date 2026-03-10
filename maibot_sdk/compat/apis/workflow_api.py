"""旧版 workflow_api 兼容层

复刻旧版 src.plugin_system.apis.workflow_api 的公开函数签名。
工作流引擎在新版 IPC 架构中不再暴露给插件子进程。
"""

import logging
import warnings
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("legacy_plugin.workflow_api")

# 本地注册表
_local_steps: dict[str, Any] = {}
_local_handlers: dict[str, Callable[..., Any]] = {}


def register_workflow_step(step_info: Any, step_handler: Callable[..., Any]) -> bool:
    """注册 workflow step (兼容层下仅在进程内有效)"""
    warnings.warn("workflow_api.register_workflow_step() 已弃用", DeprecationWarning, stacklevel=2)
    key = getattr(step_info, "step_name", str(step_info))
    _local_steps[key] = step_info
    _local_handlers[key] = step_handler
    return True


def get_steps_by_stage(stage: Any, enabled_only: bool = False) -> dict[str, Any]:
    warnings.warn("workflow_api.get_steps_by_stage() 已弃用", DeprecationWarning, stacklevel=2)
    return {}


def get_workflow_step(step_name: str, stage: Any = None) -> Any:
    warnings.warn("workflow_api.get_workflow_step() 已弃用", DeprecationWarning, stacklevel=2)
    return _local_steps.get(step_name)


def get_workflow_step_handler(step_name: str, stage: Any = None) -> Callable[..., Any] | None:
    warnings.warn("workflow_api.get_workflow_step_handler() 已弃用", DeprecationWarning, stacklevel=2)
    return _local_handlers.get(step_name)


def enable_workflow_step(step_name: str, stage: Any = None) -> bool:
    warnings.warn("workflow_api.enable_workflow_step() 已弃用", DeprecationWarning, stacklevel=2)
    return step_name in _local_steps


def disable_workflow_step(step_name: str, stage: Any = None) -> bool:
    warnings.warn("workflow_api.disable_workflow_step() 已弃用", DeprecationWarning, stacklevel=2)
    return step_name in _local_steps


def get_execution_trace(trace_id: str) -> dict[str, Any] | None:
    warnings.warn("workflow_api.get_execution_trace() 已弃用", DeprecationWarning, stacklevel=2)
    return None


def clear_execution_trace(trace_id: str) -> bool:
    warnings.warn("workflow_api.clear_execution_trace() 已弃用", DeprecationWarning, stacklevel=2)
    return False


async def execute_workflow_message(
    message: Any = None,
    stream_id: str | None = None,
    action_usage: list[str] | None = None,
    context: Any = None,
) -> tuple[Any, Any, Any]:
    """执行 workflow 消息"""
    warnings.warn("workflow_api.execute_workflow_message() 已弃用", DeprecationWarning, stacklevel=2)
    from maibot_sdk.compat.base.workflow_types import WorkflowContext, WorkflowStepResult
    return WorkflowStepResult(success=False, error="兼容层不支持"), message, context or WorkflowContext()


async def publish_event(
    event_type: Any,
    message: Any = None,
    stream_id: str | None = None,
    action_usage: list[str] | None = None,
) -> tuple[bool, Any]:
    """发布事件"""
    warnings.warn("workflow_api.publish_event() 已弃用", DeprecationWarning, stacklevel=2)
    return False, message
