import pytest

from maibot_sdk import ReplyExtension
from maibot_sdk.components import collect_components
from maibot_sdk.types import ComponentType, ToolParameterInfo, ToolParamType


def test_reply_extension_collects_handler_schema_and_scope():
    class Plugin:
        @ReplyExtension(
            "voice", description="语音回复",
            parameters={"attach_voice": {"type": "boolean", "default": False}},
            priority=3, timeout_ms=1500, chat_scope="group", allowed_session=["chat"],
        )
        async def voice_reply(self, **kwargs):
            return {}

    component = collect_components(Plugin())[0]
    assert component["type"] == ComponentType.REPLY_EXTENSION.value
    metadata = component["metadata"]
    assert metadata["handler_name"] == "voice_reply"
    assert metadata["parameters_schema"]["properties"]["attach_voice"]["default"] is False
    assert metadata["parameters_schema"]["additionalProperties"] is False
    assert metadata["priority"] == 3
    assert metadata["timeout_ms"] == 1500
    assert component["chat_scope"] == "group"
    assert component["allowed_session"] == ["chat"]


def test_reply_extension_accepts_typed_parameters_and_no_parameters():
    class Plugin:
        @ReplyExtension("typed", parameters=[
            ToolParameterInfo(name="enabled", param_type=ToolParamType.BOOLEAN, description="开关"),
        ])
        async def typed(self, **kwargs):
            return {}

        @ReplyExtension("empty")
        async def empty(self, **kwargs):
            return {}

    components = {item["name"]: item for item in collect_components(Plugin())}
    assert components["empty"]["metadata"]["parameters_schema"]["properties"] == {}
    assert components["typed"]["metadata"]["parameters_schema"]["properties"]["enabled"]["type"] == "boolean"


def test_reply_extension_can_be_disabled_and_type_normalized():
    class Plugin:
        @ReplyExtension("disabled", enabled=False)
        async def disabled(self, **kwargs):
            return {}

    assert collect_components(Plugin())[0]["metadata"]["enabled"] is False
    assert ComponentType.from_value("reply_extension") == ComponentType.REPLY_EXTENSION


@pytest.mark.parametrize("parameters,error", [
    ({"type": "string"}, ValueError),
    ({"attach_voice": "bad schema"}, TypeError),
    (42, TypeError),
])
def test_reply_extension_rejects_malformed_declarations(parameters, error):
    with pytest.raises(error):
        ReplyExtension("bad", parameters=parameters)
