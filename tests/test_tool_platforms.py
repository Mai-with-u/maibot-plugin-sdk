import pytest

from maibot_sdk import Tool
from maibot_sdk.components import collect_components


@pytest.mark.parametrize("platforms,expected", [
    (None, []), ([], []), ("telegram", ["telegram"]),
    ([" QQ ", "Telegram", "qq"], ["qq", "telegram"]),
])
def test_platform_scope_is_serialized_without_becoming_call_parameter(platforms, expected):
    class Plugin:
        @Tool("scoped", platforms=platforms, parameters={"query": {"type": "string"}})
        async def scoped(self, **kwargs):
            return {}

    component = collect_components(Plugin())[0]
    assert component["platforms"] == expected
    assert "platforms" not in component["metadata"]
    assert set(component["metadata"]["parameters_raw"]) == {"query"}


@pytest.mark.parametrize("platforms", ["", " ", [""], [1], [None], True, 1, {}])
def test_invalid_platform_scope_is_rejected(platforms):
    with pytest.raises(ValueError, match="platforms"):
        Tool("invalid", platforms=platforms)


def test_omitted_scope_preserves_unrestricted_tools():
    class Plugin:
        @Tool("unrestricted")
        async def unrestricted(self, **kwargs):
            return {}

    component = collect_components(Plugin())[0]
    assert component["platforms"] == []
    assert component["chat_scope"] == "all"
    assert component["allowed_session"] == []


def test_chat_scope_and_sessions_are_serialized_at_top_level():
    class Plugin:
        @Tool("scoped", chat_scope="group", allowed_session=[" session-1 ", "session-1"], custom=True)
        async def scoped(self, **kwargs):
            return {}

    component = collect_components(Plugin())[0]
    assert component["chat_scope"] == "group"
    assert component["allowed_session"] == ["session-1"]
    assert component["metadata"]["custom"] is True
    assert {"chat_scope", "allowed_session"}.isdisjoint(component["metadata"])


@pytest.mark.parametrize("scope", [
    {"chat_scope": "direct"},
    {"allowed_session": "session-1"},
    {"allowed_session": [""]},
    {"allowed_session": [123]},
])
def test_invalid_chat_or_session_scope_is_rejected(scope):
    with pytest.raises(ValueError, match=next(iter(scope))):
        Tool("invalid", **scope)(lambda: None)
