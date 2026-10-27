"""聊天作用域文件能力，要求主程序支持文件服务。"""

import asyncio
import hashlib
import json
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar, cast
from urllib.request import Request, urlopen

T = TypeVar("T")

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext


def _add_transfer_error_note(error: BaseException, note: str) -> None:
    """保留原始异常；Python 3.10 通过日志记录清理失败，后续版本附加异常备注。"""
    if sys.version_info >= (3, 11):
        error.add_note(note)
    else:
        logging.getLogger(__name__).warning(note)


async def _transfer(function: Callable[[], T]) -> T:
    task = asyncio.create_task(asyncio.to_thread(function))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError as error:
        try:
            await task
        except (Exception, asyncio.CancelledError) as worker_error:
            _add_transfer_error_note(error, f"Transfer worker failed during cancellation: {worker_error!r}")
        raise


class FilesCapability:
    """只能在主程序派发的工具调用期间使用，聊天归属由 Host 注入。

    在 manifest 中分别声明 files.list/read_text/download/upload/send。
    下载和上传使用有时效的 HTTP 字节通道，不通过 RPC 携带文件内容。
    """

    def __init__(self, ctx: "PluginContext") -> None:
        self._ctx = ctx

    async def list(self, offset: int = 0) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], await self._ctx.call_capability("files.list", offset=offset))

    async def read_text(
        self, file_ref: str, offset: int = 0, limit: int = 12000, encoding: str = "utf-8-sig"
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            await self._ctx.call_capability(
                "files.read_text", file_ref=file_ref, offset=offset, limit=limit, encoding=encoding, timeout_ms=180000
            ),
        )

    async def send(self, file_ref: str) -> dict[str, Any]:
        """发送到当前聊天；unknown 表示投递结果不确定，不应自动重发。"""
        return cast(dict[str, Any], await self._ctx.call_capability("files.send", file_ref=file_ref, timeout_ms=180000))

    async def upload(self, path: Path, name: str = "", mime_type: str = "application/octet-stream") -> dict[str, Any]:
        path = Path(path)
        await asyncio.to_thread(path.stat)
        info = await self._ctx.call_capability("files.upload", name=name or path.name, mime_type=mime_type)

        def transfer() -> dict[str, Any]:
            with path.open("rb") as handle:
                size = path.stat().st_size
                if size > info["max_bytes"]:
                    raise ValueError("File exceeds the host limit")
                request = Request(
                    info["url"],
                    data=cast(Any, handle),
                    method="PUT",
                    headers={
                        "Content-Type": mime_type,
                        "Content-Length": str(size),
                    },
                )
                with urlopen(request, timeout=120) as response:
                    return cast(dict[str, Any], json.loads(response.read(65536)))

        try:
            return await _transfer(transfer)
        except BaseException as error:
            try:
                await self._ctx.call_capability("files.upload", operation="cancel", upload_token=info["upload_token"])
            except (Exception, asyncio.CancelledError) as cleanup_error:
                _add_transfer_error_note(error, f"Failed to release upload reservation: {cleanup_error!r}")
            raise

    async def download(self, file_ref: str, destination: Path) -> dict[str, Any]:
        """独占创建目标文件，失败删除部分文件，不覆盖已有文件。"""
        info = await self._ctx.call_capability("files.download", file_ref=file_ref, timeout_ms=180000)
        destination = Path(destination)

        def transfer() -> None:
            digest = hashlib.sha256()
            written = 0
            with destination.open("xb") as handle:
                try:
                    with urlopen(info["url"], timeout=120) as response:
                        while chunk := response.read(256 * 1024):
                            written += len(chunk)
                            if written > info["size"]:
                                raise ValueError("File exceeds declared size")
                            handle.write(chunk)
                            digest.update(chunk)
                    if written != info["size"] or digest.hexdigest() != info["sha256"]:
                        raise ValueError("File checksum mismatch")
                except BaseException as error:
                    try:
                        handle.close()
                        destination.unlink()
                    except OSError as cleanup_error:
                        _add_transfer_error_note(error, f"Failed to remove partial download: {cleanup_error!r}")
                    raise

        await _transfer(transfer)
        return {key: value for key, value in info.items() if key != "url"}
