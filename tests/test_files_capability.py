import hashlib
import json
import sys
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from maibot_sdk.capabilities.files import FilesCapability
from maibot_sdk.context import PluginContext


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["read_text", "send", "download"])
async def test_file_timeout_is_rpc_option_not_host_argument(method, tmp_path, monkeypatch):
    content = b"hello"
    rpc = AsyncMock(return_value={
        "url": "http://host/download", "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    })
    ctx = PluginContext("test.plugin", rpc_call=rpc)
    expected_args = {"file_ref": "ref"}
    if method == "download":
        monkeypatch.setattr("maibot_sdk.capabilities.files.urlopen", lambda *args, **kwargs: BytesIO(content))
        await ctx.files.download("ref", tmp_path / "download.txt")
    elif method == "read_text":
        await ctx.files.read_text("ref")
        expected_args.update(offset=0, limit=12000, encoding="utf-8-sig")
    else:
        await ctx.files.send("ref")
    rpc.assert_awaited_once_with(
        "cap.call", "test.plugin",
        {"capability": f"files.{method}", "args": expected_args},
        timeout_ms=180000,
    )


@pytest.mark.asyncio
async def test_file_upload_streams_without_rpc_bytes(tmp_path, monkeypatch):
    path = tmp_path / "file.txt"
    path.write_bytes(b"hello")
    calls = []
    async def capability(capability_name, **kwargs):
        calls.append((capability_name, kwargs))
        return {"url": "http://host/upload", "max_bytes": 10, "upload_token": "ticket"}
    def open_request(request, **kwargs):
        assert request.method == "PUT"
        assert request.data.read() == b"hello"
        return BytesIO(json.dumps({"file_ref": "ref"}).encode())
    monkeypatch.setattr("maibot_sdk.capabilities.files.urlopen", open_request)
    result = await FilesCapability(SimpleNamespace(call_capability=capability)).upload(path)
    assert result == {"file_ref": "ref"}
    assert calls == [("files.upload", {"name": "file.txt", "mime_type": "application/octet-stream"})]
    assert isinstance(PluginContext("plugin").files, FilesCapability)


@pytest.mark.asyncio
async def test_download_checksum_failure_removes_partial(tmp_path, monkeypatch):
    async def capability(capability_name, **kwargs):
        return {"url": "http://host/download", "size": 4, "sha256": hashlib.sha256(b"good").hexdigest()}
    monkeypatch.setattr("maibot_sdk.capabilities.files.urlopen", lambda *args, **kwargs: BytesIO(b"oops"))
    path = tmp_path / "download.txt"
    with pytest.raises(ValueError, match="checksum"):
        await FilesCapability(SimpleNamespace(call_capability=capability)).download("ref", path)
    assert not path.exists()


@pytest.mark.asyncio
async def test_upload_preflight_failure_cancels_reservation(tmp_path):
    path = tmp_path / "large.txt"
    path.write_bytes(b"too large")
    calls = []
    async def capability(capability_name, **kwargs):
        calls.append(kwargs)
        return {"url": "http://unused", "max_bytes": 1, "upload_token": "ticket"}
    with pytest.raises(ValueError, match="limit"):
        await FilesCapability(SimpleNamespace(call_capability=capability)).upload(path)
    assert calls[-1] == {"operation": "cancel", "upload_token": "ticket"}


@pytest.mark.asyncio
async def test_cleanup_rpc_failure_preserves_upload_error(tmp_path, monkeypatch, caplog):
    path = tmp_path / "file.txt"
    path.write_bytes(b"hello")
    async def capability(capability_name, **kwargs):
        if kwargs.get("operation") == "cancel":
            raise RuntimeError("cleanup unavailable")
        return {"url": "http://unused", "max_bytes": 10, "upload_token": "ticket"}
    original_error = OSError("upload connection failed")
    def failed_upload(*args, **kwargs):
        raise original_error
    monkeypatch.setattr("maibot_sdk.capabilities.files.urlopen", failed_upload)
    with pytest.raises(OSError, match="upload connection failed") as caught:
        await FilesCapability(SimpleNamespace(call_capability=capability)).upload(path)
    assert caught.value is original_error
    diagnostics = " ".join(caught.value.__notes__) if sys.version_info >= (3, 11) else caplog.text
    assert "cleanup unavailable" in diagnostics


@pytest.mark.asyncio
async def test_partial_cleanup_failure_preserves_checksum_error(tmp_path, monkeypatch, caplog):
    async def capability(capability_name, **kwargs):
        return {"url": "http://unused", "size": 4, "sha256": hashlib.sha256(b"good").hexdigest()}
    monkeypatch.setattr("maibot_sdk.capabilities.files.urlopen", lambda *args, **kwargs: BytesIO(b"oops"))
    path = tmp_path / "partial.txt"
    def denied_unlink(self, *args, **kwargs):
        raise PermissionError("file locked during cleanup")
    with monkeypatch.context() as patch:
        patch.setattr(type(path), "unlink", denied_unlink)
        with pytest.raises(ValueError, match="checksum") as caught:
            await FilesCapability(SimpleNamespace(call_capability=capability)).download("ref", path)
        diagnostics = " ".join(caught.value.__notes__) if sys.version_info >= (3, 11) else caplog.text
        assert "file locked" in diagnostics
    path.unlink()


@pytest.mark.asyncio
async def test_worker_failure_does_not_replace_cancellation(caplog):
    import asyncio
    import threading

    from maibot_sdk.capabilities.files import _transfer

    started = threading.Event()
    release = threading.Event()
    def worker():
        started.set()
        release.wait(2)
        raise OSError("worker failed while stopping")
    task = asyncio.create_task(_transfer(worker))
    assert await asyncio.to_thread(started.wait, 2)
    task.cancel()
    release.set()
    with pytest.raises(asyncio.CancelledError) as caught:
        await task
    diagnostics = " ".join(caught.value.__notes__) if sys.version_info >= (3, 11) else caplog.text
    assert "worker failed" in diagnostics
