import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      component: () => import('../views/auth/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/agin',
      redirect: '/login'
    },
    {
      path: '/register',
      component: () => import('../views/auth/Register.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/dashboard',
      component: () => import('../views/dashboard/Index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/alarms',
      component: () => import('../views/alarms/Index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/alarms/:id',
      component: () => import('../views/alarms/Detail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/cameras',
      component: () => import('../views/cameras/Index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/areas',
      component: () => import('../views/areas/Index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/users',
      component: () => import('../views/users/Index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      component: () => import('../views/settings/Index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/map',
      component: () => import('../views/map/Index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/phone-location',
      component: () => import('../views/PhoneLocation.vue'),
      meta: { requiresAuth: false }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    // 检查是否已登录
    if (authStore.isAuthenticated) {
      next()
    } else {
      // 未登录，重定向到登录页
      next('/login')
    }
  } else {
    // 不需要认证的页面直接放行
    next()
  }
})

export default router