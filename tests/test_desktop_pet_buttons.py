import pytest

from maibot_sdk import DesktopPetButton, DesktopPetButtonState, MaiBotPlugin
from maibot_sdk import PluginContext
from pydantic import ValidationError


@pytest.mark.asyncio
async def test_default_button_states_and_no_config_pollution():
    class Plugin(MaiBotPlugin):
        desktop_pet_buttons = [DesktopPetButton(id="volume", label="音量", icon="volume")]

    plugin = Plugin()
    assert await plugin.get_desktop_pet_button_states() == {"volume": DesktopPetButtonState()}
    assert plugin.get_default_config() == {}
    with pytest.raises(ValueError, match="未实现"):
        await plugin.on_desktop_pet_button_click("volume")


@pytest.mark.asyncio
async def test_dictionary_declarations_are_supported():
    class Plugin(MaiBotPlugin):
        desktop_pet_buttons = [{"id": "volume", "label": "音量"}]

    assert "volume" in await Plugin().get_desktop_pet_button_states()


def test_no_script_or_unknown_icon_in_declaration():
    with pytest.raises(ValidationError):
        DesktopPetButton(id="volume", label="音量", script="alert(1)")
    with pytest.raises(ValidationError):
        DesktopPetButton(id="volume", label="音量", icon="<svg>")


@pytest.mark.asyncio
async def test_refresh_buttons_routes_and_unwraps_status():
    calls = []
    async def rpc(method, plugin_id, payload, timeout_ms=None):
        calls.append((method, plugin_id, payload))
        return {"success": True, "result": {"ready": True}}
    context = PluginContext("test.buttons", rpc_call=rpc)
    assert await context.desktop_pet.refresh_buttons() == {"ready": True}
    assert calls == [("cap.call", "test.buttons", {"capability": "desktop_pet.refresh_buttons", "args": {}})]
