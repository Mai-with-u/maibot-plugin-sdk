"""旧版工作流类型定义 (兼容层)"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkflowStage(Enum):
    PRE_PROCESS = "pre_process"
    PROCESS = "process"
    POST_PROCESS = "post_process"
    FINALIZE = "finalize"

    def __str__(self) -> str:
        return self.value


@dataclass
class WorkflowStepInfo:
    step_name: str = ""
    step_description: str = ""
    stage: WorkflowStage = WorkflowStage.PROCESS
    order: int = 0
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStepResult:
    success: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    should_continue: bool = True


@dataclass
class WorkflowMessage:
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowContext:
    workflow_id: str = ""
    current_stage: WorkflowStage = WorkflowStage.PRE_PROCESS
    data: dict[str, Any] = field(default_factory=dict)
    messages: list[WorkflowMessage] = field(default_factory=list)
    results: list[WorkflowStepResult] = field(default_factory=list)
