"""旧版插件适配器

将旧版 BasePlugin 子类包装为新版 MaiBotPlugin 兼容接口，
使 Runner 可以统一管理新旧插件。
"""

import logging
import warnings
from typing import Any

from maibot_sdk.compat import _context_holder
from maibot_sdk.compat.base.base_plugin import BasePlugin
from maibot_sdk.types import normalize_component_type_name

logger = logging.getLogger("maibot_sdk.compat.legacy_adapter")


def _load_global_config_snapshot() -> dict[str, Any] | None:
    """尽力读取当前主程序全局配置的 dict 快照。"""
    try:
        from src.config.config import global_config

        dumped = global_config.model_dump()
        if isinstance(dumped, dict):
            return dumped
    except Exception:
        return None
    return None


class LegacyPluginAdapter:
    """将旧版 BasePlugin 包装为类 MaiBotPlugin 接口

    Runner 在检测到旧版插件后创建此适配器，使其与新版 SDK
    生命周期（on_load / on_unload / get_components / 组件调用）兼容。
    """

    def __init__(self, legacy_plugin: BasePlugin):
        warnings.warn(
            f"LegacyPluginAdapter({legacy_plugin.__class__.__name__}) — 请迁移到 MaiBotPlugin",
            DeprecationWarning,
            stacklevel=2,
        )
        self._legacy = legacy_plugin
        self._ctx = None
        self._plugin_config: dict[str, Any] = {}
        self._component_instances: dict[str, Any] = {}
        self._component_map: dict[str, dict[str, Any]] = {}

    def _set_context(self, ctx: Any) -> None:
        """由 Runner 注入上下文，同时注册到全局上下文持有者"""
        self._ctx = ctx
        # 将上下文注入到全局持有者，使旧版基类方法和 API 桩能访问
        _context_holder.set_context(ctx)
        self._sync_config_cache()

    def _sync_config_cache(self) -> None:
        """同步旧版 config_api 所需的全局/插件配置缓存。"""
        try:
            from maibot_sdk.compat.apis import config_api

            config_api.set_config_cache(
                global_cfg=_load_global_config_snapshot(),
                plugin_cfg=self._plugin_config,
            )
        except Exception:
            pass

    def set_plugin_config(self, config: dict[str, Any]) -> None:
        """由 Runner 设置插件配置，并同步到 config_api 缓存"""
        self._plugin_config = config or {}
        self._sync_config_cache()

    async def on_load(self) -> None:
        """调用旧版插件的 on_load"""
        try:
            from maibot_sdk.compat.apis import component_manage_api

            await component_manage_api.async_get_all_plugins()
        except Exception:
            pass

        if hasattr(self._legacy, "on_load"):
            await self._legacy.on_load()

    async def on_unload(self) -> None:
        """调用旧版插件的 on_unload"""
        if hasattr(self._legacy, "on_unload"):
            await self._legacy.on_unload()

    async def on_config_update(self, new_config: dict[str, Any], version: str) -> None:
        self.set_plugin_config(new_config)
        if hasattr(self._legacy, "on_config_update"):
            ret = self._legacy.on_config_update(new_config, version)
            if hasattr(ret, "__await__"):
                await ret

    def get_components(self) -> list[dict[str, Any]]:
        """将 get_plugin_components() 的结果转换为新版组件描述格式"""
        result: list[dict[str, Any]] = []

        try:
            components = self._legacy.get_plugin_components()
        except Exception as e:
            logger.error(f"旧版插件 get_plugin_components() 失败: {e}")
            return result

        for comp_info, comp_cls in components:
            if not comp_info.enabled:
                continue

            try:
                instance = comp_cls()
            except Exception as e:
                logger.error(f"创建组件 {comp_info.name} 实例失败: {e}")
                continue

            self._component_instances[comp_info.name] = instance
            converted = self._convert_component(comp_info, instance)
            if converted:
                self._component_map[comp_info.name] = converted
                result.append(converted)

        return result

    def _convert_component(self, comp_info: Any, instance: Any) -> dict[str, Any] | None:
        """将旧版 ComponentInfo + 实例转为新版组件描述 dict

        使用 comp_info.component_type 的字符串值判断组件类型，不依赖 isinstance 或枚举身份，
        因为 import hook 在 Python 3.13 中可能导致同一枚举/基类产生不同对象标识。
        """
        ctype = str(comp_info.component_type)

        if ctype == "action":
            component_type = normalize_component_type_name(ctype)
            return {
                "type": component_type,
                "name": comp_info.name,
                "description": comp_info.description or getattr(instance, "action_description", ""),
                "metadata": {
                    "activation_type": str(getattr(instance, "activation_type", "always")),
                    "action_parameters": getattr(instance, "action_parameters", {}),
                    "parallel_action": getattr(instance, "parallel_action", False),
                    "legacy": True,
                },
            }
        elif ctype == "command":
            component_type = normalize_component_type_name(ctype)
            return {
                "type": component_type,
                "name": comp_info.name,
                "description": comp_info.description or getattr(instance, "command_description", ""),
                "metadata": {
                    "command_pattern": getattr(instance, "command_pattern", ""),
                    "legacy": True,
                },
            }
        elif ctype == "tool":
            component_type = normalize_component_type_name(ctype)
            return {
                "type": component_type,
                "name": comp_info.name,
                "description": comp_info.description or getattr(instance, "description", ""),
                "metadata": {
                    "parameters": self._convert_tool_params(instance),
                    "legacy": True,
                },
            }
        elif ctype == "event_handler":
            component_type = normalize_component_type_name(ctype)
            return {
                "type": component_type,
                "name": comp_info.name,
                "description": comp_info.description or getattr(instance, "handler_description", ""),
                "metadata": {
                    "event_type": str(getattr(instance, "event_type", "on_message")),
                    "weight": getattr(instance, "weight", 0),
                    "intercept_message": getattr(instance, "intercept_message", False),
                    "legacy": True,
                },
            }
        else:
            logger.warning(f"未知组件类型 {ctype} ({comp_info.name})，跳过")
            return None

    @staticmethod
    def _convert_tool_params(tool: Any) -> list[dict[str, Any]]:
        """将旧版 Tool 参数元组列表转为 dict 列表"""
        params: list[dict[str, Any]] = []
        for p in getattr(tool, "parameters", []):
            if isinstance(p, (list, tuple)) and len(p) >= 3:
                params.append(
                    {
                        "name": p[0],
                        "type": str(p[1]),
                        "description": p[2],
                        "required": p[3] if len(p) > 3 else False,
                    }
                )
        return params

    # ── 组件调用桥接 ──────────────────────────────────────────

    async def invoke_component(self, component_name: str, **kwargs: Any) -> Any:
        """统一的组件调用入口，由 Runner 调用

        使用 component_map 中记录的组件类型判断，不依赖 isinstance，
        因为 import hook 在 Python 3.13 中可能产生类标识不一致。
        在执行期间激活当前插件的上下文，确保 API 桩获取正确的 PluginContext。
        """
        instance = self._component_instances.get(component_name)
        if instance is None:
            raise KeyError(f"未找到组件: {component_name}")

        # 激活当前插件上下文，使 get_context() 在整个调用链中返回正确的上下文
        plugin_id = self._ctx.plugin_id if self._ctx else ""
        token = _context_holder.activate_plugin(plugin_id)
        try:
            return await self._invoke_component_inner(component_name, instance, **kwargs)
        finally:
            _context_holder.deactivate_plugin(token)

    async def _invoke_component_inner(self, component_name: str, instance: Any, **kwargs: Any) -> Any:
        """实际的组件调用逻辑。"""

        comp_desc = self._component_map.get(component_name, {})
        try:
            comp_type = normalize_component_type_name(comp_desc.get("type", ""))
        except ValueError:
            comp_type = str(comp_desc.get("type", ""))

        stream_id = kwargs.get("stream_id", "")
        plugin_config = kwargs.get("plugin_config", self._plugin_config)

        if comp_type == "ACTION":
            # 对 Action 注入完整的运行时属性
            instance.action_data = kwargs.get("action_data", getattr(instance, "action_data", {}))
            instance.action_reasoning = kwargs.get("action_reasoning", getattr(instance, "action_reasoning", ""))
            instance.cycle_timers = kwargs.get("cycle_timers", getattr(instance, "cycle_timers", {}))
            instance.thinking_id = kwargs.get("thinking_id", getattr(instance, "thinking_id", ""))
            instance.chat_stream = kwargs.get("chat_stream", getattr(instance, "chat_stream", None))
            instance.plugin_config = plugin_config
            instance.action_message = kwargs.get("action_message", getattr(instance, "action_message", None))
            instance._stream_id = stream_id
            for attr in (
                "chat_id",
                "user_id",
                "message",
                "message_id",
                "platform",
                "group_id",
                "group_name",
                "user_nickname",
                "is_group",
                "target_id",
            ):
                if attr in kwargs:
                    setattr(instance, attr, kwargs[attr])
            return await instance.execute()

        elif comp_type == "COMMAND":
            if "message" in kwargs:
                instance.message = kwargs["message"]
            instance.plugin_config = plugin_config
            instance._stream_id = stream_id
            if "matched_groups" in kwargs and hasattr(instance, "set_matched_groups"):
                instance.set_matched_groups(kwargs["matched_groups"])
            return await instance.execute()

        elif comp_type == "EVENT_HANDLER":
            if hasattr(instance, "set_plugin_config"):
                instance.set_plugin_config(plugin_config)
            if hasattr(instance, "set_plugin_name"):
                instance.set_plugin_name(kwargs.get("plugin_name", self._legacy.__class__.__name__))
            return await instance.execute(kwargs.get("message"))

        elif comp_type == "TOOL":
            instance.plugin_config = plugin_config
            if "chat_stream" in kwargs:
                instance.chat_stream = kwargs["chat_stream"]
            return await instance.execute(kwargs.get("function_args", {}))

        else:
            logger.warning(f"未知组件类型: {type(instance).__name__}")
            return await instance.execute()
