# Changelog

本文件记录 maibot-plugin-sdk 的版本变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [1.2.4] - 2026-03-13

### 新增

- `chat.*` 查询接口支持显式传入 `platform` 参数，便于跨平台场景下精确查询聊天流
- `llm.generate()` 与 `llm.generate_with_tools()` 兼容 `model` / `model_name` 两套字段命名，降低与不同 Host 版本联调时的摩擦

### 修复

- `send.custom()` 发送新旧两套字段别名，提升与不同版本 Host 的兼容性
- `db.count()` 统一解包 Host 返回结果，确保始终返回 `int`
- SDK 统一解包 Host 返回的单字段能力结果；`config.get()`、`chat.*`、`message.*`、`person.*`、`frequency.get_*()`、`tool.get_definitions()` 直接返回原始值、列表或字典，而不是 RPC 包装字典
- 兼容层 `database_api`、`llm_api`、`plugin_manage_api`、`send_api` 增强返回值处理和错误日志，减少旧插件迁移时的行为偏差
- 增强旧版插件适配器在配置同步、插件加载和热重载场景下的兼容性

### 文档

- README 中将“13 种能力代理”修正为“12 种能力代理 + logger 接口”
- README、开发指南、迁移指南补充能力返回值归一化说明
- 补充聊天流平台参数、LLM 模型字段兼容性以及热重载安全切换说明

### 测试

- 补充 `db.count()`、能力结果解包、平台参数透传与兼容层 API 的回归测试

## [1.2.3] - 2026-03-13

### 修复

- 同步 SDK 包版本元数据到 1.2.3，修复因发布版本号未更新导致的 PyPI 上传冲突

## [1.2.2] - 2026-03-13

### 新增

- **兼容层上下文管理**：为旧版插件兼容层补充上下文进入与清理逻辑，确保插件调用期间能够稳定获取当前 `PluginContext`

### 修复

- 修复 `llm` 能力获取可用模型列表的逻辑，兼容从字典结果中提取模型列表
- 修复兼容层上下文持有者的类型注解，提升类型兼容性

### 文档

- 更新 `README.md` 和 `docs/migration-guide.md` 中对 `ctx.logger` 的描述，统一日志接口说明
- 更新 `docs/guide.md` 和 `docs/migration-guide.md`，补充 `EventHandler` 返回值约定与参数列表细节

### 测试

- 增加 `ctx.logger` 实例类型检查，确保返回标准 `logging.Logger`

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
