import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8089/api',
  timeout: 10000
})

// 请求拦截器（添加 token）
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器（处理错误）
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 认证相关
export const authApi = {
  login: (username, password) => {
    return api.post('/v1/token', new URLSearchParams({
      username,
      password
    }))
  },
  register: (userData) => {
    return api.post('/v1/register', userData)
  }
}

// 告警相关
export const alarmApi = {
  getRecentUnresolved: (limit = 5) => {
    return api.get('/v1/alarms/recent_unresolved', { params: { limit } })
  },
  getTodayReport: () => {
    return api.get('/v1/alarms/today_report')
  },
  getAllReport: () => {
    return api.get('/v1/alarms/all_report')
  },
  getTop3Areas: () => {
    return api.get('/v1/alarms/top3_areas')
  },
  getTodayHandleReport: () => {
    return api.get('/v1/alarms/today_handle_report')
  },
  getAlarms: (params) => {
    return api.get('/v1/alarms', { params })
  },
  getAlarm: (id) => {
    return api.get(`/v1/alarms/${id}`)
  },
  deleteAlarms: (ids) => {
    return api.delete(`/v1/alarms/${ids}`)
  }
}

// 摄像头相关
export const cameraApi = {
  getStatusReport: () => {
    return api.get('/v1/camera_infos/status_report')
  },
  searchCameras: (params) => {
    return api.get('/v1/camera_infos/search', { params })
  },
  getCamera: (id) => {
    return api.get(`/v1/camera_infos/${id}`)
  },
  createCamera: (cameraData) => {
    return api.post('/v1/camera_infos', cameraData)
  },
  updateCamera: (id, cameraData) => {
    return api.put(`/v1/camera_infos/${id}`, cameraData)
  },
  deleteCamera: (ids) => {
    return api.delete(`/v1/camera_infos/${ids}`)
  },
  testCamera: (id) => {
    return api.get(`/v1/camera_infos/test/${id}`)
  },
  getCameraPreview: (id) => {
    return api.get(`/v1/camera_infos/preview/${id}`)
  }
}

// 告警处理相关
export const alarmHandleApi = {
  getHandleRecords: (alarmId) => {
    return api.get(`/v1/alarm_handle_records/${alarmId}`)
  },
  uploadAttachment: (attachmentData) => {
    return api.post('/v1/alarm_handle_records/upload_attachment', attachmentData)
  },
  createHandleRecord: (recordData) => {
    return api.post('/v1/alarm_handle_records', recordData)
  }
}

// 园区区域相关
export const parkAreaApi = {
  searchAreas: (params) => {
    return api.get('/v1/park_areas/search/', { params })
  },
  getArea: (id) => {
    return api.get(`/v1/park_areas/${id}`)
  },
  createArea: (areaData) => {
    return api.post('/v1/park_areas/', areaData)
  },
  updateArea: (id, areaData) => {
    return api.put(`/v1/park_areas/${id}`, areaData)
  },
  deleteArea: (ids) => {
    return api.delete(`/v1/park_areas/${ids}`)
  }
}

// 用户相关
export const userApi = {
  getUser: (id) => {
    return api.get(`/v1/users/${id}`)
  },
  getUsers: (params) => {
    return api.get('/v1/users', { params })
  },
  createUser: (userData) => {
    return api.post('/v1/users', userData)
  },
  updateUser: (id, userData) => {
    return api.put(`/v1/users/${id}`, userData)
  },
  deleteUser: (ids) => {
    return api.delete(`/v1/users/${ids}`)
  }
}

export default api