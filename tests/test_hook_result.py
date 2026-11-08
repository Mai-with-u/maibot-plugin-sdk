"""执行开发指南的中止示例，确认它仍使用可经 RPC 传输的字典协议。"""

from pathlib import Path
from typing import Any

import msgpack
import pytest

from maibot_sdk import HookResult
from maibot_sdk.types import HookResult as TypesHookResult


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("request_type", "message_id", "action"),
    [("maisaka.replyer", "", "abort"), ("maisaka.replyer", "m1", "continue"), ("plugin.replyer", "", "continue")],
)
async def test_documented_hook_result_roundtrips_over_rpc(request_type: str, message_id: str, action: str) -> None:
    guide = (Path(__file__).parents[1] / "docs/guide.md").read_text(encoding="utf-8")
    section = guide.split("#### 主动中止并提供原因", 1)[1]
    example = section.split("```python\n", 1)[1].split("```", 1)[0]
    namespace: dict[str, Any] = {}
    exec(compile(example, "docs/guide.md", "exec"), namespace)
    result: HookResult = await namespace["guard_reply"](
        None,
        request_type=request_type,
        reply_message_id=message_id,
    )
    assert HookResult is TypesHookResult
    assert isinstance(result, dict)
    assert msgpack.unpackb(msgpack.packb(result, use_bin_type=True), raw=False) == result
    assert result["action"] == action
    if action == "abort":
        assert result["custom_result"]["reason"] == "没有明确的回复目标，请选择具体消息后再回复。"
