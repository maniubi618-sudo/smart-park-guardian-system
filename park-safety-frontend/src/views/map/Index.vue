<template>
  <MainLayout>
    <div class="map-container">
      <div id="map" class="map-container"></div>
      <div class="map-toolbar">
        <el-button type="primary" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
      <div class="camera-list-panel" :class="{ collapsed: cameraPanelCollapsed }" :style="cameraPanelStyle">
        <div class="panel-header">
          <el-icon><Location /></el-icon>
          <span v-if="!cameraPanelCollapsed">摄像头列表 ({{ cameras.length }})</span>
          <div class="panel-actions">
            <el-button size="small" @click="toggleCameraPanel" circle>
              <el-icon><Expand v-if="cameraPanelCollapsed" /><Fold v-else /></el-icon>
            </el-button>
            <el-button size="small" @click="startMovingCameraPanel" circle>
              <el-icon>✋</el-icon>
            </el-button>
          </div>
        </div>
        <el-scrollbar v-if="!cameraPanelCollapsed" style="height: 340px;">
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
      <div class="phone-camera-list-panel" :class="{ collapsed: phonePanelCollapsed }" :style="phonePanelStyle">
        <div class="panel-header">
          <el-icon><Phone /></el-icon>
          <span v-if="!phonePanelCollapsed">手机摄像头 ({{ Object.keys(phoneCameras).length }})</span>
          <div class="panel-actions">
            <el-button size="small" @click="togglePhonePanel" circle>
              <el-icon><Expand v-if="phonePanelCollapsed" /><Fold v-else /></el-icon>
            </el-button>
            <el-button size="small" @click="startMovingPhonePanel" circle>
              <el-icon>✋</el-icon>
            </el-button>
          </div>
        </div>
        <el-scrollbar v-if="!phonePanelCollapsed" style="height: 200px;">
          <div
            v-for="(phone, uid) in phoneCameras"
            :key="uid"
            class="camera-item"
            :class="{ active: selectedPhoneUid === uid, streaming: phone.streaming }"
            @click="selectPhoneCamera(uid)"
          >
            <div class="camera-status">
              <span :class="phone.streaming ? 'status-streaming' : 'status-offline'"></span>
            </div>
            <div class="camera-info">
              <div class="camera-name">CAM-{{ uid }}</div>
              <div class="camera-position" v-if="phone.location">
                {{ phone.location.latitude.toFixed(6) }}, {{ phone.location.longitude.toFixed(6) }}
              </div>
              <div class="camera-position" v-else>位置未知</div>
            </div>
            <div class="phone-streaming-indicator" v-if="phone.streaming">
              <el-icon><VideoCamera /></el-icon>
            </div>
          </div>
          <div v-if="Object.keys(phoneCameras).length === 0" class="empty-tip">
            暂无手机摄像头连接
          </div>
        </el-scrollbar>
      </div>
      <div class="alarm-list-panel" v-if="alarms.length > 0" :class="{ collapsed: alarmPanelCollapsed }" :style="alarmPanelStyle">
        <div class="panel-header">
          <el-icon><WarningFilled /></el-icon>
          <span v-if="!alarmPanelCollapsed">告警位置 ({{ alarms.length }})</span>
          <div class="panel-actions">
            <el-button size="small" @click="toggleAlarmPanel" circle>
              <el-icon><Expand v-if="alarmPanelCollapsed" /><Fold v-else /></el-icon>
            </el-button>
            <el-button size="small" @click="startMovingAlarmPanel" circle>
              <el-icon>✋</el-icon>
            </el-button>
          </div>
        </div>
        <el-scrollbar v-if="!alarmPanelCollapsed" style="height: 240px;">
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
      <div v-if="selectedPhoneUid && phoneCameras[selectedPhoneUid]?.streaming" class="phone-video-overlay" :style="phoneVideoStyle">
        <div class="phone-video-header">
          <span>手机摄像头 CAM-{{ selectedPhoneUid }}</span>
          <el-button size="small" @click="closePhoneVideo" circle>
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <canvas ref="phoneViewerCanvas" class="phone-viewer-canvas"></canvas>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import MainLayout from '../../components/MainLayout.vue'
import { Refresh, Location, WarningFilled, Expand, Fold, Phone, VideoCamera, Close } from '@element-plus/icons-vue'
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
const phoneCameraMarkers = ref({})

const phoneCameras = ref({})
const selectedPhoneUid = ref(null)
const phoneViewerCanvas = ref(null)
let phoneViewerWs = null
const phoneViewerConnected = ref(false)
const phoneVideoStyle = ref({ bottom: '20px', right: '20px', width: '320px', height: '240px' })

const cameraPanelCollapsed = ref(false)
const cameraPanelStyle = ref({ top: '80px', left: '20px' })
const isMovingCameraPanel = ref(false)
const initialMousePosition = ref({ x: 0, y: 0 })
const initialPanelPosition = ref({ x: 0, y: 0 })

const phonePanelCollapsed = ref(false)
const phonePanelStyle = ref({ top: '340px', left: '20px' })
const isMovingPhonePanel = ref(false)
const initialPhoneMousePosition = ref({ x: 0, y: 0 })
const initialPhonePanelPosition = ref({ x: 0, y: 0 })

const alarmPanelCollapsed = ref(false)
const alarmPanelStyle = ref({ top: '80px', right: '20px' })
const isMovingAlarmPanel = ref(false)
const initialAlarmMousePosition = ref({ x: 0, y: 0 })
const initialAlarmPanelPosition = ref({ x: 0, y: 0 })

const STORAGE_KEY = 'phone_camera_locations'

const loadPhoneCameraLocations = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.error('加载手机摄像头位置失败:', e)
  }
  return {}
}

const savePhoneCameraLocations = (locations) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(locations))
  } catch (e) {
    console.error('保存手机摄像头位置失败:', e)
  }
}

const PI = 3.1415926535897932384626
const A = 6378245.0
const EE = 0.00669342162296594323

const transformLat = (x, y) => {
  let ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x))
  ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0
  ret += (20.0 * Math.sin(y * PI) + 40.0 * Math.sin(y / 3.0 * PI)) * 2.0 / 3.0
  ret += (160.0 * Math.sin(y / 12.0 * PI) + 320.0 * Math.sin(y * PI / 30.0)) * 2.0 / 3.0
  return ret
}

const transformLon = (x, y) => {
  let ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x))
  ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0
  ret += (20.0 * Math.sin(x * PI) + 40.0 * Math.sin(x / 3.0 * PI)) * 2.0 / 3.0
  ret += (150.0 * Math.sin(x / 12.0 * PI) + 300.0 * Math.sin(x / 30.0 * PI)) * 2.0 / 3.0
  return ret
}

const wgs84ToGcj02 = (lat, lon) => {
  let dLat = transformLat(lon - 105.0, lat - 35.0)
  let dLon = transformLon(lon - 105.0, lat - 35.0)
  const radLat = lat / 180.0 * PI
  let magic = Math.sin(radLat)
  magic = 1 - EE * magic * magic
  const sqrtMagic = Math.sqrt(magic)
  dLat = (dLat * 180.0) / ((A * (1 - EE)) / (magic * sqrtMagic) * PI)
  dLon = (dLon * 180.0) / (A / sqrtMagic * Math.cos(radLat) * PI)
  const converted = {
    latitude: lat + dLat,
    longitude: lon + dLon
  }
  console.log(`坐标转换: GPS(${lat.toFixed(6)}, ${lon.toFixed(6)}) -> 高德(${converted.latitude.toFixed(6)}, ${converted.longitude.toFixed(6)})`)
  return converted
}

const gpsToAmap = (lat, lng) => {
  const converted = wgs84ToGcj02(lat, lng)
  return { latitude: converted.latitude, longitude: converted.longitude }
}

const connectPhoneViewer = (uid) => {
  if (phoneViewerWs) {
    phoneViewerWs.close()
    phoneViewerWs = null
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/api/v1/camera_infos/phone_camera/viewer`

  phoneViewerWs = new WebSocket(wsUrl)

  phoneViewerWs.onopen = () => {
    phoneViewerConnected.value = true
    console.log('手机观看WebSocket已连接')
  }

  phoneViewerWs.onmessage = (event) => {
    if (!event.data) return
    const t0 = Date.now()

    if (typeof event.data === 'string') {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'phone_connected' && msg.uid === uid) {
          phoneCameras.value[uid] = {
            ...phoneCameras.value[uid],
            meta: msg.meta,
            streaming: true
          }
        }
      } catch (e) {
        console.error('解析JSON消息失败:', e)
      }
    } else if (event.data instanceof Blob || event.data instanceof ArrayBuffer) {
      const blob = event.data instanceof ArrayBuffer ? new Blob([event.data]) : event.data
      const url = URL.createObjectURL(blob)
      const img = new Image()
      img.onload = () => {
        if (phoneViewerCanvas.value) {
          const canvas = phoneViewerCanvas.value
          canvas.width = Math.min(img.width, 640)
          canvas.height = Math.round(canvas.width * (img.height / img.width))
          const ctx = canvas.getContext('2d')
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
        }
        URL.revokeObjectURL(url)
      }
      img.src = url
    }
  }

  phoneViewerWs.onclose = () => {
    phoneViewerConnected.value = false
    console.log('手机观看WebSocket已关闭')
  }

  phoneViewerWs.onerror = (error) => {
    console.error('手机观看WebSocket错误:', error)
  }
}

const closePhoneVideo = () => {
  if (phoneViewerWs) {
    phoneViewerWs.close()
    phoneViewerWs = null
  }
  phoneViewerConnected.value = false
  selectedPhoneUid.value = null
}

const selectPhoneCamera = (uid) => {
  selectedPhoneUid.value = uid
  if (phoneCameras.value[uid]?.location) {
    const loc = phoneCameras.value[uid].location
    map.setCenter([loc.longitude, loc.latitude])
    map.setZoom(18)
  }
  if (!phoneViewerConnected.value) {
    connectPhoneViewer(uid)
  }
}

const updatePhoneCameraOnMap = (uid, data) => {
  const phone = phoneCameras.value[uid] || {}
  const updatedPhone = {
    ...phone,
    ...data,
    uid: uid
  }

  if (data.location) {
    const amapCoords = gpsToAmap(data.location.latitude, data.location.longitude)
    const storedLocations = loadPhoneCameraLocations()
    storedLocations[uid] = {
      latitude: amapCoords.latitude,
      longitude: amapCoords.longitude,
      originalLat: data.location.latitude,
      originalLng: data.location.longitude,
      timestamp: Date.now()
    }
    savePhoneCameraLocations(storedLocations)
    updatedPhone.location = amapCoords
  }

  phoneCameras.value[uid] = updatedPhone
  renderPhoneCameraMarker(uid, updatedPhone)
}

const renderPhoneCameraMarker = (uid, phone) => {
  console.log('renderPhoneCameraMarker called:', { uid, phone, hasMap: !!map, hasAMap: !!AMap, location: phone?.location })
  if (!map || !AMap || !phone?.location) {
    console.log('renderPhoneCameraMarker: early return, map or location missing')
    return
  }

  if (phoneCameraMarkers.value[uid]) {
    map.remove(phoneCameraMarkers.value[uid])
  }

  const icon = new AMap.Icon({
    size: new AMap.Size(48, 48),
    imageSize: new AMap.Size(48, 48),
    image: `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="white" stroke="${phone.streaming ? '#67c23a' : '#909399'}" stroke-width="4"/><text x="50" y="65" text-anchor="middle" font-size="36" fill="${phone.streaming ? '#67c23a' : '#909399'}">📱</text></svg>`
  })

  const marker = new AMap.Marker({
    position: [phone.location.longitude, phone.location.latitude],
    icon: icon,
    title: `手机摄像头 CAM-${uid}`,
    zIndex: 20
  })

  const infoContent = `
    <div style="padding: 10px;">
      <h4 style="margin: 0 0 10px 0;">手机摄像头 CAM-${uid}</h4>
      <p style="margin: 0 0 5px 0;">设备ID: ${uid}</p>
      <p style="margin: 0 0 5px 0;">位置: ${phone.location.latitude.toFixed(6)}, ${phone.location.longitude.toFixed(6)}</p>
      <p style="margin: 0; color: ${phone.streaming ? '#67c23a' : '#909399'};">${phone.streaming ? '● 推流中' : '○ 待机'}</p>
      <p style="margin: 5px 0 0 0; color: #409eff; font-size: 12px; cursor: pointer;" onclick="window.selectPhoneCameraMarker('${uid}')">点击查看视频</p>
    </div>
  `

  const infoWindow = new AMap.InfoWindow({
    content: infoContent,
    offset: new AMap.Pixel(0, -24)
  })

  marker.on('click', () => {
    selectPhoneCamera(uid)
    infoWindow.open(map, marker.getPosition())
  })

  map.add(marker)
  phoneCameraMarkers.value[uid] = marker
  console.log(`手机摄像头标记已添加: CAM-${uid}, 位置: ${phone.location.longitude}, ${phone.location.latitude}`)
}

const toggleCameraPanel = () => {
  cameraPanelCollapsed.value = !cameraPanelCollapsed.value
}

const startMovingCameraPanel = (e) => {
  e.preventDefault()
  isMovingCameraPanel.value = true
  initialMousePosition.value = { x: e.clientX, y: e.clientY }
  const panelRect = document.querySelector('.camera-list-panel').getBoundingClientRect()
  initialPanelPosition.value = { x: panelRect.left, y: panelRect.top }
  document.addEventListener('mousemove', handleCameraPanelMove)
  document.addEventListener('mouseup', stopMovingCameraPanel)
}

const handleCameraPanelMove = (e) => {
  if (!isMovingCameraPanel.value) return
  const dx = e.clientX - initialMousePosition.value.x
  const dy = e.clientY - initialMousePosition.value.y
  cameraPanelStyle.value = {
    top: `${initialPanelPosition.value.y + dy}px`,
    left: `${initialPanelPosition.value.x + dx}px`
  }
}

const stopMovingCameraPanel = () => {
  isMovingCameraPanel.value = false
  document.removeEventListener('mousemove', handleCameraPanelMove)
  document.removeEventListener('mouseup', stopMovingCameraPanel)
}

const togglePhonePanel = () => {
  phonePanelCollapsed.value = !phonePanelCollapsed.value
}

const startMovingPhonePanel = (e) => {
  e.preventDefault()
  isMovingPhonePanel.value = true
  initialPhoneMousePosition.value = { x: e.clientX, y: e.clientY }
  const panelRect = document.querySelector('.phone-camera-list-panel').getBoundingClientRect()
  initialPhonePanelPosition.value = { x: panelRect.left, y: panelRect.top }
  document.addEventListener('mousemove', handlePhonePanelMove)
  document.addEventListener('mouseup', stopMovingPhonePanel)
}

const handlePhonePanelMove = (e) => {
  if (!isMovingPhonePanel.value) return
  const dx = e.clientX - initialPhoneMousePosition.value.x
  const dy = e.clientY - initialPhoneMousePosition.value.y
  phonePanelStyle.value = {
    top: `${initialPhonePanelPosition.value.y + dy}px`,
    left: `${initialPhonePanelPosition.value.x + dx}px`
  }
}

const stopMovingPhonePanel = () => {
  isMovingPhonePanel.value = false
  document.removeEventListener('mousemove', handlePhonePanelMove)
  document.removeEventListener('mouseup', stopMovingPhonePanel)
}

const toggleAlarmPanel = () => {
  alarmPanelCollapsed.value = !alarmPanelCollapsed.value
}

const startMovingAlarmPanel = (e) => {
  e.preventDefault()
  isMovingAlarmPanel.value = true
  initialAlarmMousePosition.value = { x: e.clientX, y: e.clientY }
  const panelRect = document.querySelector('.alarm-list-panel').getBoundingClientRect()
  initialAlarmPanelPosition.value = { x: panelRect.right, y: panelRect.top }
  document.addEventListener('mousemove', handleAlarmPanelMove)
  document.addEventListener('mouseup', stopMovingAlarmPanel)
}

const handleAlarmPanelMove = (e) => {
  if (!isMovingAlarmPanel.value) return
  const dx = e.clientX - initialAlarmMousePosition.value.x
  const dy = e.clientY - initialAlarmMousePosition.value.y
  alarmPanelStyle.value = {
    top: `${initialAlarmPanelPosition.value.y + dy}px`,
    right: `${window.innerWidth - (initialAlarmPanelPosition.value.x + dx)}px`
  }
}

const stopMovingAlarmPanel = () => {
  isMovingAlarmPanel.value = false
  document.removeEventListener('mousemove', handleAlarmPanelMove)
  document.removeEventListener('mouseup', stopMovingAlarmPanel)
}

const initPhoneCameraWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/api/v1/camera_infos/phone_camera/viewer`

  const ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('地图页面手机摄像头WebSocket已连接')
  }

  ws.onmessage = (event) => {
    if (!event.data) return

    if (typeof event.data === 'string') {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'phone_connected') {
          const uid = msg.uid
          const meta = msg.meta || {}
          updatePhoneCameraOnMap(uid, {
            meta: meta,
            location: meta.location || null,
            streaming: true
          })
          ElMessage.success(`手机摄像头 CAM-${uid} 已连接`)
        } else if (msg.type === 'phone_disconnected') {
          const uid = msg.uid
          if (phoneCameras.value[uid]) {
            phoneCameras.value[uid].streaming = false
            renderPhoneCameraMarker(uid, phoneCameras.value[uid])
          }
          ElMessage.warning(`手机摄像头 CAM-${uid} 已断开`)
        }
      } catch (e) {
        console.error('解析WebSocket消息失败:', e)
      }
    }
  }

  ws.onclose = () => {
    console.log('地图页面手机摄像头WebSocket已关闭，3秒后重连...')
    setTimeout(initPhoneCameraWebSocket, 3000)
  }

  ws.onerror = (error) => {
    console.error('地图页面手机摄像头WebSocket错误:', error)
  }

  return ws
}

let phoneWs = null

onMounted(() => {
  window.selectPhoneCameraMarker = selectPhoneCamera
  initMap()
  phoneWs = initPhoneCameraWebSocket()
})

onUnmounted(() => {
  window.selectPhoneCameraMarker = null
  if (phoneWs) {
    phoneWs.close()
  }
  closePhoneVideo()
  if (map) {
    map.destroy()
  }
})

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
    
    renderPhoneCameraMarkersFromStorage()
  } catch (e) {
    console.error('高德地图加载失败:', e)
    console.error('错误堆栈:', e.stack)
    ElMessage.error(`地图加载失败: ${e.message || '请检查API Key配置、安全密钥和域名白名单'}`)
  }
}

const renderPhoneCameraMarkersFromStorage = () => {
  const storedLocations = loadPhoneCameraLocations()
  console.log('从localStorage加载手机摄像头位置:', storedLocations)
  for (const uid in storedLocations) {
    const loc = storedLocations[uid]
    phoneCameras.value[uid] = {
      uid: uid,
      location: { latitude: loc.latitude, longitude: loc.longitude },
      streaming: false
    }
    console.log(`渲染手机摄像头标记 CAM-${uid}:`, loc.latitude, loc.longitude)
    renderPhoneCameraMarker(uid, phoneCameras.value[uid])
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
  transition: all 0.3s ease;
}

.phone-camera-list-panel {
  position: absolute;
  top: 340px;
  left: 20px;
  width: 280px;
  max-height: 260px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
  transition: all 0.3s ease;
}

.el-scrollbar {
  height: calc(100% - 48px);
  overflow-y: auto;
}

.panel-header {
  padding: 12px 16px;
  font-weight: 600;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #303133;
  justify-content: space-between;
}

.panel-actions {
  display: flex;
  gap: 4px;
}

.camera-list-panel.collapsed,
.phone-camera-list-panel.collapsed,
.alarm-list-panel.collapsed {
  width: 60px;
  max-height: 48px;
  transition: all 0.3s ease;
}

.camera-list-panel.collapsed .panel-header,
.phone-camera-list-panel.collapsed .panel-header,
.alarm-list-panel.collapsed .panel-header {
  border-bottom: none;
  padding: 8px;
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
  overflow: hidden;
  transition: all 0.3s ease;
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

.camera-item.streaming {
  background: #f0f9eb;
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

.status-streaming {
  background: #67c23a;
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
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.camera-alarm {
  color: #f56c6c;
}

.phone-streaming-indicator {
  color: #67c23a;
}

.empty-tip {
  padding: 20px;
  text-align: center;
  color: #909399;
  font-size: 13px;
}

.phone-video-overlay {
  position: absolute;
  background: rgba(0, 0, 0, 0.9);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
  z-index: 2000;
}

.phone-video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 13px;
}

.phone-viewer-canvas {
  width: 100%;
  height: calc(100% - 36px);
  display: block;
}
</style>