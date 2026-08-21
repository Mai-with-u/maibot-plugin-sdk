import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    emptyOutDir: true,
    lib: {
      entry: 'src/main.ts',
      formats: ['es'],
      fileName: () => 'index.js',
    },
    outDir: 'webui/dist',
  },
})
