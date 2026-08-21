# MaiBot WebUI Vite + Vue 3 示例

这个示例展示如何使用 Vite 和 Vue 3 构建 MaiBot 插件页面。构建结果是 Host
约定的单个 ESM 入口：`webui/dist/index.js`。

## 使用方式

```bash
npm install
npm run build
```

将生成的 `webui/` 目录复制到插件根目录，并在 `_manifest.json` 中声明：

```json
{
  "extensions": {
    "webui_pages": [
      {
        "id": "hello",
        "title": "Hello World",
        "route": "hello",
        "entry": "webui/dist/index.js",
        "component": "mount",
        "permissions": ["webui.page:view"],
        "api": {"greet": "webui.hello.greet"}
      }
    ]
  }
}
```

页面入口通过 `mount(container, context)` 导出。请把 `webui.d.ts` 复制到插件前端
项目，或通过 TypeScript 的 `typeRoots`/路径引用它，以获得 `context.request` 的类型提示。
构建产物不要包含开发服务器地址、密钥或 Host 内部模块。
