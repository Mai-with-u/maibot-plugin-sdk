"""旧版配置类型定义 (兼容层)"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConfigField:
    type: type
    default: Any
    description: str
    example: str | None = None
    required: bool = False
    choices: list[Any] | None = field(default_factory=list)
    min: float | None = None
    max: float | None = None
    step: float | None = None
    pattern: str | None = None
    max_length: int | None = None
    label: str | None = None
    placeholder: str | None = None
    hint: str | None = None
    icon: str | None = None
    hidden: bool = False
    disabled: bool = False
    order: int = 0
    input_type: str | None = None
    rows: int = 3
    group: str | None = None
    depends_on: str | None = None
    depends_value: Any = None
    item_type: str | None = None
    item_fields: dict[str, Any] | None = None
    min_items: int | None = None
    max_items: int | None = None

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

    def to_dict(self) -> dict[str, Any]:
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
    description: str | None = None
    icon: str | None = None
    collapsed: bool = False
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "icon": self.icon,
            "collapsed": self.collapsed,
            "order": self.order,
        }


@dataclass
class ConfigTab:
    id: str
    title: str
    sections: list[str] = field(default_factory=list)
    icon: str | None = None
    order: int = 0
    badge: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "sections": self.sections,
            "icon": self.icon,
            "order": self.order,
            "badge": self.badge,
        }


@dataclass
class ConfigLayout:
    type: str = "auto"
    tabs: list[ConfigTab] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "tabs": [t.to_dict() for t in self.tabs]}


def section_meta(
    title: str,
    description: str | None = None,
    icon: str | None = None,
    collapsed: bool = False,
    order: int = 0,
) -> str | ConfigSection:
    return ConfigSection(title=title, description=description, icon=icon, collapsed=collapsed, order=order)
