# WebUI 文件上传（SDK 2.11.0 / 宿主 1.3.6）

使用上传领取接口需要 SDK 2.11.0 及支持 `file_upload_v1` 的宿主（MaiBot 1.3.6）。插件 manifest 应声明自身最低版本；本地开发时可以使用宿主的 `MAIBOT_PLUGIN_SDK_PATH` 指向 SDK 仓库。

插件 manifest 声明 `webui.claim_upload`。webui.json 的 `required_capabilities` 声明 `["file_upload_v1"]`，`upload` 组件绑定本页面的 action；该 action 对应的静态 API 必须接收必填字符串 `upload_id`，不能使用 confirmation。其他表单参数依然适用原声明校验。

```python
@API("receive_image", version="1")
async def receive_image(self, upload_id: str):
    upload = await self.ctx.webui.claim_upload(upload_id)
    # upload = {path, sha256, upload_id}，path 位于本插件 data_dir/uploads。
    # 转存到自己的数据目录并执行业务校验；原始文件字节不经 JSON/RPC。
    return {"received": True}
```

宿主先验证管理员 WebUI 会话和上传操作归属，再接受 multipart 文件。凭证归属于目标插件，一小时有效，只能领取一次；API 无法指定领取到别的插件或任意路径。SDK 不自动标注、训练或转存文件。

首版仅 JPEG、PNG、静态 WebP，每文件20MiB、解码4000万像素；压缩包和动画拒绝。文件扩展名根据真实解码格式生成，客户端文件名不用于存储路径。失败需显示具体信息；凭证过期或重复领取返回错误，不自动重试有副作用的操作。

插件长任务必须立即返回任务编号，查询进度；页面可用 `poll_interval_seconds: 5` 轮询只读 queries。0关闭，启用时3至60秒，现有声明无需新增字段。分页与缩略图仍受宿主512KiB响应限制。
