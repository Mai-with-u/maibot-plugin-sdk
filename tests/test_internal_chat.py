import asyncio
from unittest.mock import AsyncMock

from maibot_sdk.context import PluginContext


def test_send_unwraps_result_and_passes_only_text():
    rpc = AsyncMock(return_value={"success": True, "result": {"message_id": "m1"}})
    ctx = PluginContext("test.plugin", rpc_call=rpc)
    result = asyncio.run(ctx.internal_chat.send("你好"))
    assert result == {"message_id": "m1"}
    rpc.assert_awaited_once_with(
        "cap.call",
        "test.plugin",
        {"capability": "internal_chat.send", "args": {"text": "你好"}},
    )


def test_identity_unwraps_platform_and_owner_user():
    rpc = AsyncMock(return_value={"success": True, "result": {"platform": "internal", "user_id": "owner"}})
    ctx = PluginContext("test.plugin", rpc_call=rpc)
    assert asyncio.run(ctx.internal_chat.identity()) == {"platform": "internal", "user_id": "owner"}
    rpc.assert_awaited_once_with("cap.call", "test.plugin", {"capability": "internal_chat.identity", "args": {}})
