# MaiBot Plugin SDK

MaiBot 插件开发的唯一依赖。提供插件基类、配置模型、组件装饰器、能力代理和类型定义。

> **完整文档**：[插件开发指南](docs/guide.md) — 覆盖 15 种能力代理、日志接口、6 种正式组件装饰器、1 种兼容装饰器、配置模型、消息模型、生命周期、调试与发布。
>
> **Breaking change（2.0.0）**：`WorkflowStep` 已移除并重命名为 `HookHandler`。组件协议值统一为大写（如 `ACTION`、`EVENT_HANDLER`）。顶层仍保留 `WorkflowStep` 名称，但只会在运行时抛出明确错误，不再提供兼容映射。

## 安装

```bash
pip install maibot-plugin-sdk
```

## 快速开始

```python
from maibot_sdk import CONFIG_RELOAD_SCOPE_SELF, Command, MaiBotPlugin, Tool
from maibot_sdk.types import ToolParameterInfo, ToolParamType

class MyPlugin(MaiBotPlugin):
    async def on_load(self) -> None:
        return None

    async def on_unload(self) -> None:
        return None

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        if scope == CONFIG_RELOAD_SCOPE_SELF:
            self.ctx.logger.info("插件配置已更新: version=%s", version)
        del config_data

    @Tool(
        "greet",
        brief_description="在合适的时候向用户打招呼",
        detailed_description="参数说明：\n- stream_id：string，必填。当前聊天流 ID。",
        parameters=[
            ToolParameterInfo(
                name="stream_id",
                param_type=ToolParamType.STRING,
                description="当前聊天流 ID",
                required=True,
            ),
        ],
    )
    async def handle_greet(self, stream_id: str, **kwargs):
        del kwargs
        await self.ctx.send.text("你好！", stream_id)
        return {"success": True, "message": "已回复"}

    @Command("hello", pattern=r"^/hello")
    async def handle_hello(self, **kwargs):
        await self.ctx.send.text("Hello!", kwargs["stream_id"])
        return True, "Hello!", 2

def create_plugin():
    return MyPlugin()
```

将上述代码保存为 `plugin.py`，放入 MaiBot 的 `plugins/` 目录即可自动加载。

如果你是在迁移旧插件，`Action` 装饰器仍然可以继续使用；但它现在只是兼容入口，SDK 内部会把它转换成 Tool 声明，新的插件建议直接使用 `@Tool`。

如果你在编写平台接入插件，请使用 `@MessageGateway` 声明消息网关组件，并通过 `self.ctx.gateway.route_message()` 将外部平台消息注入 Host。详细示例见 [插件开发指南](docs/guide.md) 中的 `MessageGateway` 章节。

## 能力一览

通过 `self.ctx` 访问所有能力，调用自动转发为 RPC 请求：

| 属性 | 说明 |
|------|------|
| `ctx.api` | 插件 API 查询、调用与动态同步 |
| `ctx.gateway` | 消息网关路由与运行时状态上报 |
| `ctx.send` | 发送文本、图片、表情、转发、混合消息 |
| `ctx.db` | 数据库增删改查计数 |
| `ctx.llm` | LLM 文本生成与工具调用 |
| `ctx.config` | 插件配置读取 |
| `ctx.emoji` | 表情包管理 |
| `ctx.message` | 历史消息查询 |
| `ctx.frequency` | 发言频率控制 |
| `ctx.component` | 插件与组件管理 |
| `ctx.chat` | 聊天流查询 |
| `ctx.person` | 用户信息查询 |
| `ctx.render` | 将 HTML 渲染为 PNG 图片 |
| `ctx.knowledge` | LPMM 知识库搜索 |
| `ctx.tool` | LLM 工具定义查询 |
| `ctx.logger` | 插件日志（标准 logging.Logger） |

## 消息网关插件

如果插件负责把外部平台接入 MaiBot，可使用 `@MessageGateway` 声明消息网关组件：

```python
from typing import Any

from maibot_sdk import CONFIG_RELOAD_SCOPE_SELF, MaiBotPlugin, MessageGateway


class NapCatGatewayPlugin(MaiBotPlugin):
    async def on_load(self) -> None:
        await self.ctx.gateway.update_state(
            gateway_name="napcat_gateway",
            ready=True,
            platform="qq",
            account_id="10001",
            scope="primary",
            metadata={"protocol": "napcat"},
        )

    async def on_unload(self) -> None:
        await self.ctx.gateway.update_state(
            gateway_name="napcat_gateway",
            ready=False,
        )

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        if scope == CONFIG_RELOAD_SCOPE_SELF:
            self.ctx.logger.info("配置已更新: %s", version)
        del config_data

    @MessageGateway(
        route_type="duplex",
        name="napcat_gateway",
        platform="qq",
        protocol="napcat",
        account_id="10001",
        scope="primary",
    )
    async def send_to_platform(
        self,
        message: dict[str, Any],
        route: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        # 将 Host MessageDict 转成平台动作并发送
        return {"success": True, "external_message_id": "platform-msg-1"}

    async def handle_inbound(self, payload: dict[str, Any]) -> None:
        accepted = await self.ctx.gateway.route_message(
            gateway_name="napcat_gateway",
            {
                "message_id": payload["message_id"],
                "platform": "qq",
                "message_info": {
                    "user_info": {
                        "user_id": payload["user_id"],
                        "user_nickname": payload["nickname"],
                    },
                    "additional_config": {},
                },
                "raw_message": payload["message"],
            },
            route_metadata={"self_id": "10001", "connection_id": "primary"},
            external_message_id=payload["message_id"],
            dedupe_key=payload["message_id"],
        )
        if not accepted:
            self.ctx.logger.warning("Host 未接收入站消息: %s", payload["message_id"])


def create_plugin():
    return NapCatGatewayPlugin()
```

主程序会根据 `route_type` 和运行时状态选择可用网关：

- `route_type="send"` 或 `"duplex"` 的网关可被 Platform IO 选中处理出站消息
- `route_type="receive"` 或 `"duplex"` 的网关可通过 `ctx.gateway.route_message()` 注入入站消息
- 插件应在链路可用时调用 `ctx.gateway.update_state(..., ready=True)`，在断开或卸载时上报 `ready=False`

## 配置模型

如果你希望 Runner 自动补齐默认配置、向 WebUI 暴露结构化 Schema，并在插件内以强类型对象读取配置，可以声明 `config_model`：

```python
from maibot_sdk import Field, MaiBotPlugin, PluginConfigBase


class PluginSection(PluginConfigBase):
    """插件基础配置。"""

    __ui_label__ = "插件设置"

    enabled: bool = Field(default=True, description="是否启用插件")
    greeting: str = Field(default="你好！", description="默认问候语")


class MyPluginConfig(PluginConfigBase):
    """插件完整配置。"""

    plugin: PluginSection = Field(default_factory=PluginSection)


class MyPlugin(MaiBotPlugin):
    config_model = MyPluginConfig

    async def on_load(self) -> None:
        self.ctx.logger.info("当前问候语: %s", self.config.plugin.greeting)
```

配置来源仍然是插件目录下的 `config.toml`。当插件声明了 `config_model` 后，Runner / Host 可以基于模型生成默认配置和 WebUI Schema，插件代码则可以通过 `self.config` 访问校验后的强类型配置对象；需要临时读取原始配置值时，也仍可继续使用 `await self.ctx.config.get(...)`。

## 兼容说明

- Runner 会在调用 `on_load()` 之前先注入 `PluginContext` 并完成 capability bootstrap，因此插件可以在 `on_load()` 中直接调用 `self.ctx.send.*`、`self.ctx.db.*` 等能力，无需自行等待“注册完成”信号。
- SDK 插件必须实现 `on_load()`、`on_unload()` 和 `on_config_update(scope, config_data, version)` 三个生命周期方法；未实现时 Runner 会拒绝加载。
- `HookHandler` 现在基于命名 Hook 点注册，不再依赖固定的 workflow stage；插件通过 `hook`、`mode`、`order` 描述自己的订阅位置。
- `PluginContext` 当前暴露 15 个能力代理：`api`、`gateway`、`send`、`db`、`llm`、`config`、`emoji`、`message`、`frequency`、`component`、`chat`、`person`、`render`、`knowledge`、`tool`。
- `ctx.gateway.route_message()` / `ctx.gateway.update_state()` 分别对应主程序的入站路由和网关状态上报接口；只有处于 `ready=True` 的消息网关才会被主程序接收入站消息或纳入出站路由。
- `ctx.api` 支持查询、调用其他插件公开的 API，也支持用 `register_dynamic_api()` / `sync_dynamic_apis()` 动态更新当前插件的 API 集合。
- 如果插件声明了 `config_model`，Runner 会在注入配置时按模型补齐默认值并构造 `self.config` 强类型对象；Host / WebUI 也可复用 `get_default_config()` 与 `get_webui_config_schema()` 导出的配置元数据。
- `ctx.send.custom(custom_type, data, stream_id)` 现在会同时发送新旧两套字段别名，便于与不同版本 Host 兼容。
- `ctx.db.count(model_name, filters)` 直接返回 `int`，SDK 会自动解包 Host 返回的 RPC 结果。
- 对于 `config.get()`、`chat.*`、`message.*`、`person.*`、`frequency.get_*()`、`tool.get_definitions()` 等接口，SDK 会自动把 Host 返回的单字段包装结果解包为插件更直观的值、列表或字典；兼容层异步 API 也保持相同语义。
- `ctx.render.html2png()` 可将 HTML 模板渲染为 PNG 图片，适合卡片、榜单或分享图等需要图片化输出的场景。
- 兼容层 `emoji_api.get_random()` / `emoji_api.get_by_description()` 会返回归一化后的字典结果，而不是旧版 tuple 结构；迁移旧插件时请按字段读取。
- `ctx.chat.*` 查询接口支持显式传入 `platform`，不再被固定到默认平台。
- `ctx.llm.generate*()` 会同时兼容 `model` 和 `model_name` 字段；插件侧优先读取 `model` 即可。
- 旧版同步 `component_manage_api` / `plugin_manage_api` 查询函数会返回最近一次运行时同步到本地的插件快照；如果需要实时状态，优先使用新的异步 `ctx.component.*` 能力。
- 插件热重载采用“验证通过后切换”的安全策略。正常插件开发无需感知 generation 细节，但在 reload 失败时，旧插件实例会继续提供服务。
- `ctx.component.load_plugin()` / `ctx.component.reload_plugin()` 在新运行时里只会在切换成功后返回成功；如果新 Runner 预热失败并回滚，SDK 会收到失败结果，而不是“已回滚但仍返回成功”的假阳性。

## 插件目录结构

```
my_plugin/
    plugin.py          # 插件入口，包含 create_plugin()
    config.toml        # 可选配置
```

## 环境要求

- Python >= 3.10
- pydantic >= 2.0
- msgpack >= 1.0

## 开发

```bash
git clone https://github.com/Mai-with-u/maibot-plugin-sdk.git
cd maibot-plugin-sdk
uv sync --extra dev

uv run ruff check .           # lint
uv run ruff format --check .  # 格式检查
uv run mypy .                 # 类型检查
uv run pytest -v              # 测试
```

## 许可证

[LGPL-3.0](LICENSE)
