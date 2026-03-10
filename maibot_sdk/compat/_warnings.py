"""兼容层警告: 首次导入横幅"""

import logging
import warnings

_logger = logging.getLogger("maibot_sdk.compat")

_banner_shown = False

_BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║         ⚠️  旧版插件系统兼容层已激活 (DEPRECATED)  ⚠️            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  检测到插件正在使用旧版 src.plugin_system 接口。                 ║
║  旧版插件系统已被新版 IPC 隔离插件系统 (maibot_sdk) 替代。      ║
║                                                                  ║
║  当前通过兼容层运行，功能可能受限。                             ║
║  请尽快将插件迁移到新版 SDK：                                   ║
║    - 继承 MaiBotPlugin 替代 BasePlugin                          ║
║    - 使用 @Action/@Command/@Tool/@EventHandler 装饰器           ║
║    - 通过 self.ctx.<capability> 访问能力代理                    ║
║                                                                  ║
║  兼容层将在未来版本中移除！                                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""


def show_banner_once() -> None:
    """显示首次导入警告横幅（仅显示一次）"""
    global _banner_shown
    if not _banner_shown:
        _banner_shown = True
        _logger.warning(_BANNER)
        warnings.warn(
            "旧版插件系统 (src.plugin_system) 已弃用，请迁移到新版 maibot_sdk。"
            "此兼容层将在未来版本中移除。",
            DeprecationWarning,
            stacklevel=3,
        )
