import { defineStore } from 'pinia'
import { authApi } from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: (() => {
      try {
        const userStr = localStorage.getItem('user')
        return userStr && userStr !== 'undefined' ? JSON.parse(userStr) : null
      } catch (e) {
        localStorage.removeItem('user')
        return null
      }
    })(),
    token: localStorage.getItem('token') || null,
    loading: false,
    error: null
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    userRole: (state) => state.user?.user_role || null
  },
  actions: {
    enterBridgeSession() {
      this.token = 'clawpro-local-bridge'
      this.user = {
        name: 'ClawPro 项目联动',
        user_name: 'ClawPro 项目联动',
        user_role: 'bridge'
      }
      sessionStorage.setItem('parkSafetyBridge', 'true')
      localStorage.setItem('token', this.token)
      localStorage.setItem('user', JSON.stringify(this.user))
    },

    async login(username, password) {
      this.loading = true
      this.error = null
      try {
        const response = await authApi.login(username, password)
        console.log('Login response:', response)
        
        // 检查 access_token 可能存在的位置
        const data = response.data || response
        if (data.access_token) {
          this.token = data.access_token
          this.user = data.user_info || { username: username }
          localStorage.setItem('token', this.token)
          localStorage.setItem('user', JSON.stringify(this.user))
          return { success: true, data: data, message: response.msg || '登录成功' }
        } else {
          this.error = response.msg || '登录失败'
          return { success: false, message: this.error }
        }
      } catch (error) {
        console.log('Login error:', error)
        this.error = error.message || '登录失败'
        return { success: false, message: this.error }
      } finally {
        this.loading = false
      }
    },
    
    async register(userData) {
      this.loading = true
      this.error = null
      try {
        const response = await authApi.register(userData)
        console.log('Register response:', response)
        
        // 检查 access_token 可能存在的位置
        const data = response.data || response
        if (data.access_token) {
          this.token = data.access_token
          this.user = data.user_info || { username: userData.username }
          localStorage.setItem('token', this.token)
          localStorage.setItem('user', JSON.stringify(this.user))
          return { success: true, data: data, message: response.msg || '注册成功' }
        } else {
          this.error = response.msg || '注册失败'
          return { success: false, message: this.error }
        }
      } catch (error) {
        console.log('Register error:', error)
        this.error = error.message || '注册失败'
        return { success: false, message: this.error }
      } finally {
        this.loading = false
      }
    },
    
    logout() {
      this.token = null
      this.user = null
      this.error = null
      sessionStorage.removeItem('parkSafetyBridge')
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
    
    clearError() {
      this.error = null
    },
    
    async initAuth() {
      // 检查本地存储是否有token
      const token = localStorage.getItem('token')
      if (token) {
        this.token = token
        this.user = JSON.parse(localStorage.getItem('user')) || null
        // 可以在这里添加验证token有效性的逻辑
        // 例如调用API验证token是否过期
      }
    }
  }
})
