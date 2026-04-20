<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ 'collapsed': isCollapsed }">
      <div class="sidebar-header">
        <h3 v-if="!isCollapsed">园区智能安防系统</h3>
        <button class="collapse-btn" @click="toggleCollapse">
          <img src="../assets/项目管理.png" alt="收缩" class="collapse-icon">
        </button>
      </div>
      <ul class="sidebar-menu">
        <li class="sidebar-menu-item" :class="{ active: $route.path === '/dashboard' }">
          <router-link to="/dashboard">
            <el-icon class="icon"><HomeFilled /></el-icon>
            <span v-if="!isCollapsed">仪表盘</span>
          </router-link>
        </li>
        <li class="sidebar-menu-item" :class="{ active: $route.path === '/alarms' }">
          <router-link to="/alarms">
            <el-icon class="icon"><WarningFilled /></el-icon>
            <span v-if="!isCollapsed">告警管理</span>
          </router-link>
        </li>
        <li class="sidebar-menu-item" :class="{ active: $route.path === '/map' }">
          <router-link to="/map">
            <el-icon class="icon"><MapLocation /></el-icon>
            <span v-if="!isCollapsed">3D地图</span>
          </router-link>
        </li>
        <li class="sidebar-menu-item" :class="{ active: $route.path === '/cameras' }">
          <router-link to="/cameras">
            <el-icon class="icon"><VideoCamera /></el-icon>
            <span v-if="!isCollapsed">摄像头管理</span>
          </router-link>
        </li>
        <li class="sidebar-menu-item" :class="{ active: $route.path === '/areas' }">
          <router-link to="/areas">
            <el-icon class="icon"><LocationFilled /></el-icon>
            <span v-if="!isCollapsed">园区管理</span>
          </router-link>
        </li>
        <li class="sidebar-menu-item" :class="{ active: $route.path === '/users' }">
          <router-link to="/users">
            <el-icon class="icon"><UserFilled /></el-icon>
            <span v-if="!isCollapsed">用户管理</span>
          </router-link>
        </li>
        <li class="sidebar-menu-item" :class="{ active: $route.path === '/settings' }">
          <router-link to="/settings">
            <el-icon class="icon"><Setting /></el-icon>
            <span v-if="!isCollapsed">系统设置</span>
          </router-link>
        </li>
      </ul>
      <div class="sidebar-footer">
        <el-button link @click="handleLogout" class="logout-btn">
          <el-icon><SwitchButton /></el-icon>
          <span v-if="!isCollapsed">退出登录</span>
        </el-button>
      </div>
    </aside>
    
    <!-- 主内容区域 -->
    <main class="main-content" :class="{ 'sidebar-collapsed': isCollapsed }">
      <div class="content-header">
        <h2>{{ pageTitle }}</h2>
        <div class="user-info">
          <span v-if="userName">{{ userName }}</span>
        </div>
      </div>
      <div class="content-body">
        <slot></slot>
      </div>
    </main>

    <!-- AI助手组件 -->
    <AIAssistant />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useLayoutStore } from '../stores/layout'
import { HomeFilled, WarningFilled, VideoCamera, LocationFilled, UserFilled, SwitchButton, Setting, MapLocation } from '@element-plus/icons-vue'
import AIAssistant from './AIAssistant.vue'

const router = useRouter()
const authStore = useAuthStore()
const layoutStore = useLayoutStore()

const isCollapsed = computed(() => layoutStore.isSidebarCollapsed)

const toggleCollapse = () => {
  layoutStore.toggleSidebar()
}

const pageTitle = computed(() => {
  const pathMap = {
    '/dashboard': '仪表盘',
    '/alarms': '告警管理',
    '/map': '3D地图',
    '/cameras': '摄像头管理',
    '/areas': '园区管理',
    '/users': '用户管理',
    '/settings': '系统设置'
  }
  return pathMap[router.currentRoute.value.path] || '园区智能安防系统'
})

const userName = computed(() => {
  return authStore.user?.name || authStore.user?.user_name
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.sidebar-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 0.75rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  color: #fff;
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
  flex: 1;
}

.collapse-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.collapse-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.collapse-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
  transition: transform 0.3s ease;
}

.sidebar.collapsed .collapse-icon {
  transform: rotate(180deg);
}

.sidebar-menu-item {
  margin: 0.25rem 0;
}

.sidebar-menu-item a {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.25rem;
  color: #fff;
  text-decoration: none;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.sidebar-menu-item a:hover,
.sidebar-menu-item.active a {
  background-color: rgba(255, 255, 255, 0.1);
  border-left-color: var(--primary-color);
  color: #fff;
}

.icon {
  margin-right: 0.75rem;
  font-size: 1.5rem;
}

.sidebar-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0.75rem 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.logout-btn {
  color: #fff;
  width: 100%;
  justify-content: flex-start;
  padding: 0.5rem 0;
}

.logout-btn:hover {
  color: #ff4d4f;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border-color);
}

.content-header h2 {
  margin: 0;
  color: var(--text-color);
  font-size: 1.25rem;
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-info span {
  margin-right: 1rem;
  color: var(--text-color-secondary);
  font-size: 0.875rem;
}

.content-body {
  min-height: calc(100vh - 100px);
}

/* 侧边栏收缩状态 */
.sidebar {
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar.collapsed .sidebar-menu-item a {
  padding: 0.75rem 0.5rem;
  justify-content: center;
}

.sidebar.collapsed .icon {
  margin-right: 0;
}

.sidebar.collapsed .sidebar-footer {
  padding: 0.75rem 0.5rem;
}

.sidebar.collapsed .logout-btn {
  justify-content: center;
}

/* 主内容区域调整 */
.main-content {
  transition: margin-left 0.3s ease;
}

.main-content.sidebar-collapsed {
  margin-left: 60px;
}
</style>
