<script setup lang="ts">
import { ref } from 'vue'

import type { PluginWebuiContext } from '../../../webui'

const props = defineProps<{ context?: PluginWebuiContext }>()
const message = ref('')
const loading = ref(false)
const error = ref('')

async function greet(): Promise<void> {
  if (!props.context) {
    message.value = '请通过 MaiBot Host 加载页面后再调用 API。'
    return
  }

  loading.value = true
  error.value = ''
  try {
    const result = await props.context.request<{ message: string }>('greet', {
      body: { message: '来自 Vite + Vue 3' },
    })
    message.value = result.message
  } catch (requestError: unknown) {
    error.value = requestError instanceof Error ? requestError.message : String(requestError)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="page">
    <p class="eyebrow">MaiBot WebUI 插件示例</p>
    <h1>Hello World</h1>
    <p>这是一个可直接构建到 <code>webui/dist/index.js</code> 的 Vue 3 页面。</p>
    <button type="button" :disabled="loading" @click="greet">
      {{ loading ? '请求中…' : '调用插件 API' }}
    </button>
    <p v-if="message" class="result">{{ message }}</p>
    <p v-if="error" class="error">{{ error }}</p>
  </main>
</template>

<style scoped>
.page {
  max-width: 42rem;
  margin: 0 auto;
  padding: 2rem;
  font-family: system-ui, sans-serif;
}

.eyebrow {
  color: #64748b;
  font-size: 0.875rem;
}

button {
  margin-top: 1rem;
  padding: 0.55rem 0.8rem;
}

.result {
  color: #166534;
}

.error {
  color: #b91c1c;
}
</style>
