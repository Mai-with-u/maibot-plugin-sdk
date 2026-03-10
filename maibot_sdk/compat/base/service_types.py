"""旧版服务类型定义 (兼容层)"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PluginServiceInfo:
    service_name: str = ""
    service_description: str = ""
    service_version: str = "1.0.0"
    service_type: str = "generic"
    endpoints: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
