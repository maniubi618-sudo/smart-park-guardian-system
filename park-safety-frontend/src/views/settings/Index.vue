<template>
  <MainLayout>
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
            <el-card class="setting-section" shadow="never">
              <template #header>
                <div class="section-header">
                  <span class="section-title">功能开关</span>
                </div>
              </template>
              <el-form :model="detectionSettings" label-width="140px">
                <el-form-item label="安全帽检测">
                  <el-switch v-model="detectionSettings.enableHelmet" />
                  <span class="form-help">开启后检测是否佩戴安全帽</span>
                </el-form-item>
                <el-form-item label="反光衣检测">
                  <el-switch v-model="detectionSettings.enableVest" />
                  <span class="form-help">开启后检测是否穿戴反光衣</span>
                </el-form-item>
                <el-form-item label="区域入侵检测">
                  <el-switch v-model="detectionSettings.enableVehicleIntrusion" />
                  <span class="form-help">开启后检测区域内的人体和车辆</span>
                </el-form-item>
                <el-form-item label="火警检测">
                  <el-switch v-model="detectionSettings.enableFire" />
                  <span class="form-help">开启后检测火焰和烟雾</span>
                </el-form-item>
              </el-form>
            </el-card>
            
            <el-card class="setting-section" shadow="never" style="margin-top: 20px;">
              <template #header>
                <div class="section-header">
                  <span class="section-title">检测阈值</span>
                </div>
              </template>
              <el-form :model="detectionSettings" label-width="140px">
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
            </el-card>
          </el-tab-pane>
          
          <!-- 农业检测参数配置 -->
          <el-tab-pane label="农业检测">
            <el-card class="setting-section" shadow="never">
              <template #header>
                <div class="section-header">
                  <span class="section-title">柑橘成熟度检测</span>
                </div>
              </template>
              <el-form :model="agricultureSettings" label-width="140px">
                <el-form-item label="置信度阈值">
                  <el-slider
                    v-model="agricultureSettings.citrusConfidence"
                    :min="0.05"
                    :max="0.8"
                    :step="0.01"
                    show-input
                    :marks="{ 0.1: '0.1', 0.25: '0.25', 0.5: '0.5', 0.8: '0.8' }"
                  />
                  <span class="form-help">值越低检出越多，可能误报。建议值：0.25</span>
                </el-form-item>
                
                <el-form-item label="IOU阈值">
                  <el-slider
                    v-model="agricultureSettings.citrusIouThreshold"
                    :min="0.1"
                    :max="0.8"
                    :step="0.01"
                    show-input
                  />
                  <span class="form-help">值越高去重越严格，可能漏检重叠目标。建议值：0.45</span>
                </el-form-item>
              </el-form>
            </el-card>
            
            <el-card class="setting-section" shadow="never" style="margin-top: 20px;">
              <template #header>
                <div class="section-header">
                  <span class="section-title">作物病害检测</span>
                </div>
              </template>
              <el-form :model="agricultureSettings" label-width="140px">
                <el-form-item label="置信度阈值">
                  <el-slider
                    v-model="agricultureSettings.cropDiseaseConfidence"
                    :min="0.05"
                    :max="0.8"
                    :step="0.01"
                    show-input
                  />
                  <span class="form-help">通用兜底阈值。番茄、苹果、水稻优先使用下方专用阈值。</span>
                </el-form-item>

                <el-form-item v-if="agricultureSettings.cropDiseaseConfidenceByCrop" label="番茄阈值">
                  <el-slider
                    v-model="agricultureSettings.cropDiseaseConfidenceByCrop.tomato"
                    :min="0.05"
                    :max="0.8"
                    :step="0.01"
                    show-input
                  />
                </el-form-item>

                <el-form-item v-if="agricultureSettings.cropDiseaseConfidenceByCrop" label="苹果阈值">
                  <el-slider
                    v-model="agricultureSettings.cropDiseaseConfidenceByCrop.apple"
                    :min="0.05"
                    :max="0.8"
                    :step="0.01"
                    show-input
                  />
                </el-form-item>

                <el-form-item v-if="agricultureSettings.cropDiseaseConfidenceByCrop" label="水稻阈值">
                  <el-slider
                    v-model="agricultureSettings.cropDiseaseConfidenceByCrop.rice"
                    :min="0.05"
                    :max="0.8"
                    :step="0.01"
                    show-input
                  />
                  <span class="form-help">值越低检出越多，可能误报；水稻模型分数偏低，建议 0.05。</span>
                </el-form-item>
                
                <el-form-item label="IOU阈值">
                  <el-slider
                    v-model="agricultureSettings.cropDiseaseIouThreshold"
                    :min="0.1"
                    :max="0.8"
                    :step="0.01"
                    show-input
                  />
                  <span class="form-help">值越高越保留重叠框，减少小病斑被合并。建议值：0.50-0.55</span>
                </el-form-item>

                <el-form-item label="空画面过滤">
                  <el-switch v-model="agricultureSettings.cropDiseaseRequireCropContent" />
                  <span class="form-help">开启后，黑屏、空画面、无明显作物区域的帧不会触发病害提示。</span>
                </el-form-item>

                <el-form-item label="作物占比下限">
                  <el-slider
                    v-model="agricultureSettings.cropDiseaseMinCropContentRatio"
                    :min="0.005"
                    :max="0.08"
                    :step="0.001"
                    show-input
                  />
                  <span class="form-help">误报多就调高，漏检弱画面就调低。建议值：0.015</span>
                </el-form-item>
              </el-form>
            </el-card>
            
            <div class="button-group" style="margin-top: 20px;">
              <el-button @click="resetToDefault" type="info">
                重置默认值
              </el-button>
            </div>
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

              <el-form-item label="启用QQ推送通知">
                <el-switch v-model="notificationSettings.enableOpenClaw" />
                <span class="form-help">通过QQ机器人发送告警通知（需OpenClaw Gateway运行）</span>
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
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout from '../../components/MainLayout.vue'
import { configApi } from '../../services/api.js'

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
  debounceTime: 1,
  enableHelmet: true,
  enableVest: true,
  enableVehicleIntrusion: true,
  enableFire: true
})

// 农业检测配置
const agricultureSettings = ref({
  citrusConfidence: 0.25,
  citrusIouThreshold: 0.45,
  cropDiseaseConfidence: 0.25,
  cropDiseaseIouThreshold: 0.55,
  cropDiseaseEnableTTA: true,
  cropDiseaseEnablePreprocess: false,
  cropDiseaseConfidenceByCrop: {
    tomato: 0.45,
    apple: 0.20,
    rice: 0.05
  },
  cropDiseaseIouByCrop: {
    tomato: 0.55,
    apple: 0.50,
    rice: 0.55
  },
  cropDiseaseRequireCropContent: true,
  cropDiseaseMinCropContentRatio: 0.015,
  cropDiseaseMinCropContentRatioByCrop: {
    tomato: 0.30,
    rice: 0.12
  },
  cropDiseaseMinGreenRatioByCrop: {},
  cropDiseaseMinBoxAreaRatio: 0.003,
  cropDiseaseHealthySuppressionMargin: 0.0
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
  enableOpenClaw: true,
  emailServer: '',
  emailPort: 587,
  emailSender: '',
  emailPassword: '',
  emailRecipients: ''
})

// 加载配置
const loadSettings = async () => {
  try {
    const response = await configApi.getConfig()
    if (response.success && response.data) {
      const config = response.data
      if (config.detection) {
        detectionSettings.value = { ...detectionSettings.value, ...config.detection }
      }
      if (config.agriculture) {
        agricultureSettings.value = { ...agricultureSettings.value, ...config.agriculture }
      }
      if (config.system) {
        systemSettings.value = { ...systemSettings.value, ...config.system }
      }
      if (config.notification) {
        notificationSettings.value = { ...notificationSettings.value, ...config.notification }
      }
    }
    console.log('配置加载成功')
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

// 保存配置
const saveSettings = async () => {
  loading.value = true
  message.value = ''
  
  try {
    const configData = {
      detection: detectionSettings.value,
      agriculture: agricultureSettings.value,
      system: systemSettings.value,
      notification: notificationSettings.value
    }
    
    const response = await configApi.updateConfig(configData)
    
    if (response.success) {
      message.value = '配置保存成功！'
      messageType.value = 'success'
    } else {
      message.value = response.message || '保存配置失败'
      messageType.value = 'error'
    }
    
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

// 重置为默认值
const resetToDefault = () => {
  agricultureSettings.value = {
    citrusConfidence: 0.25,
    citrusIouThreshold: 0.45,
    cropDiseaseConfidence: 0.25,
    cropDiseaseIouThreshold: 0.55,
    cropDiseaseEnableTTA: true,
    cropDiseaseEnablePreprocess: false,
    cropDiseaseConfidenceByCrop: {
      tomato: 0.45,
      apple: 0.20,
      rice: 0.05
    },
    cropDiseaseIouByCrop: {
      tomato: 0.55,
      apple: 0.50,
      rice: 0.55
    },
    cropDiseaseRequireCropContent: true,
    cropDiseaseMinCropContentRatio: 0.015,
    cropDiseaseMinCropContentRatioByCrop: {
      tomato: 0.30,
      rice: 0.12
    },
    cropDiseaseMinGreenRatioByCrop: {},
    cropDiseaseMinBoxAreaRatio: 0.003,
    cropDiseaseHealthySuppressionMargin: 0.0
  }
  message.value = '已重置为默认值，点击保存生效'
  messageType.value = 'info'
  setTimeout(() => {
    message.value = ''
  }, 3000)
}

// 页面加载时获取配置
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-container {
  width: 100%;
  min-height: calc(100vh - 136px);
}

.settings-card {
  max-width: 1180px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.card-title {
  color: var(--text-color);
  font-size: 18px;
  font-weight: 850;
  margin: 0;
}

.message-alert {
  margin-bottom: 18px;
}

.form-help {
  display: inline-flex;
  margin-left: 12px;
  color: var(--text-color-muted);
  font-size: 12px;
  font-weight: 600;
}

.el-tabs {
  margin-top: 18px;
}

.el-form-item {
  margin-bottom: 18px;
}

.setting-section + .setting-section {
  margin-top: 18px !important;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  position: relative;
  padding-left: 12px;
  color: var(--text-color);
  font-size: 15px;
  font-weight: 850;
}

.section-title::before {
  content: "";
  position: absolute;
  left: 0;
  top: 50%;
  width: 4px;
  height: 16px;
  border-radius: 999px;
  background: var(--primary-color);
  transform: translateY(-50%);
}

.button-group {
  display: flex;
  gap: 10px;
}
</style>
