import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 3003,
    https: false,
    proxy: {
      '/api/v1/camera_infos/phone_camera': {
        target: 'https://127.0.0.1:8443',
        changeOrigin: true,
        secure: false,
        ws: true
      },
      // 告警广播 WebSocket 必须路由到 HTTPS 后端(8443)
      // 因为手机摄像头 YOLO 检测的告警在 HTTPS 进程中广播
      '/api/v1/safety_analysis/ws': {
        target: 'https://127.0.0.1:8443',
        changeOrigin: true,
        secure: false,
        ws: true
      },
      '/api': {
        target: 'http://localhost:8089',
        changeOrigin: true,
        secure: false,
        ws: true
      }
    }
  }
})
