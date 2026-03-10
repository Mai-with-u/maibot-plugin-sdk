"""旧版配置类型定义 (兼容层)"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class ConfigField:
    type: type
    default: Any
    description: str
    example: Optional[str] = None
    required: bool = False
    choices: Optional[List[Any]] = field(default_factory=list)
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    pattern: Optional[str] = None
    max_length: Optional[int] = None
    label: Optional[str] = None
    placeholder: Optional[str] = None
    hint: Optional[str] = None
    icon: Optional[str] = None
    hidden: bool = False
    disabled: bool = False
    order: int = 0
    input_type: Optional[str] = None
    rows: int = 3
    group: Optional[str] = None
    depends_on: Optional[str] = None
    depends_value: Any = None
    item_type: Optional[str] = None
    item_fields: Optional[Dict[str, Any]] = None
    min_items: Optional[int] = None
    max_items: Optional[int] = None

    def get_ui_type(self) -> str:
        if self.input_type:
            return self.input_type
        if self.type is bool:
            return "switch"
        elif self.type in (int, float):
            if self.min is not None and self.max is not None:
                return "slider"
            return "number"
        elif self.type is str:
            if self.choices:
                return "select"
            return "text"
        elif self.type is list:
            return "list"
        elif self.type is dict:
            return "json"
        return "text"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.__name__ if isinstance(self.type, type) else str(self.type),
            "default": self.default,
            "description": self.description,
            "example": self.example,
            "required": self.required,
            "choices": self.choices if self.choices else None,
            "min": self.min,
            "max": self.max,
            "step": self.step,
            "pattern": self.pattern,
            "max_length": self.max_length,
            "label": self.label or self.description,
            "placeholder": self.placeholder,
            "hint": self.hint,
            "icon": self.icon,
            "hidden": self.hidden,
            "disabled": self.disabled,
            "order": self.order,
            "input_type": self.input_type,
            "ui_type": self.get_ui_type(),
            "rows": self.rows,
            "group": self.group,
            "depends_on": self.depends_on,
            "depends_value": self.depends_value,
            "item_type": self.item_type,
            "item_fields": self.item_fields,
            "min_items": self.min_items,
            "max_items": self.max_items,
        }


@dataclass
class ConfigSection:
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    collapsed: bool = False
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title, "description": self.description,
            "icon": self.icon, "collapsed": self.collapsed, "order": self.order,
        }


@dataclass
class ConfigTab:
    id: str
    title: str
    sections: List[str] = field(default_factory=list)
    icon: Optional[str] = None
    order: int = 0
    badge: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "title": self.title, "sections": self.sections,
            "icon": self.icon, "order": self.order, "badge": self.badge,
        }


@dataclass
class ConfigLayout:
    type: str = "auto"
    tabs: List[ConfigTab] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "tabs": [t.to_dict() for t in self.tabs]}


def section_meta(
    title: str, description: Optional[str] = None,
    icon: Optional[str] = None, collapsed: bool = False, order: int = 0,
) -> Union[str, ConfigSection]:
    return ConfigSection(title=title, description=description, icon=icon, collapsed=collapsed, order=order)
