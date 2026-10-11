import asyncio
from pathlib import Path
from typing import Any

from maibot_sdk import PluginContext, PluginPaths


def test_resolve_image_preserves_host_result_and_reference(tmp_path: Path) -> None:
    async def check() -> None:
        expected = {"success": True, "image": {"binary_data_base64": "aW1hZ2U=", "binary_hash": "hash"}}

        async def rpc(method: str, plugin_id: str, payload: Any, **kwargs: Any) -> Any:
            assert method == "cap.call" and plugin_id == "test.plugin"
            assert payload == {
                "capability": "maisaka.context.resolve_image",
                "args": {"stream_id": "current", "source_id": "tool_result:call_x:1", "index": 0},
            }
            return expected

        ctx = PluginContext("test.plugin", rpc, PluginPaths(tmp_path, tmp_path))
        result = await ctx.maisaka.context.resolve_image("current", "tool_result:call_x:1")
        assert result == expected

    asyncio.run(check())
