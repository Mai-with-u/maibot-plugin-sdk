# Changelog

本文件记录 maibot-plugin-sdk 的版本变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [1.2.1] - 2026-03-12

### 变更

- **日志系统重写**：移除 `ctx.logging` 异步 API（`LoggingCapability`），改用标准 `logging` 模块作为唯一日志接口
  - 新增 `ctx.logger` 属性，返回 `logging.Logger`（名称为 `plugin.<plugin_id>`）
  - Runner 进程全局安装 `RunnerIPCLogHandler`，自动将所有 stdlib logging 日志（含第三方库）通过 IPC 批量传输到主进程
  - 主进程通过 `RunnerLogBridge` 重放为真实 `LogRecord`，接入已有的 structlog Handler 链
  - 插件无需 `await`，同步 `logger.info()` 即可使用，第三方库日志也能自动捕获
- 兼容层 `get_logger()` 不再发出 `DeprecationWarning`，直接返回 `logging.Logger`

### 文档

- 更新 `docs/guide.md` 日志章节，文档化新的 `ctx.logger` 用法和迁移说明

## [1.2.0] - 2026-03-10

### 新增

- **旧版插件兼容层** (`maibot_sdk.compat`): 通过 import hook 拦截 `from src.plugin_system import ...`，自动重定向到兼容实现并发出 `DeprecationWarning`，旧版插件无需改动即可在新 IPC 运行时中加载
  - 完整复刻 `BaseAction`、`BaseCommand`、`BaseEventHandler`、`BaseTool` 四个基类
  - 复刻全部 15 个 API 模块 (send_api, config_api, llm_api 等)
  - 复刻 `constants`、`component_types`、`config_types`、`workflow_types` 等类型定义
  - `@register_plugin` 装饰器兼容无参和带参两种用法
  - `LegacyPluginAdapter` 将旧版 BasePlugin 包装为新版组件描述格式
- **迁移指南** (`docs/migration-guide.md`)

### 修复

- 修复 `message.py`、`send.py` 类型注解错误
- 修复 E402 lint 错误
- 解决 Python 3.13 import hook 模块身份问题

### 文档

- 简化 README，添加完整指南链接

## [1.1.0] - 2026-03-08

### 新增

- 补全能力代理至 13 个 (新增 chat, person, knowledge, tool, logging)
- 修复 llm namespace 问题
- 补充 SDK 使用指南

## [1.0.0] - 2026-03-07

### 新增

- `MaiBotPlugin` 插件基类，支持生命周期回调
- 组件装饰器: `@Action`, `@Command`, `@Tool`, `@EventHandler`, `@WorkflowStep`
- `PluginContext` 运行时上下文，提供 8 种能力代理
- 能力代理: `send`, `db`, `llm`, `config`, `emoji`, `message`, `frequency`, `component`
- `MaiMessages` 统一消息格式
- 完整类型定义: 枚举、组件信息模型、工具参数模型
- `py.typed` 标记，支持类型检查
