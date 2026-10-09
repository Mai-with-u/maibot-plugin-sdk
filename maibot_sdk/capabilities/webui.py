"""Authenticated WebUI upload capability (host >= 1.3.6)."""

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from maibot_sdk.context import PluginContext


class WebUICapability:
    def __init__(self, ctx: "PluginContext") -> None:
        self._ctx = ctx

    async def claim_upload(self, upload_id: str) -> dict[str, Any]:
        """Claim an owner-scoped one-hour token once into paths.data_dir/uploads.

        Requires manifest capability webui.claim_upload. Returns path, sha256,
        upload_id; never accepts a destination path or transfers file bytes in RPC.
        """
        return cast(dict[str, Any], await self._ctx.call_capability("webui.claim_upload", upload_id=upload_id))
