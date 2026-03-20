# MaiBot 插件系统迁移指南：从旧版迁移到新版 SDK

> **适用版本**：从旧版 `src.plugin_system`（基于类继承 + `@register_plugin`）迁移到新版 `maibot-plugin-sdk`（基于装饰器 + RPC 隔离架构）。

---

## 目录

- [概述：为什么要迁移？](#概述为什么要迁移)
- [架构差异总览](#架构差异总览)
- [迁移清单](#迁移清单)
- [第一步：替换依赖和导入](#第一步替换依赖和导入)
- [第二步：改写插件主类](#第二步改写插件主类)
- [第三步：迁移 Action 组件](#第三步迁移-action-组件)
- [第四步：迁移 Command 组件](#第四步迁移-command-组件)
- [第五步：迁移 Tool 组件](#第五步迁移-tool-组件)
- [第六步：迁移 EventHandler 组件](#第六步迁移-eventhandler-组件)
- [第七步：新增 - HookHandler 组件](#第七步新增---hookhandler-组件)
- [第八步：迁移配置系统](#第八步迁移配置系统)
  - [WebUI 配置可视化](#webui-配置可视化)
- [第九步：迁移 API 调用](#第九步迁移-api-调用)
- [第十步：迁移 Manifest 文件](#第十步迁移-manifest-文件)
- [完整迁移示例](#完整迁移示例)
- [常见问题 FAQ](#常见问题-faq)
- [AI 自助迁移 Prompt](#ai-自助迁移-prompt)

---

## 概述：为什么要迁移？

新版插件系统带来了以下关键改进：

| 改进项 | 旧系统 | 新系统 |
|--------|--------|--------|
| **进程隔离** | 插件运行在主进程内，崩溃影响全局 | 插件运行在独立子进程中，崩溃自动恢复 |
| **依赖隔离** | 插件直接导入 `src.*`，版本冲突风险 | 只依赖 `maibot-plugin-sdk`，完全隔离 |
| **组件声明** | 继承基类 + 手动注册（`get_plugin_components`） | 装饰器声明，自动收集 |
| **API 访问** | 直接调用内部模块 | 通过 `self.ctx` 能力代理（RPC 透传） |
| **热重载** | 需要重启 | 支持运行时热重载（新 Runner 验证通过后再切换 generation） |
| **安全模型** | 无隔离，插件可访问一切 | 能力令牌 + 策略引擎控制权限 |

补充说明：新版运行时会在 `on_load()` 之前完成 `PluginContext` 注入和 capability bootstrap，因此迁移后的插件可以在 `on_load()` 中直接调用 `self.ctx.*` 能力；热重载失败时 Host 会回滚到旧 Runner，`reload_plugin()` 将返回失败而不是误报成功。

---

## 架构差异总览

### 旧系统架构

```
主进程
├── PluginManager（加载插件）
├── BasePlugin ← 你的插件（直接继承）
│   ├── BaseAction（类属性声明组件）
│   ├── BaseCommand（类属性声明组件）
│   ├── BaseTool（类属性声明组件）
│   └── BaseEventHandler（类属性声明组件）
├── @register_plugin 装饰器注册
└── get_plugin_components() 手动返回组件列表
```

### 新系统架构

```
Host 主进程
├── PluginRuntimeManager
│   ├── PluginSupervisor（管理子进程生命周期）
│   └── CapabilityService（处理插件能力请求）
│
Runner 子进程（独立进程）
├── PluginLoader（发现和加载插件）
├── MaiBotPlugin ← 你的插件（继承基类）
│   ├── @Action 装饰器（直接标注方法）
│   ├── @Command 装饰器
│   ├── @Tool 装饰器
│   ├── @EventHandler 装饰器
│   └── @HookHandler 装饰器（新增）
├── self.ctx（能力代理，通过 RPC 与 Host 通信）
└── create_plugin() 工厂函数
```

### 核心思维转变

| 旧思维 | 新思维 |
|--------|--------|
| "我在主进程里运行" | "我在独立子进程里运行" |
| "我可以 import 任何 src.* 模块" | "我只能 import maibot_sdk 和第三方库" |
| "我直接调用内部 API" | "我通过 self.ctx 能力代理发起 RPC 调用" |
| "每个组件是一个独立类" | "每个组件是插件类上的一个被装饰的方法" |
| "我手动注册组件到列表里" | "装饰器自动收集，无需手动注册" |
| "配置通过 ConfigField + config_schema 定义" | "配置通过 config.toml + self.ctx.config 读取" |

---

## 迁移清单

> 在开始迁移之前，请确认以下清单：

- [ ] 已安装 `maibot-plugin-sdk`（`pip install maibot-plugin-sdk`）
- [ ] 已确认插件目录下有 `_manifest.json`
- [ ] 已备份旧代码

**迁移步骤概要**：

1. ~~`from src.plugin_system import ...`~~ → `from maibot_sdk import ...`
2. ~~`class MyPlugin(BasePlugin)` + `@register_plugin`~~ → `class MyPlugin(MaiBotPlugin)` + `def create_plugin()`
3. ~~独立组件类（`BaseAction` / `BaseCommand` / `BaseTool` / `BaseEventHandler`）~~ → 装饰器方法
4. ~~`get_plugin_components()` 手动注册~~ → 自动收集（删除该方法）
5. ~~`self.send_text()` / `self.send_emoji()` 等基类方法~~ → `self.ctx.send.text()` / `self.ctx.send.emoji()`
6. ~~`self.get_config(key)` 基类方法~~ → `await self.ctx.config.get(key)`
7. ~~`ConfigField` + `config_schema` 配置声明~~ → `config.toml` 手动编写
8. ~~`self.action_data` / `self.matched_groups` 属性~~ → 方法参数 `**kwargs`

---

## 第一步：替换依赖和导入

### 旧系统导入

```python
from typing import List, Tuple, Type, Dict, Any, Optional
from src.plugin_system import (
    BasePlugin,
    register_plugin,
    BaseAction,
    BaseCommand,
    BaseTool,
    BaseEventHandler,
    ComponentInfo,
    ConfigField,
    ActionActivationType,
    ChatMode,
    ToolParamType,
)
from src.plugin_system.base.component_types import ToolInfo, ComponentType, EventType
from src.plugin_system.base.config_types import section_meta
from src.common.logger import get_logger
```

### 新系统导入

```python
from maibot_sdk import MaiBotPlugin, Action, Command, Tool, EventHandler
from maibot_sdk.types import (
    ActivationType,       # 对应旧版 ActionActivationType
    ChatMode,             # 保持不变
    EventType,            # 保持不变
    ToolParameterInfo,    # 替代旧版 tuple 参数声明
    ToolParamType,        # 保持不变
)
# 如果使用 HookHandler（新增功能）：
from maibot_sdk import HookHandler
from maibot_sdk.types import WorkflowStage, HookResult, ErrorPolicy
```

### 导入映射表

| 旧导入 | 新导入 |
|--------|--------|
| `from src.plugin_system import BasePlugin` | `from maibot_sdk import MaiBotPlugin` |
| `from src.plugin_system import register_plugin` | **删除** — 不再需要 |
| `from src.plugin_system import BaseAction` | `from maibot_sdk import Action` (装饰器) |
| `from src.plugin_system import BaseCommand` | `from maibot_sdk import Command` (装饰器) |
| `from src.plugin_system import BaseTool` | `from maibot_sdk import Tool` (装饰器) |
| `from src.plugin_system import BaseEventHandler` | `from maibot_sdk import EventHandler` (装饰器) |
| `from src.plugin_system import ComponentInfo` | **删除** — 自动收集 |
| `from src.plugin_system import ConfigField` | **删除** — 配置不再在代码中声明 |
| `from src.plugin_system import ActionActivationType` | `from maibot_sdk.types import ActivationType` |
| `from src.plugin_system.base.component_types import ToolInfo` | **删除** — 内部使用 |
| `from src.plugin_system.base.component_types import ComponentType` | **删除** — 内部使用（SDK 自动处理） |
| `from src.plugin_system.base.component_types import EventType` | `from maibot_sdk.types import EventType` |
| `from src.plugin_system.base.config_types import section_meta` | **删除** — 新系统无此概念 |
| `from src.common.logger import get_logger` | `self.ctx.logger.info(msg)` 或用标准 `print()` |

> **重要**：新系统中，插件**不得**导入任何 `src.*` 模块。这会被 Runner 的 sys.path 隔离机制阻止。

---

## 第二步：改写插件主类

### 旧写法

```python
@register_plugin
class MyPlugin(BasePlugin):
    plugin_name: str = "my_plugin"
    enable_plugin: bool = True
    dependencies: List[str] = []
    python_dependencies: List[str] = ["aiohttp"]
    config_file_name: str = "config.toml"

    config_section_descriptions = {
        "plugin": section_meta("插件开关", order=1),
        "settings": section_meta("设置", order=2),
    }

    config_schema: dict = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="是否启用"),
            "config_version": ConfigField(type=str, default="1.0.0", description="配置版本"),
        },
        "settings": {
            "timeout": ConfigField(type=float, default=30.0, description="超时秒数"),
        },
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        components = []
        components.append((MyAction.get_action_info(), MyAction))
        components.append((MyCommand.get_command_info(), MyCommand))
        components.append((MyToolInfo, MyTool))
        components.append((MyEventHandler.get_handler_info(), MyEventHandler))
        return components

    async def on_load(self):
        """插件加载"""
        pass

    async def on_unload(self):
        """插件卸载"""
        pass
```

### 新写法

```python
from maibot_sdk import MaiBotPlugin, Action, Command, Tool, EventHandler


class MyPlugin(MaiBotPlugin):
    """我的插件"""

    # 不再需要：
    # - plugin_name（从 _manifest.json 读取）
    # - enable_plugin（从 config.toml 的 [plugin] enabled 控制）
    # - dependencies（从 _manifest.json 读取）
    # - python_dependencies（插件自行管理依赖）
    # - config_file_name（固定为 config.toml）
    # - config_schema / config_section_descriptions（配置文件手动编写）
    # - get_plugin_components()（装饰器自动收集）
    # - @register_plugin 装饰器（使用 create_plugin() 工厂函数）

    # ===== 组件直接定义在类方法上 =====

    @Action("my_action", description="做某事")
    async def handle_my_action(self, stream_id: str = "", **kwargs):
        await self.ctx.send.text("Hello!", stream_id)
        return True, "已执行"

    @Command("my_cmd", description="命令", pattern=r"^/mycmd$")
    async def handle_my_cmd(self, stream_id: str = "", **kwargs):
        await self.ctx.send.text("命令已执行", stream_id)
        return True, "已执行", True

    @Tool("my_tool", description="工具")
    async def handle_my_tool(self, **kwargs):
        return {"name": "my_tool", "content": "结果"}

    @EventHandler("on_start", event_type=EventType.ON_START)
    async def handle_start(self, **kwargs):
        return True, True, "启动完成", None, None

    # ===== 生命周期 =====

    async def on_load(self):
        """插件加载（可选）"""
        pass

    async def on_unload(self):
        """插件卸载（可选）"""
        pass

    async def on_config_update(self, new_config, version):
        """配置热更新（可选，新增）"""
        pass


# 必须提供工厂函数（替代 @register_plugin）
def create_plugin():
    return MyPlugin()
```

### 关键变化

| 项目 | 旧系统 | 新系统 |
|------|--------|--------|
| 基类 | `BasePlugin` | `MaiBotPlugin` |
| 注册方式 | `@register_plugin` 类装饰器 | `create_plugin()` 工厂函数 |
| 组件注册 | `get_plugin_components()` 返回列表 | 装饰器自动收集（删除此方法） |
| 插件名称 | `plugin_name = "xxx"` 类属性 | `_manifest.json` 中的 `name` 字段 |
| 依赖声明 | `dependencies` / `python_dependencies` 类属性 | `_manifest.json` 中声明 |
| 配置声明 | `config_schema` + `ConfigField` | 只需要 `config.toml` 文件 |
| 配置热更 | 无 | 新增 `on_config_update()` 回调 |

---

## 第三步：迁移 Action 组件

### 变化概述

旧系统中 Action 是一个**独立类**，继承 `BaseAction`，通过类属性声明元数据，在 `execute()` 方法中实现逻辑。

新系统中 Action 是插件类上的一个**方法**，通过 `@Action` 装饰器声明元数据。

### 旧写法

```python
class HelloAction(BaseAction):
    action_name = "hello_greeting"
    action_description = "向用户发送问候消息"
    activation_type = ActionActivationType.ALWAYS
    action_parameters = {"greeting_message": "要发送的问候消息"}
    action_require = ["需要发送友好问候时使用", "当有人向你问好时使用"]
    associated_types = ["text"]
    parallel_action = False

    async def execute(self) -> Tuple[bool, str]:
        greeting_message = self.action_data.get("greeting_message", "")
        base_message = self.get_config("greeting.message", "嗨！")
        message = base_message + greeting_message
        await self.send_text(message)
        return True, "发送了问候消息"
```

### 新写法

```python
@Action(
    "hello_greeting",
    description="向用户发送问候消息",
    activation_type=ActivationType.ALWAYS,
    action_parameters={"greeting_message": "要发送的问候消息"},
    action_require=["需要发送友好问候时使用", "当有人向你问好时使用"],
    associated_types=["text"],
    parallel_action=False,
)
async def handle_hello(self, stream_id: str = "", greeting_message: str = "", **kwargs):
    config_result = await self.ctx.config.get("greeting.message")
    base_message = config_result if isinstance(config_result, str) else "嗨！"
    message = base_message + greeting_message
    await self.ctx.send.text(message, stream_id)
    return True, "发送了问候消息"
```

### Action 迁移对照表

| 旧系统 | 新系统 |
|--------|--------|
| `class MyAction(BaseAction):` | `@Action("my_action", ...)` 方法装饰器 |
| `action_name = "xxx"` | `@Action("xxx", ...)` 第一个参数 |
| `action_description = "xxx"` | `@Action(..., description="xxx")` |
| `activation_type = ActionActivationType.ALWAYS` | `activation_type=ActivationType.ALWAYS` |
| `activation_keywords = [...]` | `activation_keywords=[...]` |
| `random_activation_probability = 0.5` | `activation_probability=0.5` |
| `action_parameters = {...}` | `action_parameters={...}` |
| `action_require = [...]` | `action_require=[...]` |
| `associated_types = [...]` | `associated_types=[...]` |
| `parallel_action = False` | `parallel_action=False` |
| `self.action_data.get("param")` | 方法参数：`param: str = ""` 或 `kwargs.get("param")` |
| `self.chat_id`（等同于 `self.chat_stream.session_id`） | 方法参数：`stream_id: str = ""`（概念相同，旧系统叫 `chat_id`） |
| `self.get_config(key, default)` | `await self.ctx.config.get(key)` **(注意：异步)** |
| `await self.send_text(text)` | `await self.ctx.send.text(text, stream_id)` **(需要传 stream_id)** |
| `await self.send_emoji(base64)` | `await self.ctx.send.emoji(base64, stream_id)` |
| `await self.send_image(base64)` | `await self.ctx.send.image(base64, stream_id)` |
| `return True, "结果"` | `return True, "结果"` **(保持不变)** |

### ActivationType 枚举对照

| 旧枚举（`ActionActivationType`） | 新枚举（`ActivationType`） |
|----------------------------------|---------------------------|
| `ActionActivationType.NEVER` | `ActivationType.NEVER` |
| `ActionActivationType.ALWAYS` | `ActivationType.ALWAYS` |
| `ActionActivationType.RANDOM` | `ActivationType.RANDOM` |
| `ActionActivationType.KEYWORD` | `ActivationType.KEYWORD` |

---

## 第四步：迁移 Command 组件

### 变化概述

旧系统中 Command 是一个**独立类**，继承 `BaseCommand`。

新系统中 Command 是插件类上的一个**方法**，通过 `@Command` 装饰器声明。

### 旧写法

```python
class TimeCommand(BaseCommand):
    command_name = "time"
    command_description = "查询当前时间"
    command_pattern = r"^/time$"

    async def execute(self) -> Tuple[bool, Optional[str], bool]:
        time_format = self.get_config("time.format", "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        time_str = now.strftime(time_format)
        await self.send_text(f"⏰ 当前时间：{time_str}")
        return True, f"显示了时间: {time_str}", True
```

### 新写法

```python
@Command("time", description="查询当前时间", pattern=r"^/time$")
async def handle_time(self, stream_id: str = "", **kwargs):
    config_result = await self.ctx.config.get("time.format")
    time_format = config_result if isinstance(config_result, str) else "%Y-%m-%d %H:%M:%S"
    now = datetime.datetime.now()
    time_str = now.strftime(time_format)
    await self.ctx.send.text(f"⏰ 当前时间：{time_str}", stream_id)
    return True, f"显示了时间: {time_str}", True
```

### Command 迁移对照表

| 旧系统 | 新系统 |
|--------|--------|
| `class MyCmd(BaseCommand):` | `@Command("my_cmd", ...)` 方法装饰器 |
| `command_name = "xxx"` | `@Command("xxx", ...)` 第一个参数 |
| `command_description = "xxx"` | `@Command(..., description="xxx")` |
| `command_pattern = r"..."` | `@Command(..., pattern=r"...")` |
| `self.matched_groups` | 方法参数：`matched_groups: dict = None` 或 `kwargs.get("matched_groups")` |
| `self.message`（`SessionMessage` 对象） | 方法参数：`raw_message: str = ""`、`stream_id: str = ""` 等（旧系统通过 `self.message.session_id` 获取会话 ID） |
| `self.message.session_id` | 方法参数：`stream_id: str = ""` |
| `self.get_config(key, default)` | `await self.ctx.config.get(key)` |
| `await self.send_text(text)` | `await self.ctx.send.text(text, stream_id)` |
| `await self.send_command(cmd, args)` | `await self.ctx.send.command(cmd, stream_id)` |
| `return True, "msg", 2`（第三参是 `int`：0=不拦截，1=不触发回复但 replyer 可见，2=完全拦截） | `return True, "msg", True`（新系统简化为 `bool`，`True` 相当于旧 `2`，`False` 相当于旧 `0`） |

### 带参数的 Command 迁移

如果你的旧命令使用了正则命名捕获组来获取参数：

**旧写法**：
```python
class SetFreqCommand(BaseCommand):
    command_name = "set_freq"
    command_pattern = r"^/chat\s+(?:talk_frequency|t)\s+(?P<value>[+-]?\d*\.?\d+)$"

    async def execute(self):
        value_str = self.matched_groups.get("value")
        value = float(value_str)
        # ...
```

**新写法**：
```python
@Command(
    "set_freq",
    description="设置频率",
    pattern=r"^/chat\s+(?:talk_frequency|t)\s+(?P<value>[+-]?\d*\.?\d+)$",
)
async def handle_set_freq(self, stream_id: str = "", matched_groups: dict | None = None, **kwargs):
    if not matched_groups or "value" not in matched_groups:
        return False, "格式错误", False
    value = float(matched_groups["value"])
    # ...
```

---

## 第五步：迁移 Tool 组件

### 变化概述

旧系统中 Tool 是一个**独立类**，继承 `BaseTool`，属性包含组件名和参数定义（tuple 列表格式）。

新系统使用 `@Tool` 装饰器，参数定义支持**结构化 `ToolParameterInfo`** 和 **兼容 dict** 两种格式。

### 旧写法

```python
class WeatherTool(BaseTool):
    name = "weather_query"
    description = "查询天气"
    available_for_llm = True
    parameters = [
        ("city", ToolParamType.STRING, "城市名称", True, None),
        ("country", ToolParamType.STRING, "国家代码", False, None),
    ]

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        city = function_args.get("city")
        country = function_args.get("country", "")
        result = f"查询 {city} 的天气"
        return {"name": self.name, "content": result}
```

### 新写法（推荐：结构化参数）

```python
from maibot_sdk.types import ToolParameterInfo, ToolParamType

@Tool(
    "weather_query",
    description="查询天气",
    parameters=[
        ToolParameterInfo(name="city", param_type=ToolParamType.STRING, description="城市名称", required=True),
        ToolParameterInfo(name="country", param_type=ToolParamType.STRING, description="国家代码", required=False),
    ],
)
async def handle_weather(self, city: str = "", country: str = "", **kwargs):
    result = f"查询 {city} 的天气"
    return {"name": "weather_query", "content": result}
```

### 新写法（兼容：dict 参数）

```python
@Tool(
    "weather_query",
    description="查询天气",
    parameters={"city": {"type": "string", "description": "城市名称"}},
)
async def handle_weather(self, city: str = "", **kwargs):
    return {"name": "weather_query", "content": f"查询 {city}"}
```

### Tool 参数定义对照

| 旧系统（tuple 格式） | 新系统（ToolParameterInfo） |
|---------------------|---------------------------|
| `("name", ToolParamType.STRING, "描述", True, None)` | `ToolParameterInfo(name="name", param_type=ToolParamType.STRING, description="描述", required=True)` |
| `("limit", ToolParamType.INTEGER, "限制", False, ["10", "20"])` | `ToolParameterInfo(name="limit", param_type=ToolParamType.INTEGER, description="限制", required=False, default=10)` |

### Tool 迁移对照表

| 旧系统 | 新系统 |
|--------|--------|
| `class MyTool(BaseTool):` | `@Tool("my_tool", ...)` 方法装饰器 |
| `name = "xxx"` | `@Tool("xxx", ...)` 第一个参数 |
| `description = "xxx"` | `@Tool(..., description="xxx")` |
| `parameters = [(tuple)]` | `@Tool(..., parameters=[ToolParameterInfo(...)])` |
| `available_for_llm = True` | **默认可用**（不再需要声明） |
| `function_args.get("key")` | 方法参数：`key: str = ""` 或 `kwargs.get("key")` |
| `return {"name": self.name, "content": result}` | `return {"name": "tool_name", "content": result}` **(一致)** |

---

## 第六步：迁移 EventHandler 组件

### 变化概述

旧系统中 EventHandler 是一个**独立类**，继承 `BaseEventHandler`。

新系统使用 `@EventHandler` 装饰器。

### 旧写法

```python
class StartupHandler(BaseEventHandler):
    event_type = EventType.ON_START
    handler_name = "my_startup"
    handler_description = "启动处理"
    weight = 0
    intercept_message = False

    async def execute(self, message: Optional[Any]) -> Tuple[bool, bool, Optional[str], None, None]:
        # 初始化逻辑
        return (True, True, None, None, None)


class MessageHandler(BaseEventHandler):
    event_type = EventType.ON_MESSAGE
    handler_name = "msg_printer"
    handler_description = "打印消息"
    weight = 100
    intercept_message = True

    async def execute(self, message: Optional[Any]) -> Tuple[bool, bool, Optional[str], None, None]:
        if message:
            raw = message.get("raw_message", "")
            print(f"收到: {raw}")
        return (True, True, "消息已打印", None, None)
```

### 新写法

```python
@EventHandler("my_startup", description="启动处理", event_type=EventType.ON_START)
async def handle_start(self, **kwargs):
    # 初始化逻辑
    return None  # 返回 None 表示不干预


@EventHandler(
    "msg_printer",
    description="打印消息",
    event_type=EventType.ON_MESSAGE,
    intercept_message=True,
    weight=100,
)
async def handle_message(self, message=None, **kwargs):
    if message:
        raw = message.get("raw_message", "") if isinstance(message, dict) else str(message)
        print(f"收到: {raw}")
    return None  # 不拦截，继续传播


@EventHandler(
    "spam_filter",
    description="过滤垃圾消息",
    event_type=EventType.ON_MESSAGE_PRE_PROCESS,
    intercept_message=True,
    weight=200,
)
async def filter_spam(self, plain_text="", **kwargs):
    if "spam" in plain_text:
        return {"blocked": True}  # 拦截消息
    return None
```

### EventHandler 迁移对照表

| 旧系统 | 新系统 |
|--------|--------|
| `class MyHandler(BaseEventHandler):` | `@EventHandler("my_handler", ...)` 方法装饰器 |
| `handler_name = "xxx"` | `@EventHandler("xxx", ...)` 第一个参数 |
| `handler_description = "xxx"` | `@EventHandler(..., description="xxx")` |
| `event_type = EventType.ON_MESSAGE` | `@EventHandler(..., event_type=EventType.ON_MESSAGE)` |
| `weight = 100` | `@EventHandler(..., weight=100)` |
| `intercept_message = True` | `@EventHandler(..., intercept_message=True)` |
| `async def execute(self, message)` | `async def handle_xxx(self, message=None, **kwargs)` |
| 返回 5 元组 `(bool, bool, str, None, None)` | 返回 `dict`（如 `{"blocked": True}`）或 `None`（不干预） |

### EventType 枚举（完全一致）

新旧系统的 `EventType` 枚举值完全相同：

| 事件类型 | 说明 |
|---------|------|
| `ON_START` | 应用启动 |
| `ON_STOP` | 应用关闭 |
| `ON_MESSAGE_PRE_PROCESS` | 消息接收，处理前 |
| `ON_MESSAGE` | 消息处理 |
| `ON_PLAN` | LLM 规划阶段 |
| `POST_LLM` | LLM 生成后 |
| `AFTER_LLM` | LLM 完成后 |
| `POST_SEND_PRE_PROCESS` | 发送前处理 |
| `POST_SEND` | 发送后 |
| `AFTER_SEND` | 发送完成后 |

---

## 第七步：新增 - HookHandler 组件

> SDK 2.0 起，`WorkflowStep` 已移除并更名为 `HookHandler`。这是一次不向后兼容更改。
>
> 旧系统的 `BasePlugin` 已有 `get_workflow_steps()` 方法支持 workflow 注册，但采用回调函数 + `WorkflowStepInfo` 的方式，使用较少。新系统通过 `@HookHandler` 装饰器大幅简化了声明方式。如果你的旧插件没有用到 workflow 可跳过本节。

`HookHandler` 允许插件参与 MaiBot 的 6 阶段消息处理流水线：

```
INGRESS → PRE_PROCESS → PLAN → TOOL_EXECUTE → POST_PROCESS → EGRESS
```

### 使用示例

```python
from maibot_sdk import HookHandler
from maibot_sdk.types import WorkflowStage, HookResult

@HookHandler(
    "content_filter",
    stage=WorkflowStage.INGRESS,
    description="内容过滤",
    priority=10,          # 阶段内优先级，越高越先执行
    blocking=True,        # 串行执行，可修改消息
    timeout_ms=5000,      # 超时 5 秒
)
async def filter_content(self, context, message, **kwargs):
    """过滤不当内容"""
    text = message.get("plain_text", "")
    if "敏感词" in text:
        return {
            "hook_result": HookResult.ABORT.value,  # 终止流水线
            "modified_message": None,
        }
    return {
        "hook_result": HookResult.CONTINUE.value,  # 继续
        "modified_message": message,
    }
```

### HookHandler 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | str | 组件名称 |
| `stage` | WorkflowStage | 所属阶段（INGRESS/PRE_PROCESS/PLAN/TOOL_EXECUTE/POST_PROCESS/EGRESS） |
| `priority` | int | 阶段内优先级（越高越先执行） |
| `blocking` | bool | `True`=串行可修改消息，`False`=并发只读 |
| `timeout_ms` | int | 超时毫秒数，0=不限时 |
| `error_policy` | ErrorPolicy | 异常策略：ABORT（终止）/ SKIP（跳过）/ LOG（记录） |
| `filter` | dict | 前置过滤条件 |

---

## 第八步：迁移配置系统

### 核心变化

旧系统使用**代码声明**配置（`ConfigField` + `config_schema`），系统自动生成 `config.toml`。

新系统中，`config.toml` 由开发者**手动编写**。插件通过 `self.ctx.config` 异步读取配置。

### 旧系统配置声明

```python
# 在插件类中
config_section_descriptions = {
    "plugin": section_meta("插件开关", order=1),
    "greeting": section_meta("问候设置", order=2),
}

config_schema = {
    "plugin": {
        "enabled": ConfigField(type=bool, default=True, description="是否启用"),
        "config_version": ConfigField(type=str, default="1.0.0", description="版本"),
    },
    "greeting": {
        "message": ConfigField(type=str, default="你好！", description="默认问候语"),
        "enable_emoji": ConfigField(type=bool, default=True, description="是否启用表情"),
    },
}
```

### 新系统配置方式

**config.toml**（手动编写，放在插件目录下）：
```toml
[plugin]
config_version = "1.0.0"
enabled = true

[greeting]
message = "你好！"
enable_emoji = true
```

**在代码中读取配置**：
```python
# 旧系统（同步）
message = self.get_config("greeting.message", "默认值")

# 新系统（异步）
message = await self.ctx.config.get("greeting.message")
if message is None:
    message = "默认值"

# 获取插件全部配置
all_config = await self.ctx.config.get_plugin()

# 获取全局配置
global_config = await self.ctx.config.get_all()
```

### 配置相关 API 对照

| 旧系统 | 新系统 |
|--------|--------|
| `self.get_config("key", default)` | `await self.ctx.config.get("key")` |
| `self.config["section"]["key"]` | `await self.ctx.config.get("section.key")` |
| `ConfigField(...)` 声明 | 手动编写 `config.toml` |
| `config_schema` 字典 | 不再需要 |
| `config_section_descriptions` | 不再需要 |
| `config_layout`（可选的 `ConfigLayout`） | 不再需要（WebUI 自动推断布局） |
| 自动生成 config.toml | 手动编写 config.toml |
| 配置版本自动迁移 | 开发者自行处理（可在 `on_config_update` 中实现） |

> **注意**：新系统的 `self.ctx.config.get()` 是 **异步** 的（返回 `Awaitable`），必须使用 `await`。旧系统的 `self.get_config()` 是同步的。

### WebUI 配置可视化

旧系统中，`ConfigField` 携带了丰富的前端渲染元数据（`label`、`hint`、`placeholder`、`icon`、`input_type`、`choices`、`min/max/step`、`depends_on`、`item_type/item_fields` 等），WebUI 通过 `get_webui_config_schema()` 方法获取这些信息来动态生成配置表单。

新系统中，**WebUI 会自动从 `config.toml` 文件推断 Schema**：

| 值类型 | 自动推断的控件 |
|--------|-------------|
| `bool` (`true`/`false`) | Switch 开关 |
| `int` / `float` | Number 数字输入框 |
| `string` | Text 文本输入框 |
| `list` | List 列表编辑器（自动推断元素类型） |
| `dict` / 嵌套表 | JSON 代码编辑器 |

**自动推断的局限性**：由于 `config.toml` 不包含 UI 元数据，以下旧系统特性在自动推断模式下不可用：

- ❌ 自定义 `label`（显示为字段名原文）
- ❌ `hint` / `placeholder` / `icon` / `description`
- ❌ `slider` 控件（数值只会显示为 number 输入框）
- ❌ `select` 下拉选择（即使有有限选项）
- ❌ `password` 类型掩码
- ❌ `depends_on` 条件显示
- ❌ `choices` 枚举约束
- ❌ `min/max/step` 范围约束
- ❌ `collapsed` / `order` 排序

**增强方案 — `config_schema.json`**：如果你需要这些富 UI 特性，可以在插件目录下创建 `config_schema.json` 文件来声明完整的 Schema，格式与旧系统 `get_webui_config_schema()` 的返回值一致：

```json
{
  "plugin_id": "my_plugin",
  "plugin_info": {
    "name": "我的插件",
    "version": "1.0.0",
    "description": "插件描述",
    "author": "作者"
  },
  "sections": {
    "plugin": {
      "name": "plugin",
      "title": "插件开关",
      "description": null,
      "icon": null,
      "collapsed": false,
      "order": 1,
      "fields": {
        "enabled": {
          "name": "enabled",
          "type": "bool",
          "default": true,
          "description": "是否启用插件",
          "label": "启用",
          "ui_type": "switch",
          "required": false,
          "hidden": false,
          "disabled": false,
          "order": 0
        }
      }
    },
    "settings": {
      "name": "settings",
      "title": "设置",
      "description": "高级设置项",
      "icon": "Settings",
      "collapsed": false,
      "order": 2,
      "fields": {
        "timeout": {
          "name": "timeout",
          "type": "float",
          "default": 30.0,
          "description": "请求超时秒数",
          "label": "超时时间",
          "ui_type": "slider",
          "min": 1,
          "max": 120,
          "step": 1,
          "hint": "建议 10-60 秒",
          "required": false,
          "hidden": false,
          "disabled": false,
          "order": 0
        },
        "api_key": {
          "name": "api_key",
          "type": "str",
          "default": "",
          "description": "API 密钥",
          "label": "API Key",
          "ui_type": "password",
          "placeholder": "请输入你的 API Key",
          "required": true,
          "hidden": false,
          "disabled": false,
          "order": 1
        },
        "mode": {
          "name": "mode",
          "type": "str",
          "default": "auto",
          "description": "运行模式",
          "label": "模式",
          "ui_type": "select",
          "choices": ["auto", "manual", "hybrid"],
          "required": false,
          "hidden": false,
          "disabled": false,
          "order": 2
        }
      }
    }
  },
  "layout": {
    "type": "auto",
    "tabs": []
  }
}
```

**`config_schema.json` 完整字段参考**（与旧系统 `ConfigField` 一一对应）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 字段名 |
| `type` | string | 值类型：`bool`/`str`/`int`/`float`/`list`/`dict` |
| `default` | any | 默认值 |
| `description` | string | 字段描述 |
| `label` | string | 前端显示标签 |
| `ui_type` | string | 控件类型：`switch`/`number`/`slider`/`select`/`text`/`textarea`/`password`/`list`/`json` |
| `hint` | string | 提示文字 |
| `placeholder` | string | 占位文字 |
| `icon` | string | 图标名称 |
| `hidden` | bool | 是否隐藏 |
| `disabled` | bool | 是否禁用 |
| `order` | int | 排列顺序 |
| `required` | bool | 是否必填 |
| `choices` | array | 选择项列表（配合 `select`） |
| `min` / `max` / `step` | number | 数值范围和步进（配合 `slider`/`number`） |
| `input_type` | string | HTML input type（`text`/`password`/`textarea`/`number`/`color`/`code`/`file`/`json`） |
| `rows` | int | textarea 行数 |
| `group` | string | 分组名称 |
| `depends_on` | string | 条件依赖字段名 |
| `depends_value` | any | 条件依赖值 |
| `item_type` | string | 列表元素类型：`string`/`number`/`object` |
| `item_fields` | object | 当 `item_type=object` 时的子字段定义 |
| `min_items` / `max_items` | int | 列表长度约束 |

> **提示**：如果不需要富 UI 特性，只需提供 `config.toml` 即可，WebUI 会自动推断出基础表单。`config_schema.json` 是**可选**的增强方案。

---

## 第九步：迁移 API 调用

新系统中，所有 API 通过 `self.ctx` 的能力代理访问，代理方法均为 **异步** 的。

### 发送消息

| 旧系统 | 新系统 |
|--------|--------|
| `await self.send_text(content)` | `await self.ctx.send.text(content, stream_id)` |
| `await self.send_emoji(base64)` | `await self.ctx.send.emoji(base64, stream_id)` |
| `await self.send_image(base64)` | `await self.ctx.send.image(base64, stream_id)` |
| `await self.send_type("text", content)` | `await self.ctx.send.text(content, stream_id)` |
| `await self.send_command(cmd, args)` | `await self.ctx.send.command(cmd, stream_id)` |
| — | `await self.ctx.send.forward(messages, stream_id)` **(新增)** |
| — | `await self.ctx.send.hybrid(segments, stream_id)` **(新增)** |
| `await self.send_type(custom_type, data)` | `await self.ctx.send.custom(custom_type, data, stream_id)` |

> **重要变化**：旧系统中 `send_text()` 等方法不需要传 `stream_id`（基类自动携带上下文），新系统必须**显式传入 `stream_id`**。

> **兼容说明**：`ctx.send.custom()` 会自动同时发送 `custom_type/data` 和 `message_type/content` 字段，插件作者无需区分 Host 版本。

> **返回值说明**：新版 SDK 与兼容层异步 API 会自动解包 Host 的单字段 RPC 包装结果。像 `await self.ctx.config.get(...)`、`await self.ctx.chat.get_all_streams()`、`await self.ctx.message.get_recent(...)`、`await self.ctx.person.get_id(...)`、`await self.ctx.frequency.get_current_talk_value(...)` 这类调用，都会直接返回配置值、列表、字符串或数值，而不是带 `success/value/messages/streams` 的外层字典。

### 配置

| 旧系统 | 新系统 |
|--------|--------|
| `self.get_config("key", default)` | `await self.ctx.config.get("key")` |
| `self.config["section"]["key"]` | `await self.ctx.config.get("section.key")` |
| — | `await self.ctx.config.get_plugin()` **(获取当前插件全部配置)** |
| — | `await self.ctx.config.get_all()` **(获取全部配置)** |

### 数据库

| 旧系统 | 新系统 |
|--------|--------|
| `from src.plugin_system.apis import database_api` | `await self.ctx.db.query(table, filters)` |
| — | `await self.ctx.db.save(table, data)` |
| — | `await self.ctx.db.get(table, key_field, key_value)` |
| — | `await self.ctx.db.delete(table, filters)` |
| — | `await self.ctx.db.count(table)` |

> **返回值说明**：`await self.ctx.db.count(...)` 直接返回 `int`，不需要再从字典中手动读取 `count` 字段。

### LLM

| 旧系统 | 新系统 |
|--------|--------|
| `from src.plugin_system.apis import llm_api` | `await self.ctx.llm.generate(prompt)` |
| — | `await self.ctx.llm.generate_with_tools(prompt, tools)` |
| — | `await self.ctx.llm.get_available_models()` |

### 表情包

| 旧系统 | 新系统 |
|--------|--------|
| `await self.send_emoji(base64)` / `emoji_api.*` | `await self.ctx.send.emoji(base64, stream_id)` |
| `from src.plugin_system.apis import emoji_api` | `await self.ctx.emoji.get_random(count)` |
| — | `await self.ctx.emoji.get_by_description(desc)` |
| — | `await self.ctx.emoji.get_count()` |
| — | `await self.ctx.emoji.get_all()` |
| — | `await self.ctx.emoji.register_emoji(base64)` |
| — | `await self.ctx.emoji.delete_emoji(hash)` |

> **兼容层说明**：旧版 `emoji_api.get_random()` / `emoji_api.get_by_description()` 在 IPC 运行时下会直接返回新版 SDK 的归一化字典结果（如 `{"base64": ..., "description": ..., "emotion": ...}`），而不是旧系统里常见的 tuple 结构。迁移时不要再按位置解包。

### 消息查询

| 旧系统 | 新系统 |
|--------|--------|
| `from src.plugin_system.apis import message_api` | `await self.ctx.message.get_recent(chat_id, limit)` |
| — | `await self.ctx.message.get_by_time(start, end)` |
| — | `await self.ctx.message.get_by_time_in_chat(chat_id, start, end)` |
| — | `await self.ctx.message.count_new(chat_id, since)` |
| — | `await self.ctx.message.build_readable(messages, **kwargs)` — 也可传 `chat_id + start_time + end_time` 由 Host 查询 |

### 聊天流

| 旧系统 | 新系统 |
|--------|--------|
| `from src.plugin_system.apis import chat_api` | `await self.ctx.chat.get_all_streams()` |
| — | `await self.ctx.chat.get_group_streams()` |
| — | `await self.ctx.chat.get_private_streams()` |
| — | `await self.ctx.chat.get_stream_by_group_id(group_id)` |
| — | `await self.ctx.chat.get_stream_by_user_id(user_id)` |

### 发言频率

| 旧系统 | 新系统 |
|--------|--------|
| `from src.plugin_system.apis import frequency_api` | `await self.ctx.frequency.get_current_talk_value(chat_id)` |
| — | `await self.ctx.frequency.set_adjust(chat_id, value)` |
| — | `await self.ctx.frequency.get_adjust(chat_id)` |

### 人物信息

| 旧系统 | 新系统 |
|--------|--------|
| `from src.plugin_system.apis import person_api` | `await self.ctx.person.get_id(platform, user_id)` |
| — | `await self.ctx.person.get_value(person_id, field)` |
| — | `await self.ctx.person.get_id_by_name(name)` |

### 组件管理

| 旧系统 | 新系统 |
|--------|--------|
| `from src.plugin_system.apis import component_manage_api` / `plugin_manage_api` | `await self.ctx.component.get_all_plugins()` |
| — | `await self.ctx.component.get_plugin_info(name)` |
| — | `await self.ctx.component.enable_component(name, type)` — `name` 支持全名或短名 |
| — | `await self.ctx.component.disable_component(name, type)` — `name` 支持全名或短名 |
| — | `await self.ctx.component.reload_plugin(name)` |

> **兼容层说明**：旧版同步 `component_manage_api` / `plugin_manage_api` 查询函数现在返回最近一次运行时拉取到的快照；若你需要实时状态，优先迁移到新的异步 `self.ctx.component.*` 接口。

### 知识库、工具内省、日志

| 旧系统 | 新系统 |
|--------|--------|
| 无（旧系统无知识库 API） | `await self.ctx.knowledge.search(query, limit)` |
| `from src.plugin_system.apis import tool_api` | `await self.ctx.tool.get_definitions()` |
| `from src.common.logger import get_logger` | `self.ctx.logger.info("消息")` |
| `logger.debug("msg")` | `self.ctx.logger.debug("msg")` |
| `logger.warning("msg")` | `self.ctx.logger.warning("msg")` |
| `logger.error("msg")` | `self.ctx.logger.error("msg")` |

> **注意**：`self.ctx.logger` 是标准的 `logging.Logger` 实例，使用同步接口（`.info()` / `.debug()` 等）。日志会由 Runner 进程的 IPC 日志处理器自动转发到主进程。

---

## 第十步：迁移 Manifest 文件

`_manifest.json` 文件格式基本不变，但推荐补全以下字段：

```json
{
  "manifest_version": 1,
  "name": "我的插件",
  "version": "2.0.0",
  "description": "插件描述",
  "author": {
    "name": "作者名",
    "url": "https://github.com/xxx"
  },
  "license": "GPL-v3.0-or-later",
  "host_application": {
    "min_version": "1.0.0"
  },
  "plugin_info": {
    "is_built_in": false,
    "plugin_type": "功能类型",
    "capabilities": [
      "send.text",
      "config.get",
      "emoji.get_random"
    ],
    "components": [
      {
        "type": "action",
        "name": "hello_greeting",
        "description": "向用户发送问候"
      },
      {
        "type": "command",
        "name": "time",
        "description": "查询时间",
        "pattern": "/time"
      }
    ]
  },
  "id": "author.plugin-name"
}
```

### Manifest 新增字段

| 字段 | 说明 |
|------|------|
| `plugin_info.capabilities` | 声明插件使用的能力列表（如 `send.text`、`config.get`），用于权限控制 |
| `plugin_info.components` | 组件声明列表，与旧系统一致 |
| `id` | 全局唯一插件 ID，格式为 `author.plugin-name` |

---

## 完整迁移示例

### 旧版插件（完整代码）

```python
"""旧版 Hello World 插件"""
import datetime
from typing import List, Tuple, Type, Dict, Any, Optional

from src.plugin_system import (
    BasePlugin, register_plugin, BaseAction, BaseCommand,
    BaseTool, BaseEventHandler, ComponentInfo, ConfigField,
    ActionActivationType, ChatMode, ToolParamType,
)
from src.plugin_system.base.component_types import ToolInfo, ComponentType, EventType
from src.common.logger import get_logger

logger = get_logger("hello_world")


class HelloAction(BaseAction):
    action_name = "hello_greeting"
    action_description = "向用户发送问候消息"
    activation_type = ActionActivationType.ALWAYS
    action_parameters = {"greeting_message": "问候消息"}
    action_require = ["需要问候时使用"]
    associated_types = ["text"]

    async def execute(self) -> Tuple[bool, str]:
        greeting = self.action_data.get("greeting_message", "")
        base = self.get_config("greeting.message", "嗨！")
        await self.send_text(base + greeting)
        return True, "已问候"


class TimeCommand(BaseCommand):
    command_name = "time"
    command_description = "查询时间"
    command_pattern = r"^/time$"

    async def execute(self) -> Tuple[bool, Optional[str], bool]:
        fmt = self.get_config("time.format", "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now().strftime(fmt)
        await self.send_text(f"⏰ {now}")
        return True, f"时间: {now}", True


class CompareTool(BaseTool):
    name = "compare_numbers"
    description = "比较两个数"
    parameters = [
        ("num1", ToolParamType.FLOAT, "第一个数", True, None),
        ("num2", ToolParamType.FLOAT, "第二个数", True, None),
    ]
    available_for_llm = True

    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        n1 = function_args.get("num1", 0)
        n2 = function_args.get("num2", 0)
        result = f"{n1} {'>' if n1 > n2 else '<=' if n1 <= n2 else '=='} {n2}"
        return {"name": self.name, "content": result}


class PrintHandler(BaseEventHandler):
    event_type = EventType.ON_MESSAGE
    handler_name = "print_msg"
    handler_description = "打印消息"
    weight = 0
    intercept_message = False

    async def execute(self, message) -> Tuple[bool, bool, Optional[str], None, None]:
        if message:
            raw = message.get("raw_message", "")
            logger.info(f"收到: {raw}")
        return (True, True, "已打印", None, None)


@register_plugin
class HelloWorldPlugin(BasePlugin):
    plugin_name = "hello_world_plugin"
    enable_plugin = True
    dependencies = []
    python_dependencies = []
    config_file_name = "config.toml"

    config_schema = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="启用"),
            "config_version": ConfigField(type=str, default="1.0.0", description="版本"),
        },
        "greeting": {
            "message": ConfigField(type=str, default="嗨！", description="问候语"),
        },
        "time": {
            "format": ConfigField(type=str, default="%Y-%m-%d %H:%M:%S", description="时间格式"),
        },
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        compare_tool_info = ToolInfo(
            name="compare_numbers",
            tool_description="比较两个数",
            enabled=True,
            tool_parameters=CompareTool.parameters,
            component_type=ComponentType.TOOL,
        )
        return [
            (HelloAction.get_action_info(), HelloAction),
            (TimeCommand.get_command_info(), TimeCommand),
            (compare_tool_info, CompareTool),
            (PrintHandler.get_handler_info(), PrintHandler),
        ]
```

### 新版插件（迁移后完整代码）

```python
"""新版 Hello World 插件 — 使用 maibot-plugin-sdk"""
import datetime

from maibot_sdk import MaiBotPlugin, Action, Command, Tool, EventHandler
from maibot_sdk.types import ActivationType, EventType, ToolParameterInfo, ToolParamType


class HelloWorldPlugin(MaiBotPlugin):
    """Hello World 示例插件"""

    # ===== Action =====

    @Action(
        "hello_greeting",
        description="向用户发送问候消息",
        activation_type=ActivationType.ALWAYS,
        action_parameters={"greeting_message": "问候消息"},
        action_require=["需要问候时使用"],
        associated_types=["text"],
    )
    async def handle_hello(self, stream_id: str = "", greeting_message: str = "", **kwargs):
        config_result = await self.ctx.config.get("greeting.message")
        base = config_result if isinstance(config_result, str) else "嗨！"
        await self.ctx.send.text(base + greeting_message, stream_id)
        return True, "已问候"

    # ===== Command =====

    @Command("time", description="查询时间", pattern=r"^/time$")
    async def handle_time(self, stream_id: str = "", **kwargs):
        config_result = await self.ctx.config.get("time.format")
        fmt = config_result if isinstance(config_result, str) else "%Y-%m-%d %H:%M:%S"
        now = datetime.datetime.now().strftime(fmt)
        await self.ctx.send.text(f"⏰ {now}", stream_id)
        return True, f"时间: {now}", True

    # ===== Tool =====

    @Tool(
        "compare_numbers",
        description="比较两个数",
        parameters=[
            ToolParameterInfo(name="num1", param_type=ToolParamType.FLOAT, description="第一个数", required=True),
            ToolParameterInfo(name="num2", param_type=ToolParamType.FLOAT, description="第二个数", required=True),
        ],
    )
    async def handle_compare(self, num1: float = 0, num2: float = 0, **kwargs):
        result = f"{num1} {'>' if num1 > num2 else '<='} {num2}"
        return {"name": "compare_numbers", "content": result}

    # ===== EventHandler =====

    @EventHandler("print_msg", description="打印消息", event_type=EventType.ON_MESSAGE)
    async def handle_print(self, message=None, **kwargs):
        if message:
            raw = message.get("raw_message", "") if isinstance(message, dict) else str(message)
            print(f"收到: {raw}")
        return True, True, "已打印", None, None

    # ===== 生命周期 =====

    async def on_load(self):
        pass

    async def on_unload(self):
        pass


def create_plugin():
    return HelloWorldPlugin()
```

### config.toml（手动创建）

```toml
[plugin]
config_version = "1.0.0"
enabled = true

[greeting]
message = "嗨！"

[time]
format = "%Y-%m-%d %H:%M:%S"
```

---

## 常见问题 FAQ

### Q1: 新系统还支持 `from src.xxx import ...` 吗？

**不支持**。新系统的插件运行在独立子进程中，Runner 会过滤 `sys.path`，阻止插件导入 `src.*` 模块。你只能导入：
- `maibot_sdk`（SDK 核心）
- Python 标准库
- 第三方库（如 `aiohttp`、`pydantic` 等）

### Q2: 旧插件可以不迁移直接运行吗？

**不能**。新系统的 Runner 会查找 `create_plugin()` 工厂函数并调用它来实例化插件。如果你的插件使用 `@register_plugin` + `BasePlugin` 模式，将无法被新 Runner 加载。

### Q3: `self.action_data` 在新系统中怎么获取？

旧系统中，LLM 传递给 Action 的参数存储在 `self.action_data` 字典中。新系统中，这些参数会被**展平为方法参数**：

```python
# 旧系统
greeting = self.action_data.get("greeting_message", "")

# 新系统
async def handle_hello(self, greeting_message: str = "", **kwargs):
    # greeting_message 直接作为方法参数传入
    # 或者从 kwargs 中获取
    greeting = kwargs.get("greeting_message", "")
```

### Q4: `self.stream_id` 在新系统中怎么获取？

新系统中 `stream_id` 作为方法参数传入：

```python
async def handle_action(self, stream_id: str = "", **kwargs):
    await self.ctx.send.text("Hello", stream_id)
```

### Q5: 配置热更新怎么处理？

新系统新增了 `on_config_update` 回调：

```python
async def on_config_update(self, new_config: dict, version: str):
    """配置文件更新时自动回调"""
    # 更新内部状态
    self.my_setting = new_config.get("my_section", {}).get("key", "default")
```

### Q6: 旧插件用到了全局变量（如 `_plugin_instance`）怎么办？

旧系统中一些复杂插件（如 MCP Bridge）使用全局变量来在 EventHandler 中引用插件实例。新系统中所有组件都是插件类的方法，可以直接访问 `self`，不再需要全局变量：

```python
# 旧系统
_plugin_instance = None

class StartupHandler(BaseEventHandler):
    async def execute(self, message):
        global _plugin_instance
        if _plugin_instance:
            await _plugin_instance._connect_servers()

# 新系统
@EventHandler("startup", event_type=EventType.ON_START)
async def handle_start(self, **kwargs):
    await self._connect_servers()  # 直接用 self
```

### Q7: 旧系统的 `get_action_info()` / `get_command_info()` / `get_handler_info()` 去哪了？

**已删除**。新系统中装饰器会自动将组件元数据附加到方法上，Runner 加载时通过 `collect_components()` 自动收集，无需手动调用 `get_xxx_info()`。

### Q8: 旧系统中组件的 `ComponentInfo` / `ToolInfo` 还需要吗？

**不需要**。这些是旧系统内部用于注册的数据结构。新系统中装饰器参数直接映射到 SDK 的 `ActionComponentInfo` / `CommandComponentInfo` / `ToolComponentInfo` 等 Pydantic 模型。

### Q9: 新系统的消息格式有变化吗？

新系统引入了统一的 `MaiMessages` Pydantic 模型：

```python
from maibot_sdk.messages import MaiMessages, MessageSegment

# 在 HookHandler 或 EventHandler 中
msg = MaiMessages.from_rpc_dict(message)
print(msg.plain_text)
print(msg.stream_id)
print(msg.message_segments)

# 安全修改
msg.modify_prompt("新 prompt")
msg.modify_plain_text("新文本")
```

### Q10: 第三方依赖怎么安装？

在你的插件目录下创建 `requirements.txt`，Runner 会自动安装依赖。或者在 `_manifest.json` 中的 `python_dependencies` 数组中声明。

---

## AI 自助迁移 Prompt

> 将以下 Prompt 发送给 AI（如 ChatGPT、Claude、GitHub Copilot 等），附上你的旧版插件代码，即可自动完成迁移。

````markdown
# MaiBot 插件迁移任务

请帮我将以下 MaiBot 旧版插件代码迁移到新版 SDK 格式。

## 迁移规则

### 1. 导入替换
- `from src.plugin_system import BasePlugin, register_plugin, ...` → `from maibot_sdk import MaiBotPlugin, Action, Command, Tool, EventHandler`
- `from src.plugin_system import ActionActivationType` → `from maibot_sdk.types import ActivationType`
- `from src.plugin_system import BaseAction, BaseCommand, BaseTool, BaseEventHandler` → 删除，改用装饰器
- `from src.plugin_system import ConfigField, ComponentInfo` → 删除
- `from src.plugin_system.base.component_types import ...` → 删除
- `from src.plugin_system.base.config_types import section_meta` → 删除
- `from src.common.logger import get_logger` → 删除，使用 `self.ctx.logger.info()` 或 `print()`
- **禁止**保留任何 `from src.*` 或 `import src.*` 的导入

### 2. 主类改写
- `@register_plugin` 装饰器 → 删除
- `class MyPlugin(BasePlugin):` → `class MyPlugin(MaiBotPlugin):`
- 删除类属性：`plugin_name`, `enable_plugin`, `dependencies`, `python_dependencies`, `config_file_name`, `config_schema`, `config_section_descriptions`
- 删除 `get_plugin_components()` 方法
- 在文件末尾添加：`def create_plugin(): return MyPlugin()`

### 3. Action 组件迁移
- 旧：独立类 `class MyAction(BaseAction):` + 类属性 + `execute()` 方法
- 新：在插件类中使用 `@Action("name", description="...", ...)` 装饰方法
- `action_name` → 装饰器第一个参数
- `action_description` → `description=`
- `activation_type = ActionActivationType.XXX` → `activation_type=ActivationType.XXX`
- `action_parameters`, `action_require`, `associated_types` → 同名装饰器参数
- `self.action_data.get("key")` → 方法参数 `key: str = ""` 或 `kwargs.get("key")`
- `self.stream_id` → 方法参数 `stream_id: str = ""`
- `self.get_config("key", default)` → `await self.ctx.config.get("key")`
- `await self.send_text(text)` → `await self.ctx.send.text(text, stream_id)`
- `await self.send_emoji(b64)` → `await self.ctx.send.emoji(b64, stream_id)`
- 返回值保持 `(bool, str)` 不变

### 4. Command 组件迁移
- 旧：独立类 `class MyCmd(BaseCommand):` + `execute()` 
- 新：`@Command("name", description="...", pattern=r"...")` 装饰方法
- `self.matched_groups` → 方法参数 `matched_groups: dict | None = None`
- `self.raw_message` → 方法参数 `raw_message: str = ""`
- `await self.send_text(text)` → `await self.ctx.send.text(text, stream_id)`
- `self.get_config(key)` → `await self.ctx.config.get(key)`
- 返回值保持 `(bool, Optional[str], bool)` 不变

### 5. Tool 组件迁移
- 旧：独立类 `class MyTool(BaseTool):` + tuple 参数列表
- 新：`@Tool("name", description="...", parameters=[ToolParameterInfo(...)])` 装饰方法
- 参数格式：旧 `("name", ToolParamType.STRING, "desc", True, None)` → 新 `ToolParameterInfo(name="name", param_type=ToolParamType.STRING, description="desc", required=True)`
- `function_args.get("key")` → 方法参数 `key: str = ""` 或 `kwargs.get("key")`
- 返回值保持 `{"name": "xxx", "content": "xxx"}` 不变

### 6. EventHandler 组件迁移
- 旧：独立类 `class MyHandler(BaseEventHandler):` + 类属性
- 新：`@EventHandler("name", event_type=EventType.XXX, ...)` 装饰方法
- `handler_name`, `handler_description` → 装饰器参数 name, description
- `event_type`, `weight`, `intercept_message` → 同名装饰器参数
- `execute(self, message)` → 方法参数 `message=None, **kwargs`
- 返回值保持 `(bool, bool, Optional[str], None, None)` 五元组不变

### 7. 全局变量消除
- 旧系统中 EventHandler/Command 等独立类需要 `global _plugin_instance` 引用插件
- 新系统中所有组件都是插件类的方法，直接使用 `self` 访问插件实例和状态

### 8. 配置文件
- 删除代码中的 `config_schema` 和 `ConfigField` 声明
- 根据原 config_schema 生成一份等效的 `config.toml` 文件
- 代码中 `self.get_config(key)` → `await self.ctx.config.get(key)`

### 9. API 调用替换
- `await self.send_text(text)` → `await self.ctx.send.text(text, stream_id)`
- `await self.send_emoji(b64)` → `await self.ctx.send.emoji(b64, stream_id)`
- `await self.send_image(b64)` → `await self.ctx.send.image(b64, stream_id)`
- `await self.send_command(cmd)` → `await self.ctx.send.command(cmd, stream_id)`
- `self.get_config(key, default)` → `await self.ctx.config.get(key)`（异步！）
- `logger.info(msg)` → `self.ctx.logger.info(msg)` 或 `print(msg)`

### 10. 类型导入
- `from maibot_sdk.types import ActivationType, ChatMode, EventType, ToolParameterInfo, ToolParamType`
- 如需 HookHandler：`from maibot_sdk import HookHandler` + `from maibot_sdk.types import WorkflowStage, HookResult, ErrorPolicy`
- 如需消息模型：`from maibot_sdk.messages import MaiMessages, MessageSegment`

## 输出要求

1. 输出完整的迁移后 `plugin.py` 文件
2. 输出对应的 `config.toml` 文件（基于原 config_schema 生成）
3. 输出更新后的 `_manifest.json` 文件（添加 capabilities 和 id 字段）
4. 列出所有变更点的简要说明

## 以下是我的旧版插件代码

```python
# 在这里粘贴你的旧版插件代码
```
````

---

## 附录：能力代理完整参考

以下是 `self.ctx` 上所有可用的能力代理及其方法：

| 代理 | 方法 | 说明 |
|------|------|------|
| `self.ctx.send` | `.text(text, stream_id)` | 发送文本 |
| | `.emoji(emoji_data, stream_id)` | 发送表情 |
| | `.image(image_data, stream_id)` | 发送图片 |
| | `.forward(messages, stream_id)` | 发送转发消息 |
| | `.hybrid(segments, stream_id)` | 发送混合消息 |
| | `.command(command, stream_id)` | 发送命令 |
| `self.ctx.config` | `.get(key)` | 获取配置值 |
| | `.get_plugin()` | 获取当前插件配置 |
| | `.get_all()` | 获取全部配置 |
| `self.ctx.db` | `.query(table, filters, ...)` | 查询数据 |
| | `.save(table, data, ...)` | 保存数据 |
| | `.get(table, key_field, key_value)` | 获取单条 |
| | `.delete(table, filters)` | 删除数据 |
| | `.count(table)` | 统计数量 |
| `self.ctx.llm` | `.generate(prompt, ...)` | LLM 生成 |
| | `.generate_with_tools(prompt, tools, ...)` | 带工具生成 |
| | `.get_available_models()` | 获取可用模型 |
| `self.ctx.emoji` | `.get_random(count)` | 随机表情 |
| | `.get_by_description(desc)` | 按描述搜索 |
| | `.get_count()` | 总数 |
| | `.get_all()` | 全部表情 |
| | `.get_info()` | 统计信息 |
| | `.get_emotions()` | 情感标签 |
| | `.register_emoji(base64)` | 注册表情 |
| | `.delete_emoji(hash)` | 删除表情 |
| `self.ctx.message` | `.get_recent(chat_id, limit)` | 最近消息 |
| | `.get_by_time(start, end)` | 按时间查询 |
| | `.get_by_time_in_chat(chat_id, start, end)` | 按时间+聊天查询 |
| | `.count_new(chat_id, since)` | 统计新消息 |
| | `.build_readable(messages)` | 构建可读文本 |
| `self.ctx.chat` | `.get_all_streams()` | 全部聊天流 |
| | `.get_group_streams()` | 群聊流 |
| | `.get_private_streams()` | 私聊流 |
| | `.get_stream_by_group_id(id)` | 按群组查找 |
| | `.get_stream_by_user_id(id)` | 按用户查找 |
| `self.ctx.frequency` | `.get_current_talk_value(chat_id)` | 当前频率 |
| | `.set_adjust(chat_id, value)` | 设置调整值 |
| | `.get_adjust(chat_id)` | 获取调整值 |
| `self.ctx.person` | `.get_id(platform, user_id)` | 获取人物 ID |
| | `.get_value(person_id, field)` | 获取字段值 |
| | `.get_id_by_name(name)` | 按名称查找 |
| `self.ctx.knowledge` | `.search(query, limit)` | 知识库搜索 |
| `self.ctx.tool` | `.get_definitions()` | 获取工具定义 |
| `self.ctx.component` | `.get_all_plugins()` | 全部插件 |
| | `.get_plugin_info(name)` | 插件信息 |
| | `.list_loaded_plugins()` | 已加载插件 |
| | `.list_registered_plugins()` | 已注册插件 |
| | `.enable_component(name, type)` | 启用组件 |
| | `.disable_component(name, type)` | 禁用组件 |
| | `.reload_plugin(name)` | 重载插件 |
| `self.ctx.logger` | `.debug(msg)` | Debug 日志 |
| | `.info(msg)` | Info 日志 |
| | `.warning(msg)` | Warning 日志 |
| | `.error(msg)` | Error 日志 |
