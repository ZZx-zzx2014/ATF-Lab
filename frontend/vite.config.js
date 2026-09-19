import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// ATF Lab 前端构建配置
// ⚠️ 仅供教学演示
//
// 同域部署：不设 VITE_API_BASE，API 走相对路径 /api/v1/...
// 分离部署：设 VITE_API_BASE=https://api.example.com 后重新构建
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // 开发模式下把 API 请求转发到后端，便于前后端分离调试
      '/api': {
        target: process.env.ATF_API_PROXY || 'http://127.0.0.1:8899',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
  },
})
