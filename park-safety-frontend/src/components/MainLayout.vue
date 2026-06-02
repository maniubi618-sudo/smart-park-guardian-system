<template>
  <div class="main-layout">
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="sidebar-header">
        <div class="brand-mark">
          <el-icon><Monitor /></el-icon>
        </div>
        <div v-if="!isCollapsed" class="brand-copy">
          <strong>园区智能安防</strong>
          <span>Command Center</span>
        </div>
        <button class="collapse-btn" type="button" @click="toggleCollapse" aria-label="切换导航">
          <el-icon><Fold v-if="!isCollapsed" /><Expand v-else /></el-icon>
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
        <div v-if="!isCollapsed" class="operator-card">
          <span class="operator-label">当前账号</span>
          <strong>{{ userName || '值班人员' }}</strong>
        </div>
        <button class="logout-btn" type="button" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span v-if="!isCollapsed">退出登录</span>
        </button>
      </div>
    </aside>

    <main class="main-content" :class="{ 'sidebar-collapsed': isCollapsed }">
      <div class="content-header">
        <div>
          <p class="content-kicker">SMART PARK SECURITY</p>
          <h2>{{ pageTitle }}</h2>
        </div>
        <div class="header-status">
          <button class="project-link" type="button" @click="goExternal(AGRICULTURE_DASHBOARD_URL)">
            <el-icon><Monitor /></el-icon>
            <span>农业大屏</span>
          </button>
          <button class="project-link" type="button" @click="goExternal(STRAWBERRY_DASHBOARD_URL)">
            <el-icon><VideoCamera /></el-icon>
            <span>智慧大棚</span>
          </button>
          <div class="status-pill">
            <span class="status-dot"></span>
            <span>系统在线</span>
          </div>
          <div class="user-info">
            <el-icon><UserFilled /></el-icon>
            <span>{{ userName || '值班人员' }}</span>
          </div>
        </div>
      </div>
      <div class="content-body">
        <slot></slot>
      </div>
    </main>

    <AIAssistant />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useLayoutStore } from '../stores/layout'
import {
  HomeFilled,
  WarningFilled,
  VideoCamera,
  LocationFilled,
  UserFilled,
  SwitchButton,
  Setting,
  MapLocation,
  Monitor,
  Fold,
  Expand
} from '@element-plus/icons-vue'
import AIAssistant from './AIAssistant.vue'

const router = useRouter()
const authStore = useAuthStore()
const layoutStore = useLayoutStore()

const AGRICULTURE_DASHBOARD_URL = 'http://127.0.0.1:8001/system/index/'
const STRAWBERRY_DASHBOARD_URL = 'http://127.0.0.1:5173/'

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

const goExternal = (targetUrl) => {
  document.body.classList.add('is-page-leaving')
  window.setTimeout(() => {
    window.location.href = targetUrl
  }, 420)
}
</script>

<style scoped>
.sidebar {
  display: grid;
  grid-template-rows: auto 1fr auto;
  animation: dockLand var(--motion-page) var(--motion-ease) both;
}

@keyframes dockLand {
  from {
    opacity: 0;
    transform: translateX(-18px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

.sidebar::before {
  content: "";
  position: absolute;
  inset: 16px;
  z-index: -1;
  border-radius: inherit;
  background:
    linear-gradient(135deg, rgba(83, 111, 136, 0.12), transparent 42%),
    radial-gradient(circle at 50% 12%, rgba(197, 138, 69, 0.16), transparent 9rem);
  pointer-events: none;
  transition: opacity var(--motion-slow) var(--motion-ease), transform var(--motion-slow) var(--motion-ease);
}

.sidebar-header {
  min-height: 112px;
  padding: 18px 16px 14px;
  border-bottom: 1px solid rgba(83, 111, 136, 0.16);
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.brand-mark {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  color: #fbfaf7;
  background: #536f88;
  border: 1px solid rgba(32, 38, 42, 0.08);
  border-radius: 16px;
  font-size: 23px;
  box-shadow: 0 14px 28px rgba(83, 111, 136, 0.28);
  transition: border-radius var(--motion-slow) var(--motion-ease), transform var(--motion-base) var(--motion-ease), box-shadow var(--motion-base) var(--motion-ease);
}

.brand-mark:hover {
  transform: rotate(-3deg) scale(1.04);
  box-shadow: 0 18px 36px rgba(83, 111, 136, 0.32);
}

.brand-copy {
  flex: 1;
  min-width: 0;
  animation: labelSlideIn var(--motion-slow) var(--motion-ease) both;
}

@keyframes labelSlideIn {
  from {
    opacity: 0;
    transform: translateX(-8px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.brand-copy strong {
  display: block;
  color: var(--text-color);
  font-size: 16px;
  font-weight: 920;
  line-height: 1.2;
}

.brand-copy span {
  display: block;
  margin-top: 4px;
  color: var(--text-color-muted);
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.collapse-btn {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  color: #536f88;
  background: rgba(83, 111, 136, 0.09);
  border: 1px solid rgba(83, 111, 136, 0.16);
  cursor: pointer;
  padding: 0;
  border-radius: 999px;
  transition: transform var(--motion-base) var(--motion-ease), background-color var(--motion-base) var(--motion-ease), border-color var(--motion-base) var(--motion-ease), color var(--motion-base) var(--motion-ease), box-shadow var(--motion-base) var(--motion-ease);
}

.collapse-btn:hover {
  color: #fbfaf7;
  background-color: #536f88;
  border-color: #536f88;
  transform: translateY(-2px) rotate(2deg);
  box-shadow: 0 10px 22px rgba(83, 111, 136, 0.20);
}

.sidebar-menu {
  list-style: none;
  padding: 18px 12px;
  margin: 0;
  overflow-y: auto;
  scrollbar-width: none;
}

.sidebar-menu::-webkit-scrollbar {
  display: none;
}

.sidebar-menu-item {
  margin: 0 0 10px;
  position: relative;
  animation: dockItemIn var(--motion-slow) var(--motion-ease) both;
}

.sidebar-menu-item:nth-child(1) { animation-delay: 40ms; }
.sidebar-menu-item:nth-child(2) { animation-delay: 70ms; }
.sidebar-menu-item:nth-child(3) { animation-delay: 100ms; }
.sidebar-menu-item:nth-child(4) { animation-delay: 130ms; }
.sidebar-menu-item:nth-child(5) { animation-delay: 160ms; }
.sidebar-menu-item:nth-child(6) { animation-delay: 190ms; }
.sidebar-menu-item:nth-child(7) { animation-delay: 220ms; }

@keyframes dockItemIn {
  from {
    opacity: 0;
    transform: translateX(-12px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.sidebar-menu-item::before {
  content: "";
  position: absolute;
  left: -3px;
  top: 11px;
  bottom: 11px;
  width: 3px;
  border-radius: 999px;
  background: #536f88;
  opacity: 0;
  transform: scaleY(0.25);
  transform-origin: 50% 50%;
  transition: opacity var(--motion-base) var(--motion-ease), transform var(--motion-slow) var(--motion-ease);
}

.sidebar-menu-item.active::before {
  opacity: 1;
  transform: scaleY(1);
}

.sidebar-menu-item a {
  display: flex;
  align-items: center;
  min-height: 52px;
  padding: 0 14px;
  color: #56626c;
  text-decoration: none;
  border-radius: 18px;
  border: 1px solid transparent;
  transition: transform var(--motion-base) var(--motion-ease), background-color var(--motion-base) var(--motion-ease), border-color var(--motion-base) var(--motion-ease), color var(--motion-base) var(--motion-ease), box-shadow var(--motion-base) var(--motion-ease);
  gap: 12px;
  font-size: 14px;
  font-weight: 760;
  position: relative;
  overflow: hidden;
}

.sidebar-menu-item a::after {
  content: "";
  position: absolute;
  inset: auto 14px 9px 50px;
  height: 2px;
  background: linear-gradient(90deg, #536f88, transparent);
  opacity: 0;
  transform: translateX(-36%);
  transition: opacity var(--motion-base) var(--motion-ease), transform var(--motion-slow) var(--motion-ease);
}

.sidebar-menu-item a:hover,
.sidebar-menu-item.active a {
  background-color: rgba(255, 255, 255, 0.82);
  border-color: rgba(83, 111, 136, 0.18);
  color: #20262a;
  transform: translateX(5px);
  box-shadow: 0 14px 30px rgba(83, 111, 136, 0.13);
}

.sidebar-menu-item.active a {
  background:
    linear-gradient(90deg, rgba(83, 111, 136, 0.14), rgba(255, 255, 255, 0.88)),
    #ffffff;
  border-color: rgba(83, 111, 136, 0.28);
}

.sidebar-menu-item.active a::after {
  opacity: 1;
  transform: translateX(0);
}

.icon {
  margin-right: 0;
  font-size: 19px;
  color: #536f88;
  transition: transform var(--motion-base) var(--motion-ease), color var(--motion-base) var(--motion-ease);
}

.sidebar-menu-item a:hover .icon,
.sidebar-menu-item.active .icon {
  transform: scale(1.08);
}

.sidebar-footer {
  position: relative;
  padding: 14px 14px 16px;
  border-top: 1px solid rgba(83, 111, 136, 0.16);
  background: rgba(251, 250, 247, 0.56);
}

.operator-card {
  padding: 13px;
  margin-bottom: 10px;
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(83, 111, 136, 0.11), rgba(255, 255, 255, 0.72)),
    #fbfaf7;
  border: 1px solid rgba(83, 111, 136, 0.16);
  animation: labelSlideIn var(--motion-slow) var(--motion-ease) both;
}

.operator-card .operator-label {
  display: block;
  margin-bottom: 4px;
  color: var(--text-color-muted);
  font-size: 11px;
  font-weight: 760;
}

.operator-card strong {
  color: var(--text-color);
  font-size: 14px;
  font-weight: 900;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 42px;
  padding: 0 10px;
  color: #56626c;
  background: transparent;
  border: 1px solid rgba(83, 111, 136, 0.18);
  border-radius: 999px;
  cursor: pointer;
  font-weight: 820;
  justify-content: center;
  transition: transform var(--motion-base) var(--motion-ease), background-color var(--motion-base) var(--motion-ease), border-color var(--motion-base) var(--motion-ease), color var(--motion-base) var(--motion-ease), box-shadow var(--motion-base) var(--motion-ease);
}

.logout-btn:hover {
  color: #b75a4b;
  border-color: rgba(183, 90, 75, 0.32);
  background: rgba(183, 90, 75, 0.08);
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(183, 90, 75, 0.12);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 90px;
  padding: 20px 28px 16px;
  border-bottom: 1px solid rgba(83, 111, 136, 0.12);
  background:
    linear-gradient(90deg, rgba(251, 250, 247, 0.84), rgba(255, 255, 255, 0.56));
  backdrop-filter: blur(18px);
  position: sticky;
  top: 0;
  z-index: 20;
  transition: min-height var(--motion-slow) var(--motion-ease), background-color var(--motion-base) var(--motion-ease), box-shadow var(--motion-base) var(--motion-ease);
  animation: headerDriftIn var(--motion-page) var(--motion-ease) both;
}

@keyframes headerDriftIn {
  from {
    opacity: 0;
    transform: translateY(-12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.content-kicker {
  margin: 0 0 4px;
  color: var(--text-color-muted);
  font-size: 11px;
  font-weight: 860;
  letter-spacing: 0.18em;
}

.content-header h2 {
  margin: 0;
  color: var(--text-color);
  font-size: 24px;
  font-weight: 940;
  letter-spacing: -0.02em;
}

.header-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-pill,
.user-info,
.project-link {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 36px;
  padding: 0 12px;
  color: var(--text-color-secondary);
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(83, 111, 136, 0.18);
  border-radius: 999px;
  font-size: 13px;
  font-weight: 760;
}

.project-link {
  cursor: pointer;
  font-family: inherit;
  transition: transform var(--motion-base) var(--motion-ease), border-color var(--motion-base) var(--motion-ease), box-shadow var(--motion-base) var(--motion-ease), background var(--motion-base) var(--motion-ease);
}

.project-link:hover {
  transform: translateY(-1px);
  border-color: rgba(83, 111, 136, 0.32);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 22px rgba(83, 111, 136, 0.12);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #c58a45;
  box-shadow: 0 0 0 4px rgba(197, 138, 69, 0.16);
  animation: softPulse 2.4s var(--motion-ease) infinite;
}

.user-info {
  color: var(--text-color);
}

.content-body {
  min-height: calc(100vh - 88px);
}

.sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding: 18px 10px 58px;
  min-height: 128px;
}

.sidebar.collapsed .brand-mark {
  border-radius: 999px;
}

.sidebar.collapsed .collapse-btn {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
}

.sidebar.collapsed .collapse-btn:hover {
  transform: translateX(-50%) translateY(-1px);
}

.sidebar.collapsed .sidebar-menu {
  padding: 12px 12px;
}

.sidebar.collapsed .sidebar-menu-item {
  margin-bottom: 12px;
}

.sidebar.collapsed .sidebar-menu-item a {
  padding: 0;
  justify-content: center;
  border-radius: 999px;
  min-height: 52px;
}

.sidebar.collapsed .sidebar-menu-item a::after {
  display: none;
}

.sidebar.collapsed .sidebar-menu-item a:hover,
.sidebar.collapsed .sidebar-menu-item.active a {
  transform: translateX(0) scale(1.06);
}

.sidebar.collapsed .sidebar-footer {
  padding: 12px 10px;
}

.sidebar.collapsed .logout-btn {
  min-height: 52px;
  border-radius: 999px;
  padding: 0;
}

@media (max-width: 900px) {
  .sidebar {
    position: relative;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    min-height: auto;
    overflow: visible;
    box-shadow: 0 10px 26px rgba(47, 57, 66, 0.10);
  }

  .sidebar-header {
    width: 100%;
    min-height: 72px;
    padding: 12px 16px;
  }

  .sidebar-menu {
    display: flex;
    width: 100%;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 0 12px 12px;
    gap: 8px;
  }

  .sidebar-menu-item {
    flex: 0 0 auto;
    margin: 0;
  }

  .sidebar-menu-item a {
    min-height: 44px;
    padding: 0 14px;
    border-radius: 999px;
  }

  .sidebar-menu-item a:hover,
  .sidebar-menu-item.active a {
    transform: none;
  }

  .sidebar-menu-item::before {
    left: 14px;
    right: 14px;
    top: auto;
    bottom: -2px;
    width: auto;
    height: 3px;
    transform: scaleX(0.25);
  }

  .sidebar-menu-item.active::before {
    transform: scaleX(1);
  }

  .sidebar-footer {
    position: static;
    width: 100%;
    display: flex;
    padding: 10px 14px 14px;
  }

  .operator-card {
    display: none;
  }

  .logout-btn {
    max-width: 360px;
  }

  .content-header {
    position: static;
    padding: 16px;
    align-items: flex-start;
    gap: 12px;
    flex-direction: column;
  }

  .header-status {
    flex-wrap: wrap;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .brand-copy,
  .sidebar-menu-item,
  .operator-card,
  .content-header,
  .status-dot {
    animation: none !important;
  }
}
</style>
