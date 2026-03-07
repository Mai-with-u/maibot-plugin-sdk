# MaiBot Plugin SDK

MaiBot 插件开发的唯一依赖。提供插件基类、组件装饰器、能力代理和类型定义。

> **完整文档**：[插件开发指南](docs/guide.md) — 覆盖全部 13 种能力代理、5 种组件装饰器、消息模型、生命周期、调试与发布。

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

将上述代码保存为 `plugin.py`，放入 MaiBot 的 `plugins/` 目录即可自动加载。

## 能力一览

通过 `self.ctx` 访问所有能力，调用自动转发为 RPC 请求：

| 属性 | 说明 |
|------|------|
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
| `ctx.knowledge` | LPMM 知识库搜索 |
| `ctx.tool` | LLM 工具定义查询 |
| `ctx.logging` | 插件日志 |

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
pip install -e ".[dev]"

ruff check maibot_sdk/    # lint
mypy maibot_sdk/          # 类型检查
pytest -v                 # 测试
```

## 许可证

[AGPL-3.0](LICENSE)
