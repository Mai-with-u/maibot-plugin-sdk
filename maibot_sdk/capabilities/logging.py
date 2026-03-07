"""日志能力代理

提供插件日志记录功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext


class LoggingCapability:
    """日志记录能力"""

    def __init__(self, ctx: PluginContext):
        self._ctx = ctx

    async def log(self, level: str, message: str) -> Any:
        """写入日志

        Args:
            level: 日志级别（debug/info/warning/error）
            message: 日志消息
        """
        return await self._ctx.call_capability(
            "logging.log",
            level=level,
            message=message,
        )

    async def debug(self, message: str) -> Any:
        """写入 debug 级别日志"""
        return await self.log("debug", message)

    async def info(self, message: str) -> Any:
        """写入 info 级别日志"""
        return await self.log("info", message)

    async def warning(self, message: str) -> Any:
        """写入 warning 级别日志"""
        return await self.log("warning", message)

    async def error(self, message: str) -> Any:
        """写入 error 级别日志"""
        return await self.log("error", message)
