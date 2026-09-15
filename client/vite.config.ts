import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

/**
 * Vite 配置文件
 */
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/uploads33': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // 将重量级 UI/图表依赖拆出，避免单个入口 chunk 阻塞首屏加载。
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('element-plus') || id.includes('@element-plus')) return 'element-plus'
          if (id.includes('echarts') || id.includes('vue-echarts')) return 'charts'
          if (id.includes('markdown-it') || id.includes('dompurify')) return 'content-tools'
          if (id.includes('vue') || id.includes('pinia') || id.includes('vue-router')) return 'vue-core'
          return 'vendor'
        },
      },
    },
  },
})
