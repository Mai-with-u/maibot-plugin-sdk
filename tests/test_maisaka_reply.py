from unittest.mock import AsyncMock

import pytest

from maibot_sdk.context import PluginContext


@pytest.mark.asyncio
async def test_generate_returns_host_result_and_forwards_rpc_timeout():
    expected = {"success": True, "text": "总结正文", "selected_expression_ids": [1]}
    rpc = AsyncMock(return_value=expected)
    ctx = PluginContext("test", rpc_call=rpc)
    assert await ctx.maisaka.reply.generate(
        "real-stream", "原帖材料", format_instruction="三段", model_name="writer", timeout_ms=180000,
    ) == expected
    assert rpc.await_args.args[2] == {
        "capability": "maisaka.reply.generate",
        "args": {"stream_id": "real-stream", "reference": "原帖材料",
                 "format_instruction": "三段", "model_name": "writer"},
    }
    assert rpc.await_args.kwargs == {"timeout_ms": 180000}


@pytest.mark.asyncio
async def test_append_preserves_reply_target_and_default_behavior():
    rpc = AsyncMock(return_value={"success": True})
    ctx = PluginContext("test", rpc_call=rpc)
    user = {"user_id": "123", "user_nickname": "作者", "platform": "xiaoheihe"}
    await ctx.maisaka.context.append(
        "real-stream", [], message_id="comment:123", replyable=True, user_info=user,
    )
    args = rpc.await_args.args[2]["args"]
    assert args["message_id"] == "comment:123"
    assert args["replyable"] is True and args["user_info"] == user
    await ctx.maisaka.append_context("real-stream", [])
    args = rpc.await_args.args[2]["args"]
    assert args["replyable"] is False and args["user_info"] is None


@pytest.mark.asyncio
async def test_generate_preserves_host_failure():
    expected = {"success": False, "error": "未找到已存在的聊天流"}
    ctx = PluginContext("test", rpc_call=AsyncMock(return_value=expected))
    assert await ctx.maisaka.reply.generate("unknown", "材料") == expected
