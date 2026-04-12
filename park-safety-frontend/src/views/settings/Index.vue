<template>
  <div class="settings-container">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <h2 class="card-title">系统配置</h2>
          <el-button type="primary" @click="saveSettings" :loading="loading" :disabled="loading">
            保存配置
          </el-button>
        </div>
      </template>

      <el-alert
        v-if="message"
        :title="message"
        :type="messageType"
        show-icon
        :closable="false"
        class="message-alert"
      />

      <el-tabs type="border-card">
        <!-- 检测参数配置 -->
        <el-tab-pane label="检测参数">
          <el-form :model="detectionSettings" label-width="120px">
            <el-form-item label="火灾检测阈值">
              <el-slider
                v-model="detectionSettings.fireThreshold"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
              />
              <span class="form-help">值越低灵敏度越高，建议值：0.7</span>
            </el-form-item>

            <el-form-item label="安全帽检测阈值">
              <el-slider
                v-model="detectionSettings.helmetThreshold"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
              />
              <span class="form-help">值越低灵敏度越高，建议值：0.7</span>
            </el-form-item>

            <el-form-item label="反光衣检测阈值">
              <el-slider
                v-model="detectionSettings.vestThreshold"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
              />
              <span class="form-help">值越低灵敏度越高，建议值：0.7</span>
            </el-form-item>

            <el-form-item label="告警延迟（秒）">
              <el-input-number v-model="detectionSettings.alarmDelay" :min="0" :max="60" :step="1" />
              <span class="form-help">告警触发前的延迟时间，建议值：0</span>
            </el-form-item>

            <el-form-item label="防抖时间（秒）">
              <el-input-number v-model="detectionSettings.debounceTime" :min="0" :max="60" :step="1" />
              <span class="form-help">避免瞬时误报的防抖时间，建议值：1</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 系统配置 -->
        <el-tab-pane label="系统配置">
          <el-form :model="systemSettings" label-width="120px">
            <el-form-item label="数据库主机">
              <el-input v-model="systemSettings.dbHost" placeholder="输入数据库主机地址" />
            </el-form-item>

            <el-form-item label="数据库端口">
              <el-input-number v-model="systemSettings.dbPort" :min="1" :max="65535" />
            </el-form-item>

            <el-form-item label="数据库用户">
              <el-input v-model="systemSettings.dbUser" placeholder="输入数据库用户名" />
            </el-form-item>

            <el-form-item label="数据库密码">
              <el-input v-model="systemSettings.dbPassword" type="password" placeholder="输入数据库密码" />
            </el-form-item>

            <el-form-item label="数据库名称">
              <el-input v-model="systemSettings.dbName" placeholder="输入数据库名称" />
            </el-form-item>

            <el-form-item label="告警快照保存路径">
              <el-input v-model="systemSettings.snapshotPath" placeholder="输入快照保存路径" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 告警通知配置 -->
        <el-tab-pane label="告警通知">
          <el-form :model="notificationSettings" label-width="120px">
            <el-form-item label="启用WebSocket推送">
              <el-switch v-model="notificationSettings.enableWebSocket" />
            </el-form-item>

            <el-form-item label="启用邮件通知">
              <el-switch v-model="notificationSettings.enableEmail" />
            </el-form-item>

            <el-form-item label="邮件服务器">
              <el-input v-model="notificationSettings.emailServer" placeholder="输入邮件服务器地址" />
            </el-form-item>

            <el-form-item label="邮件端口">
              <el-input-number v-model="notificationSettings.emailPort" :min="1" :max="65535" />
            </el-form-item>

            <el-form-item label="发件人邮箱">
              <el-input v-model="notificationSettings.emailSender" placeholder="输入发件人邮箱" />
            </el-form-item>

            <el-form-item label="发件人密码">
              <el-input v-model="notificationSettings.emailPassword" type="password" placeholder="输入发件人密码" />
            </el-form-item>

            <el-form-item label="接收人邮箱">
              <el-input v-model="notificationSettings.emailRecipients" placeholder="多个邮箱用逗号分隔" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const message = ref('')
const messageType = ref('success')

// 检测参数配置
const detectionSettings = ref({
  fireThreshold: 0.7,
  helmetThreshold: 0.7,
  vestThreshold: 0.7,
  alarmDelay: 0,
  debounceTime: 1
})

// 系统配置
const systemSettings = ref({
  dbHost: 'localhost',
  dbPort: 3306,
  dbUser: 'root',
  dbPassword: '123456',
  dbName: 'yolo_safety',
  snapshotPath: './snapshots/'
})

// 告警通知配置
const notificationSettings = ref({
  enableWebSocket: true,
  enableEmail: false,
  emailServer: '',
  emailPort: 587,
  emailSender: '',
  emailPassword: '',
  emailRecipients: ''
})

// 加载配置
const loadSettings = async () => {
  try {
    // 这里应该从后端API获取配置
    // 暂时使用默认值
    console.log('加载配置成功')
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

// 保存配置
const saveSettings = async () => {
  loading.value = true
  message.value = ''
  
  try {
    // 这里应该调用后端API保存配置
    // 暂时模拟保存成功
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    message.value = '配置保存成功！'
    messageType.value = 'success'
    
    // 3秒后清除消息
    setTimeout(() => {
      message.value = ''
    }, 3000)
  } catch (error) {
    console.error('保存配置失败:', error)
    message.value = '保存配置失败，请重试'
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

// 页面加载时获取配置
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-container {
  width: 100%;
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.settings-card {
  max-width: 1000px;
  margin: 0 auto;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.message-alert {
  margin-bottom: 20px;
}

.form-help {
  color: #909399;
  font-size: 12px;
  margin-left: 10px;
}

.el-tabs {
  margin-top: 20px;
}

.el-form-item {
  margin-bottom: 20px;
}
</style>
