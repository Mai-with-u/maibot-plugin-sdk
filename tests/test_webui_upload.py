import asyncio
from unittest.mock import AsyncMock
from maibot_sdk.context import PluginContext


def test_claim_upload_normalizes_result_and_scopes_rpc():
    rpc = AsyncMock(
        return_value={
            "success": True,
            "upload": {"path": "data/plugins/test.plugin/uploads/a.png", "sha256": "abc", "upload_id": "a"},
        }
    )
    ctx = PluginContext("test.plugin", rpc_call=rpc)
    result = asyncio.run(ctx.webui.claim_upload("a"))
    assert result["upload_id"] == "a" and "upload" not in result
    rpc.assert_awaited_once_with(
        "cap.call", "test.plugin", {"capability": "webui.claim_upload", "args": {"upload_id": "a"}}
    )
