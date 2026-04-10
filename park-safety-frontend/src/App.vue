<template>
  <div class="app-container">
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import websocketService from './services/websocket'

const authStore = useAuthStore()

onMounted(() => {
  // 检查是否有token
  const token = localStorage.getItem('token')
  if (token) {
    // 这里可以添加获取用户信息的逻辑
  }
  
  // 监听WebSocket消息
  websocketService.subscribe((data) => {
    console.log('WebSocket message:', data)
    // 处理实时告警推送
  })
})
</script>

<style scoped>
.app-container {
  width: 100%;
  min-height: 100vh;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>