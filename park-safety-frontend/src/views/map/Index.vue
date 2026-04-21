<template>
  <MainLayout>
    <div class="map-container">
      <div id="map" class="map-container"></div>
      <div class="map-toolbar">
        <el-button type="primary" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新数
        </el-button>
      </div>
      <div class="camera-list-panel">
        <div class="panel-header">
          <el-icon><Location /></el-icon>
          摄像头列表 ({{ cameras.length }})
        </div>
        <el-scrollbar>
          <div
            v-for="camera in cameras"
            :key="camera.camera_id"
            class="camera-item"
            :class="{ active: selectedCamera?.camera_id === camera.camera_id }"
            @click="selectCamera(camera)"
          >
            <div class="camera-status">
              <span :class="getStatusClass(camera.camera_status)"></span>
            </div>
            <div class="camera-info">
              <div class="camera-name">{{ camera.camera_name }}</div>
              <div class="camera-position">{{ camera.install_position }}</div>
            </div>
            <div class="camera-alarm" v-if="camera.hasAlarm">
              <el-icon><WarningFilled /></el-icon>
            </div>
          </div>
        </el-scrollbar>
      </div>
      <div class="alarm-list-panel" v-if="alarms.length > 0">
        <div class="panel-header">
          <el-icon><WarningFilled /></el-icon>
          告警位置 ({{ alarms.length }})
        </div>
        <el-scrollbar>
          <div
            v-for="alarm in alarms"
            :key="alarm.alarm_id"
            class="alarm-item"
            @click="focusAlarm(alarm)"
          >
            <el-tag :type="getAlarmTypeTag(alarm.alarm_type)" size="small">
              {{ getAlarmTypeName(alarm.alarm_type) }}
            </el-tag>
            <span class="alarm-time">{{ formatTime(alarm.alarm_time) }}</span>
          </div>
        </el-scrollbar>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import MainLayout from '../../components/MainLayout.vue'
import { Refresh, Location, WarningFilled } from '@element-plus/icons-vue'
import { useCameraStore } from '../../stores/cameras'
import { useAlarmStore } from '../../stores/alarms'
import AMapLoader from '@amap/amap-jsapi-loader'

const cameraStore = useCameraStore()
const alarmStore = useAlarmStore()

let map = null
let AMap = null
const cameras = ref([])
const alarms = ref([])
const selectedCamera = ref(null)
const markers = ref([])
const alarmMarkers = ref([])
const phoneCameraMarker = ref(null) // 手机摄像头标记

const getStatusClass = (status) => {
  const map = {
    0: 'status-offline',
    1: 'status-online',
    2: 'status-analyzing'
  }
  return map[status] || 'status-offline'
}

const getStatusTag = (status) => {
  const map = {
    0: 'info',
    1: 'success',
    2: 'warning'
  }
  return map[status] || 'info'
}

const getStatusName = (status) => {
  const map = {
    0: '离线',
    1: '在线未分析',
    2: '分析中'
  }
  return map[status] || '未知'
}

const getAlarmTypeName = (type) => {
  const map = {
    0: '安全规范',
    1: '区域入侵',
    2: '火警'
  }
  return map[type] || '未知'
}

const getAlarmTypeTag = (type) => {
  const map = {
    0: 'warning',
    1: 'danger',
    2: 'success'
  }
  return map[type] || 'info'
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return `${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

const initMap = async () => {
  try {
    console.log('开始加载高德地图...')
    
    window._AMapSecurityConfig = {
      securityJsCode: 'e28f703885b6c7d913617debb34efa16'
    }
    
    await AMapLoader.load({
      key: '326f7adda5ee7fe41266647c41d8c189',
      version: '2.0',
      plugins: ['AMap.Scale', 'AMap.ToolBar', 'AMap.InfoWindow']
    })
    
    AMap = window.AMap
    
    console.log('高德地图加载成功，AMap:', !!AMap)
    if (!AMap) {
      throw new Error('AMap 未成功加载到 window 上')
    }
    
    console.log('初始化地图...')
    map = new AMap.Map('map', {
      zoom: 18,
      center: [110.410382, 20.043675],
      viewMode: '3D',
      pitch: 60,
      rotation: 0,
      mapStyle: 'amap://styles/normal'
    })

    map.addControl(new AMap.Scale())
    map.addControl(new AMap.ToolBar({ position: 'RT' }))
    
    console.log('地图初始化完成，加载数据...')
    await loadData()
  } catch (e) {
    console.error('高德地图加载失败:', e)
    console.error('错误堆栈:', e.stack)
    ElMessage.error(`地图加载失败: ${e.message || '请检查API Key配置、安全密钥和域名白名单'}`)
  }
}

const loadData = async () => {
  try {
    await cameraStore.fetchCameras({ page: 1, page_size: 100 })
    cameras.value = cameraStore.cameras

    await alarmStore.fetchAlarms({ page: 1, page_size: 50, is_resolved: 0 })
    if (alarmStore.alarms) {
      alarms.value = alarmStore.alarms
    }

    renderMarkers()
  } catch (e) {
    console.error('加载数据失败:', e)
  }
}

const createCameraIcon = (status, hasAlarm) => {
  const color = hasAlarm ? '#f56c6c' : 
                status === 0 ? '#909399' : 
                status === 1 ? '#67c23a' : '#409eff'
  
  return new AMap.Icon({
    size: new AMap.Size(36, 36),
    imageSize: new AMap.Size(36, 36),
    image: `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="white" stroke="${color}" stroke-width="4"/><text x="50" y="65" text-anchor="middle" font-size="40" fill="${color}">📷</text></svg>`
  })
}

const createAlarmIcon = (type) => {
  const color = type === 0 ? '#e6a23c' : type === 1 ? '#f56c6c' : '#67c23a'
  return new AMap.Icon({
    size: new AMap.Size(32, 32),
    imageSize: new AMap.Size(32, 32),
    image: `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="white" stroke="${color}" stroke-width="4"/><text x="50" y="65" text-anchor="middle" font-size="40" fill="${color}">⚠️</text></svg>`
  })
}

const renderMarkers = () => {
  if (!map || !AMap) return

  markers.value.forEach(m => map.remove(m))
  markers.value = []

  const availableCameras = cameras.value.filter(c => c.latitude && c.longitude)
  
  if (availableCameras.length > 0) {
    const first = availableCameras[0]
    map.setCenter([first.longitude, first.latitude])
  }

  cameras.value.forEach(camera => {
    if (!camera.latitude || !camera.longitude) return

    const hasAlarm = alarms.value.some(a => a.camera_id === camera.camera_id)
    const icon = createCameraIcon(camera.camera_status, hasAlarm)
    
    const marker = new AMap.Marker({
      position: [camera.longitude, camera.latitude],
      icon: icon,
      title: camera.camera_name,
      zIndex: 10
    })

    const infoWindow = new AMap.InfoWindow({
      content: `<div style="padding: 10px;"><h3 style="margin: 0 0 10px;">${camera.camera_name}</h3><p style="margin: 0 0 5px;">位置: ${camera.install_position}</p><p style="margin: 0;">状态: ${getStatusName(camera.camera_status)}</p></div>`,
      offset: new AMap.Pixel(0, -30)
    })

    marker.on('click', () => {
      selectCamera(camera)
      infoWindow.open(map, marker.getPosition())
    })

    map.add(marker)
    markers.value.push(marker)
  })

  renderAlarmMarkers()
}

const renderAlarmMarkers = () => {
  if (!map || !AMap) return

  alarmMarkers.value.forEach(m => map.remove(m))
  alarmMarkers.value = []

  alarms.value.forEach(alarm => {
    const camera = cameras.value.find(c => c.camera_id === alarm.camera_id)
    if (!camera?.latitude || !camera?.longitude) return

    const icon = createAlarmIcon(alarm.alarm_type)
    const marker = new AMap.Marker({
      position: [camera.longitude, camera.latitude],
      icon: icon,
      title: getAlarmTypeName(alarm.alarm_type),
      zIndex: 100
    })

    const infoWindow = new AMap.InfoWindow({
      content: `<div style="padding: 10px;"><h3 style="margin: 0 0 10px;">${getAlarmTypeName(alarm.alarm_type)}</h3><p style="margin: 0 0 5px;">摄像头: ${camera.camera_name}</p><p style="margin: 0;">时间: ${alarm.alarm_time}</p></div>`,
      offset: new AMap.Pixel(0, -30)
    })

    marker.on('click', () => {
      focusAlarm(alarm)
      infoWindow.open(map, marker.getPosition())
    })

    map.add(marker)
    alarmMarkers.value.push(marker)
  })
}

const selectCamera = (camera) => {
  selectedCamera.value = camera
  if (camera.latitude && camera.longitude && map) {
    map.setCenter([camera.longitude, camera.latitude])
    map.setZoom(17)
  }
}

const focusAlarm = (alarm) => {
  const camera = cameras.value.find(c => c.camera_id === alarm.camera_id)
  if (camera && camera.latitude && camera.longitude && map) {
    selectedCamera.value = camera
    map.setCenter([camera.longitude, camera.latitude])
    map.setZoom(18)
  }
}

const refreshData = async () => {
  ElMessage.info('正在刷新数据...')
  await loadData()
  ElMessage.success('数据已刷新')
}

// 处理手机摄像头位置更新
const handlePhoneCameraLocationUpdate = (event) => {
  const location = event.detail
  console.log('收到手机摄像头位置更新:', location)
  
  // 移除旧标记
  if (phoneCameraMarker.value) {
    map.remove(phoneCameraMarker.value)
    phoneCameraMarker.value = null
  }
  
  if (location && location.latitude && location.longitude) {
    // 创建新标记
    const marker = new AMap.Marker({
      position: [location.longitude, location.latitude],
      title: '手机摄像头',
      icon: new AMap.Icon({
        image: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0OCIgaGVpZ2h0PSI0OCI+PGNpcmNsZSBjeD0iMjQiIGN5PSIyNCIgcj0iMjAiIGZpbGw9IiM0MDllZmYiLz48Y2lyY2xlIGN4PSIyNCIgY3k9IjI0IiByPSIxMCIgZmlsbD0id2hpdGUiLz48Y2lyY2xlIGN4PSIyNCIgY3k9IjI0IiByPSI2IiBmaWxsPSIjNDA5ZWZmIi8+PC9zdmc+',
        size: new AMap.Size(48, 48),
        imageSize: new AMap.Size(48, 48),
        anchor: new AMap.Pixel(24, 24)
      })
    })
    
    // 添加点击事件
    marker.on('click', () => {
      const infoWindow = new AMap.InfoWindow({
        content: `
          <div style="padding: 10px;">
            <h4 style="margin: 0 0 10px 0;">手机摄像头</h4>
            <p style="margin: 0;">位置: ${location.longitude.toFixed(6)}, ${location.latitude.toFixed(6)}</p>
            <p style="margin: 5px 0 0 0; color: #909399; font-size: 12px;">正在连接中...</p>
          </div>
        `,
        offset: new AMap.Pixel(0, -24)
      })
      infoWindow.open(map, marker.getPosition())
    })
    
    map.add(marker)
    phoneCameraMarker.value = marker
    
    // 移动地图到该位置
    map.setCenter([location.longitude, location.latitude])
    map.setZoom(18)
    
    ElMessage.success('手机摄像头位置已更新')
  }
}

onMounted(() => {
  initMap()
  // 监听手机摄像头位置更新事件
  window.addEventListener('phoneCameraLocationUpdate', handlePhoneCameraLocationUpdate)
})

onUnmounted(() => {
  window.removeEventListener('phoneCameraLocationUpdate', handlePhoneCameraLocationUpdate)
  if (map) {
    map.destroy()
  }
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: calc(100vh - 80px);
  position: relative;
}

.map-toolbar {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 1000;
  display: flex;
  gap: 10px;
}

.camera-list-panel {
  position: absolute;
  top: 80px;
  left: 20px;
  width: 280px;
  max-height: 400px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px;
  font-weight: 600;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #303133;
}

.camera-item {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f5f5f5;
}

.camera-item:hover {
  background: #f5f7fa;
}

.camera-item.active {
  background: #ecf5ff;
}

.camera-status {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-offline {
  background: #909399;
}

.status-online {
  background: #67c23a;
}

.status-analyzing {
  background: #409eff;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.camera-info {
  flex: 1;
  min-width: 0;
}

.camera-name {
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.camera-position {
  font-size: 12px;
  color: #909399;
}

.camera-alarm {
  color: #f56c6c;
}

.alarm-list-panel {
  position: absolute;
  top: 80px;
  right: 20px;
  width: 240px;
  max-height: 300px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.alarm-item {
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f5f5f5;
}

.alarm-item:hover {
  background: #f5f7fa;
}

.alarm-time {
  font-size: 12px;
  color: #909399;
}
</style>