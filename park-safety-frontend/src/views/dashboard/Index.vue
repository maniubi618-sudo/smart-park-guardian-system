<template>
  <MainLayout>
    <div class="ops-dashboard">
      <section class="ops-hero">
        <div class="hero-copy">
          <span class="hero-index">01</span>
          <span class="ops-kicker">Security Operations Brief</span>
          <h1>作物状态监测</h1>
          <p>聚焦今日风险、设备在线状态与未处理告警，辅助值班人员快速判断处置优先级。</p>
        </div>

        <div class="risk-panel">
          <div class="risk-panel__label">当前风险</div>
          <div class="risk-panel__value" :class="{ danger: pendingAlarmCount > 0 }">
            {{ pendingAlarmCount > 0 ? '待处置' : '平稳' }}
          </div>
          <div class="risk-meter" :style="{ '--risk': `${pendingRate}%` }">
            <span></span>
          </div>
          <div class="risk-panel__meta">
            <span>未处理 {{ pendingAlarmCount }}</span>
            <span>在线率 {{ onlineRate }}%</span>
          </div>
        </div>
      </section>

      <section class="metric-strip" aria-label="今日核心指标">
        <article class="metric-card alert">
          <div class="metric-card__icon">
            <el-icon><WarningFilled /></el-icon>
          </div>
          <div>
            <span>今日告警</span>
            <strong>{{ todayAlarmCount }}</strong>
            <em>较昨日 {{ trend > 0 ? '+' : '' }}{{ trend }}%</em>
          </div>
        </article>

        <article class="metric-card camera">
          <div class="metric-card__icon">
            <el-icon><VideoCamera /></el-icon>
          </div>
          <div>
            <span>摄像头状态</span>
            <strong>{{ onlineCameras }}/{{ totalCameras }}</strong>
            <em>{{ onlineRate }}% 在线</em>
          </div>
        </article>

        <article class="metric-card pending">
          <div class="metric-card__icon">
            <el-icon><Timer /></el-icon>
          </div>
          <div>
            <span>未处理告警</span>
            <strong>{{ pendingAlarmCount }}</strong>
            <em>{{ pendingRate }}% 未处理</em>
          </div>
        </article>
      </section>

      <section class="ops-grid">
        <article class="ops-panel radar-panel">
          <header class="panel-heading">
            <div>
              <span>RADAR</span>
              <h2>告警类型态势</h2>
            </div>
            <el-icon><PieChart /></el-icon>
          </header>
          <div class="radar-stage">
            <div class="radar-visual" aria-hidden="true">
              <span class="ring ring-one"></span>
              <span class="ring ring-two"></span>
              <span class="ring ring-three"></span>
              <span class="radar-line"></span>
              <span class="target target-a"></span>
              <span class="target target-b"></span>
              <span class="target target-c"></span>
            </div>
            <div id="alarmTypeChart" ref="alarmTypeChart" class="chart radar-chart"></div>
          </div>
        </article>

        <article class="ops-panel trend-panel">
          <header class="panel-heading">
            <div>
              <span>TREND</span>
              <h2>告警趋势</h2>
            </div>
            <el-icon><DataLine /></el-icon>
          </header>
          <div id="alarmTrendChart" ref="alarmTrendChart" class="chart trend-chart"></div>
        </article>
      </section>

      <section class="ops-panel alarm-queue">
        <header class="panel-heading queue-heading">
          <div>
            <span>QUEUE</span>
            <h2>最近未处理告警</h2>
          </div>
          <el-button type="primary" size="small" @click="$router.push('/alarms')">
            查看全部
          </el-button>
        </header>

        <el-table :data="recentAlarms" class="ops-table" style="width: 100%">
          <el-table-column prop="alarm_id" label="告警ID" width="110" align="center" />
          <el-table-column prop="alarm_type" label="告警类型">
            <template #default="scope">
              <el-tag :type="getAlarmTypeTag(scope.row.alarm_type)">
                {{ getAlarmTypeName(scope.row.alarm_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="告警时间" min-width="180">
            <template #default="scope">
              {{ formatTime(scope.row.alarm_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="alarm_status" label="状态" width="120">
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
      </section>
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
import { WarningFilled, VideoCamera, Timer, PieChart, DataLine } from '@element-plus/icons-vue'

const router = useRouter()
const alarmStore = useAlarmStore()
const cameraStore = useCameraStore()

const todayAlarmCount = ref(0)
const totalCameras = ref(0)
const onlineCameras = ref(0)
const pendingAlarmCount = ref(0)
const recentAlarms = ref([])
const trend = ref(0)

const alarmTypeChart = ref(null)
const alarmTrendChart = ref(null)
const chartInstances = []

const onlineRate = computed(() => {
  if (totalCameras.value === 0) return 0
  return Math.round((onlineCameras.value / totalCameras.value) * 100)
})

const pendingRate = computed(() => {
  if (todayAlarmCount.value === 0) return 0
  return Math.round((pendingAlarmCount.value / todayAlarmCount.value) * 100)
})

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

const handleAlarm = (alarm) => {
  router.push(`/alarms/${alarm.alarm_id}`)
}

const initCharts = () => {
  if (alarmTypeChart.value) {
    const chart = echarts.init(alarmTypeChart.value)
    chartInstances.push(chart)

    chart.setOption({
      animation: true,
      animationDuration: 1200,
      animationEasing: 'cubicOut',
      color: ['#b75a4b', '#c58a45', '#536f88'],
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(37, 43, 48, 0.96)',
        borderColor: 'rgba(83, 111, 136, 0.18)',
        borderWidth: 1,
        textStyle: { color: '#f8faf9', fontWeight: 700 }
      },
      legend: {
        bottom: 6,
        left: 'center',
        itemWidth: 10,
        itemHeight: 10,
        textStyle: { color: '#65717c', fontWeight: 700 }
      },
      series: [
        {
          name: '告警类型',
          type: 'pie',
          radius: ['48%', '72%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: true,
          label: {
            color: '#232a2f',
            fontWeight: 800,
            formatter: '{b}'
          },
          labelLine: {
            lineStyle: { color: 'rgba(83, 111, 136, 0.22)' }
          },
          data: [
            { value: 3, name: '火警' }
          ],
          itemStyle: {
            borderColor: '#fbfaf7',
            borderWidth: 5,
            shadowBlur: 0,
            shadowColor: 'transparent'
          },
          animationType: 'scale',
          animationEasing: 'elasticOut'
        }
      ]
    })
  }

  if (alarmTrendChart.value) {
    const chart = echarts.init(alarmTrendChart.value)
    chartInstances.push(chart)

    chart.setOption({
      animation: true,
      animationDuration: 1400,
      animationEasing: 'quadraticOut',
      color: ['#536f88'],
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(37, 43, 48, 0.96)',
        borderColor: 'rgba(83, 111, 136, 0.18)',
        borderWidth: 1,
        textStyle: { color: '#f8faf9', fontWeight: 700 }
      },
      grid: {
        top: 28,
        right: 24,
        bottom: 34,
        left: 42,
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
        axisLine: { lineStyle: { color: 'rgba(83, 111, 136, 0.22)' } },
        axisLabel: { color: '#65717c', fontWeight: 700 },
        axisTick: { show: false }
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: 'rgba(83, 111, 136, 0.12)' } },
        axisLabel: { color: '#7b858d', fontWeight: 700 }
      },
      series: [
        {
          data: [3, 5, 8, 12, 7, 4],
          type: 'line',
          smooth: true,
          showSymbol: true,
          animationDelay: (idx) => idx * 80,
          symbolSize: 9,
          lineStyle: {
            width: 3,
            shadowBlur: 0,
            shadowColor: 'transparent'
          },
          itemStyle: {
            borderColor: '#fbfaf7',
            borderWidth: 3
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(83, 111, 136, 0.16)' },
                { offset: 0.58, color: 'rgba(83, 111, 136, 0.05)' },
                { offset: 1, color: 'rgba(83, 111, 136, 0)' }
              ]
            }
          }
        }
      ]
    })
  }
}

const resizeCharts = () => {
  chartInstances.forEach(chart => chart.resize())
}

onMounted(async () => {
  await alarmStore.fetchTodayHandleReport()
  await alarmStore.fetchRecentUnresolved()
  await cameraStore.fetchStatusReport()

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

  setTimeout(initCharts, 100)
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  chartInstances.forEach(chart => chart.dispose())
  window.removeEventListener('resize', resizeCharts)
})
</script>

<style scoped>
.ops-dashboard {
  position: relative;
  min-height: calc(100vh - 136px);
  margin: -24px;
  padding: 34px;
  overflow: hidden;
  color: #20262a;
  background:
    linear-gradient(90deg, rgba(216, 226, 233, 0.82) 0 29%, transparent 29% 100%),
    linear-gradient(125deg, transparent 0 68%, rgba(232, 220, 195, 0.82) 68% 100%),
    radial-gradient(circle at 77% 13%, rgba(197, 138, 69, 0.13), transparent 18rem),
    linear-gradient(145deg, #f8f5ed 0%, #f3f1eb 48%, #e7edf1 100%);
  isolation: isolate;
  animation: dashboardCanvasIn var(--motion-page) var(--motion-ease) both;
}

@keyframes dashboardCanvasIn {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ops-dashboard::before {
  content: "";
  position: absolute;
  inset: 34px 34px auto auto;
  width: min(36vw, 520px);
  height: 280px;
  z-index: -1;
  pointer-events: none;
  background: #dbe6ee;
  clip-path: polygon(10% 0, 100% 0, 88% 100%, 0 100%);
  opacity: 0.72;
  animation: editorialBlockDrift 8s var(--motion-ease) infinite alternate;
}

@keyframes editorialBlockDrift {
  from {
    transform: translate3d(0, 0, 0);
  }
  to {
    transform: translate3d(-14px, 10px, 0);
  }
}

.ops-dashboard::after {
  content: "";
  position: absolute;
  left: 34px;
  right: 34px;
  top: 34px;
  bottom: 34px;
  z-index: -1;
  pointer-events: none;
  border: 1px solid rgba(83, 111, 136, 0.18);
  background-image:
    linear-gradient(rgba(83, 111, 136, 0.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(83, 111, 136, 0.055) 1px, transparent 1px);
  background-size: 68px 68px;
  mask-image: linear-gradient(90deg, rgba(0, 0, 0, 0.38), transparent 34%, transparent 66%, rgba(0, 0, 0, 0.25));
}

.ops-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 24px;
  align-items: stretch;
  margin-bottom: 16px;
}

.ops-hero,
.metric-strip,
.ops-grid,
.alarm-queue {
  animation: panelReveal var(--motion-slow) var(--motion-ease) both;
}

.metric-strip { animation-delay: 90ms; }
.ops-grid { animation-delay: 160ms; }
.alarm-queue { animation-delay: 230ms; }

.hero-copy,
.risk-panel,
.ops-panel,
.metric-card {
  border: 1px solid rgba(115, 126, 135, 0.28);
  background: #fbfaf7;
  box-shadow: 0 18px 42px rgba(54, 62, 68, 0.08);
  transition: transform var(--motion-base) var(--motion-ease), box-shadow var(--motion-base) var(--motion-ease), border-color var(--motion-base) var(--motion-ease);
}

.hero-copy:hover,
.risk-panel:hover,
.ops-panel:hover,
.metric-card:hover {
  transform: translateY(-3px);
  border-color: rgba(83, 111, 136, 0.34);
  box-shadow: 0 22px 54px rgba(54, 62, 68, 0.13);
}

.hero-copy {
  position: relative;
  min-height: 268px;
  padding: 32px 38px 30px;
  border-radius: 4px;
  overflow: hidden;
  background:
    linear-gradient(90deg, #fbfaf7 0 63%, transparent 63%),
    linear-gradient(116deg, transparent 0 68%, rgba(197, 138, 69, 0.19) 68% 100%),
    #e6eef3;
}

.hero-copy::before {
  content: "";
  position: absolute;
  left: 38px;
  right: 38px;
  top: 26px;
  height: 8px;
  background: linear-gradient(90deg, #536f88 0 22%, #b75a4b 22% 33%, #c58a45 33% 42%, transparent 42%);
  transform-origin: 0 50%;
  animation: headlineRuleIn 900ms var(--motion-ease) both;
}

@keyframes headlineRuleIn {
  from {
    transform: scaleX(0);
  }
  to {
    transform: scaleX(1);
  }
}

.hero-copy::after {
  content: "OPS";
  position: absolute;
  right: 22px;
  bottom: -16px;
  color: rgba(83, 111, 136, 0.11);
  font-size: clamp(96px, 16vw, 210px);
  line-height: 0.8;
  font-weight: 950;
  letter-spacing: -0.02em;
  pointer-events: none;
  animation: ghostTypeDrift 7s var(--motion-ease) infinite alternate;
}

@keyframes ghostTypeDrift {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-12px);
  }
}

.hero-index {
  position: absolute;
  top: 38px;
  right: 34px;
  z-index: 1;
  color: #536f88;
  font-size: clamp(54px, 7vw, 108px);
  line-height: 0.86;
  font-weight: 950;
  letter-spacing: -0.04em;
  opacity: 0.86;
}

.ops-kicker,
.panel-heading span,
.risk-panel__label,
.metric-card span {
  display: block;
  color: #647382;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}

.hero-copy h1 {
  position: relative;
  z-index: 2;
  max-width: 760px;
  margin: 44px 0 14px;
  color: #20262a;
  font-size: clamp(56px, 8vw, 112px);
  line-height: 0.86;
  letter-spacing: -0.03em;
  text-wrap: pretty;
}

.hero-copy p {
  position: relative;
  z-index: 2;
  max-width: 620px;
  margin: 0;
  color: #65717c;
  font-size: 16px;
  line-height: 1.72;
  font-weight: 680;
}

.hero-copy .ops-kicker {
  position: relative;
  z-index: 2;
  margin-top: 18px;
  color: #536f88;
}

.risk-panel {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 28px;
  border-radius: 4px;
  background:
    linear-gradient(180deg, rgba(219, 230, 238, 0.86), rgba(251, 250, 247, 0.94)),
    #fbfaf7;
}

.risk-panel__value {
  margin-top: 14px;
  color: #4f6f8f;
  font-size: 58px;
  line-height: 1;
  font-weight: 950;
  letter-spacing: -0.05em;
}

.risk-panel__value.danger {
  color: #b75a4b;
}

.risk-meter {
  height: 12px;
  margin: 30px 0 16px;
  border-radius: 0;
  overflow: hidden;
  background: rgba(83, 111, 136, 0.14);
}

.risk-meter span {
  display: block;
  width: max(10%, var(--risk));
  height: 100%;
  border-radius: 0;
  background: linear-gradient(90deg, #536f88, #c58a45, #b75a4b);
  animation: riskFill 1200ms var(--motion-ease) both;
}

@keyframes riskFill {
  from {
    width: 0;
  }
}

.risk-panel__meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #65717c;
  font-size: 13px;
  font-weight: 800;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.metric-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 56px;
  gap: 18px;
  align-items: start;
  min-height: 152px;
  padding: 22px;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
  background: #fbfaf7;
}

.metric-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 8px;
  background: #536f88;
}

.metric-card::after {
  content: "";
  position: absolute;
  right: -56px;
  bottom: -72px;
  width: 180px;
  height: 180px;
  background: rgba(83, 111, 136, 0.10);
  transform: rotate(24deg);
  transition: transform var(--motion-slow) var(--motion-ease), opacity var(--motion-base) var(--motion-ease);
}

.metric-card:hover::after {
  transform: rotate(18deg) translate(-10px, -8px);
}

.metric-card.alert::before {
  background: #b75a4b;
}

.metric-card.pending::before {
  background: #c58a45;
}

.metric-card.alert::after {
  background: rgba(183, 90, 75, 0.11);
}

.metric-card.pending::after {
  background: rgba(197, 138, 69, 0.13);
}

.metric-card__icon {
  grid-column: 2;
  grid-row: 1 / span 3;
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  color: #4f6f8f;
  border-radius: 4px;
  background: rgba(83, 111, 136, 0.10);
  border: 1px solid rgba(83, 111, 136, 0.24);
  font-size: 24px;
  transition: transform var(--motion-base) var(--motion-ease), background-color var(--motion-base) var(--motion-ease);
}

.metric-card:hover .metric-card__icon {
  transform: rotate(-4deg) scale(1.05);
}

.metric-card.alert .metric-card__icon {
  color: #b94a3d;
  background: rgba(185, 74, 61, 0.10);
  border-color: rgba(185, 74, 61, 0.22);
}

.metric-card.pending .metric-card__icon {
  color: #c58a45;
  background: rgba(197, 138, 69, 0.12);
  border-color: rgba(197, 138, 69, 0.24);
}

.metric-card strong {
  display: block;
  margin: 12px 0 6px;
  color: #20262a;
  font-size: clamp(36px, 4vw, 52px);
  line-height: 1;
  font-weight: 950;
  letter-spacing: -0.05em;
  animation: numberPop 760ms var(--motion-ease) both;
}

@keyframes numberPop {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.94);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.metric-card em {
  color: #65717c;
  font-size: 13px;
  font-style: normal;
  font-weight: 800;
}

.ops-grid {
  display: grid;
  grid-template-columns: minmax(360px, 0.92fr) minmax(420px, 1.28fr);
  gap: 16px;
  margin-bottom: 16px;
}

.ops-panel {
  border-radius: 4px;
  overflow: hidden;
}

.radar-panel {
  background:
    linear-gradient(180deg, rgba(251, 250, 247, 0.92), rgba(230, 238, 243, 0.86)),
    #fbfaf7;
}

.trend-panel {
  background:
    linear-gradient(90deg, rgba(232, 220, 195, 0.42) 0 24%, transparent 24%),
    #fbfaf7;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 82px;
  padding: 22px 26px 18px;
  border-bottom: 1px solid rgba(115, 126, 135, 0.22);
}

.panel-heading h2 {
  margin: 7px 0 0;
  color: #20262a;
  font-size: 24px;
  font-weight: 920;
  letter-spacing: -0.02em;
}

.panel-heading > .el-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  color: #536f88;
  font-size: 22px;
  border: 1px solid rgba(83, 111, 136, 0.22);
  background: rgba(83, 111, 136, 0.08);
}

.radar-stage {
  position: relative;
  min-height: 410px;
}

.radar-visual {
  position: absolute;
  inset: 26px;
  display: grid;
  place-items: center;
  opacity: 0.72;
}

.ring {
  position: absolute;
  border: 1px solid rgba(83, 111, 136, 0.18);
  border-radius: 4px;
  transform: rotate(8deg);
}

.ring-one { width: 76%; aspect-ratio: 1; }
.ring-two { width: 50%; aspect-ratio: 1; }
.ring-three { width: 24%; aspect-ratio: 1; }

.radar-line {
  position: absolute;
  width: 46%;
  height: 1px;
  left: 50%;
  top: 50%;
  transform-origin: 0 50%;
  transform: rotate(-12deg);
  background: linear-gradient(90deg, rgba(83, 111, 136, 0.72), transparent);
  animation: radarSweep 5.4s linear infinite;
}

@keyframes radarSweep {
  from {
    transform: rotate(-12deg);
  }
  to {
    transform: rotate(348deg);
  }
}

.target {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 0;
  background: #4f6f8f;
  box-shadow: 0 0 0 7px rgba(83, 111, 136, 0.10);
  animation: targetPing 2.6s var(--motion-ease) infinite;
}

.target-b { animation-delay: 420ms; }
.target-c { animation-delay: 820ms; }

@keyframes targetPing {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.22);
  }
}

.target-a { left: 28%; top: 34%; }
.target-b { right: 27%; top: 45%; background: #c58a45; box-shadow: 0 0 0 7px rgba(197, 138, 69, 0.12); }
.target-c { left: 49%; bottom: 24%; background: #b75a4b; box-shadow: 0 0 0 7px rgba(183, 90, 75, 0.12); }

.chart {
  position: relative;
  width: 100%;
}

.radar-chart {
  height: 410px;
}

.trend-chart {
  height: 410px;
}

.alarm-queue {
  margin-bottom: 0;
  background:
    linear-gradient(90deg, #fbfaf7 0 74%, rgba(219, 230, 238, 0.68) 74% 100%),
    #fbfaf7;
}

.queue-heading {
  min-height: 78px;
}

.alarm-queue :deep(.el-table) {
  --el-table-border-color: rgba(115, 126, 135, 0.16);
  --el-table-header-bg-color: rgba(83, 111, 136, 0.08);
  --el-table-tr-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(83, 111, 136, 0.07);
  color: #343b40;
  background: transparent !important;
}

.alarm-queue :deep(.el-table__inner-wrapper::before) {
  background: rgba(115, 126, 135, 0.18);
}

.alarm-queue :deep(th.el-table__cell) {
  background: rgba(83, 111, 136, 0.08) !important;
  color: #63707b;
  font-weight: 900;
  letter-spacing: 0.03em;
}

.alarm-queue :deep(.el-table td.el-table__cell) {
  background: transparent !important;
  border-bottom-color: rgba(115, 126, 135, 0.14);
}

.alarm-queue :deep(.el-table__row) {
  animation: queueRowIn 460ms var(--motion-ease) both;
}

.alarm-queue :deep(.el-table__row:nth-child(2)) { animation-delay: 50ms; }
.alarm-queue :deep(.el-table__row:nth-child(3)) { animation-delay: 100ms; }
.alarm-queue :deep(.el-table__row:nth-child(4)) { animation-delay: 150ms; }
.alarm-queue :deep(.el-table__row:nth-child(5)) { animation-delay: 200ms; }

@keyframes queueRowIn {
  from {
    opacity: 0;
    transform: translateX(-14px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.alarm-queue :deep(.el-table__empty-text) {
  color: #8a949c;
}

.alarm-queue :deep(.el-button--primary) {
  background: #536f88 !important;
  border-color: #536f88 !important;
  color: #fbfaf7 !important;
  border-radius: 3px;
  box-shadow: none !important;
}

.alarm-queue :deep(.el-tag) {
  border-radius: 3px;
  font-weight: 850;
}

@media (max-width: 1120px) {
  .ops-hero,
  .ops-grid {
    grid-template-columns: 1fr;
  }

  .metric-strip {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .ops-dashboard {
    margin: -16px;
    padding: 18px;
    background:
      linear-gradient(180deg, rgba(216, 226, 233, 0.86) 0 260px, transparent 260px),
      linear-gradient(145deg, #f8f5ed 0%, #f3f1eb 52%, #e7edf1 100%);
  }

  .ops-dashboard::before,
  .ops-dashboard::after {
    display: none;
  }

  .hero-copy {
    min-height: 0;
    padding: 24px;
  }

  .hero-copy::before {
    left: 24px;
    right: 24px;
  }

  .hero-index {
    top: 28px;
    right: 22px;
    font-size: 58px;
  }

  .hero-copy h1 {
    margin-top: 48px;
    font-size: 46px;
    line-height: 0.92;
  }

  .hero-copy p {
    font-size: 14px;
  }

  .risk-panel {
    padding: 20px;
  }

  .risk-panel__value {
    font-size: 44px;
  }

  .metric-card {
    min-height: 136px;
  }

  .metric-card strong {
    font-size: 38px;
  }

  .ops-grid {
    display: block;
  }

  .ops-panel {
    margin-bottom: 16px;
  }

  .radar-stage,
  .radar-chart,
  .trend-chart {
    min-height: 300px;
    height: 300px;
  }

  .alarm-queue {
    overflow-x: auto;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ops-dashboard,
  .ops-dashboard::before,
  .ops-hero,
  .metric-strip,
  .ops-grid,
  .alarm-queue,
  .hero-copy::before,
  .hero-copy::after,
  .risk-meter span,
  .metric-card strong,
  .radar-line,
  .target,
  .alarm-queue :deep(.el-table__row) {
    animation: none !important;
  }
}
</style>
