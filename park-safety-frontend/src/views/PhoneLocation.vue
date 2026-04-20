<template>
  <div class="phone-location-container">
    <div class="header">
      <h2>获取位置信息</h2>
      <p>点击下方按钮获取您的当前位置</p>
    </div>
    
    <div class="status-section" v-if="status !== 'success'">
      <div class="status-icon" :class="status">
        <el-icon :size="60">
          <Location v-if="status === 'idle'" />
          <Loading v-else-if="status === 'loading'" class="is-loading" />
          <CircleClose v-else-if="status === 'error'" />
        </el-icon>
      </div>
      <div class="status-text">
        <p>{{ statusText }}</p>
      </div>
    </div>
    
    <div class="location-info" v-if="currentLocation && status === 'success'">
      <div class="info-item">
        <span class="label">纬度:</span>
        <span class="value">{{ currentLocation.latitude.toFixed(6) }}</span>
      </div>
      <div class="info-item">
        <span class="label">经度:</span>
        <span class="value">{{ currentLocation.longitude.toFixed(6) }}</span>
      </div>
      <div class="info-item" v-if="currentLocation.accuracy">
        <span class="label">精度:</span>
        <span class="value">{{ Math.round(currentLocation.accuracy) }} 米</span>
      </div>
      <div class="info-item" v-if="currentLocation.address">
        <span class="label">地址:</span>
        <span class="value address">{{ currentLocation.address }}</span>
      </div>
    </div>
    
    <div class="action-section">
      <el-button 
        type="primary" 
        size="large" 
        @click="getLocation" 
        :loading="status === 'loading'"
        :disabled="status === 'success'"
        class="get-location-btn"
      >
        获取位置
      </el-button>
      
      <el-button 
        type="success" 
        size="large" 
        @click="sendLocation" 
        :disabled="!currentLocation || status !== 'success'"
        v-if="currentLocation"
        class="send-location-btn"
      >
        发送位置
      </el-button>
      
      <el-button 
        size="large" 
        @click="reset"
        v-if="status === 'success'"
      >
        重新获取
      </el-button>
    </div>
    
    <div class="instruction-section">
      <h3>使用说明:</h3>
      <ol>
        <li>确保手机GPS已开启</li>
        <li>允许浏览器访问位置权限</li>
        <li>在室外或靠近窗户的位置以获得更好的信号</li>
        <li>获取位置后点击"发送位置"将位置传回</li>
      </ol>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Location, Loading, CircleClose } from '@element-plus/icons-vue'

const status = ref('idle')
const currentLocation = ref(null)

const statusText = computed(() => {
  const map = {
    'idle': '点击下方按钮获取位置',
    'loading': '正在获取位置，请稍候...',
    'error': '获取位置失败，请检查GPS是否开启',
    'success': '位置获取成功！'
  }
  return map[status.value]
})

const getLocation = () => {
  if (!navigator.geolocation) {
    ElMessage.error('您的浏览器不支持地理位置功能')
    status.value = 'error'
    return
  }

  status.value = 'loading'

  navigator.geolocation.getCurrentPosition(
    (position) => {
      currentLocation.value = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy
      }
      status.value = 'success'
      ElMessage.success('位置获取成功！')
    },
    (error) => {
      console.error('Geolocation error:', error)
      let errorMsg = '获取位置失败'
      switch(error.code) {
        case 1:
          errorMsg = '您拒绝了位置访问权限'
          break
        case 2:
          errorMsg = '无法获取位置信息'
          break
        case 3:
          errorMsg = '获取位置超时'
          break
      }
      ElMessage.error(errorMsg)
      status.value = 'error'
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0
    }
  )
}

const sendLocation = () => {
  if (!currentLocation.value) {
    ElMessage.warning('请先获取位置')
    return
  }

  try {
    const message = {
      type: 'location',
      data: currentLocation.value
    }
    
    if (window.opener) {
      window.opener.postMessage(message, '*')
      ElMessage.success('位置已发送！')
      setTimeout(() => window.close(), 1000)
    } else {
      ElMessage.warning('请通过主页面打开此页面')
    }
  } catch (error) {
    console.error('Send location error:', error)
    ElMessage.error('发送位置失败')
  }
}

const reset = () => {
  status.value = 'idle'
  currentLocation.value = null
}

onMounted(() => {
  getLocation()
})
</script>

<style scoped>
.phone-location-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 40px 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header {
  text-align: center;
  color: white;
  margin-bottom: 40px;
}

.header h2 {
  font-size: 28px;
  margin-bottom: 10px;
}

.header p {
  opacity: 0.9;
  font-size: 16px;
}

.status-section {
  background: white;
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  margin-bottom: 30px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.status-icon {
  margin-bottom: 20px;
}

.status-icon.idle {
  color: #909399;
}

.status-icon.loading {
  color: #409eff;
}

.status-icon.error {
  color: #f56c6c;
}

.status-text p {
  font-size: 16px;
  color: #606266;
  margin: 0;
}

.location-info {
  background: white;
  border-radius: 16px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  font-weight: 500;
  color: #606266;
  font-size: 15px;
}

.info-item .value {
  font-size: 15px;
  color: #303133;
  font-weight: 600;
}

.info-item .value.address {
  max-width: 60%;
  word-wrap: break-word;
  text-align: right;
}

.action-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 30px;
}

.get-location-btn,
.send-location-btn {
  width: 100%;
  height: 50px;
  font-size: 17px;
  border-radius: 12px;
}

.instruction-section {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  padding: 30px;
  color: white;
}

.instruction-section h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 20px;
}

.instruction-section ol {
  margin: 0;
  padding-left: 20px;
}

.instruction-section li {
  margin-bottom: 12px;
  line-height: 1.6;
  font-size: 15px;
  opacity: 0.95;
}
</style>
