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

    metadata = collect_components(Plugin())[0]["metadata"]
    assert metadata["platforms"] == expected
    assert set(metadata["parameters_raw"]) == {"query"}


@pytest.mark.parametrize("platforms", ["", " ", [""], [1], [None], True, 1, {}])
def test_invalid_platform_scope_is_rejected(platforms):
    with pytest.raises(ValueError, match="platforms"):
        Tool("invalid", platforms=platforms)


def test_omitted_scope_preserves_unrestricted_tools():
    class Plugin:
        @Tool("unrestricted")
        async def unrestricted(self, **kwargs):
            return {}

    assert collect_components(Plugin())[0]["metadata"]["platforms"] == []
