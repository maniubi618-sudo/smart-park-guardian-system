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
      '/api': {
        target: 'http://localhost:8089',
        changeOrigin: true,
        secure: false,
        ws: true
      }
    }
  }
})
