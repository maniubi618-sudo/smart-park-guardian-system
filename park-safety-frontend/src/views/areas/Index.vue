<template>
  <MainLayout>
    <div class="areas">
      <!-- 搜索 -->
      <el-card class="search-card">
        <el-form :model="searchForm" inline>
          <el-form-item label="园区区域名称">
            <el-input v-model="searchForm.park_area" placeholder="请输入园区区域名称" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="resetForm">重置</el-button>
            <el-button type="success" @click="addArea">添加园区区域</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 园区区域列表 -->
      <el-card class="table-card">
        <div class="table-header" style="margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
          <span></span>
          <el-button type="danger" @click="batchDeleteAreas" :disabled="selectedAreas.length === 0">
            批量删除
          </el-button>
        </div>
        <el-table :data="areas" stripe style="width: 100%" v-loading="loading" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="55" />
          <el-table-column prop="park_area_id" label="区域ID" width="100" align="center" />
          <el-table-column prop="park_area" label="区域名称" />
          <el-table-column prop="remark" label="区域描述" />
          <el-table-column label="创建时间" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.create_time) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button type="primary" size="small" @click="editArea(scope.row)">
                编辑
              </el-button>
              <el-button type="danger" size="small" @click="deleteArea(scope.row)">
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

      <!-- 添加园区区域对话框 -->
      <el-dialog
        v-model="addDialogVisible"
        title="添加园区区域"
        width="500px"
      >
        <el-form :model="addForm" :rules="areaRules" ref="addFormRef">
          <el-form-item label="区域名称" prop="park_area">
            <el-input v-model="addForm.park_area" placeholder="请输入区域名称" />
          </el-form-item>
          <el-form-item label="区域描述" prop="remark">
            <el-input v-model="addForm.remark" type="textarea" :rows="4" placeholder="请输入区域描述" />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="addDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitAddArea" :loading="addLoading">提交</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 编辑园区区域对话框 -->
      <el-dialog
        v-model="editDialogVisible"
        title="编辑园区区域"
        width="500px"
      >
        <el-form :model="editForm" :rules="areaRules" ref="editFormRef">
          <el-form-item label="区域名称" prop="park_area">
            <el-input v-model="editForm.park_area" placeholder="请输入区域名称" />
          </el-form-item>
          <el-form-item label="区域描述" prop="remark">
            <el-input v-model="editForm.remark" type="textarea" :rows="4" placeholder="请输入区域描述" />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="editDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitEditArea" :loading="editLoading">提交</el-button>
          </span>
        </template>
      </el-dialog>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAreaStore } from '../../stores/areas'
import MainLayout from '../../components/MainLayout.vue'
import { LocationFilled } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'

const areaStore = useAreaStore()

// 格式化时间函数
const formatDateTime = (dateTime) => {
  if (!dateTime) return ''
  const date = new Date(dateTime)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// 搜索表单
const searchForm = reactive({
  park_area: ''
})

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)

// 园区区域列表
const areas = ref([])
const selectedAreas = ref([])

// 添加园区区域对话框
const addDialogVisible = ref(false)
const addForm = reactive({
  park_area: '',
  remark: ''
})
const addFormRef = ref(null)
const addLoading = ref(false)

// 编辑园区区域对话框
const editDialogVisible = ref(false)
const editForm = reactive({
  park_area_id: '',
  park_area: '',
  remark: ''
})
const editFormRef = ref(null)
const editLoading = ref(false)

const areaRules = {
  park_area: [
    { required: true, message: '请输入区域名称', trigger: 'blur' }
  ]
}

// 方法
const handleSearch = async () => {
  currentPage.value = 1
  await fetchAreas()
}

const resetForm = () => {
  searchForm.park_area = ''
  currentPage.value = 1
  fetchAreas()
}

const fetchAreas = async () => {
  loading.value = true
  try {
    // 构建参数，过滤掉空值
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    
    // 只添加非空值
    if (searchForm.park_area) params.park_area = searchForm.park_area
    
    const result = await areaStore.fetchAreas(params)
    if (result.success) {
      areas.value = result.data.rows || []
      total.value = result.data.total || 0
    }
  } catch (error) {
    console.error('获取园区区域列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (size) => {
  pageSize.value = size
  fetchAreas()
}

const handleCurrentChange = (current) => {
  currentPage.value = current
  fetchAreas()
}

const addArea = () => {
  // 重置添加表单
  addForm.park_area = ''
  addForm.remark = ''
  addDialogVisible.value = true
}

const editArea = (area) => {
  editForm.park_area_id = area.park_area_id
  editForm.park_area = area.park_area
  editForm.remark = area.remark
  editDialogVisible.value = true
}

const deleteArea = async (area) => {
  try {
    await ElMessageBox.confirm('确定要删除这个园区区域吗？', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const result = await areaStore.deleteArea(area.park_area_id)
    if (result.success) {
      await fetchAreas()
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除园区区域失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理表格选择变化
const handleSelectionChange = (val) => {
  selectedAreas.value = val
}

// 批量删除园区区域
const batchDeleteAreas = async () => {
  if (selectedAreas.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedAreas.value.length} 个园区区域吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const ids = selectedAreas.value.map(area => area.park_area_id).join(',')
    const result = await areaStore.deleteArea(ids)
    if (result.success) {
      selectedAreas.value = []
      await fetchAreas()
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除园区区域失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const submitAddArea = async () => {
  if (!addFormRef.value) return
  
  try {
    const valid = await addFormRef.value.validate()
    if (valid) {
      addLoading.value = true
      try {
        // 添加园区区域
        const createData = {
          park_area: addForm.park_area,
          remark: addForm.remark
        }
        const result = await areaStore.createArea(createData)
        
        if (result.success) {
          addDialogVisible.value = false
          // 重新获取列表
          await fetchAreas()
          ElMessage.success('保存成功')
        } else {
          ElMessage.error(result.message)
        }
      } catch (error) {
        console.error('保存园区区域失败:', error)
        ElMessage.error('保存失败')
      } finally {
        addLoading.value = false
      }
    }
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

const submitEditArea = async () => {
  if (!editFormRef.value) return
  
  try {
    const valid = await editFormRef.value.validate()
    if (valid) {
      editLoading.value = true
      try {
        // 编辑园区区域，移除park_area_id字段
        const updateData = {
          park_area: editForm.park_area,
          remark: editForm.remark
        }
        const result = await areaStore.updateArea(editForm.park_area_id, updateData)
        
        if (result.success) {
          editDialogVisible.value = false
          // 重新获取列表
          await fetchAreas()
          ElMessage.success('保存成功')
        } else {
          ElMessage.error(result.message)
        }
      } catch (error) {
        console.error('保存园区区域失败:', error)
        ElMessage.error('保存失败')
      } finally {
        editLoading.value = false
      }
    }
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

// 生命周期
onMounted(() => {
  fetchAreas()
})
</script>

<style scoped>
.areas {
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

.search-card :deep(.el-button--success) {
  background: linear-gradient(135deg, #536f88 0%, #6f879c 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
}

.search-card :deep(.el-button--success:hover) {
  background: linear-gradient(135deg, #6f879c 0%, #536f88 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(103, 194, 58, 0.4);
}

.search-card :deep(.el-button:not(.el-button--primary):not(.el-button--success):hover) {
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

.dialog-footer {
  text-align: right;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .areas {
    padding: 10px;
  }
  
  .search-card {
    padding: 10px;
  }
  
  .table-card {
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
</style>
