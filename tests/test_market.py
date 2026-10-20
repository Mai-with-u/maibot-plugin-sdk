from unittest.mock import AsyncMock

import pytest

from maibot_sdk.context import PluginContext


@pytest.mark.asyncio
@pytest.mark.parametrize("method,args,kwargs", [
    ("search", ("语音",), {"category": "Audio", "page": 2, "limit": 5, "sort_by": "downloads",
                          "compatible_only": True, "include_manifest": True, "include_stats": True,
                          "force_refresh": True}),
    ("get_detail", ("test.voice",), {"force_refresh": True}),
    ("get_readme", ("test.voice",), {"max_chars": 1000, "prefer_local": False, "branch": "docs",
                                     "force_refresh": True}),
])
async def test_market_forwards_parameters_and_unwraps_results(method, args, kwargs):
    expected = {"source": "official", "features": {"stats": True}}
    rpc = AsyncMock(return_value={"success": True, "result": expected})
    ctx = PluginContext("test", rpc_call=rpc)
    result = await getattr(ctx.market, method)(*args, **kwargs)
    assert result == expected
    payload = rpc.await_args.args[2]
    assert payload["capability"] == f"market.{method}"
    assert payload["args"] == {("query" if method == "search" else "plugin_id"): args[0], **kwargs}


@pytest.mark.asyncio
async def test_market_propagates_network_errors_and_rejects_invalid_results():
    ctx = PluginContext("test", rpc_call=AsyncMock(side_effect=RuntimeError("source offline")))
    with pytest.raises(RuntimeError, match="source offline"):
        await ctx.market.search()
    ctx = PluginContext("test", rpc_call=AsyncMock(return_value=[]))
    with pytest.raises(TypeError, match="非字典"):
        await ctx.market.search()
