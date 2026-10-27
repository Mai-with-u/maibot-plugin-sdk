from unittest.mock import AsyncMock

import pytest

from maibot_sdk.context import PluginContext


@pytest.mark.asyncio
@pytest.mark.parametrize("method,args,kwargs,expected", [
    ("search", ("query",), {}, {"query": "query", "max_results": 5}),
    ("search", ("query",), {"max_results": 2}, {"query": "query", "max_results": 2}),
    ("fetch", ("https://example.com",), {}, {"url": "https://example.com"}),
])
async def test_web_forwards_parameters_and_unwraps_results(method, args, kwargs, expected):
    result = {"service": "shared", "content_kind": "page_text", "content": "正文"}
    rpc = AsyncMock(return_value={"success": True, "result": result})
    ctx = PluginContext("test", rpc_call=rpc)
    assert await getattr(ctx.web, method)(*args, **kwargs) == result
    rpc.assert_awaited_once_with(
        "cap.call", "test", {"capability": f"web.{method}", "args": expected}, timeout_ms=310000,
    )


@pytest.mark.asyncio
async def test_web_propagates_errors_and_rejects_invalid_results():
    ctx = PluginContext("test", rpc_call=AsyncMock(side_effect=RuntimeError("未启用")))
    with pytest.raises(RuntimeError, match="未启用"):
        await ctx.web.search("query")
    ctx = PluginContext("test", rpc_call=AsyncMock(return_value=[]))
    with pytest.raises(TypeError, match="非字典"):
        await ctx.web.fetch("https://example.com")
