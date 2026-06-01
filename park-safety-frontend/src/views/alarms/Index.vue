<template>
  <MainLayout>
    <div class="alarms">
      <!-- 搜索和筛选 -->
      <el-card class="search-card">
        <el-form :model="searchForm" inline>
          <el-form-item label="告警类型">
            <el-select v-model="searchForm.alarm_type" placeholder="请选择告警类型">
              <el-option label="火警" value="2" />
            </el-select>
          </el-form-item>
          <el-form-item label="告警状态">
            <el-select v-model="searchForm.alarm_status" placeholder="请选择告警状态">
              <el-option label="未处理" value="0" />
              <el-option label="确认误报" value="1" />
              <el-option label="处理中" value="2" />
              <el-option label="处理完成" value="3" />
            </el-select>
          </el-form-item>
          <el-form-item label="开始时间">
            <el-date-picker v-model="searchForm.start_time" type="datetime" placeholder="选择开始时间" />
          </el-form-item>
          <el-form-item label="结束时间">
            <el-date-picker v-model="searchForm.end_time" type="datetime" placeholder="选择结束时间" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 告警列表 -->
      <el-card class="table-card">
        <div class="table-header" style="margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
          <span></span>
          <el-button type="danger" @click="batchDeleteAlarms" :disabled="selectedAlarms.length === 0">
            批量删除
          </el-button>
        </div>
        <el-table :data="alarms" stripe style="width: 100%" v-loading="loading" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="55" />
          <el-table-column prop="alarm_id" label="告警ID" width="120" align="center" />
          <el-table-column prop="alarm_type" label="告警类型" width="100">
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
          <el-table-column prop="camera_name" label="摄像头" min-width="180" />
          <el-table-column prop="park_area" label="区域" width="120" />
          <el-table-column label="操作" width="200">
            <template #default="scope">
              <el-button type="primary" size="small" @click="handleAlarm(scope.row)">
                处理
              </el-button>
              <el-button type="info" size="small" @click="viewAlarm(scope.row)">
                查看
              </el-button>
              <el-button type="danger" size="small" @click="deleteAlarm(scope.row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination" v-if="total > 0">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>

      <!-- 告警处理对话框 -->
      <el-dialog
        v-model="dialogVisible"
        title="告警处理"
        width="500px"
      >
        <el-form :model="handleForm" :rules="handleRules" ref="handleFormRef">
          <el-form-item label="告警描述" disabled>
            <el-input v-model="handleForm.alarm_desc" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="处理状态" prop="alarm_status">
            <el-select v-model="handleForm.alarm_status" placeholder="请选择处理状态">
              <el-option label="确认误报" value="1" />
              <el-option label="处理中" value="2" />
              <el-option label="处理完成" value="3" />
            </el-select>
          </el-form-item>
          <el-form-item label="处理备注" prop="handle_remark">
            <el-input v-model="handleForm.handle_remark" type="textarea" :rows="4" placeholder="请输入处理备注" />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitHandle" :loading="submitLoading">提交</el-button>
          </span>
        </template>
      </el-dialog>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAlarmStore } from '../../stores/alarms'
import { alarmHandleApi } from '../../services/api'
import MainLayout from '../../components/MainLayout.vue'
import { WarningFilled } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'

const router = useRouter()
const alarmStore = useAlarmStore()

// 搜索表单
const searchForm = reactive({
  alarm_type: '',
  alarm_status: '',
  start_time: '',
  end_time: ''
})

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)

// 告警列表
const alarms = ref([])
const selectedAlarms = ref([])

// 处理对话框
const dialogVisible = ref(false)
const handleForm = reactive({
  alarm_id: '',
  alarm_desc: '',
  alarm_status: '',
  handle_remark: ''
})
const handleFormRef = ref(null)
const submitLoading = ref(false)

const handleRules = {
  alarm_status: [
    { required: true, message: '请选择处理状态', trigger: 'blur' }
  ],
  handle_remark: [
    { required: true, message: '请输入处理备注', trigger: 'blur' }
  ]
}

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
const handleSearch = async () => {
  currentPage.value = 1
  await fetchAlarms()
}

const resetForm = () => {
  searchForm.alarm_type = ''
  searchForm.alarm_status = ''
  searchForm.start_time = ''
  searchForm.end_time = ''
  currentPage.value = 1
  fetchAlarms()
}

const fetchAlarms = async () => {
  loading.value = true
  try {
    // 构建参数，过滤掉空值
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }

    // 只添加非空值
    if (searchForm.start_time) {
      params.start_time = new Date(searchForm.start_time).toISOString()
    }
    if (searchForm.end_time) {
      params.end_time = new Date(searchForm.end_time).toISOString()
    }
    if (searchForm.alarm_type !== '' && searchForm.alarm_type !== null) {
      params.alarm_type = parseInt(searchForm.alarm_type)
    }
    if (searchForm.alarm_status !== '' && searchForm.alarm_status !== null) {
      params.alarm_status = parseInt(searchForm.alarm_status)
    }

    const result = await alarmStore.fetchAlarms(params)
    if (result.success) {
      alarms.value = result.data.rows || []
      total.value = result.data.total || 0
    }
  } catch (error) {
    console.error('获取告警列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (size) => {
  pageSize.value = size
  fetchAlarms()
}

const handleCurrentChange = (current) => {
  currentPage.value = current
  fetchAlarms()
}

const handleAlarm = (alarm) => {
  handleForm.alarm_id = alarm.alarm_id
  handleForm.alarm_desc = alarm.alarm_desc
  handleForm.alarm_status = ''
  handleForm.handle_remark = ''
  dialogVisible.value = true
}

const viewAlarm = (alarm) => {
  // 跳转到告警详情页面
  router.push(`/alarms/${alarm.alarm_id}`)
}

// 处理表格选择变化
const handleSelectionChange = (val) => {
  selectedAlarms.value = val
}

// 删除单个告警
const deleteAlarm = async (alarm) => {
  try {
    await ElMessageBox.confirm('确定要删除这个告警吗？', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const result = await alarmStore.deleteAlarms(alarm.alarm_id)
    if (result.success) {
      await fetchAlarms()
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除告警失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 批量删除告警
const batchDeleteAlarms = async () => {
  if (selectedAlarms.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedAlarms.value.length} 个告警吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const ids = selectedAlarms.value.map(alarm => alarm.alarm_id).join(',')
    const result = await alarmStore.deleteAlarms(ids)
    if (result.success) {
      selectedAlarms.value = []
      await fetchAlarms()
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除告警失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const submitHandle = async () => {
  if (!handleFormRef.value) return
  
  try {
    const valid = await handleFormRef.value.validate()
    if (valid) {
      submitLoading.value = true
      try {
        // 转换为后端期望的格式
        // 前端alarm_status: 1=确认误报, 2=处理中, 3=处理完成
        // 后端handle_action: 0=标记误报, 1=派单处理, 2=标记已解决
        let handleAction = 0
        if (handleForm.alarm_status === '1') {
          handleAction = 0 // 确认误报
        } else if (handleForm.alarm_status === '2') {
          handleAction = 1 // 处理中
        } else if (handleForm.alarm_status === '3') {
          handleAction = 2 // 处理完成
        }
        
        const handleRecordData = {
          alarm_id: parseInt(handleForm.alarm_id),
          handle_action: handleAction,
          handle_content: handleForm.handle_remark,
          handler_user_id: 1 // 假设当前用户ID为1，实际应该从登录状态获取
        }
        // 调用告警处理API
        const response = await alarmHandleApi.createHandleRecord(handleRecordData)
        if (response.code === 1) {
          dialogVisible.value = false
          // 重新获取列表
          await fetchAlarms()
        } else {
          console.error('处理告警失败:', response.msg)
        }
      } catch (error) {
        console.error('处理告警失败:', error)
      } finally {
        submitLoading.value = false
      }
    }
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

// 生命周期
onMounted(() => {
  fetchAlarms()
})
</script>

<style scoped>
.alarms {
  padding: 20px;
  width: 100%;
  background-color: #f5f7fa;
  min-height: 100vh;
  box-sizing: border-box;
}

/* 搜索卡片样式优化 */
.search-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  overflow: hidden;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
}

.search-card:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.08);
}

.search-card :deep(.el-card__body) {
  padding: 20px 24px;
}

/* 搜索表单样式 */
.search-card :deep(.el-form) {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
}

.search-card :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.search-card :deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
  font-size: 14px;
  padding-right: 12px;
}

/* 输入框样式优化 */
.search-card :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.search-card :deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
}

.search-card :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #536f88, 0 4px 8px rgba(83, 111, 136, 0.15);
}

/* 选择器样式优化 */
.search-card :deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
}

/* 日期选择器样式优化 */
.search-card :deep(.el-date-picker) {
  border-radius: 8px;
}

/* 按钮组样式 */
.search-card :deep(.el-button) {
  border-radius: 8px;
  padding: 10px 20px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.search-card :deep(.el-button--primary) {
  background: linear-gradient(135deg, #536f88 0%, #6f879c 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(83, 111, 136, 0.3);
}

.search-card :deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #6f879c 0%, #536f88 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(83, 111, 136, 0.4);
}

.search-card :deep(.el-button:not(.el-button--primary):hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.table-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  overflow: hidden;
}

.table-card:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.08);
}

.table-header {
  padding: 15px 20px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 0 !important;
}

.table-card :deep(el-table) {
  border-radius: 8px;
  overflow: hidden;
}

.table-card :deep(el-table__header-wrapper) {
  background-color: #f5f7fa;
}

.table-card :deep(el-table th) {
  font-weight: 600;
  background-color: #f5f7fa !important;
  border-bottom: 1px solid #e4e7ed;
  padding: 12px 0;
}

.table-card :deep(el-table tr) {
  transition: all 0.3s ease;
}

.table-card :deep(el-table tr:hover) {
  background-color: #f5f7fa !important;
}

.table-card :deep(el-table td) {
  border-bottom: 1px solid #ebeef5;
  padding: 12px 0;
}

.table-card :deep(el-button) {
  border-radius: 6px;
  transition: all 0.3s ease;
  margin-right: 8px;
}

.table-card :deep(el-button:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px 0 rgba(83, 111, 136, 0.3);
}

.table-card :deep(el-tag) {
  border-radius: 6px;
  font-size: 0.75rem;
  padding: 2px 8px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
  padding: 0 20px 20px;
}

.dialog-footer {
  text-align: right;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .alarms {
    padding: 10px;
  }
  
  .search-card {
    padding: 10px;
  }
  
  .table-card {
    padding: 10px;
  }
  
  .table-header {
    padding: 10px;
  }
  
  .table-card :deep(el-button) {
    margin-right: 4px;
    padding: 4px 8px;
    font-size: 12px;
  }
  
  .pagination {
    padding: 10px;
    margin-top: 10px;
  }
  
  .pagination :deep(.el-pagination) {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .pagination :deep(.el-pagination__sizes) {
    margin-right: 0;
  }
  
  .pagination :deep(.el-select .el-input) {
    width: 90px;
    min-width: 90px;
  }
  
  .pagination :deep(.el-pagination__page) {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }
  
  .pagination :deep(.el-pagination__prev),
  .pagination :deep(.el-pagination__next) {
    width: 28px;
    height: 28px;
  }
  
  .pagination :deep(.el-pagination__total) {
    font-size: 12px;
  }
  
  .pagination :deep(.el-pagination__jump) {
    font-size: 12px;
  }
  
  .pagination :deep(.el-pagination__jump .el-input) {
    width: 70px;
  }
}

@media screen and (max-width: 480px) {
  .table-card :deep(el-table th),
  .table-card :deep(el-table td) {
    padding: 8px 0;
    font-size: 12px;
  }
  
  .table-card :deep(el-button) {
    margin-right: 2px;
    padding: 2px 6px;
    font-size: 11px;
  }
  
  .pagination :deep(.el-pagination) {
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
  }
  
  .pagination :deep(.el-pagination__sizes) {
    order: -1;
  }
}

/* 分页器样式 */
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 12px 16px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.pagination :deep(.el-pagination) {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination :deep(.el-pagination__sizes) {
  margin-right: 8px;
}

.pagination :deep(.el-select .el-input) {
  width: 100px;
  border-radius: 6px;
  border: 1px solid #dcdfe6;
  transition: all 0.2s ease;
  min-width: 100px;
}

.pagination :deep(.el-select .el-input__inner) {
  text-align: center;
  font-size: 14px;
  color: #303133;
  padding: 0 20px 0 12px;
}

.pagination :deep(.el-select .el-input__suffix) {
  right: 8px;
}

.pagination :deep(.el-select .el-input:hover) {
  border-color: #536f88;
  box-shadow: 0 0 0 2px rgba(83, 111, 136, 0.2);
}

.pagination :deep(.el-select .el-input.is-focus) {
  border-color: #536f88;
  box-shadow: 0 0 0 2px rgba(83, 111, 136, 0.2);
}

.pagination :deep(.el-select-dropdown) {
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.pagination :deep(.el-select-dropdown__item) {
  padding: 8px 16px;
  transition: all 0.2s ease;
  border-radius: 0;
}

.pagination :deep(.el-select-dropdown__item:hover) {
  background-color: #eef2f5;
  color: #536f88;
}

.pagination :deep(.el-select-dropdown__item.selected) {
  background-color: #eef2f5;
  color: #536f88;
  font-weight: 500;
}

.pagination :deep(.el-select-dropdown__item.hover) {
  background-color: #eef2f5;
  color: #536f88;
}

.pagination :deep(.el-pagination__total) {
  font-size: 14px;
  color: #606266;
  font-weight: 400;
}

.pagination :deep(.el-pagination__prev),
.pagination :deep(.el-pagination__next) {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid #dcdfe6;
  background-color: #ffffff;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pagination :deep(.el-pagination__prev:hover),
.pagination :deep(.el-pagination__next:hover) {
  border-color: #536f88;
  color: #536f88;
  box-shadow: 0 2px 8px rgba(83, 111, 136, 0.15);
}

.pagination :deep(.el-pagination__prev.is-disabled),
.pagination :deep(.el-pagination__next.is-disabled) {
  border-color: #ebeef5;
  color: #c0c4cc;
  cursor: not-allowed;
}

.pagination :deep(.el-pagination__page) {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid #dcdfe6;
  background-color: #ffffff;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 2px;
}

.pagination :deep(.el-pagination__page:hover) {
  border-color: #536f88;
  color: #536f88;
}

.pagination :deep(.el-pagination__page.is-current) {
  background-color: #536f88;
  border-color: #536f88;
  color: #ffffff;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(83, 111, 136, 0.3);
}

.pagination :deep(.el-pagination__page.is-current:hover) {
  background-color: #6f879c;
  border-color: #6f879c;
}

.pagination :deep(.el-pagination__jump) {
  font-size: 14px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination :deep(.el-pagination__jump .el-input) {
  width: 80px;
}

.pagination :deep(.el-pagination__jump .el-input__wrapper) {
  border-radius: 6px;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .pagination {
    flex-direction: column;
    align-items: flex-end;
    gap: 10px;
  }
  
  .pagination :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  
  .pagination :deep(.el-pagination__sizes) {
    margin-right: 0;
  }
}
</style>
