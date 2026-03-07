# 贡献指南

感谢你对 maibot-plugin-sdk 的关注。

## 开发环境

```bash
git clone https://github.com/Mai-with-u/maibot-plugin-sdk.git
cd maibot-plugin-sdk
pip install -e ".[dev]"
```

## 代码规范

- 使用 [Ruff](https://docs.astral.sh/ruff/) 进行格式化和 lint
- 使用 [Mypy](https://mypy-lang.org/) 进行类型检查
- 提交前运行: `ruff check maibot_sdk/ && mypy maibot_sdk/`

## 提交流程

1. Fork 本仓库
2. 创建特性分支: `git checkout -b feature/xxx`
3. 提交更改并确保通过 lint 和测试
4. 发起 Pull Request 到 `main` 分支

## 版本号

遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/):

- MAJOR: 不兼容的 API 变更
- MINOR: 向后兼容的新功能
- PATCH: 向后兼容的问题修复
