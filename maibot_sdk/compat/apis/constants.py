"""旧版 constants 兼容层

复刻旧版 src.plugin_system.apis.constants 的路径常量。
"""

from dataclasses import dataclass
from pathlib import Path

# 从 SDK 包的位置反推项目根目录
_SDK_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
# 如果 SDK 是作为子目录 (packages/maibot-plugin-sdk) 安装的，向上找 pyproject.toml
_PROJECT_ROOT = _SDK_DIR
for _candidate in [_SDK_DIR, _SDK_DIR.parent, _SDK_DIR.parent.parent]:
    if (_candidate / "pyproject.toml").exists():
        _PROJECT_ROOT = _candidate
        break


@dataclass(frozen=True)
class _SystemConstants:
    PROJECT_ROOT: Path = _PROJECT_ROOT
    CONFIG_DIR: Path = _PROJECT_ROOT / "config"
    BOT_CONFIG_PATH: Path = (_PROJECT_ROOT / "config" / "bot_config.toml").resolve()
    MODEL_CONFIG_PATH: Path = (_PROJECT_ROOT / "config" / "model_config.toml").resolve()
    PLUGINS_DIR: Path = (_PROJECT_ROOT / "plugins").resolve()
    INTERNAL_PLUGINS_DIR: Path = (_PROJECT_ROOT / "src" / "plugins").resolve()


_system_constants = _SystemConstants()

PROJECT_ROOT: Path = _system_constants.PROJECT_ROOT
CONFIG_DIR: Path = _system_constants.CONFIG_DIR
BOT_CONFIG_PATH: Path = _system_constants.BOT_CONFIG_PATH
MODEL_CONFIG_PATH: Path = _system_constants.MODEL_CONFIG_PATH
PLUGINS_DIR: Path = _system_constants.PLUGINS_DIR
INTERNAL_PLUGINS_DIR: Path = _system_constants.INTERNAL_PLUGINS_DIR
