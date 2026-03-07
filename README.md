# MaiBot Plugin SDK

MaiBot 插件开发的唯一依赖。提供插件基类、组件装饰器、能力代理和类型定义。

## 安装

```bash
pip install maibot-plugin-sdk
```

## 快速开始

```python
from maibot_sdk import MaiBotPlugin, Action, Command

class MyPlugin(MaiBotPlugin):

    @Action("greet", description="打招呼")
    async def handle_greet(self, **kwargs):
        await self.ctx.send.text("你好！", kwargs["stream_id"])
        return True, "已回复"

    @Command("hello", pattern=r"^/hello")
    async def handle_hello(self, **kwargs):
        await self.ctx.send.text("Hello!", kwargs["stream_id"])
        return True, "Hello!", 2

def create_plugin():
    return MyPlugin()
```

将上述代码保存为 `plugin.py`，放置在 MaiBot 的 `plugins/` 目录下，即可被自动加载。

## 核心概念

### 插件基类

所有插件必须继承 `MaiBotPlugin`，并通过模块级 `create_plugin()` 函数返回实例。

生命周期回调：

| 方法 | 说明 |
|------|------|
| `on_load()` | 插件加载完成后调用 |
| `on_unload()` | 插件卸载前调用 |
| `on_config_update(new_config, version)` | 配置热更新时调用 |

### 组件装饰器

通过装饰器声明插件组件，由运行时自动收集和注册：

| 装饰器 | 用途 |
|--------|------|
| `@Action` | 声明一个响应动作，支持关键词/概率/始终触发等激活方式 |
| `@Command` | 声明一个命令处理器，支持正则匹配和别名 |
| `@Tool` | 声明一个工具，供 LLM 调用 |
| `@EventHandler` | 声明一个事件处理器，可拦截或异步处理消息链事件 |
| `@WorkflowStep` | 声明一个工作流步骤，参与消息处理管线 |

### 能力代理

通过 `self.ctx` 访问 8 种能力，所有调用自动转发为 RPC 请求：

| 属性 | 类型 | 说明 |
|------|------|------|
| `ctx.send` | `SendCapability` | 发送文本、图片、表情等消息 |
| `ctx.db` | `DatabaseCapability` | 数据库增删改查 |
| `ctx.llm` | `LLMCapability` | LLM 文本生成和工具调用 |
| `ctx.config` | `ConfigCapability` | 插件配置读取 |
| `ctx.emoji` | `EmojiCapability` | 表情包管理 |
| `ctx.message` | `MessageCapability` | 历史消息查询 |
| `ctx.frequency` | `FrequencyCapability` | 发言频率控制 |
| `ctx.component` | `ComponentCapability` | 插件和组件管理 |

### 消息模型

`MaiMessages` 是跨组件传递的统一消息格式：

```python
from maibot_sdk.messages import MaiMessages

msg = MaiMessages(plain_text="你好", stream_id="group_123")
msg.modify_prompt("新的 prompt")
data = msg.to_rpc_dict()
```

## 类型定义

SDK 导出的主要类型定义位于 `maibot_sdk.types`：

- `ActivationType` -- Action 激活方式（ALWAYS / KEYWORD / RANDOM / NEVER）
- `ChatMode` -- 聊天模式（NORMAL / FOCUS / PRIORITY / ALL）
- `EventType` -- 事件类型（ON_MESSAGE / ON_START / POST_LLM 等）
- `WorkflowStage` -- 工作流阶段（INGRESS / PRE_PROCESS / PLAN / EGRESS 等）
- `HookResult` -- 工作流返回值（CONTINUE / SKIP_STAGE / ABORT）
- `ToolParameterInfo` -- 工具参数定义模型
- `ComponentType` -- 组件类型枚举

完整定义参见源码 `maibot_sdk/types.py`。

## 插件目录结构

推荐的插件目录结构：

```
my_plugin/
    plugin.py          # 插件入口，包含 create_plugin()
    config.toml        # 插件配置（可选）
    README.md          # 插件说明（可选）
```

## 环境要求

- Python >= 3.10
- pydantic >= 2.0.0
- msgpack >= 1.0.0

## 开发

```bash
# 克隆仓库
git clone https://github.com/Mai-with-u/maibot-plugin-sdk.git
cd maibot-plugin-sdk

# 安装开发依赖
pip install -e ".[dev]"

# 运行检查
ruff check maibot_sdk/
mypy maibot_sdk/

# 运行测试
pytest
```

## 许可证

本项目使用 [AGPL-3.0](LICENSE) 许可证。
