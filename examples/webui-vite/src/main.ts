import { createApp } from 'vue'

import App from './App.vue'

import type { PluginPageCleanup, PluginWebuiContext } from '../../../webui'

/** MaiBot Host 加载的页面入口。 */
export function mount(container: HTMLElement, context: PluginWebuiContext): PluginPageCleanup {
  const app = createApp(App, { context })
  app.mount(container)
  return () => app.unmount()
}

// 开发预览时提供一个最小上下文；正式产物由 Host 调用 mount，不会执行这里。
if (import.meta.env.DEV) {
  const container = document.querySelector<HTMLElement>('#app')
  if (container) {
    createApp(App).mount(container)
  }
}
