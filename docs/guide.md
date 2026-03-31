# MaiBot 插件开发指南

本文档面向 MaiBot 插件开发者，覆盖从环境搭建到发布上线的完整流程。

---

## 目录

- [环境准备](#环境准备)
- [快速开始](#快速开始)
- [插件结构](#插件结构)
- [插件基类](#插件基类)
- [组件装饰器](#组件装饰器)
  - [API](#api)
  - [Action](#action)
  - [Command](#command)
  - [Tool](#tool)
  - [EventHandler](#eventhandler)
  - [HookHandler](#hookhandler)
  - [MessageGateway](#messagegateway)
- [能力代理](#能力代理)
  - [API -- 插件 API](#api----插件-api)
  - [Gateway -- 消息网关](#gateway----消息网关)
  - [Send -- 消息发送](#send----消息发送)
  - [Database -- 数据库](#database----数据库)
  - [LLM -- 大语言模型](#llm----大语言模型)
  - [Config -- 配置](#config----配置)
  - [Emoji -- 表情包](#emoji----表情包)
  - [Message -- 消息查询](#message----消息查询)
  - [Frequency -- 频率控制](#frequency----频率控制)
  - [Component -- 组件管理](#component----组件管理)
  - [Chat -- 聊天流](#chat----聊天流)
  - [Person -- 用户信息](#person----用户信息)
  - [Knowledge -- 知识库](#knowledge----知识库)
  - [Tool -- 工具定义](#tool----工具定义)
  - [Logger -- 日志](#logger----日志)
- [消息模型](#消息模型)
- [类型定义](#类型定义)
- [生命周期](#生命周期)
- [运行机制](#运行机制)
- [调试与测试](#调试与测试)
- [发布插件](#发布插件)
- [常见问题](#常见问题)

---

## 环境准备

Python >= 3.10。

```bash
pip install maibot-plugin-sdk
```

安装后即可在代码中导入：

```python
from maibot_sdk import API, Command, EventHandler, HookHandler, MaiBotPlugin, MessageGateway, Tool
```

SDK 的运行时依赖仅有 `pydantic` 和 `msgpack`，不会引入额外框架。
如果你正在迁移旧插件，仍可导入 `Action`；但它现在是兼容入口，内部会自动转换成 Tool 声明。

---

## 快速开始

创建一个最小插件，只需三步：

1. 在 MaiBot 的 `plugins/` 目录下新建文件夹，例如 `plugins/hello/`
2. 创建 `plugin.py`：

```python
from maibot_sdk import Command, CONFIG_RELOAD_SCOPE_SELF, MaiBotPlugin, Tool
from maibot_sdk.types import ToolParameterInfo, ToolParamType


class HelloPlugin(MaiBotPlugin):
    async def on_load(self) -> None:
        return None

    async def on_unload(self) -> None:
        return None

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        if scope == CONFIG_RELOAD_SCOPE_SELF:
            self.ctx.logger.info("插件配置已更新: version=%s", version)
        del config_data

    @Tool(
        "say_hello",
        brief_description="在当前聊天中发送问候",
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
    return HelloPlugin()
```

3. 启动 MaiBot，插件会被自动发现和加载。

**关键约束**：

- 入口文件必须是 `plugin.py`
- 必须定义模块级函数 `create_plugin()`，返回 `MaiBotPlugin` 子类实例
- SDK 插件必须实现 `on_load()`、`on_unload()`、`on_config_update(scope, config_data, version)` 三个生命周期方法
- 插件代码不得直接 import `src.*` 模块，所有能力通过 `self.ctx` 获取

---

## 插件结构

推荐的目录布局：

```
plugins/
  my_plugin/
    plugin.py        # 入口文件（必需）
    config.toml      # 插件配置（可选）
    README.md        # 插件说明（可选）
    utils.py         # 自定义工具模块（可选）
    ...
```

`plugin.py` 是唯一约定的文件名。其他文件按需添加。

---

## 插件基类

所有插件必须继承 `MaiBotPlugin`：

```python
from maibot_sdk import MaiBotPlugin

class MyPlugin(MaiBotPlugin):
    async def on_load(self) -> None:
        return None

    async def on_unload(self) -> None:
        return None

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        del scope
        del config_data
        del version

def create_plugin():
    return MyPlugin()
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `self.ctx` | `PluginContext` | 运行时上下文，由 Runner 注入。未初始化时访问会抛出 `RuntimeError` |

### 类属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `config_reload_subscriptions` | `Iterable[str]` | 订阅全局配置热更新广播，仅支持 `bot` / `model` |

### 生命周期回调

| 方法 | 说明 |
|------|------|
| `async on_load()` | 插件完成上下文注入、配置注入、能力 bootstrap 和组件注册后调用，可用于初始化资源 |
| `async on_unload()` | 插件卸载前调用，可用于清理资源 |
| `async on_config_update(scope, config_data, version)` | 配置热更新时调用；`scope` 取值为 `self`、`bot`、`model` |

这三个方法对 SDK 插件都是必选实现。Runner 在加载阶段会检查子类是否覆盖；未实现时会直接拒绝加载。

### get_components()

`get_components()` 由 Runner 自动调用，收集所有被装饰器标记的组件声明，并自动合并通过 `register_dynamic_api()` 注册的动态 API 组件，无需手动覆盖。

### get_config_reload_subscriptions()

`get_config_reload_subscriptions()` 会返回归一化后的全局配置热更新订阅列表。普通插件通常只需要在类属性上声明：

```python
from maibot_sdk import MaiBotPlugin, ON_BOT_CONFIG_RELOAD, ON_MODEL_CONFIG_RELOAD


class ConfigAwarePlugin(MaiBotPlugin):
    config_reload_subscriptions = {ON_BOT_CONFIG_RELOAD, ON_MODEL_CONFIG_RELOAD}
```

插件自身目录下的 `config.toml` 更新不需要声明订阅，Runner 会固定通过 `on_config_update(scope="self", ...)` 通知。

---

## 组件装饰器

组件是插件对外暴露的功能单元。通过装饰器声明组件，Runner 在加载插件时自动收集并注册到 Host。

当前 SDK 对外推荐 6 种正式组件装饰器：`API`、`Command`、`Tool`、`EventHandler`、`HookHandler`、`MessageGateway`。`Action` 仍然保留，但仅作为旧插件迁移时的兼容入口，内部会自动转换成 Tool 声明。`WorkflowStep` 已在 2.0 中移除，仅保留一个会抛错的占位入口用于提示迁移。

### API

`@API` 用于声明插件向其他插件暴露的可调用接口。只有设置 `public=True` 的 API 才能被其他插件通过 `self.ctx.api.call()` 调用。

```python
from maibot_sdk import API, MaiBotPlugin


class MathPlugin(MaiBotPlugin):
    async def on_load(self) -> None:
        return None

    async def on_unload(self) -> None:
        return None

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        del scope
        del config_data
        del version

    @API("sum_numbers", description="计算整数和", version="1", public=True)
    async def sum_numbers(self, a: int, b: int) -> dict[str, int]:
        return {"result": a + b}
```

**参数列表**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | (必填) | API 名称 |
| `description` | `str` | `""` | API 描述 |
| `version` | `str` | `"1"` | API 版本 |
| `public` | `bool` | `False` | 是否允许其他插件调用 |
| `**metadata` | `dict[str, Any]` | `{}` | 附加元数据 |

说明：

- API 组件会注册到 Host 的 API 注册表中，可被 `ctx.api.get()` / `ctx.api.list()` / `ctx.api.call()` 查询和调用。
- `public=False` 时，API 仍会注册，但默认仅供插件自身或 Host 内部流程使用。
- 除静态 `@API` 外，插件也可以通过 `register_dynamic_api()` / `unregister_dynamic_api()` / `sync_dynamic_apis()` 维护动态 API 集合，适合 MCP 服务上下线这类场景。

### Action

`Action` 现在是**兼容旧插件的声明入口**，不再是 SDK 推荐的新能力声明方式。主程序内部已经统一按 Tool 抽象处理这类能力，所以：

- 新插件请优先使用 `@Tool`
- 旧插件迁移时如果想少改动，可以暂时保留 `@Action`
- `@Action` 会在 SDK 内部自动转换成 Tool 声明，并保留旧的激活条件、提示语和参数信息到元数据/详细描述中

```python
from maibot_sdk import Action
from maibot_sdk.types import ActivationType, ChatMode

@Action(
    "greet",
    description="向用户打招呼",
    activation_type=ActivationType.KEYWORD,
    activation_keywords=["你好", "hello"],
    chat_mode=ChatMode.NORMAL,
    action_require=["send"],
)
async def handle_greet(self, **kwargs):
    stream_id = kwargs["stream_id"]
    await self.ctx.send.text("你好！", stream_id)
    return True, "已回复"
```

如果你是在写新插件，推荐直接改成：

```python
from maibot_sdk import Tool
from maibot_sdk.types import ToolParameterInfo, ToolParamType

@Tool(
    "greet",
    brief_description="向用户打招呼",
    detailed_description="当对话需要寒暄、欢迎或礼貌回应时使用。",
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
```

**参数列表**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | (必填) | 组件名称，全局唯一 |
| `description` | `str` | `""` | 组件描述 |
| `activation_type` | `ActivationType` | `ALWAYS` | 激活方式 |
| `activation_keywords` | `list[str]` | `[]` | 关键词列表（`KEYWORD` 模式下生效） |
| `activation_probability` | `float` | `1.0` | 随机触发概率（`RANDOM` 模式下生效） |
| `chat_mode` | `ChatMode` | `NORMAL` | 生效的聊天模式 |
| `action_parameters` | `dict` | `{}` | Action 自定义参数 |
| `action_require` | `list[str]` | `[]` | 前置需求（如 `["send"]`） |
| `associated_types` | `list[str]` | `[]` | 关联的消息类型 |
| `parallel_action` | `bool` | `False` | 是否允许并行执行 |
| `action_prompt` | `str` | `""` | LLM 规划时使用的 prompt 提示 |

**ActivationType 枚举**：

| 值 | 含义 |
|----|------|
| `ALWAYS` | 始终参与调度 |
| `KEYWORD` | 消息包含关键词时触发 |
| `RANDOM` | 按概率随机触发 |
| `NEVER` | 禁用（不参与调度） |

**返回值**：`(success: bool, reason: str)`

- `success` -- 动作是否执行成功
- `reason` -- 结果描述

### Command

Command 是命令处理器，通过正则表达式匹配用户输入。

```python
from maibot_sdk import Command

@Command("set_mode", description="设置模式", pattern=r"^/mode\s+(\w+)", aliases=["/m"])
async def handle_mode(self, **kwargs):
    # kwargs 中包含 match 对象和原始消息
    await self.ctx.send.text("模式已切换", kwargs["stream_id"])
    return True, "done", 2
```

**参数列表**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | (必填) | 组件名称 |
| `description` | `str` | `""` | 描述 |
| `pattern` | `str` | `""` | 正则匹配模式 |
| `aliases` | `list[str]` | `[]` | 命令别名 |

**返回值**：`(success: bool, response: str, priority: int)`

- `priority` -- 回复优先级（数值越大越优先）

### Tool

Tool 供 LLM Agent 在规划阶段调用。参数定义会被序列化为 JSON Schema 传递给 LLM。

```python
from maibot_sdk import Tool
from maibot_sdk.types import ToolParameterInfo, ToolParamType

@Tool(
    "web_search",
    description="搜索互联网",
    brief_description="查询互联网信息并返回结果摘要",
    detailed_description="参数说明：\n- query：string，必填。搜索关键词。\n- limit：integer，可选。返回结果数量。",
    parameters=[
        ToolParameterInfo(
            name="query",
            param_type=ToolParamType.STRING,
            description="搜索关键词",
            required=True,
        ),
        ToolParameterInfo(
            name="limit",
            param_type=ToolParamType.INTEGER,
            description="返回结果数",
            required=False,
            default=5,
        ),
    ],
)
async def handle_search(self, query: str, limit: int = 5, **kwargs):
    # 执行搜索逻辑
    results = await do_search(query, limit)
    return results
```

描述字段约定：

- `brief_description`：给主程序或小模型快速判断“这个工具是做什么的”
- `detailed_description`：描述参数、必填项、可选项和调用约束
- `description`：兼容旧写法；如果不显式提供 `brief_description`，会自动作为简要描述使用

**ToolParamType 枚举**：

| 值 | 含义 |
|----|------|
| `STRING` | 字符串 |
| `INTEGER` | 整数 |
| `FLOAT` | 浮点数 |
| `BOOLEAN` | 布尔值 |
| `ARRAY` | 数组 |
| `OBJECT` | 对象 |

也支持 dict 方式声明参数（兼容旧式写法）：

```python
@Tool("search", parameters={"query": {"type": "string", "description": "关键词"}})
async def handle_search(self, query: str, **kwargs):
    ...
```

### EventHandler

EventHandler 监听消息链中的事件。可以选择阻塞消息链（拦截模式）或异步触发。

```python
from maibot_sdk import EventHandler
from maibot_sdk.types import EventType

# 异步监听（不影响消息链）
@EventHandler("logger", event_type=EventType.ON_MESSAGE)
async def log_message(self, **kwargs):
    print(f"收到消息: {kwargs.get('plain_text', '')}")

# 拦截模式（阻塞消息链，可修改/过滤消息）
@EventHandler(
    "spam_filter",
    event_type=EventType.ON_MESSAGE_PRE_PROCESS,
    intercept_message=True,
    weight=100,
)
async def filter_spam(self, **kwargs):
    text = kwargs.get("plain_text", "")
    if "spam" in text:
        return {"blocked": True}
    return None
```

**EventHandler 返回值**：

返回 `None` 表示不干预。返回 `dict` 时，支持以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `blocked` | `bool` | `True` 则阻止消息继续传播（等价于 `continue_processing=False`） |
| `continue_processing` | `bool` | 是否允许消息继续传播，默认 `True` |
| `modified_message` | `Any` | 替换后续处理中使用的消息内容（可选） |
| `custom_result` | `Any` | 自定义返回数据（可选） |

> 推荐使用 `{"blocked": True}` 来拦截消息，语义更清晰。

**参数列表**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | (必填) | 组件名称 |
| `description` | `str` | `""` | 描述 |
| `event_type` | `EventType` | `ON_MESSAGE` | 监听的事件类型 |
| `intercept_message` | `bool` | `False` | `True` = 阻塞消息链；`False` = 异步触发 |
| `weight` | `int` | `0` | 优先级（越高越先执行） |

**EventType 枚举**：

| 值 | 说明 |
|----|------|
| `ON_START` | 系统启动 |
| `ON_STOP` | 系统关闭 |
| `ON_MESSAGE_PRE_PROCESS` | 消息预处理（在 Action/Command 之前） |
| `ON_MESSAGE` | 收到消息 |
| `ON_PLAN` | 规划阶段 |
| `POST_LLM` | LLM 响应后 |
| `AFTER_LLM` | LLM 后处理完成 |
| `POST_SEND_PRE_PROCESS` | 发送前预处理 |
| `POST_SEND` | 消息发送后 |
| `AFTER_SEND` | 发送后处理完成 |

### HookHandler

`HookHandler` 用于订阅主程序真实执行路径上的命名 Hook 点。主程序在任意位置调用
`await manager.invoke_hook("hook.name", **kwargs)` 时，所有订阅该 Hook 的插件处理器都会被 Host 调度执行。

```python
from maibot_sdk import HookHandler
from maibot_sdk.types import ErrorPolicy, HookMode, HookOrder

@HookHandler(
    "heart_fc.heart_flow_cycle_start",
    name="keyword_guard",
    mode=HookMode.BLOCKING,
    order=HookOrder.EARLY,
    timeout_ms=5000,
    error_policy=ErrorPolicy.SKIP,
)
async def guard_cycle_start(self, session_id="", cycle_id="", **kwargs):
    if not session_id:
        return {"action": "abort"}
    return {
        "action": "continue",
        "modified_kwargs": {
            "session_id": session_id,
            "cycle_id": cycle_id,
            **kwargs,
        },
    }

@HookHandler(
    "heart_fc.heart_flow_cycle_start",
    name="analytics_observer",
    mode=HookMode.OBSERVE,
    order=HookOrder.LATE,
)
async def collect_analytics(self, session_id="", cycle_id="", **kwargs):
    await self.ctx.db.query(
        model_name="HookLog",
        query_type="insert",
        data={"session_id": session_id, "cycle_id": cycle_id},
    )
```

**参数列表**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `hook` | `str` | (必填) | 订阅的命名 Hook 名称 |
| `name` | `str` | `方法名` | 组件名称；留空时默认使用被装饰方法名 |
| `description` | `str` | `""` | 描述 |
| `mode` | `HookMode` | `BLOCKING` | `BLOCKING` 为串行控制点，`OBSERVE` 为并发观察者 |
| `order` | `HookOrder` | `NORMAL` | 同一模式内的顺序槽位：`EARLY` / `NORMAL` / `LATE` |
| `timeout_ms` | `int` | `0` | 超时毫秒数，`0` 表示使用当前 Hook 的默认值 |
| `error_policy` | `ErrorPolicy` | `SKIP` | 异常处理策略 |

**Host 执行顺序**：

1. `BLOCKING` 先于 `OBSERVE`
2. `EARLY` 先于 `NORMAL` 先于 `LATE`
3. 内置插件先于第三方插件
4. 同槽位内按 `plugin_id` 和处理器名称稳定排序

**HookHandler 返回值**：

| 字段 | 含义 |
|------|------|
| `action="continue"` | 继续执行后续 blocking 处理器 |
| `action="abort"` | 中止本次 Hook 调用 |
| `modified_kwargs` | 仅 `BLOCKING` 处理器可返回，用于覆盖后续处理器看到的参数 |
| `custom_result` | 额外返回值；主要用于日志和上层附加处理 |

**ErrorPolicy 错误策略**：

| 值 | 含义 |
|----|------|
| `ABORT` | 异常时终止当前 Hook 调用 |
| `SKIP` | 记录日志，跳过此步骤继续 |
| `LOG` | 记录日志，并继续后续步骤 |

### MessageGateway

`@MessageGateway` 用于声明插件承担“消息网关”角色。主程序会根据它的 `route_type`、静态声明和运行时状态，把它纳入 Platform IO 的入站/出站路由。

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
        await self.ctx.gateway.update_state(gateway_name="napcat_gateway", ready=False)

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
        del route
        del metadata
        del kwargs
        return {"success": True, "external_message_id": "platform-msg-1"}
```

**参数列表**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `route_type` | `str` | (必填) | 路由类型，支持 `send`、`receive`、`duplex` |
| `name` | `str` | `""` | 组件名；留空时默认使用方法名 |
| `description` | `str` | `""` | 组件描述 |
| `platform` | `str` | `""` | 可选的平台名称 |
| `protocol` | `str` | `""` | 可选的协议或接入方言名称 |
| `account_id` | `str` | `""` | 可选的账号 ID / `self_id` |
| `scope` | `str` | `""` | 可选的路由作用域 |
| `**metadata` | `dict[str, Any]` | `{}` | 额外元数据 |

说明：

- `route_type="send"` 的网关只参与出站路由。
- `route_type="receive"` 的网关只参与入站注入。
- `route_type="duplex"` 的网关同时承担入站和出站职责。
- 仅声明 `@MessageGateway` 还不够；插件还需要在链路可用时调用 `ctx.gateway.update_state(..., ready=True)`，主程序才会把它纳入实际路由。

---

## 能力代理

所有能力通过 `self.ctx` 访问。底层统一转发为 RPC 请求，插件无需关心 IPC 细节。

当前 `PluginContext` 暴露 14 个能力代理：`api`、`gateway`、`send`、`db`、`llm`、`config`、`emoji`、`message`、`frequency`、`component`、`chat`、`person`、`knowledge`、`tool`，以及一个标准 `logging.Logger` 形式的 `logger` 属性。

### API -- 插件 API

```python
api = self.ctx.api
```

| 方法 | 说明 |
|------|------|
| `await api.call(api_name, version="", **kwargs)` | 调用其他插件公开的 API |
| `await api.get(api_name, version="")` | 获取单个可见 API 的元信息 |
| `await api.list(plugin_id="")` | 列出当前插件可见的 API |
| `await api.replace_dynamic_apis(apis, offline_reason="动态 API 已下线")` | 用新的动态 API 集合替换当前插件已暴露的动态 API |

示例：

```python
# 调用其他插件公开的 API
result = await self.ctx.api.call("plugin_a.sum_numbers", a=1, b=2)

# 查询可见 API
apis = await self.ctx.api.list()
info = await self.ctx.api.get("plugin_a.sum_numbers", version="1")

# 动态 API 同步
self.register_dynamic_api(
    "mcp_search",
    handler=self.handle_mcp_search,
    description="MCP 搜索接口",
    version="1",
    public=True,
)
await self.sync_dynamic_apis(offline_reason="MCP 服务已关闭")
```

说明：

- `api_name` 支持完整名 `plugin_id.api_name`，也支持唯一短名。
- `replace_dynamic_apis()` 适合 MCP 服务器、外部能力市场等“API 集合会动态变化”的场景。
- 动态 API 下线后，Host 会把它们标记为 offline，并对后续调用返回 `offline_reason`。

### Gateway -- 消息网关

```python
gateway = self.ctx.gateway
```

| 方法 | 说明 |
|------|------|
| `await gateway.route_message(gateway_name, message, route_metadata=None, external_message_id="", dedupe_key="")` | 通过指定消息网关把外部平台消息注入 Host |
| `await gateway.update_state(gateway_name, ready, platform="", account_id="", scope="", metadata=None)` | 向 Host 上报消息网关运行时状态 |
| `await gateway.receive_external_message(message, gateway_name=..., ...)` | `route_message()` 的兼容别名 |
| `await gateway.update_runtime_state(gateway_name=..., connected=..., ...)` | `update_state()` 的兼容别名 |

消息网关插件通常会在链路连接成功后上报 `ready=True`，并在收到平台消息时注入 Host：

```python
await self.ctx.gateway.update_state(
    gateway_name="napcat_gateway",
    ready=True,
    platform="qq",
    account_id="10001",
    scope="primary",
    metadata={"protocol": "napcat"},
)

accepted = await self.ctx.gateway.route_message(
    gateway_name="napcat_gateway",
    message={
        "message_id": "msg-1",
        "platform": "qq",
        "message_info": {
            "user_info": {
                "user_id": "u1",
                "user_nickname": "tester",
            },
            "group_info": {
                "group_id": "g1",
                "group_name": "group",
            },
            "additional_config": {},
        },
        "raw_message": [],
    },
    route_metadata={"self_id": "10001", "connection_id": "primary"},
    external_message_id="external-1",
    dedupe_key="dedupe-1",
)
```

说明：

- `message` 需要遵守 Host 当前的 `MessageDict` 结构，至少保证 `message_id`、`platform`、`message_info.user_info.user_id`、`message_info.user_info.user_nickname` 和 `raw_message` 存在。
- 只有已经声明 `@MessageGateway(route_type="receive" | "duplex")` 且运行时处于 `ready=True` 的网关，Host 才会接受入站注入。
- `route_metadata` 常见字段包括 `self_id`、`connection_id`，Host 会把其中的账号/作用域信息补充到 Platform IO 路由键中。

### Send -- 消息发送

```python
send = self.ctx.send
```

| 方法 | 参数 | 说明 |
|------|------|------|
| `await send.text(text, stream_id)` | `text: str`, `stream_id: str` | 发送文本消息 |
| `await send.image(image_data, stream_id)` | `image_data: str (base64)` | 发送图片 |
| `await send.emoji(emoji_data, stream_id)` | `emoji_data: str (base64)` | 发送表情 |
| `await send.command(command, stream_id)` | `command: str`, `stream_id: str` | 发送指令消息 |
| `await send.forward(messages, stream_id)` | `messages: list[dict]` | 发送转发消息 |
| `await send.hybrid(segments, stream_id)` | `segments: list[dict]` | 发送图文混合消息 |
| `await send.custom(custom_type, data, stream_id)` | `custom_type: str`, `data: Any` | 发送自定义类型消息 |

说明：`send.custom()` 会同时携带 `custom_type/data` 和 `message_type/content` 两套字段名，用于兼容不同版本的 Host 实现。插件侧只需要继续传 `custom_type` 与 `data`。

示例：

```python
# 发送文本
await self.ctx.send.text("你好", stream_id)

# 发送图片（base64）
import base64
with open("image.png", "rb") as f:
    data = base64.b64encode(f.read()).decode()
await self.ctx.send.image(data, stream_id)

# 图文混合
await self.ctx.send.hybrid([
    {"type": "text", "content": "看看这张图："},
    {"type": "image", "content": image_base64},
], stream_id)
```

### Database -- 数据库

```python
db = self.ctx.db
```

| 方法 | 说明 |
|------|------|
| `await db.query(model_name, query_type="get", data=None, filters=None, order_by=None, limit=None, single_result=False)` | 通用数据库操作 |
| `await db.save(model_name, data, key_field="id", key_value=None)` | 插入或按字段更新 |
| `await db.get(model_name, filters=None, limit=None, order_by=None, single_result=False)` | 按条件获取记录 |
| `await db.delete(model_name, filters)` | 删除数据 |
| `await db.count(model_name, filters)` | 计数 |

`db.count()` 的返回值始终是 `int`。即使 Host 侧 RPC 返回的是带 `count` 字段的对象，SDK 也会自动解包。

注意：这里的 `model_name` 必须是 Host 侧 `src.common.database.database_model` 中存在的模型类名，例如 `"ChatHistory"`、`"ActionRecord"`。旧版 `table` 参数名和 `db.get(key_field, key_value)` 形式已经废弃。

能力返回值兼容说明：对于 `config.get()`、`chat.*`、`message.*`、`person.*`、`frequency.get_*()`、`tool.get_definitions()` 这类本来就应返回单个值或列表的接口，SDK 会自动把 Host 侧 `{"success": true, "value": ...}`、`{"success": true, "streams": ...}` 这类 RPC 包装结果还原成插件更直观的返回值。插件代码通常不需要再手动读取 `value`、`messages`、`streams` 等字段。

示例：

```python
# 查询
results = await self.ctx.db.query(
    model_name="ChatHistory",
    query_type="get",
    filters={"session_id": "session-123"},
    order_by=["-start_timestamp"],
    limit=10,
)

# 获取单条记录
record = await self.ctx.db.get(
    model_name="ActionRecord",
    filters={"action_id": "a-1"},
    single_result=True,
)

# 插入
await self.ctx.db.save(
    model_name="ActionRecord",
    data={"action_id": "a-1", "session_id": "session-123", "action_name": "reply"},
)

# 更新
updated = await self.ctx.db.query(
    model_name="ChatHistory",
    query_type="update",
    data={"summary": "updated"},
    filters={"session_id": "session-123"},
)

# 删除
await self.ctx.db.delete(
    model_name="ChatHistory",
    filters={"session_id": "session-123"},
)

# 计数
count = await self.ctx.db.count("ChatHistory", {"session_id": "session-123"})
```

### LLM -- 大语言模型

```python
llm = self.ctx.llm
```

| 方法 | 说明 |
|------|------|
| `await llm.generate(prompt, model, temperature, max_tokens)` | 文本生成 |
| `await llm.generate_with_tools(prompt, tools, ...)` | 带工具调用的生成 |
| `await llm.get_available_models()` | 获取可用模型列表，返回 `list[str]` |

**generate 返回值**：

```python
{
    "success": True,
    "response": "生成的文本",
    "reasoning": "推理内容（如有）",
    "model": "实际使用的模型名",
    "model_name": "实际使用的模型名"
}
```

说明：SDK 会始终补齐 `model` 字段；若 Host 仍返回旧字段名 `model_name`，SDK 会自动兼容。

示例：

```python
# 简单文本生成
result = await self.ctx.llm.generate(
    prompt="请用一句话介绍 Python",
    temperature=0.5,
)
if result["success"]:
    text = result["response"]

# 用消息列表格式
result = await self.ctx.llm.generate(
    prompt=[
        {"role": "system", "content": "你是一个翻译助手"},
        {"role": "user", "content": "翻译：Hello World"},
    ],
)

# 带工具调用
result = await self.ctx.llm.generate_with_tools(
    prompt="今天天气怎么样",
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询天气",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
            },
        },
    }],
)
tool_calls = result.get("tool_calls", [])
```

### Config -- 配置

```python
config = self.ctx.config
```

| 方法 | 说明 |
|------|------|
| `await config.get(key, default)` | 获取配置值，`key` 支持点分割 |
| `await config.get_plugin(plugin_name)` | 获取指定插件的配置 |
| `await config.get_all()` | 获取插件全部配置 |

配置来源为插件目录下的 `config.toml`。

`config.get()`、`config.get_plugin()` 和 `config.get_all()` 都会直接返回配置值或配置字典，不需要手动从 RPC 结果中读取 `value` 字段。

示例：

```python
# 读取单个值
api_key = await self.ctx.config.get("api_key", "")
timeout = await self.ctx.config.get("network.timeout", 30)

# 读取全部配置
all_config = await self.ctx.config.get_all()
```

配置热更新时 `on_config_update` 会被调用：

- 修改插件目录下的 `config.toml` 时，Runner 会以 `scope="self"` 推送配置更新，并先把最新插件配置写回当前实例。
- 修改总配置中的 bot/model 段时，Host 会向已声明 `config_reload_subscriptions` 的插件广播一次配置更新通知。
- 修改 `plugin.py`、`_manifest.json` 或插件源码文件时，会触发所属 Supervisor 的安全热重载。

```python
from maibot_sdk import CONFIG_RELOAD_SCOPE_SELF, ON_MODEL_CONFIG_RELOAD


class MyPlugin(MaiBotPlugin):
    config_reload_subscriptions = {ON_MODEL_CONFIG_RELOAD}

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        if scope == CONFIG_RELOAD_SCOPE_SELF:
            self.api_key = str(config_data.get("api_key", ""))
        elif scope == ON_MODEL_CONFIG_RELOAD:
            self.ctx.logger.info("模型配置已更新: %s", version)
```

说明：

- `scope="self"` 表示插件自身的 `config.toml` 更新。
- `scope="bot"` / `scope="model"` 表示主程序全局配置广播。
- 配置更新不会自动重启插件；只要 Host 发来的是配置更新事件，Runner 会直接调用 `on_config_update()`，适合保留内存态或长连接状态。

### Emoji -- 表情包

```python
emoji = self.ctx.emoji
```

| 方法 | 说明 |
|------|------|
| `await emoji.get_random(count)` | 随机获取表情包 |
| `await emoji.get_by_description(description, limit)` | 按描述搜索 |
| `await emoji.get_count()` | 获取总数 |
| `await emoji.get_info()` | 获取统计信息 |
| `await emoji.get_emotions()` | 获取情感标签列表 |
| `await emoji.get_all()` | 获取全部表情包 |
| `await emoji.register_emoji(emoji_base64)` | 注册新表情 |
| `await emoji.delete_emoji(emoji_hash)` | 删除表情 |

### Message -- 消息查询

```python
message = self.ctx.message
```

| 方法 | 说明 |
|------|------|
| `await message.get_recent(chat_id, limit)` | 获取最近消息 |
| `await message.build_readable(messages, **kwargs)` | 将消息列表格式化为可读字符串 |
| `await message.get_by_time(start_time, end_time)` | 按时间范围查询（全局） |
| `await message.get_by_time_in_chat(chat_id, start_time, end_time)` | 按时间范围查询指定聊天 |
| `await message.count_new(chat_id, since)` | 统计新消息数（`since` 为 UNIX 时间戳字符串） |

`build_readable` 支持两种调用方式：

```python
# 方式 1：传入已查询的消息列表
msgs = await self.ctx.message.get_recent(chat_id, limit=20)
readable = await self.ctx.message.build_readable(msgs)

# 方式 2：通过关键字参数传入 chat_id + 时间范围，由 Host 端查询
readable = await self.ctx.message.build_readable(
    messages=None,
    chat_id=chat_id,
    start_time=start_ts,
    end_time=end_ts,
)
```

可选关键字参数：`replace_bot_name`（默认 `True`）、`timestamp_mode`（默认 `"relative"`）、`truncate`（默认 `False`）。

`message.get_by_time()`、`message.get_by_time_in_chat()` 和 `message.get_recent()` 会直接返回消息列表；`message.count_new()` 直接返回数量；`message.build_readable()` 直接返回字符串。

### Frequency -- 频率控制

```python
frequency = self.ctx.frequency
```

| 方法 | 说明 |
|------|------|
| `await frequency.get_current_talk_value(chat_id)` | 获取当前 talk value |
| `await frequency.set_adjust(chat_id, value)` | 设置频率调整值 |
| `await frequency.get_adjust(chat_id)` | 获取频率调整值 |

两个 `get_*` 方法都会直接返回数值；`set_adjust()` 返回布尔值表示是否设置成功。

### Component -- 组件管理

```python
component = self.ctx.component
```

| 方法 | 说明 |
|------|------|
| `await component.get_all_plugins()` | 获取所有插件信息（含各插件注册的组件列表） |
| `await component.get_plugin_info(plugin_name)` | 获取指定插件信息 |
| `await component.list_loaded_plugins()` | 列出已加载插件 |
| `await component.list_registered_plugins()` | 列出已注册插件 |
| `await component.enable_component(name, type, scope, stream_id)` | 启用组件（`name` 支持 `plugin_id.comp_name` 全名或短名） |
| `await component.disable_component(name, type, scope, stream_id)` | 禁用组件（`name` 支持 `plugin_id.comp_name` 全名或短名） |
| `await component.load_plugin(plugin_name)` | 加载插件（会校验插件是否存在并路由到对应 Supervisor） |
| `await component.unload_plugin(plugin_name)` | 卸载插件 |
| `await component.reload_plugin(plugin_name)` | 重新加载插件 |

`scope` 支持 `"global"` 和 `"stream"`，`stream` 级别需传入 `stream_id`。

> **注意**：`enable_component` / `disable_component` 的 `name` 参数既可以传完整名称 `"my_plugin.my_command"`，也可以只传短名 `"my_command"`（Host 会自动按 `component_type` 匹配）。当使用短名且存在同名组件时，优先匹配指定 `type` 的组件。
>
> `load_plugin()` / `reload_plugin()` 返回 `True` 仅表示新 Runner 已完成初始化并成功切换；如果预热失败且 Host 回滚到旧 Runner，这两个接口会返回 `False`。

### Chat -- 聊天流

```python
chat = self.ctx.chat
```

| 方法 | 参数 | 说明 |
|------|------|------|
| `await chat.get_all_streams(platform)` | `platform: str = "qq"` | 获取所有聊天流 |
| `await chat.get_group_streams(platform)` | `platform: str = "qq"` | 获取所有群聊流 |
| `await chat.get_private_streams(platform)` | `platform: str = "qq"` | 获取所有私聊流 |
| `await chat.get_stream_by_group_id(group_id, platform)` | `group_id: str` | 按群 ID 查找聊天流 |
| `await chat.get_stream_by_user_id(user_id, platform)` | `user_id: str` | 按用户 ID 查找私聊流 |

`chat.get_all_streams()`、`chat.get_group_streams()`、`chat.get_private_streams()` 会直接返回聊天流列表；两个 `get_stream_by_*()` 方法会直接返回单个聊天流字典或 `None`。

示例：

```python
# 获取所有群聊流
streams = await self.ctx.chat.get_group_streams()

# 根据群号查找
stream = await self.ctx.chat.get_stream_by_group_id("123456")
if stream:
    await self.ctx.send.text("hello", stream["session_id"])
```

### Person -- 用户信息

```python
person = self.ctx.person
```

| 方法 | 参数 | 说明 |
|------|------|------|
| `await person.get_id(platform, user_id)` | `platform: str`, `user_id: str` | 获取 person_id |
| `await person.get_value(person_id, field_name)` | `person_id: str`, `field_name: str` | 获取用户字段值 |
| `await person.get_id_by_name(person_name)` | `person_name: str` | 根据用户名获取 person_id |

`person.get_id()` / `person.get_id_by_name()` 直接返回 `person_id` 字符串；`person.get_value()` 直接返回对应字段值。

示例：

```python
# 获取 person_id
pid = await self.ctx.person.get_id("qq", "12345")

# 获取昵称
name = await self.ctx.person.get_value(pid, "nickname") or "未知"
```

### Knowledge -- 知识库

```python
knowledge = self.ctx.knowledge
```

| 方法 | 参数 | 说明 |
|------|------|------|
| `await knowledge.search(query, limit)` | `query: str`, `limit: int = 5` | 搜索 LPMM 知识库 |

示例：

```python
content = await self.ctx.knowledge.search("Python 是什么", limit=3)
if content:
    print(content)
```

### Tool -- 工具定义

```python
tool = self.ctx.tool
```

| 方法 | 说明 |
|------|------|
| `await tool.get_definitions()` | 获取 LLM 可用的工具定义列表 |

返回的列表中每个元素包含 `name` 和 `definition` 字段。

`tool.get_definitions()` 会直接返回工具定义列表，不需要再从 RPC 结果里手动读取 `tools` 字段。

### Logger -- 日志

插件通过标准 `logging` 模块记录日志——Runner 进程会自动将所有日志通过 IPC 批量传输到主进程显示，**无需 `await`，无需特殊 API**。

#### 推荐写法

```python
# 方式一：通过 ctx.logger（名称自动为 plugin.<plugin_id>）
logger = self.ctx.logger
logger.info("插件已启动")
logger.error(f"请求失败: {err}", exc_info=True)

# 方式二：直接用 stdlib logging（同样会被自动传输）
import logging
logger = logging.getLogger(__name__)
logger.warning("配置缺失，使用默认值")
```

#### ctx.logger

| 属性 | 类型 | 说明 |
|------|------|------|
| `self.ctx.logger` | `logging.Logger` | 标准 Logger，名称为 `plugin.<plugin_id>` |

支持所有标准 `logging.Logger` 方法：`debug()`、`info()`、`warning()`、`error()`、`critical()`，以及 `exc_info=True` 参数。

#### 工作原理

Runner 进程启动后会在 `logging.root` 上安装一个 IPC Handler，拦截进程内**所有** `logging` 调用（包括第三方库的日志），批量发送到主进程。主进程收到后以 `plugin.<plugin_id>` 为 Logger 名称重放，接入控制台、日志文件、Dashboard 等已有的 Handler 链。

> **注意**：旧版的 `await self.ctx.logging.info(...)` 异步 API 已移除。请改用上述标准 `logging` 写法。

---

## 消息模型

`MaiMessages` 是跨组件传递的统一消息格式，用于 EventHandler、HookHandler、Action 之间共享消息数据。

```python
from maibot_sdk.messages import MaiMessages, MessageSegment
```

### 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `message_segments` | `list[MessageSegment]` | 消息段列表 |
| `plain_text` | `str` | 纯文本内容 |
| `llm_prompt` | `str \| None` | LLM 输入 prompt |
| `llm_response_content` | `str \| None` | LLM 回复文本 |
| `llm_response_reasoning` | `str \| None` | LLM 推理内容 |
| `llm_response_model` | `str \| None` | 使用的模型 |
| `llm_response_tool_call` | `list[dict] \| None` | LLM 工具调用 |
| `stream_id` | `str \| None` | 聊天流 ID |
| `is_group_message` | `bool` | 是否群聊 |
| `is_private_message` | `bool` | 是否私聊 |
| `message_base_info` | `dict` | 消息元信息 |
| `raw_message` | `Any \| None` | 原始消息对象 |
| `action_usage` | `list[str] \| None` | 已执行的 Action 列表 |
| `additional_data` | `dict` | 附加数据（自由扩展） |
| `modify_flags` | `dict[str, bool]` | 修改权限标志 |

### 安全修改

消息内容受修改权限标志保护，应使用安全修改方法：

```python
msg = MaiMessages(plain_text="原始内容")

# 检查权限
if msg.can_modify(ModifyFlag.CAN_MODIFY_MESSAGE):
    msg.modify_plain_text("新内容")

# 直接调用安全修改（内部自动检查权限）
success = msg.modify_prompt("新 prompt")       # 修改 LLM prompt
success = msg.modify_response("新回复")         # 修改 LLM response
success = msg.modify_plain_text("新文本")       # 修改纯文本

# 设置权限标志（通常由 Host 设置，插件一般只读）
msg.set_modify_flag(ModifyFlag.CAN_MODIFY_MESSAGE, False)
```

### 序列化

```python
# 序列化为 dict（用于 RPC 传输）
data = msg.to_rpc_dict()

# 从 dict 恢复
msg = MaiMessages.from_rpc_dict(data)

# 深拷贝
msg_copy = msg.deepcopy()
```

---

## 类型定义

所有公共类型位于 `maibot_sdk.types`：

```python
from maibot_sdk.types import (
    # 枚举
    ActivationType,      # Action 激活方式
    ChatMode,            # 聊天模式 (FOCUS/NORMAL/PRIORITY/ALL)
    ComponentType,       # 组件类型 (ACTION/API/COMMAND/TOOL/EVENT_HANDLER/HOOK_HANDLER/MESSAGE_GATEWAY)
    ErrorPolicy,         # 异常策略 (ABORT/SKIP/LOG)
    EventType,           # 事件类型
    HookMode,            # Hook 处理模式 (BLOCKING/OBSERVE)
    HookOrder,           # Hook 顺序槽位 (EARLY/NORMAL/LATE)
    MessageGatewayRouteType,  # 消息网关路由类型
    ModifyFlag,          # 消息修改标志
    ToolParamType,       # 工具参数类型

    # 模型
    ToolParameterInfo,   # 工具参数定义
    ComponentInfo,       # 组件基础信息
    ActionComponentInfo, # Action 组件信息
    APIComponentInfo,    # API 组件信息
    CommandComponentInfo,# Command 组件信息
    ToolComponentInfo,   # Tool 组件信息
    EventHandlerComponentInfo,  # EventHandler 组件信息
    HookHandlerComponentInfo,   # HookHandler 组件信息
    MessageGatewayComponentInfo, # 消息网关组件信息
    CapabilityResult,    # 能力调用结果
)
```

说明：

- `ComponentType.MESSAGE_GATEWAY` 已是 SDK 的正式公开组件类型，对应 `@MessageGateway`。
- `ComponentType.API` 对应 `@API`，可配合 `ctx.api` 能力做插件间互调。
- `WorkflowStep` 不是可继续使用的兼容别名；调用它会直接抛错，插件应迁移到 `HookHandler`。

---

## 生命周期

插件从加载到卸载的完整生命周期：

```
1. Runner 发现 plugins/my_plugin/plugin.py
2. Runner 调用 create_plugin() 获取插件实例
3. Runner 注入 PluginContext (self._ctx)
4. Runner 应用插件自身配置（如 config.toml）
5. Runner 向 Host bootstrap capability 令牌
6. Runner 调用 get_components() / get_config_reload_subscriptions() 收集组件与订阅声明
7. Runner 将组件声明发送给 Host 注册
8. Runner 调用 on_load()
9. Runner 向 Host 发送 ready 信号
   ---- 插件进入运行状态 ----
10. Host 根据事件/消息调度组件执行
11. 配置变更时 Host 通知 Runner 调用 on_config_update(scope, config_data, version)
   ---- 插件卸载 ----
12. Runner 调用 on_unload()
13. 组件从 Host 注销
14. Runner 撤销 capability bootstrap 并清理模块缓存
```

### on_load 阶段可做什么

`PluginContext` 在 `on_load()` 之前已经完成注入，插件配置也已经应用，且 Host 已为当前插件签发 capability 令牌、完成组件注册。因此以下操作在 `on_load()` 中是安全的：

- 调用 `self.ctx.send.*`、`self.ctx.db.*`、`self.ctx.config.*` 等能力
- 创建需要依赖配置内容的内存缓存
- 执行一次性初始化检查或探测
- 对消息网关插件调用 `self.ctx.gateway.update_state(..., ready=True)` 上报链路就绪

更具体地说，`on_load()` 不需要等待“组件注册完成”后再调用 capability。对插件作者来说，`on_load()` 可以视为“插件已经对 Host 完成注册，但还没收到真实业务流量”的初始化阶段。

建议避免在 `on_load()` 中执行特别耗时的网络操作；如果初始化时间过长，会延后整个 Runner 的 ready 信号与热重载切换。

---

## 运行机制

### 热重载与切换语义

新版运行时在插件热重载时，会先拉起新的 Runner，完成握手、插件初始化、组件注册和 ready/health 校验；只有全部验证成功后，才会切换到新 generation。

这意味着：

- reload 成功前，旧插件实例会继续对外提供服务。
- reload 失败时，会回滚到旧 generation，不会因为新 Runner 预热失败而立刻丢失服务。
- 只有在新 Runner 发出 ready 信号后，Host 才会把它视为“可接流量”的实例。
- 插件代码通常不需要处理 generation；只要避免在模块级保存不可重建的全局状态即可。

### 对插件开发的实际影响

- 可以在 `on_load()` 中安全调用 capability，因为 bootstrap 发生在 `on_load()` 之前。
- 不要假设 `reload_plugin()` 返回后一定切到新实例；应始终检查返回值，失败意味着 Host 已保留旧实例继续服务。
- 如果你在 `on_load()` 中维护外部资源，请确保同一份初始化逻辑可以被重复执行，因为热重载会创建全新的 Runner 进程。

MaiBot 采用双子进程架构：

```
MaiBot 主进程 (Host)
  |
  +-- 内置插件 Runner 子进程
  |     加载 src/plugins/built_in/ 下的插件
  |
  +-- 第三方插件 Runner 子进程
        加载 plugins/ 下的插件
```

- Host 与 Runner 之间通过 MsgPack-RPC over TCP/Unix Socket 通信
- 插件代码运行在 Runner 子进程中，与主进程隔离
- 能力调用（`self.ctx.xxx`）自动序列化为 RPC 请求发送到 Host，由 Host 执行后返回结果
- 插件崩溃不影响主进程稳定性

---

## 调试与测试

### 单元测试

SDK 基于 Pydantic，可以在不启动 MaiBot 的情况下测试组件声明和消息处理：

```python
import pytest
from maibot_sdk import MaiBotPlugin, Action
from maibot_sdk.types import ActivationType

class MyPlugin(MaiBotPlugin):
    async def on_load(self) -> None:
        return None

    async def on_unload(self) -> None:
        return None

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        del scope
        del config_data
        del version

    @Action("test", activation_type=ActivationType.KEYWORD, activation_keywords=["hello"])
    async def handle(self, **kwargs):
        return True, "ok"

def test_components():
    plugin = MyPlugin()
    components = plugin.get_components()
    assert len(components) == 1
    assert components[0]["name"] == "test"

def test_messages():
    from maibot_sdk.messages import MaiMessages
    msg = MaiMessages(plain_text="test", stream_id="s1")
    data = msg.to_rpc_dict()
    restored = MaiMessages.from_rpc_dict(data)
    assert restored.plain_text == "test"
```

运行测试：

```bash
uv sync --extra dev
uv run pytest -v
```

### 开发依赖

```bash
uv sync --extra dev
# 包含 ruff、mypy、pytest、pytest-asyncio
```

### 类型检查

SDK 附带 `py.typed` 标记，支持静态类型检查：

```bash
uv run mypy my_plugin/
```

---

## 发布插件

插件不需要打包为 Python 包。直接将插件目录放入 MaiBot 的 `plugins/` 目录即可。

如果需要通过 Git 分发：

```
my-maibot-plugin/
  plugin.py
  config.toml
  README.md
  requirements.txt   # 插件自身的额外依赖（如有）
```

用户只需将目录 clone 到 `plugins/` 下。

---

## 常见问题

**Q: 插件可以 import MaiBot 主程序的模块吗？**

不可以。插件运行在独立子进程中，不能直接 import `src.*`。所有交互通过 `self.ctx` 能力代理完成。

**Q: 插件之间可以互相通信吗？**

可以。推荐方式是由提供方插件声明 `@API(..., public=True)`，调用方通过 `self.ctx.api.call()` 访问。除此之外，也可以通过 `self.ctx.db` 共享数据，或用 `self.ctx.component` 管理其他插件的加载状态。

**Q: 插件抛出异常会怎样？**

不会影响主进程。Runner 进程会捕获异常并上报给 Host，Host 会记录日志。`HookHandler` 的行为取决于 `error_policy` 设置。

**Q: 如何正确处理插件的额外依赖？**

在插件目录放置 `requirements.txt`，用户在安装 MaiBot 后手动运行 `pip install -r plugins/my_plugin/requirements.txt`。

**Q: `create_plugin()` 可以接受参数吗？**

不可以。Runner 调用 `create_plugin()` 时不传递任何参数。初始化逻辑请放在 `on_load()` 中，通过 `self.ctx.config` 读取配置。

**Q: 插件可以使用多线程/多进程吗？**

可以使用 `asyncio` 和 `threading`。不建议使用 `multiprocessing`，因为插件已经运行在子进程中。
