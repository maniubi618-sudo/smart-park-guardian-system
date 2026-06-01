import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { existsSync } from 'fs'

const certDir = path.resolve(__dirname, '../app')
const certFile = path.join(certDir, 'server.crt')
const keyFile = path.join(certDir, 'server.key')

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    https: existsSync(certFile) && existsSync(keyFile) ? {
      cert: certFile,
      key: keyFile
    } : false,
    proxy: {
      '/api/v1/camera_infos/phone_camera': {
        target: 'https://127.0.0.1:8443',
        changeOrigin: true,
        secure: false,
        ws: true
      },
      // 告警广播 WebSocket 必须路由到 HTTPS 后端(8443)
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
