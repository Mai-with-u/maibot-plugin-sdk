/**
 * MaiBot 插件 WebUI 页面运行时契约。
 *
 * 页面入口由 Host 以同源 ESM 方式加载，插件只应依赖这里声明的上下文，
 * 不要直接访问 Host 的 React/Vue 实例或内部 API。
 */

export interface PluginPageRequestOptions {
  /** 页面 API 当前只接受 POST 请求。 */
  method?: 'POST'
  /** 发送给插件 @API 处理器的 JSON 请求体。 */
  body?: unknown
  /** 取消尚未完成的 Host 代理请求。 */
  signal?: AbortSignal
  /** 开启 Host 链路诊断；成功响应会附带 request_id。 */
  debug?: boolean
}

export interface PluginPageDebugResponse<T> {
  /** 插件 API 的业务数据。 */
  data: T
  /** Host 为本次跨层调用生成的链路标识。 */
  request_id: string
}

export interface PluginWebuiContext {
  readonly pluginId: string
  readonly pageId: string
  readonly hostVersion: string
  /** 当前页面 API 代理基址。 */
  readonly apiBase: string
  /** 当前插件静态资源基址。 */
  readonly assetsBase: string
  /** 通过 Manifest api 白名单调用插件后端 API。 */
  request<T = unknown>(
    operation: string,
    options?: Omit<PluginPageRequestOptions, 'debug'> & { debug?: false }
  ): Promise<T>
  /** 开启调试时返回业务数据和 Host 链路 request_id。 */
  request<T = unknown>(
    operation: string,
    options: Omit<PluginPageRequestOptions, 'debug'> & { debug: true }
  ): Promise<PluginPageDebugResponse<T>>
  /** 当 debug 值来自运行时变量时，返回值需要按实际选项判断。 */
  request<T = unknown>(
    operation: string,
    options?: PluginPageRequestOptions
  ): Promise<T | PluginPageDebugResponse<T>>
}

export type PluginPageCleanup = () => void

export type PluginPageMount = (
  container: HTMLElement,
  context: PluginWebuiContext,
) => void | PluginPageCleanup

export interface PluginPageModule {
  mount?: PluginPageMount
  [exportName: string]: unknown
}
