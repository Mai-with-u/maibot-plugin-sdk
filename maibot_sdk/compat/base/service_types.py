"""旧版服务类型定义 (兼容层)"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PluginServiceInfo:
    service_name: str = ""
    service_description: str = ""
    service_version: str = "1.0.0"
    service_type: str = "generic"
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
