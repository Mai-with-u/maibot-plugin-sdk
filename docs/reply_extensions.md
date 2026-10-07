# 回复扩展（SDK 2.10.0）

需要支持 `REPLY_EXTENSION` 的 MaiBot 主程序（1.3.5 开发版本）和 `maibot-plugin-sdk>=2.10.0`。插件只依赖 SDK，无需导入主程序或修改 Planner Hook。

`@ReplyExtension(name, description, parameters, priority=0, timeout_ms=60000, **metadata)`
注册一个组件。`parameters` 与 Tool 相同，支持 `ToolParameterInfo` 列表、属性字典或完整 object JSON Schema。主程序校验类型、必填项、枚举和默认值；不支持 `$ref`/`$dynamicRef`，请内联声明。未知顶层参数默认拒绝。默认值只在模型选择本扩展时补齐，不会自动启用插件。

`chat_scope="group"/"private"/"all"`、`allowed_session=[...]` 和组件启用开关沿用通用组件机制。停用、卸载后参数从后续 reply 声明中移除；正在生成的回复如果其扩展被卸载或重载，会明确失败。多个扩展按 priority 从小到大、完整名称字典序依次处理，上一个扩展输出交给下一个。

模型的具体调用参数（假设插件 ID 为 `voice_plugin`，组件名为 `voice`）：

```json
{
  "msg_id": "m123",
  "set_quote": true,
  "plugin_options": {
    "voice_plugin.voice": {"attach_voice": true, "keep_text": false}
  }
}
```

省略 `voice_plugin.voice` 时不会调用该插件；两个插件的同名参数不会冲突。模型参数属于 Planner 的 reply 工具，Replyer 根据这些参数生成正文。

处理器每次收到这些关键字参数：

| 参数 | 含义 |
| --- | --- |
| phase | `prepare`（生成前）或 `before_send`（后处理和附件完成后、任何消息发送前） |
| reply_id | 主程序为本次回复生成的唯一 ID，两个阶段相同；并发回复各自独立 |
| call_id | 原始 reply 工具调用 ID |
| session_id / reply_message_id | 聊天流 ID / 目标消息 ID |
| chat | platform、is_group_chat、group_id、user_id、session_id、stream_id |
| parameters | 仅本扩展的参数，已经校验和补默认值 |
| text | `prepare` 时为空；`before_send` 时为生成、Hook 处理后的完整正文 |
| messages | `prepare` 时为空；`before_send` 时为整组待发送消息 |

`prepare` 返回 `{"extra_prompt": "额外要求"}` 或 `{}`。主程序把要求交给 Replyer，并在生成 Hook 的 extra_prompt 中提供。`before_send` 返回 `{"messages": [...]}` 或 `{}`（保留原样）。不得直接调用 Send 代理替主程序发这组回复；主程序负责发送、记录历史、监控和失败判断。空消息组、无效返回值、插件报错和超时均使本次 reply 失败，发送前失败不会发送任何消息。

每条消息格式：`{"segments": [...], "quote_previous": false}`。顺序就是发送顺序；第一条消息沿用 reply 的 set_quote，后续消息 quote_previous=true 时引用前一条。插件修改文字时应保留无关图片、@、表情段和 quote_previous，避免丢失原始附件。多插件按顺序转换整组消息，不会分别对每个文字片段调用。

消息段沿用 SDK Send 字典协议：text、image、emoji、voice、at、reply、file、forward、dict。语音使用 `{"type":"voice","data":"语音内容描述","binary_data_base64":"..."}`，必须携带有效非空 Base64 音频；新图片、表情也应携带 Base64，原有图片/表情可保留 hash。自定义卡片使用 `{"type":"dict","data":{"type":"json","data":...}}`；具体卡片和音频格式取决于消息适配器。音频合成由插件自行完成，SDK 不内置 TTS。

## 语音示例

把下列方法放进自己的 `MaiBotPlugin` 子类，`self.synthesize_voice(text)` 是插件提供的异步 TTS 方法，返回适配器支持的音频 bytes。

```python
import base64
from maibot_sdk import ReplyExtension

@ReplyExtension(
    "voice",
    description="需要语音回复时启用，可选择同时保留文字",
    parameters={
        "attach_voice": {"type": "boolean", "default": False, "description": "是否合成语音"},
        "keep_text": {"type": "boolean", "default": True, "description": "是否同时发送文字"},
    },
    timeout_ms=60000,
)
async def reply_voice(self, *, phase, parameters, text, messages, **context):
    if not parameters["attach_voice"]:
        return {}
    if phase == "prepare":
        return {"extra_prompt": "这次回复会转成语音，请使用适合朗读的自然口语。"}
    audio = await self.synthesize_voice(text)
    result = []
    for message in messages:
        segments = [
            segment for segment in message["segments"]
            if parameters["keep_text"] or segment["type"] != "text"
        ]
        if segments:
            result.append({"segments": segments, "quote_previous": message["quote_previous"]})
    # 仅合成一次完整正文；附件原有顺序保持不变。
    voice = {
        "segments": [{
            "type": "voice", "data": text,
            "binary_data_base64": base64.b64encode(audio).decode("ascii"),
        }],
        "quote_previous": False,
    }
    result.append(voice)
    return {"messages": result}
```

本地联调可设置 `MAIBOT_PLUGIN_SDK_PATH` 为本 SDK 仓库目录；重新启动插件 Runner 后会加载本地 SDK。使用回复扩展的正式插件应在依赖声明中指定 `maibot-plugin-sdk>=2.10.0`。
