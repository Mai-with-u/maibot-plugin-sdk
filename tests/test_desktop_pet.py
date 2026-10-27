import asyncio
from unittest.mock import AsyncMock

import pytest

from maibot_sdk.context import PluginContext


@pytest.mark.parametrize("action,args", [
    ("status", {}), ("show", {}), ("hide", {}),
    ("say", {"text": "完成了"}), ("set_thinking", {"active": False}),
])
def test_desktop_pet_routes_and_unwraps_status(action, args):
    status = {"enabled": True, "supported": True, "running": True, "ready": True, "visible": False, "error": ""}
    rpc = AsyncMock(return_value={"success": True, "result": status})
    ctx = PluginContext("test.plugin", rpc_call=rpc)
    result = asyncio.run(getattr(ctx.desktop_pet, action)(**args))
    assert result == status
    rpc.assert_awaited_once_with(
        "cap.call", "test.plugin", {"capability": f"desktop_pet.{action}", "args": args},
    )
