# Changelog

本文件记录 maibot-plugin-sdk 的版本变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-03-07

### 新增

- `MaiBotPlugin` 插件基类，支持生命周期回调
- 组件装饰器: `@Action`, `@Command`, `@Tool`, `@EventHandler`, `@WorkflowStep`
- `PluginContext` 运行时上下文，提供 8 种能力代理
- 能力代理: `send`, `db`, `llm`, `config`, `emoji`, `message`, `frequency`, `component`
- `MaiMessages` 统一消息格式
- 完整类型定义: 枚举、组件信息模型、工具参数模型
- `py.typed` 标记，支持类型检查
