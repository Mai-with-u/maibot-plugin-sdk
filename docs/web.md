# 联网搜索与网页读取

SDK 2.17.0 的 `ctx.web` 提供异步搜索和网页读取，需要包含 `web.search` / `web.fetch` 能力实现的 Host。
插件使用前，在 WebUI「模型设置 → 功能分配 → 联网搜索」选择已经配置的服务。
插件复用该服务的协议、密钥和超时配置；仅添加服务而未进行功能分配时，调用会报错。

在 `_manifest.json` 中按需声明：

```json
"capabilities": ["web.search", "web.fetch"]
```

```python
search = await self.ctx.web.search("Python asyncio 文档", max_results=3)
for hit in search["results"]:
    self.ctx.logger.info("%s %s", hit["title"], hit["url"])

if search["results"]:
    page = await self.ctx.web.fetch(search["results"][0]["url"])
    text = page["content"]
```

## 搜索

`await ctx.web.search(query: str, *, max_results: int = 5)` 返回字典：

- `query`：去除首尾空白后的查询。
- `results`：列表，每项有 `title`、`url`、`snippet`、`summary`、`published_at`（可能为 `None`）。摘要不等同于网页全文。
- `content_kind`：`search_results`。
- `service`：Host 使用的服务名称，不包含配置和密钥。
- `retrieved_at`：UTC ISO 8601 获取时间。

查询不能为空，最长 1000 字符，DeepSeek 限制为 128 字符。`max_results` 必须是 1～20 的整数，AnySearch 上限为 10。
成功但无匹配项时返回空 `results`；调用失败会抛出异常。

## 网页读取

`await ctx.web.fetch(url: str)` 返回字典，包含 `url`、`title`、`content`、`content_kind="page_text"`、`service` 和 `retrieved_at`。
URL 最长 8192 字符，只接受无嵌入用户名和密码的 HTTP(S) 地址。
`content` 是联网服务提取的完整正文，可能是 Markdown；此接口不提供原始 HTML、任意 HTTP 请求或文件下载。

两个接口均支持当前统一联网服务的 DeepSeek、Tavily、AnySearch、Exa、Firecrawl 和 StepSearch MCP。
调用无需聊天 ID，不创建会话，不写入聊天工具结果缓存，也不返回 `result_id`。
结果序列化后超过 500000 字符会明确报错，不会静默截断。
服务调用遵循 Host 配置的超时（最多 300 秒），SDK 的 RPC 时限为 310 秒；调用所在组件若设置了更短时限，仍受该组件时限约束。
未授权、未启用、参数无效、网络失败和超时都会向插件抛出异常。插件应按自身业务处理错误，不应把错误当作空结果。

网页内容属于外部资料；传给模型时应标明来源，不应把网页中的文字当作系统或插件指令执行。
