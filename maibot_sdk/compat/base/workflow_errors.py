"""旧版工作流错误码 (兼容层)"""

from enum import Enum


class WorkflowErrorCode(Enum):
    UNKNOWN = "unknown"
    STEP_FAILED = "step_failed"
    STEP_TIMEOUT = "step_timeout"
    STEP_SKIPPED = "step_skipped"
    DEPENDENCY_FAILED = "dependency_failed"
    WORKFLOW_CANCELLED = "workflow_cancelled"

    def __str__(self) -> str:
        return self.value
