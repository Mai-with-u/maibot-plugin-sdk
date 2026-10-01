from unittest.mock import AsyncMock

import pytest

from maibot_sdk.context import PluginContext


@pytest.mark.asyncio
async def test_avatar_capability_decodes_result_and_passes_route():
    info = {"status": "available", "url": "https://example.com/avatar.png", "expires_at": 1000.0}
    rpc = AsyncMock(return_value={"success": True, "avatar": info})
    ctx = PluginContext("plugin", rpc_call=rpc)
    result = await ctx.chat.get_avatar(
        "custom", "person", "group", account_id="bot", scope="connection", force_refresh=True,
    )
    assert result == info
    payload = rpc.await_args.args[2]
    assert payload["capability"] == "chat.get_avatar"
    assert payload["args"] == {
        "platform": "custom", "target_id": "person", "target_type": "group",
        "account_id": "bot", "scope": "connection", "force_refresh": True,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["unsupported", "missing"])
async def test_avatar_absent_state_remains_explicit(status):
    info = {"status": status, "url": None, "expires_at": 1000.0}
    ctx = PluginContext("plugin", rpc_call=AsyncMock(return_value={"success": True, "avatar": info}))
    assert await ctx.chat.get_avatar("custom", "person") == info
