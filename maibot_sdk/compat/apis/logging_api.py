"""兼容层 logging 工具"""

import logging


def get_logger(name: str) -> logging.Logger:
    """获取插件使用的 Logger 实例。

    Runner 进程中该 Logger 的所有日志将自动通过
    :class:`~src.plugin_runtime.runner.log_handler.RunnerIPCLogHandler`
    传输到主进程显示。

    Args:
        name: Logger 名称，通常为插件名称或 ``__name__``。

    Returns:
        以 ``plugin.<name>`` 为名称的 :class:`logging.Logger` 实例。
    """
    return logging.getLogger(f"plugin.{name}")


__all__ = ["get_logger"]
