import asyncio
from unittest.mock import AsyncMock

from maibot_sdk.context import PluginContext


def test_personality_methods_unwrap_host_results():
    async def run():
        rpc = AsyncMock(return_value={"success": True, "result": {"profiles": []}})
        ctx = PluginContext("test.plugin", rpc_call=rpc)
        assert await ctx.personality.list() == {"profiles": []}
        assert rpc.call_args.args[2] == {"capability": "personality.list", "args": {}}
        rpc.return_value = {"success": True, "result": {"name": "old"}}
        assert await ctx.personality.get_current() == {"name": "old"}
        assert rpc.call_args.args[2] == {"capability": "personality.get_current", "args": {}}
        rpc.return_value = {"success": True, "result": {"changed": True, "current": {"name": "new"}}}
        assert (await ctx.personality.switch("new"))["current"]["name"] == "new"
        assert rpc.call_args.args[2] == {"capability": "personality.switch", "args": {"name": "new"}}

    asyncio.run(run())
