<template>
  <MainLayout>
    <div class="dashboard">
      <!-- 统计卡片 -->
      <el-row :gutter="20" type="flex" justify="space-between">
        <el-col :xs="24" :sm="12" :md="8" :lg="8" :xl="8">
          <el-card class="stat-card">
            <template #header>
              <div class="card-header">
                <el-icon><WarningFilled /></el-icon>
                <span>今日告警</span>
              </div>
            </template>
            <div class="stat-value">{{ todayAlarmCount }}</div>
            <div class="stat-desc">较昨日 <span class="trend" :class="{ up: trend > 0, down: trend < 0 }">{{ trend > 0 ? '+' : '' }}{{ trend }}%</span></div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="8" :xl="8">
          <el-card class="stat-card">
            <template #header>
              <div class="card-header">
                <el-icon><VideoCamera /></el-icon>
                <span>摄像头状态</span>
              </div>
            </template>
            <div class="stat-value">{{ onlineCameras }}/{{ totalCameras }}</div>
            <div class="stat-desc">{{ onlineRate }}% 在线</div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="8" :xl="8">
          <el-card class="stat-card">
            <template #header>
              <div class="card-header">
                <el-icon><Timer /></el-icon>
                <span>未处理告警</span>
              </div>
            </template>
            <div class="stat-value">{{ pendingAlarmCount }}</div>
            <div class="stat-desc">{{ pendingRate }}% 未处理</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 图表区域 -->
      <el-row :gutter="20" style="margin-top: 20px;" type="flex" justify="space-between">
        <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <el-icon><PieChart /></el-icon>
                <span>今日告警类型分布</span>
              </div>
            </template>
            <div id="alarmTypeChart" ref="alarmTypeChart" class="chart"></div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <el-icon><DataLine /></el-icon>
                <span>告警趋势</span>
              </div>
            </template>
            <div id="alarmTrendChart" ref="alarmTrendChart" class="chart"></div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 最近告警 -->
      <el-card class="recent-alarms" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">
            <el-icon><Bell /></el-icon>
            <span>最近未处理告警</span>
            <el-button type="primary" size="small" @click="$router.push('/alarms')" style="margin-left: auto;">
              查看全部
            </el-button>
          </div>
        </template>
        <el-table :data="recentAlarms" stripe style="width: 100%">
            <el-table-column prop="alarm_id" label="告警ID" width="100" align="center" />
            <el-table-column prop="alarm_type" label="告警类型">
              <template #default="scope">
                <el-tag :type="getAlarmTypeTag(scope.row.alarm_type)">
                  {{ getAlarmTypeName(scope.row.alarm_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="告警时间" width="180">
              <template #default="scope">
                {{ formatTime(scope.row.alarm_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="alarm_status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getAlarmStatusTag(scope.row.alarm_status)">
                  {{ getAlarmStatusName(scope.row.alarm_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button type="primary" size="small" @click="handleAlarm(scope.row)">
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
      </el-card>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAlarmStore } from '../../stores/alarms'
import { useCameraStore } from '../../stores/cameras'
import * as echarts from 'echarts'
import MainLayout from '../../components/MainLayout.vue'
import { WarningFilled, VideoCamera, Timer, PieChart, DataLine, Bell, HomeFilled } from '@element-plus/icons-vue'

const router = useRouter()
const alarmStore = useAlarmStore()
const cameraStore = useCameraStore()

// 统计数据
const todayAlarmCount = ref(0)
const totalCameras = ref(0)
const onlineCameras = ref(0)
const pendingAlarmCount = ref(0)
const recentAlarms = ref([])
const trend = ref(0) // 模拟数据

// 图表实例
const alarmTypeChart = ref(null)
const alarmTrendChart = ref(null)
const chartInstances = []

// 计算属性
const onlineRate = computed(() => {
  if (totalCameras.value === 0) return 0
  return Math.round((onlineCameras.value / totalCameras.value) * 100)
})

const pendingRate = computed(() => {
  if (todayAlarmCount.value === 0) return 0
  return Math.round((pendingAlarmCount.value / todayAlarmCount.value) * 100)
})

// 告警类型和状态转换
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

// 时间格式化函数
const formatTime = (time) => {
  if (!time) return ''
  
  const date = new Date(time)
  if (isNaN(date.getTime())) return time
  
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// 方法
const handleAlarm = (alarm) => {
  // 跳转到告警详情页面
  router.push(`/alarms/${alarm.alarm_id}`)
}

const initCharts = () => {
  // 告警类型分布图表
  if (alarmTypeChart.value) {
    const chart = echarts.init(alarmTypeChart.value)
    chartInstances.push(chart)
    
    const option = {
      tooltip: {
        trigger: 'item'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: '告警类型',
          type: 'pie',
          radius: '70%',
          data: [
            { value: 12, name: '安全规范' },
            { value: 8, name: '区域入侵' },
            { value: 3, name: '火警' }
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ],
      grid: {
        show: false,
        containLabel: true
      }
    }
    
    chart.setOption(option)
  }
  
  // 告警趋势图表
  if (alarmTrendChart.value) {
    const chart = echarts.init(alarmTrendChart.value)
    chartInstances.push(chart)
    
    const option = {
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          data: [3, 5, 8, 12, 7, 4],
          type: 'line',
          smooth: true
        }
      ],
      grid: {
        show: false,
        containLabel: true
      }
    }
    
    chart.setOption(option)
  }
}

const resizeCharts = () => {
  chartInstances.forEach(chart => chart.resize())
}

// 生命周期
onMounted(async () => {
  // 获取统计数据
  await alarmStore.fetchTodayHandleReport()
  await alarmStore.fetchRecentUnresolved()
  await cameraStore.fetchStatusReport()
  
  // 更新数据
  if (alarmStore.statistics.todayHandle) {
    todayAlarmCount.value = alarmStore.statistics.todayHandle.unhandled_count || 0
  }
  
  if (alarmStore.recentUnresolved) {
    recentAlarms.value = alarmStore.recentUnresolved.rows || []
    pendingAlarmCount.value = alarmStore.recentUnresolved.total || 0
  }
  
  if (cameraStore.statusReport) {
    totalCameras.value = cameraStore.statusReport.total_count || 0
    onlineCameras.value = cameraStore.statusReport.online_count || 0
  }
  
  // 初始化图表
  setTimeout(initCharts, 100)
  
  // 监听窗口 resize
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  // 销毁图表
  chartInstances.forEach(chart => chart.dispose())
  window.removeEventListener('resize', resizeCharts)
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
  width: 100%;
  background-color: #f5f7fa;
  overflow-x: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
  font-weight: 500;
  color: #303133;
}

.card-header :deep(el-icon) {
  margin-right: 8px;
  font-size: 1rem;
  color: var(--primary-color);
}

.stat-card {
  transition: all 0.3s ease;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px 0 rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 600;
  color: #303133;
  margin: 1rem 0 0.5rem;
  transition: all 0.3s ease;
}

.stat-card:hover .stat-value {
  transform: scale(1.05);
  color: var(--primary-color);
}

.stat-desc {
  color: #606266;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.trend {
  font-weight: 500;
  transition: all 0.3s ease;
}

.trend.up {
  color: #f56c6c;
  animation: pulse 1s ease-in-out;
}

.trend.down {
  color: #67c23a;
  animation: pulse 1s ease-in-out;
}

.chart-card {
  min-height: 320px;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
  padding: 10px;
}

.chart-card:hover {
  box-shadow: 0 10px 20px 0 rgba(0, 0, 0, 0.1);
}

.chart {
  height: 280px;
  width: 100%;
  overflow: hidden;
  box-sizing: border-box;
}

.recent-alarms {
  margin-top: 20px;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
}

.recent-alarms:hover {
  box-shadow: 0 10px 20px 0 rgba(0, 0, 0, 0.1);
}

.recent-alarms :deep(el-table) {
  border-radius: 8px;
  overflow: hidden;
}

.recent-alarms :deep(el-table__header-wrapper) {
  background-color: #f5f7fa;
}

.recent-alarms :deep(el-table th) {
  font-weight: 600;
  background-color: #f5f7fa !important;
  border-bottom: 1px solid #e4e7ed;
}

.recent-alarms :deep(el-table tr) {
  transition: all 0.3s ease;
}

.recent-alarms :deep(el-table tr:hover) {
  background-color: #f5f7fa !important;
}

.recent-alarms :deep(el-table td) {
  border-bottom: 1px solid #ebeef5;
  padding: 12px 0;
}

.recent-alarms :deep(el-button) {
  border-radius: 6px;
  transition: all 0.3s ease;
}

.recent-alarms :deep(el-button:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px 0 rgba(64, 158, 255, 0.3);
}

.recent-alarms :deep(el-tag) {
  border-radius: 6px;
  font-size: 0.75rem;
  padding: 2px 8px;
}

/* 动画效果 */
@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard {
    padding: 10px;
  }
  
  .stat-value {
    font-size: 1.75rem;
  }
  
  .chart-card {
    height: 280px;
  }
  
  .chart {
    height: 220px;
  }
  
  .card-header {
    font-size: 0.8125rem;
  }
  
  .card-header :deep(el-icon) {
    font-size: 0.875rem;
  }
}

@media (max-width: 480px) {
  .stat-value {
    font-size: 1.5rem;
  }
  
  .chart-card {
    height: 240px;
  }
  
  .chart {
    height: 180px;
  }
  
  .card-header {
    font-size: 0.75rem;
  }
  
  .card-header :deep(el-icon) {
    font-size: 0.8125rem;
  }
  
  .stat-desc {
    font-size: 0.75rem;
  }
}
</style>
