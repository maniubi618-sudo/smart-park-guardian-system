<template>
  <MainLayout>
    <div class="users">
      <!-- 搜索和筛选 -->
      <el-card class="search-card">
        <el-form :model="searchForm" inline>
          <el-form-item label="用户姓名">
            <el-input v-model="searchForm.name" placeholder="请输入用户姓名" />
          </el-form-item>
          <el-form-item label="性别">
            <el-select v-model="searchForm.gender" placeholder="请选择性别">
              <el-option label="男" value="1" />
              <el-option label="女" value="0" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="resetForm">重置</el-button>
            <el-button type="success" @click="openAddUserDialog">添加用户</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 用户列表 -->
      <el-card class="table-card">
        <div class="table-header" style="margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
          <span></span>
          <el-button type="danger" @click="batchDeleteUsers" :disabled="selectedUsers.length === 0">
            批量删除
          </el-button>
        </div>
        <el-table :data="users" stripe style="width: 100%" v-loading="loading" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="55" />
          <el-table-column prop="user_id" label="用户ID" width="100" align="center" />
          <el-table-column prop="user_name" label="用户名" />
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="gender" label="性别" width="80">
            <template #default="scope">
              {{ scope.row.gender === 1 ? '男' : '女' }}
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="手机号" width="150" />
          <el-table-column prop="user_role" label="角色" width="120">
            <template #default="scope">
              <el-tag :type="getUserRoleTag(scope.row.user_role)">
                {{ getUserRoleName(scope.row.user_role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="create_time" label="创建时间" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.create_time) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button type="primary" size="small" @click="editUser(scope.row)">
                编辑
              </el-button>
              <el-button type="danger" size="small" @click="deleteUser(scope.row)">
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

      <!-- 用户编辑对话框 -->
      <el-dialog
        v-model="dialogVisible"
        :title="isEdit ? '编辑用户' : '添加用户'"
        width="500px"
      >
        <el-form :model="userForm" :rules="userRules" ref="userFormRef">
          <el-form-item label="用户名" prop="user_name">
            <el-input v-model="userForm.user_name" placeholder="请输入用户名" :disabled="isEdit" />
          </el-form-item>
          <el-form-item label="姓名" prop="name">
            <el-input v-model="userForm.name" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="性别" prop="gender">
            <el-radio-group v-model="userForm.gender">
              <el-radio :label="1">男</el-radio>
              <el-radio :label="0">女</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="userForm.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="角色" prop="user_role">
            <el-select v-model="userForm.user_role" placeholder="请选择角色">
              <el-option label="管理员" :value="0" />
              <el-option label="安保管理员" :value="1" />
              <el-option label="普通操作员" :value="2" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="!isEdit" label="密码" prop="password">
            <el-input v-model="userForm.password" type="password" placeholder="请输入密码" />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitUser" :loading="submitLoading">提交</el-button>
          </span>
        </template>
      </el-dialog>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '../../stores/users'
import MainLayout from '../../components/MainLayout.vue'
import { UserFilled } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'

const userStore = useUserStore()

// 搜索表单
const searchForm = reactive({
  name: '',
  gender: ''
})

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)

// 用户列表
const users = ref([])
const selectedUsers = ref([])

// 编辑对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const userForm = reactive({
  user_id: '',
  user_name: '',
  name: '',
  gender: 1,
  phone: '',
  user_role: 2,
  password: ''
})
const userFormRef = ref(null)
const submitLoading = ref(false)

const userRules = {
  user_name: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  user_role: [
    { required: true, message: '请选择角色', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为6位', trigger: 'blur' }
  ]
}

// 方法
const getUserRoleName = (role) => {
  const roleMap = {
    0: '管理员',
    1: '安保管理员',
    2: '普通操作员'
  }
  return roleMap[role] || '未知'
}

const getUserRoleTag = (role) => {
  const tagMap = {
    0: 'danger',
    1: 'warning',
    2: 'success'
  }
  return tagMap[role] || 'info'
}

const formatDateTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const handleSearch = async () => {
  currentPage.value = 1
  await fetchUsers()
}

const resetForm = () => {
  searchForm.name = ''
  searchForm.gender = ''
  currentPage.value = 1
  fetchUsers()
}

const fetchUsers = async () => {
  loading.value = true
  try {
    // 构建参数，过滤掉空值
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    
    // 只添加非空值
    if (searchForm.name) params.name = searchForm.name
    if (searchForm.gender !== '') params.gender = parseInt(searchForm.gender)
    
    const result = await userStore.fetchUsers(params)
    if (result.success) {
      users.value = result.data.rows || []
      total.value = result.data.total || 0
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (size) => {
  pageSize.value = size
  fetchUsers()
}

const handleCurrentChange = (current) => {
  currentPage.value = current
  fetchUsers()
}

const editUser = (user) => {
  isEdit.value = true
  userForm.user_id = user.user_id
  userForm.user_name = user.user_name
  userForm.name = user.name
  userForm.gender = user.gender
  userForm.phone = user.phone
  userForm.user_role = Number(user.user_role)
  userForm.password = ''
  dialogVisible.value = true
}

const deleteUser = async (user) => {
  try {
    await ElMessageBox.confirm('确定要删除这个用户吗？', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const result = await userStore.deleteUser(user.user_id)
    if (result.success) {
      await fetchUsers()
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理表格选择变化
const handleSelectionChange = (val) => {
  selectedUsers.value = val
}

// 批量删除用户
const batchDeleteUsers = async () => {
  if (selectedUsers.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedUsers.value.length} 个用户吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const ids = selectedUsers.value.map(user => user.user_id).join(',')
    const result = await userStore.deleteUser(ids)
    if (result.success) {
      selectedUsers.value = []
      await fetchUsers()
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除用户失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const openAddUserDialog = () => {
  isEdit.value = false
  // 重置表单，确保角色默认值为2
  Object.assign(userForm, {
    user_id: '',
    user_name: '',
    name: '',
    gender: 1,
    phone: '',
    user_role: 2,
    password: ''
  })
  dialogVisible.value = true
}

const submitUser = async () => {
  if (!userFormRef.value) return
  
  try {
    const valid = await userFormRef.value.validate()
    if (valid) {
      submitLoading.value = true
      try {
        let result
        if (isEdit.value) {
          // 编辑用户 - 排除user_id字段和空密码
          const updateData = { ...userForm }
          delete updateData.user_id
          if (updateData.password === '') {
            delete updateData.password
          }
          result = await userStore.updateUser(userForm.user_id, updateData)
        } else {
          // 添加用户
          result = await userStore.createUser(userForm)
        }
        
        if (result.success) {
          dialogVisible.value = false
          // 重新获取列表
          await fetchUsers()
          ElMessage.success(isEdit.value ? '编辑成功' : '添加成功')
        } else {
          ElMessage.error(result.message || '操作失败')
        }
      } catch (error) {
        console.error('保存用户失败:', error)
        ElMessage.error('保存失败')
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
  fetchUsers()
})
</script>

<style scoped>
.users {
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

.table-card :deep(el-tag) {
  border-radius: 6px;
  font-size: 0.75rem;
  padding: 2px 8px;
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
  .users {
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
