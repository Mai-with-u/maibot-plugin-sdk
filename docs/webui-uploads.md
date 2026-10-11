# WebUI 图片上传

HTML 页面通过 `maibot.upload()` 接收图片，Python API 通过 `ctx.webui.claim_upload()` 一次性领取。Host 负责登录、归属、格式、大小和配额校验；插件负责业务校验及领取后的文件管理。

本文对应 `schema_version: 2` 的开发中协议，需要配套的主程序与 dashboard。SDK 领取接口要求 2.11.0+；本地联调可用 `MAIBOT_PLUGIN_SDK_PATH` 指向 SDK 源码。两种页面的完整规范见[WebUI 页面开发文档](https://docs.mai-mai.org/plugin/webui-pages)。

## 声明页面与能力

插件 `_manifest.json` 的 capabilities 包含 `webui.claim_upload`，在已有权限列表中加入即可。`webui.json` 中声明 `custom_pages` 和 `image_upload`；这两个标识用于页面功能兼容校验，不代替 manifest 授权。

```json
{
  "schema_version": 2,
  "required_capabilities": ["custom_pages", "image_upload"],
  "pages": [{
    "id": "images",
    "title": "图片管理",
    "mode": "custom",
    "entry": "webui/index.html",
    "layout": "document",
    "actions": {
      "receive": {
        "api": "receive_image",
        "parameters": {
          "upload_id": {"type": "string", "required": true},
          "label": {"type": "string"}
        },
        "confirmation": "确认接收这张图片？"
      }
    },
    "uploads": {"library": {"action": "receive", "image_max_edge": 4000}}
  }]
}
```

`library` 是上传别名，Host 根据声明解析到 receive action，再调用当前插件的 receive_image 静态 API。upload_id 由 Host 注入，不能由页面传入；其他参数按 binding 校验。confirmation 可省略，声明后由宿主确认，确认前复制参数，取消后不发送文件。

## 浏览器调用

HTML 页面选择文件后调用；进度回调表示浏览器上传进度，完成业务处理以 Promise 返回为准：

```javascript
await maibot.ready;
const controller = new AbortController();
try {
  const result = await maibot.upload('library', file, {label: 'sample'}, {
    signal: controller.signal,
    onProgress: percent => console.log(percent),
  });
  console.log(result);
} catch (error) {
  console.error(error.message);
}
// 将取消按钮的点击事件绑定到 controller.abort()。
```

调用经过登录后的 multipart POST `/api/webui/plugins/runtime/webui/{plugin}/{page}/uploads/{alias}`。字段是 file、args(JSON) 和 confirmed。SDK 在隔离 iframe 内读取所选文件并传递内存副本；原始文件字节不经 JSON/RPC。多选、预览、队列和重试策略由 HTML 页实现。

## Python 领取

将方法放入已实现生命周期的 `MaiBotPlugin` 子类：

```python
from maibot_sdk import API


@API("receive_image", version="1")
async def receive_image(self, upload_id: str, label: str = ""):
    upload = await self.ctx.webui.claim_upload(upload_id)
    # upload = {path, sha256, upload_id}，path 位于本插件 data_dir/uploads。
    # 在此执行业务校验、持久保存或删除；阻塞处理放进工作线程。
    return {"received": True, "label": label}
```

领取结果直接包含 path、sha256、upload_id，不需要再次从 upload 子字段解包。凭证绑定本插件，一小时有效且只能领取一次；不存在、过期或重复领取会抛错。API 无法指定其他插件或任意目标路径。SDK 不负责标注、训练、去重或批量操作。

WebUI 网关不解释 result 中的 success、message 或 navigate_page。API 失败用异常表达，业务结果由 HTML 解释，页面跳转调用 maibot.navigate。长任务立即返回任务 ID，由 HTML 自行 query 进度；预置页面的 poll_interval_seconds 不用于 HTML。

## 限制与清理

- 静态 JPEG/PNG/WebP，单文件最多 20 MiB、解码最多 4000 万像素；拒绝动画和压缩包。扩展名来自实际格式，客户端文件名不参与存储路径。
- image_max_edge 声明后，浏览器可接收最多 64 MiB / 1 亿像素的源文件并缩放为上传副本，必要时转 JPEG 压缩；未声明时源文件最多 20 MiB。原文件不变，处理后的文件仍需满足服务端 20 MiB / 4000 万像素限制。
- 上传在 multipart 解析前验证登录与绑定，从接收、解码、暂存到 API 调用占用配额：单插件最多 2 个、全局最多 4 个，超额立即返回 429，不排队。
- 请求预算 120 秒，SDK 上传等待最多 150 秒。取消时若工作线程仍在解码/写盘，会等工作结束再释放配额。取消与超时不回滚已接收文件或已提交业务操作。
- 未领取图片单插件最多 8 张、全局最多 32 张，对应最多 160 / 640 MiB。超过返回 429；凭证一小时过期，每分钟及新暂存时清理。领取后的文件由插件管理。

## 简单预览与页面选择

预置页面可用单张 image 组件：

```json
{
  "type": "image",
  "label": "图片预览",
  "value": {"source": "pictures", "field": "thumbnail"}
}
```

thumbnail 是 query 返回的 JPEG/PNG/WebP base64 data URL，最多 24000 字符；null 表示无图。查询结果整体最多 512 KiB，不接受文件路径、远程图片 URL 或 SVG。日志可用 `text.format: "log"`，显示只读滚动文本框并沿用宿主输入主题。

图库、循环、多选、批量操作和上传控件使用 HTML 自行实现。预置模式保留基础展示、标量表单和表格单行详情。只有 Host / dashboard 提供页面校验及渲染，SDK 不提供独立 WebUINode 模型。

## 迁移与排错

v1 声明需要按[迁移步骤](https://docs.mai-mai.org/plugin/webui-pages#声明迁移)更新。将 file_upload 改为 image_upload、移除 interactive_controls，把旧 upload/gallery/repeat/multi_select 等组件迁到 HTML；button.detail、select.presentation、动态 button.value 与 clear_selection 不再有效。navigate_page/navigate_params 返回值不再触发跳转。

- 页面不注册：检查 schema_version: 2、所需能力、entry，以及是否仍有旧组件字段。主程序与 dashboard 必须配套更新。
- 领取接口不存在：检查 SDK 是否包含 ctx.webui.claim_upload()；本地 SDK 路径需要在 Host 启动前设置。
- 领取被拒：检查 manifest 能力与凭证归属、有效期和是否已经领取；不要自动重试有副作用的操作。
- 上传返回 429：检查正在执行的请求和未领取图片数量；领取文件或等待过期回收后再操作。
