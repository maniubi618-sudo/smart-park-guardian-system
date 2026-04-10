import { defineStore } from 'pinia'
import { alarmApi, alarmHandleApi } from '../services/api'

export const useAlarmStore = defineStore('alarms', {
  state: () => ({
    alarms: [],
    recentUnresolved: [],
    statistics: {
      today: null,
      all: null,
      top3Areas: null,
      todayHandle: null
    },
    loading: false,
    error: null
  }),
  getters: {
    totalAlarms: (state) => state.alarms.length,
    unresolvedCount: (state) => state.recentUnresolved.total || 0
  },
  actions: {
    async fetchRecentUnresolved(limit = 5) {
      this.loading = true
      try {
        const response = await alarmApi.getRecentUnresolved(limit)
        if (response.code === 1) {
          this.recentUnresolved = response.data
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
    
    async fetchTodayReport() {
      this.loading = true
      try {
        const response = await alarmApi.getTodayReport()
        if (response.code === 1) {
          this.statistics.today = response.data
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
    
    async fetchAllReport() {
      this.loading = true
      try {
        const response = await alarmApi.getAllReport()
        if (response.code === 1) {
          this.statistics.all = response.data
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
    
    async fetchTop3Areas() {
      this.loading = true
      try {
        const response = await alarmApi.getTop3Areas()
        if (response.code === 1) {
          this.statistics.top3Areas = response.data
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
    
    async fetchTodayHandleReport() {
      this.loading = true
      try {
        const response = await alarmApi.getTodayHandleReport()
        if (response.code === 1) {
          this.statistics.todayHandle = response.data
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
    
    async fetchAlarms(params) {
      this.loading = true
      try {
        const response = await alarmApi.getAlarms(params)
        if (response.code === 1) {
          this.alarms = response.data.rows || []
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
    
    async fetchAlarmById(alarmId) {
      this.loading = true
      try {
        const response = await alarmApi.getAlarm(alarmId)
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
    
    async fetchHandleRecords(alarmId) {
      this.loading = true
      try {
        const response = await alarmHandleApi.getHandleRecords(alarmId)
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
    
    async handleAlarm(alarmData) {
      this.loading = true
      try {
        const response = await alarmHandleApi.createHandleRecord(alarmData)
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
    
    async deleteAlarms(ids) {
      this.loading = true
      try {
        const response = await alarmApi.deleteAlarms(ids)
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