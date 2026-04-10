import { defineStore } from 'pinia'
import { parkAreaApi } from '../services/api'

export const useAreaStore = defineStore('areas', {
  state: () => ({
    areas: [],
    loading: false,
    error: null
  }),
  getters: {
    totalAreas: (state) => state.areas.length
  },
  actions: {
    async fetchAreas(params) {
      this.loading = true
      try {
        const response = await parkAreaApi.searchAreas(params)
        if (response.code === 1) {
          this.areas = response.data.rows || []
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
    
    async createArea(areaData) {
      this.loading = true
      try {
        const response = await parkAreaApi.createArea(areaData)
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
    
    async updateArea(id, areaData) {
      this.loading = true
      try {
        const response = await parkAreaApi.updateArea(id, areaData)
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
    
    async deleteArea(ids) {
      this.loading = true
      try {
        const response = await parkAreaApi.deleteArea(ids)
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