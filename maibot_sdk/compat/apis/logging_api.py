"""旧版 logging_api 模块 (兼容层)"""

import logging
import warnings


def get_logger(name: str) -> logging.Logger:
    """获取插件使用的 Logger 实例

    Args:
        name: Logger 名称，通常为插件名

    Returns:
        logging.Logger 实例
    """
    warnings.warn(
        "get_logger() 已弃用，请使用 self.ctx.log 或 logging.getLogger()",
        DeprecationWarning,
        stacklevel=2,
    )
    return logging.getLogger(f"plugin.{name}")


__all__ = ["get_logger"]
