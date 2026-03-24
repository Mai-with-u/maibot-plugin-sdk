# Changelog

本文件记录 maibot-plugin-sdk 的版本变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]


## [2.1.0] - 2026-03-24

### 新增

- 新增 `API` 组件声明与 `ctx.api` 能力代理，支持按名称/版本查询、调用可见 API
- 新增动态 API 注册、注销与整表同步能力，插件可通过 `register_dynamic_api()`、`unregister_dynamic_api()`、`sync_dynamic_apis()` 维护运行时 API 集合
- 新增全局配置热更新订阅机制，`MaiBotPlugin.config_reload_subscriptions` 现可声明 `bot` / `model` 级配置广播订阅
- 新增 `MessageGateway` 组件装饰器与消息网关能力代理，支持适配器式入站消息接入与运行时状态上报

### 变更

- SDK 不再继续暴露旧的适配器能力代理，统一收敛到消息网关模型，适配器插件请改用 `MessageGateway` 和 `ctx.gateway`
- `MaiBotPlugin.on_config_update()` 的职责扩展为同时处理插件自身配置更新与全局 `bot` / `model` 配置广播
- 组件声明与上下文能力围绕动态 API / 消息网关场景补齐，便于 Host 在运行时增删 API 和管理适配器链路状态

### 修复

- 兼容层 `LegacyPluginAdapter` 现已支持全局配置热更新与订阅范围管理，减少旧版插件在新运行时中的行为偏差
- 简化组件收集逻辑，移除未使用的 `ComponentType` 依赖，降低内部维护复杂度

### 测试

- 补充 API 能力代理、动态 API、配置热更新、消息网关以及兼容层配置同步的回归测试

## [2.0.1] - 2026-03-22

### 新增

添加适配器能力代理的运行时状态上报功能及相关测试

## [2.0.0] - 2026-03-21

### 新增

- 新增 `@Adapter` 类装饰器配套文档，明确适配器插件的声明方式、出站 `send_to_platform()` 约定与入站 `ctx.adapter.receive_external_message()` 注入方式
- 补充 `PluginContext.adapter` 能力的使用说明，文档化当前 Host 对适配器入站 `MessageDict` 的最小字段要求


### 变更

- **组件协议统一**：SDK 产出的组件类型协议值统一为大写（如 `ACTION`、`EVENT_HANDLER`、`HOOK_HANDLER`），并在组件管理入口中兼容大小写不同但语义一致的输入
- **Hook 命名收敛**：`WorkflowStep` 正式移除并更名为 `HookHandler`；`ComponentType.WORKFLOW_STEP` 与 `WorkflowStep` 装饰器不再保留兼容映射，这是一次明确的不向后兼容更改
- README、开发指南与迁移指南统一为“13 种能力代理 + logger 接口”的当前实现口径
- README 与开发指南补充“5 种组件方法装饰器 + 1 种适配器类装饰器”的区分，避免把 `@Adapter` 与普通组件装饰器混淆
- 迁移指南中的配置、数据库、人物信息、知识库与 Manifest 示例对齐当前 SDK 签名和协议值


### 修复

- 兼容层旧版插件适配器改为产出新的大写组件协议值，避免与 runtime 的组件注册协议不一致
- 兼容层组件查询 API 统一按归一化后的组件类型比较，兼容 Host 返回的大写组件类型
- 修复 SDK 在 `ruff check`、`ruff format --check` 与 `mypy` 下的当前问题，统一到内建泛型与现有 import 排序规则
- 修复 `collect_adapter_info()` 的返回值类型收窄问题，避免在严格类型检查下把 `Any` 直接向外透出
- 修复 compat `emoji_api.get_by_description()` 的返回值归一化逻辑，统一返回字典结构而非 tuple
- 修复 compat `LegacyPluginAdapter` 对主程序配置模块的静态导入依赖，避免 SDK 单独运行 `mypy` 时出现 `import-not-found`

### 文档

- README、开发指南、迁移指南同步更新 `HookHandler` 命名与组件协议变更说明
- README、开发指南、迁移指南全面补充适配器插件说明，并注明 `WorkflowStep` 仅保留为显式报错入口，不再提供兼容映射
- 开发文档中的检查命令更新为 `uv sync --extra dev` / `uv run ...` 形式，与仓库当前使用方式保持一致

### 测试

- 补充组件类型归一化、`HookHandler` 组件收集和 `WorkflowStep` breaking change 的回归测试
- 补充适配器声明收集、`PluginContext.adapter` 能力调用与适配器兼容层相关回归测试
- 验证 SDK 目录下 `uv run pytest`、`uv run ruff check .`、`uv run ruff format --check .`、`uv run mypy .` 均通过

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
- 兼容层 `config_api` 现在会同步主程序全局配置缓存；同步 `component_manage_api` / `plugin_manage_api` 查询接口改为返回最近一次运行时快照

### 文档

- README 中将“13 种能力代理”修正为“12 种能力代理 + logger 接口”
- README、开发指南、迁移指南补充能力返回值归一化说明
- README、迁移指南与 compat emoji API 说明统一为字典化表情返回结构，并补充同步管理 API 的快照语义
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
