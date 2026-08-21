"""插件 WebUI 页面声明模型测试。"""

import pytest
from pydantic import ValidationError

from maibot_sdk import WEBUI_PAGE_VIEW_PERMISSION, WebUiExtensionsInfo, WebUiPageInfo


def test_webui_page_view_permission_constant_matches_manifest_protocol() -> None:
    """SDK 应提供页面查看权限的稳定常量，避免插件作者手写字符串。"""

    assert WEBUI_PAGE_VIEW_PERMISSION == "webui.page:view"


def test_webui_page_info_matches_manifest_contract() -> None:
    """页面模型应生成 Host 可直接消费的 Manifest 页面数据。"""

    page = WebUiPageInfo(
        id="hello",
        title="Hello World 页面",
        route="hello",
        entry="webui/dist/index.js",
        icon="puzzle",
        order=120,
        permissions=["webui.page:view", "webui.page:view"],
        api={"greet": "webui.hello.greet"},
    )

    assert page.permissions == ["webui.page:view"]
    assert page.to_manifest() == {
        "id": "hello",
        "title": "Hello World 页面",
        "route": "hello",
        "entry": "webui/dist/index.js",
        "component": "mount",
        "icon": "puzzle",
        "order": 120,
        "permissions": ["webui.page:view"],
        "api": {"greet": "webui.hello.greet"},
    }


def test_webui_extensions_info_rejects_duplicate_page_ids() -> None:
    """同一插件不能声明重复页面 ID。"""

    page = {
        "id": "hello",
        "title": "Hello",
        "route": "hello",
        "entry": "webui/dist/index.js",
    }

    with pytest.raises(ValidationError, match="重复的 WebUI 页面 ID"):
        WebUiExtensionsInfo(webui_pages=[page, page])


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", "Hello"),
        ("route", "nested/route"),
        ("entry", "webui/index.js"),
        ("entry", "webui/dist/../index.js"),
        ("entry", "webui\\dist\\index.js"),
        ("component", "render"),
    ],
)
def test_webui_page_info_rejects_unsafe_values(field: str, value: str) -> None:
    """页面声明的路径、入口和导出名称应遵守 Host 安全边界。"""

    page = {
        "id": "hello",
        "title": "Hello",
        "route": "hello",
        "entry": "webui/dist/index.js",
    }
    page[field] = value

    with pytest.raises(ValidationError):
        WebUiPageInfo(**page)


def test_webui_extensions_info_to_manifest() -> None:
    """扩展模型应包装为 Manifest 的 extensions 结构。"""

    extensions = WebUiExtensionsInfo(
        webui_pages=[
            WebUiPageInfo(
                id="hello",
                title="Hello",
                route="hello",
                entry="webui/dist/index.mjs",
            )
        ]
    )

    assert extensions.to_manifest() == {
        "webui_pages": [
            {
                "id": "hello",
                "title": "Hello",
                "route": "hello",
                "entry": "webui/dist/index.mjs",
                "component": "mount",
                "order": 0,
                "permissions": [],
                "api": {},
            }
        ]
    }
