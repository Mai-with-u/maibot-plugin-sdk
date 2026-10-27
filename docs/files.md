# 聊天文件能力

SDK 2.17.0 提供 `ctx.files`，需要包含独立文件服务的 Host。文件服务不依赖沙盒。文件数据通过限时 HTTP 通道传输，RPC 中只传元数据和 `file_ref`。

## 权限

主程序的「能力 → 文件功能」默认关闭，需管理员启用 `capabilities.files` 后才能调用。关闭后拒绝新的文件操作；已预留上传的取消清理仍然允许。

在插件 manifest 的 `capabilities` 中按需声明：

```json
["files.list", "files.read_text", "files.download", "files.upload", "files.send"]
```

调用必须发生在 Host 派发的工具调用期间。Host 为该插件和当前真实聊天签发临时作用域，Runner 自动附加，插件不需要也不能传 `session_id` 选择其他聊天。调用结束、取消或权限过期后，作用域失效；普通 API、启动回调和后台任务不能使用这些能力。不要把本次执行的协程留到工具返回以后继续传文件。

## 接口

| 方法 | 结果 |
| --- | --- |
| `await ctx.files.list(offset=0)` | 当前聊天附件元数据，每页 50 条，不自动下载 |
| `await ctx.files.read_text(file_ref, offset=0, limit=12000, encoding="utf-8-sig")` | 按字符分页的 TXT/Markdown/CSV/JSON 内容，必要时下载 |
| `await ctx.files.download(file_ref, Path(...))` | 独占创建本地目标文件，校验大小和 SHA-256，返回元数据 |
| `await ctx.files.upload(Path(...), name="", mime_type="application/octet-stream")` | 上传本地文件为当前聊天原件，返回 `file_ref` 等元数据 |
| `await ctx.files.send(file_ref)` | 发送到当前聊天，返回 `status`、`message_id` |

文本返回 `text`、`offset`、`next_offset`、`total_characters`、`untrusted_content`，每次最多 32000 字符。支持 UTF-8、带 BOM 的 UTF-16 和显式 GB18030；不执行文件内容。文件原文属于不可信输入，不应解释为系统或工具指令。

`send` 返回 `sent` 表示取得成功回执；`unknown` 表示结果不确定，平台仍可能随后投递，不能自动重试。SDK 不提供跨聊天转发，只有 WebUI 管理员能够明确授权。

```python
from pathlib import Path

# 在已有 @Tool 方法内部；chat_id 等上下文字段仍按原工具签名接收。
items = await self.ctx.files.list()
if items:
    page = await self.ctx.files.read_text(items[0]["file_ref"])
    text = page["text"]

# 将插件已生成的文件交给当前聊天。Host 不会自行读取这个本地路径。
asset = await self.ctx.files.upload(Path(self.ctx.paths.data_dir) / "report.csv")
result = await self.ctx.files.send(asset["file_ref"])
```

上传和下载失败会抛异常，下载的部分文件会删除，不覆盖已有目标。上传失败会请求释放尚未开始的预留；HTTP 已开始的传输由 Host 在失败、取消或超时后清理。默认单文件 50 MiB、总存储 10 GiB、文本解析 8 MiB；这些上限由管理员配置。原件保留到手动删除，平台下载缓存按最后访问时间保留 30 天。

文件字节由主程序公共 HTTP 服务传输，不需要启用 WebUI；监听地址由主程序的 `http.host` / `http.port` 配置。QQ 客户端异机部署时设置 `files.transfer_base_url` 为客户端可访问的后端地址；下载私网平台文件地址需要管理员配置精确的 `trusted_download_origins`。不要保存或传播限时传输 URL，将 `file_ref` 用作长期引用。
