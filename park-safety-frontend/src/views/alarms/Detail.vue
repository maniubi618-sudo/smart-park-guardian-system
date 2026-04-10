<template>
  <MainLayout>
    <div class="alarm-detail">
      <el-page-header @back="goBack" :content="`告警详情 #${alarmId}`" />

      <el-card class="detail-card" v-loading="loading">
        <template v-if="alarmDetail">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="告警ID">{{ alarmDetail.alarm_id }}</el-descriptions-item>
            <el-descriptions-item label="告警类型">
              <el-tag :type="getAlarmTypeTag(alarmDetail.alarm_type)">
                {{ getAlarmTypeName(alarmDetail.alarm_type) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="告警时间">{{ formatDateTime(alarmDetail.alarm_time) }}</el-descriptions-item>
            <el-descriptions-item label="告警状态">
              <el-tag :type="getAlarmStatusTag(alarmDetail.alarm_status)">
                {{ getAlarmStatusName(alarmDetail.alarm_status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="摄像头">{{ alarmDetail.camera_name }}</el-descriptions-item>
            <el-descriptions-item label="区域">{{ alarmDetail.park_area }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDateTime(alarmDetail.create_time) }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ formatDateTime(alarmDetail.update_time) }}</el-descriptions-item>
          </el-descriptions>

          <el-divider />

          <h3>处理记录</h3>
          <el-table :data="handleRecords" stripe style="width: 100%" v-if="handleRecords.length > 0">
            <el-table-column prop="handle_record_id" label="记录ID" width="100" align="center" />
            <el-table-column prop="handle_time" label="处理时间" width="180">
              <template #default="scope">
                {{ formatDateTime(scope.row.handle_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="handle_user_name" label="处理人" width="120" />
            <el-table-column prop="alarm_status" label="处理状态" width="120">
              <template #default="scope">
                <el-tag :type="getAlarmStatusTag(scope.row.alarm_status)">
                  {{ getAlarmStatusName(scope.row.alarm_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="handle_remark" label="处理备注" />
          </el-table>
          <el-empty v-else description="暂无处理记录" />

          <el-divider />

          <div class="action-buttons">
            <el-button type="primary" @click="handleAlarm">处理告警</el-button>
            <el-button @click="goBack">返回列表</el-button>
          </div>
        </template>
        <el-empty v-else description="暂无数据" />
      </el-card>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAlarmStore } from '../../stores/alarms'
import MainLayout from '../../components/MainLayout.vue'

const route = useRoute()
const router = useRouter()
const alarmStore = useAlarmStore()

const alarmId = ref(route.params.id)
const alarmDetail = ref(null)
const handleRecords = ref([])
const loading = ref(false)

const getAlarmTypeName = (type) => {
  const typeMap = {
    0: '安全规范',
    1: '区域入侵',
    2: '火警'
  }
  return typeMap[type] || '未知'
}

const getAlarmTypeTag = (type) => {
  const tagMap = {
    0: 'warning',
    1: 'danger',
    2: 'success'
  }
  return tagMap[type] || 'info'
}

const getAlarmStatusName = (status) => {
  const statusMap = {
    0: '未处理',
    1: '确认误报',
    2: '处理中',
    3: '处理完成'
  }
  return statusMap[status] || '未知'
}

const getAlarmStatusTag = (status) => {
  const tagMap = {
    0: 'danger',
    1: 'info',
    2: 'warning',
    3: 'success'
  }
  return tagMap[status] || 'info'
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const goBack = () => {
  router.push('/alarms')
}

const handleAlarm = () => {
  router.push(`/alarms`)
}

const fetchAlarmDetail = async () => {
  loading.value = true
  try {
    const result = await alarmStore.fetchAlarmById(alarmId.value)
    if (result.success) {
      alarmDetail.value = result.data
    }
  } catch (error) {
    console.error('获取告警详情失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchHandleRecords = async () => {
  try {
    const result = await alarmStore.fetchHandleRecords(alarmId.value)
    if (result.success) {
      handleRecords.value = result.data || []
    }
  } catch (error) {
    console.error('获取处理记录失败:', error)
  }
}

onMounted(() => {
  fetchAlarmDetail()
  fetchHandleRecords()
})
</script>

<style scoped>
.alarm-detail {
  padding: 20px;
  width: 100%;
  background-color: #f5f7fa;
  min-height: 100vh;
  box-sizing: border-box;
}

.detail-card {
  margin-top: 20px;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  overflow: hidden;
}

.detail-card:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.08);
}

.detail-card :deep(el-descriptions) {
  border-radius: 8px;
  overflow: hidden;
}

.detail-card :deep(el-descriptions__label) {
  font-weight: 600;
  color: #303133;
  background-color: #f5f7fa;
}

.detail-card :deep(el-descriptions__content) {
  color: #606266;
}

.detail-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #303133;
  margin: 20px 0 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e4e7ed;
}

.detail-card :deep(el-table) {
  border-radius: 8px;
  overflow: hidden;
  margin-top: 15px;
}

.detail-card :deep(el-table__header-wrapper) {
  background-color: #f5f7fa;
}

.detail-card :deep(el-table th) {
  font-weight: 600;
  background-color: #f5f7fa !important;
  border-bottom: 1px solid #e4e7ed;
  padding: 12px 0;
}

.detail-card :deep(el-table tr) {
  transition: all 0.3s ease;
}

.detail-card :deep(el-table tr:hover) {
  background-color: #f5f7fa !important;
}

.detail-card :deep(el-table td) {
  border-bottom: 1px solid #ebeef5;
  padding: 12px 0;
}

.detail-card :deep(el-tag) {
  border-radius: 6px;
  font-size: 0.75rem;
  padding: 2px 8px;
}

.action-buttons {
  margin-top: 30px;
  text-align: center;
  padding-bottom: 20px;
}

.action-buttons .el-button {
  margin: 0 10px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.action-buttons .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px 0 rgba(64, 158, 255, 0.3);
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .alarm-detail {
    padding: 10px;
  }
  
  .detail-card :deep(el-descriptions) {
    :column="1";
  }
  
  .action-buttons .el-button {
    margin: 5px;
  }
  
  .detail-card :deep(el-table th),
  .detail-card :deep(el-table td) {
    padding: 8px 0;
    font-size: 12px;
  }
}

@media screen and (max-width: 480px) {
  .detail-card h3 {
    font-size: 1rem;
  }
  
  .action-buttons {
    margin-top: 20px;
  }
  
  .action-buttons .el-button {
    margin: 3px;
    padding: 8px 12px;
    font-size: 12px;
  }
}
</style>
