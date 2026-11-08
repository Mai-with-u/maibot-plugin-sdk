import pytest

from maibot_sdk import Tool
from maibot_sdk.components import collect_components
from maibot_sdk.types import ToolComponentInfo, ToolParameterInfo, ToolParamType


@pytest.mark.parametrize(
    "fields, expected",
    [
        ({"description": " primary ", "brief_description": "brief", "detailed_description": "detail"}, "primary"),
        ({"brief_description": " brief ", "detailed_description": "detail"}, "brief\n\ndetail"),
        ({"detailed_description": " detail "}, "detail"),
        ({"description": " ", "brief_description": " ", "detailed_description": "detail"}, "detail"),
        ({}, ""),
    ],
)
@pytest.mark.parametrize("kind", ["tool", "model"])
def test_description_is_normalized_before_registration(fields, expected, kind):
    original = dict(fields)
    if kind == "model":
        metadata = ToolComponentInfo(name="sample", **fields).model_dump()
    else:

        async def sample(self, **kwargs):
            return {}

        method = Tool(
            "sample",
            **fields,
            parameters=[
                ToolParameterInfo(
                    name="query", param_type=ToolParamType.STRING, description="query help", required=True
                )
            ],
            core_tool=True,
        )(sample)
        plugin = type("Plugin", (), {"sample": method})()
        metadata = collect_components(plugin)[0]["metadata"]
        assert metadata["core_tool"] is True
        assert metadata["parameters"][0]["description"] == "query help"
        assert metadata["parameters"][0]["required"] is True
    assert metadata["description"] == expected
    assert "brief_description" not in metadata
    assert "detailed_description" not in metadata
    assert fields == original
