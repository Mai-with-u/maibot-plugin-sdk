"""由 Host 统一渲染的桌宠扩展按钮。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool


class DesktopPetButton(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    label: str = Field(min_length=1, max_length=32)
    icon: Literal["puzzle", "volume", "settings", "refresh", "star", "heart", "book", "bell"] = "puzzle"
    order: int = Field(default=0, strict=True, ge=-10000, le=10000)


class DesktopPetButtonState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    visible: StrictBool = True
    disabled: StrictBool = False
    text: str = Field(default="", max_length=200)
