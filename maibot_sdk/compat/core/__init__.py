"""旧版 core 模块 (兼容层)

component_registry 和 plugin_manager 在新架构中不再由插件直接使用。
提供空占位以防止导入失败。
"""

import warnings


class _StubComponentRegistry:
    def __getattr__(self, name: str):
        warnings.warn("ComponentRegistry 已弃用，新版 SDK 自动管理组件注册", DeprecationWarning, stacklevel=2)
        return lambda *a, **kw: None


class _StubPluginManager:
    def __getattr__(self, name: str):
        warnings.warn("PluginManager 已弃用，请使用新版 PluginLoader", DeprecationWarning, stacklevel=2)
        return lambda *a, **kw: None


component_registry = _StubComponentRegistry()
plugin_manager = _StubPluginManager()
