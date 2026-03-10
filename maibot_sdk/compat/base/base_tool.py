"""旧版 BaseTool 抽象基类 (兼容层)

完整复刻旧版 src.plugin_system.base.base_tool.BaseTool 的接口和行为。
"""

import warnings
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from maibot_sdk.compat.base.component_types import ComponentType, ToolInfo, ToolParamType


class BaseTool(ABC):
    """Tool 组件基类

    Tool 是插件的一种组件类型，供 LLM 在推理时调用。

    子类通过类属性描述工具元数据:
    - name: 工具名称
    - description: 工具功能说明
    - available_for_llm: 是否可被 LLM 调用
    - parameters: 参数列表，每项为 (name, type, description, required, default_values)
    """

    # ── 类属性 ────────────────────────────────────────────────
    name: str = ""
    description: str = ""
    available_for_llm: bool = True
    # 参数列表: (name, type, description, required, default_values)
    parameters: List[Tuple[str, ToolParamType, str, bool, Optional[List[str]]]] = []

    def __init__(
        self,
        plugin_config: Optional[dict] = None,
        chat_stream: Any = None,
        **kwargs: Any,
    ):
        """初始化 Tool 组件

        Args:
            plugin_config: 插件配置字典
            chat_stream: 聊天流对象（BotChatSession）
        """
        self.plugin_config = plugin_config or {}
        self.chat_stream = chat_stream
        self.log_prefix = "[Tool]"

    @abstractmethod
    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具

        Args:
            function_args: 工具参数字典

        Returns:
            {"name": self.name, "content": 结果内容}
        """
        ...

    # ── 配置访问 ──────────────────────────────────────────────

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取插件配置值，使用嵌套键访问"""
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
    def get_tool_definition(cls) -> Dict[str, Any]:
        """生成 OpenAI function calling 格式的工具定义"""
        properties: Dict[str, Any] = {}
        required_list: List[str] = []

        for param in cls.parameters:
            param_name = param[0]
            param_type = param[1]
            param_desc = param[2]
            param_required = param[3] if len(param) > 3 else False
            param_defaults = param[4] if len(param) > 4 else None

            # 映射 ToolParamType 到 JSON Schema 类型
            type_map = {
                ToolParamType.STRING: "string",
                ToolParamType.INTEGER: "integer",
                ToolParamType.FLOAT: "number",
                ToolParamType.BOOLEAN: "boolean",
                ToolParamType.ARRAY: "array",
                ToolParamType.OBJECT: "object",
            }
            json_type = type_map.get(param_type, "string")

            prop: Dict[str, Any] = {
                "type": json_type,
                "description": param_desc,
            }
            if param_defaults:
                prop["enum"] = param_defaults

            properties[param_name] = prop
            if param_required:
                required_list.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": cls.name,
                "description": cls.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required_list,
                },
            },
        }

    @classmethod
    def get_tool_info(cls) -> ToolInfo:
        """从类属性生成 ToolInfo"""
        return ToolInfo(
            name=cls.name,
            component_type=ComponentType.TOOL,
            description=cls.description,
            tool_description=cls.description,
            tool_parameters=list(cls.parameters),
        )
