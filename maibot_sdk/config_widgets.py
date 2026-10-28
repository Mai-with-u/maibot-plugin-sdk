"""配置页运行时控件协议；所有值仅在内存中传输，不参与 TOML 配置。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConfigWidget(BaseModel):
    """静态控件声明。id 在插件内唯一；action 只能调用声明的按钮。"""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_.-]+$")
    kind: Literal["qrcode", "status", "action"]
    label: str = Field(min_length=1, max_length=200)
    confirmation: str | None = Field(default=None, max_length=500)


class ConfigWidgetState(BaseModel):
    """控件最新状态。二维码使用 PNG/JPEG data URL，expires_at 为 Unix 秒。"""

    model_config = ConfigDict(extra="forbid")
    text: str = Field(default="", max_length=2000)
    tone: Literal["neutral", "success", "warning", "error"] = "neutral"
    image: str | None = Field(
        default=None, max_length=1_000_000, pattern=r"^data:image/(png|jpeg);base64,[A-Za-z0-9+/=]+$"
    )
    expires_at: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    visible: bool = True
    disabled: bool = False


class ConfigWidgetSnapshot(BaseModel):
    """完整快照，不做增量合并，避免保留过期二维码。"""

    model_config = ConfigDict(extra="forbid")
    widgets: list[ConfigWidget] = Field(default_factory=list, max_length=50)
    states: dict[str, ConfigWidgetState] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ids(self) -> "ConfigWidgetSnapshot":
        ids = [widget.id for widget in self.widgets]
        if len(ids) != len(set(ids)):
            raise ValueError("运行时控件 ID 重复")
        if set(self.states) != set(ids):
            raise ValueError("必须为每个运行时控件提供状态，且不能包含未声明的控件")
        return self
