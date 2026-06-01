<template>
  <div class="app-container">
    <router-view v-slot="{ Component }">
      <transition name="route-canvas" mode="out-in">
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

.route-canvas-enter-active {
  transition: opacity var(--motion-slow) var(--motion-ease), transform var(--motion-slow) var(--motion-ease), filter var(--motion-slow) var(--motion-ease);
}

.route-canvas-leave-active {
  transition: opacity var(--motion-fast) var(--motion-exit), transform var(--motion-fast) var(--motion-exit), filter var(--motion-fast) var(--motion-exit);
}

.route-canvas-enter-from {
  opacity: 0;
  transform: translateY(14px);
  filter: blur(8px);
}

.route-canvas-leave-to {
  opacity: 0;
  transform: translateY(-8px);
  filter: blur(4px);
}
</style>
