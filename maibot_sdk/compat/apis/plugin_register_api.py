"""旧版 @register_plugin 装饰器 (兼容层)

旧版插件系统使用 ``@register_plugin`` 标记插件类。
兼容层记录被标记的类，以便 LegacyPluginAdapter 发现它。

支持两种用法:
    @register_plugin          # 旧版无参用法
    @register_plugin(name=..., ...)  # 带元数据用法
"""

import warnings
from typing import Any


def register_plugin(cls: type | None = None, **kwargs: Any) -> Any:
    """标记一个类为旧版插件入口

    支持无参 ``@register_plugin`` 和带参 ``@register_plugin(name=..., ...)`` 两种形式。
    兼容层会在类上设置 ``_plugin_meta`` 和 ``_is_legacy_registered`` 属性，
    供 LegacyPluginAdapter 发现。
    """

    def _decorator(klass: type) -> type:
        warnings.warn(
            "@register_plugin 已弃用，请在模块中定义 create_plugin() 工厂函数",
            DeprecationWarning,
            stacklevel=2,
        )
        klass._is_legacy_registered = True  # type: ignore[attr-defined]
        klass._plugin_meta = kwargs  # type: ignore[attr-defined]

        # 在调用方所在模块打标记
        import inspect

        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        if module is not None:
            module._legacy_plugin_class = klass  # type: ignore[attr-defined]

        return klass

    # @register_plugin (无参) —— cls 是类本身
    if cls is not None:
        return _decorator(cls)

    # @register_plugin(name=..., ...) —— 返回装饰器
    return _decorator
