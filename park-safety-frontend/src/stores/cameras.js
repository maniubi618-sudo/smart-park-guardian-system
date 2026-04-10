import { defineStore } from 'pinia'
import { cameraApi } from '../services/api'

export const useCameraStore = defineStore('cameras', {
  state: () => ({
    cameras: [],
    statusReport: null,
    loading: false,
    error: null
  }),
  getters: {
    totalCameras: (state) => state.statusReport?.total_count || 0,
    onlineCameras: (state) => state.statusReport?.online_count || 0,
    offlineCameras: (state) => state.statusReport?.offline_count || 0
  },
  actions: {
    async fetchStatusReport() {
      this.loading = true
      try {
        const response = await cameraApi.getStatusReport()
        if (response.code === 1) {
          this.statusReport = response.data
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
    
    async fetchCameras(params) {
      this.loading = true
      try {
        const response = await cameraApi.searchCameras(params)
        if (response.code === 1) {
          this.cameras = response.data.rows || []
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
    
    async createCamera(cameraData) {
      this.loading = true
      try {
        const response = await cameraApi.createCamera(cameraData)
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
    
    async updateCamera(id, cameraData) {
      this.loading = true
      try {
        const response = await cameraApi.updateCamera(id, cameraData)
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
    
    async deleteCamera(ids) {
      this.loading = true
      try {
        const response = await cameraApi.deleteCamera(ids)
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
    
    async testCamera(id) {
      this.loading = true
      try {
        const response = await cameraApi.testCamera(id)
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

    async getCameraPreview(id) {
      this.loading = true
      try {
        const response = await cameraApi.getCameraPreview(id)
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