import { defineStore } from 'pinia'
import { userApi } from '../services/api'

export const useUserStore = defineStore('users', {
  state: () => ({
    users: [],
    loading: false,
    error: null
  }),
  getters: {
    totalUsers: (state) => state.users.length
  },
  actions: {
    async fetchUsers(params) {
      this.loading = true
      try {
        const response = await userApi.getUsers(params)
        if (response.code === 1) {
          this.users = response.data.rows || []
          return { success: true, data: response.data, message: response.msg }
        }
        return { success: false, message: response.msg }
      } catch (error) {
        this.error = error.message
        return { success: false, message: error.message }
      } finally {
        this.loading = false
      }
    },
    
    async createUser(userData) {
      this.loading = true
      try {
        const response = await userApi.createUser(userData)
        if (response.code === 1) {
          return { success: true, data: response.data, message: response.msg }
        }
        return { success: false, message: response.msg }
      } catch (error) {
        this.error = error.message
        return { success: false, message: error.message }
      } finally {
        this.loading = false
      }
    },
    
    async updateUser(id, userData) {
      this.loading = true
      try {
        const response = await userApi.updateUser(id, userData)
        if (response.code === 1) {
          return { success: true, data: response.data, message: response.msg }
        }
        return { success: false, message: response.msg }
      } catch (error) {
        this.error = error.message
        return { success: false, message: error.message }
      } finally {
        this.loading = false
      }
    },
    
    async deleteUser(ids) {
      this.loading = true
      try {
        const response = await userApi.deleteUser(ids)
        if (response.code === 1) {
          return { success: true, data: response.data, message: response.msg }
        }
        return { success: false, message: response.msg }
      } catch (error) {
        this.error = error.message
        return { success: false, message: error.message }
      } finally {
        this.loading = false
      }
    },
    
    clearError() {
      this.error = null
    }
  }
})