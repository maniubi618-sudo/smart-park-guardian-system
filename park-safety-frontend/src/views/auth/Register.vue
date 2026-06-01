<template>
  <div class="auth-page register-page">
    <section class="auth-visual" aria-hidden="true">
      <img class="auth-asset" src="../../assets/auth-command-center.svg" alt="">
      <div class="radar-panel">
        <div class="radar-grid"></div>
        <div class="radar-sweep"></div>
        <div class="radar-point point-a"></div>
        <div class="radar-point point-b"></div>
        <div class="radar-point point-c"></div>
      </div>
      <div class="visual-copy">
        <span>ACCESS PROVISIONING</span>
        <h1>创建安防控制台账号</h1>
        <p>为园区值班、设备巡检和告警处置人员开通统一操作身份</p>
      </div>
    </section>

    <section class="auth-panel">
      <div class="auth-card register-card">
        <div class="auth-title">
          <div class="auth-logo">
            <el-icon><UserFilled /></el-icon>
          </div>
          <div>
            <span>Command Center</span>
            <h2>注册新账号</h2>
          </div>
        </div>

        <el-form :model="registerForm" :rules="rules" ref="registerFormRef" label-position="top" @submit.prevent="handleRegister">
          <el-form-item label="用户名" prop="username" :required="false">
            <el-input v-model="registerForm.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="密码" prop="password" :required="false">
            <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword" :required="false">
            <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请确认密码" />
          </el-form-item>
          <el-form-item label="姓名" prop="name" :required="false">
            <el-input v-model="registerForm.name" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone" :required="false">
            <el-input v-model="registerForm.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="性别" prop="gender" :required="false">
            <el-radio-group v-model="registerForm.gender">
              <el-radio label="1">男</el-radio>
              <el-radio label="0">女</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="error" class="error-message">
            <el-alert :title="error" type="error" show-icon :closable="false" />
          </el-form-item>
          <el-button type="primary" native-type="submit" class="auth-submit" size="large" :loading="loading">
            注册
          </el-button>
          <div class="auth-footer-link">
            <el-link type="primary" @click="$router.push('/login')">返回登录</el-link>
          </div>
        </el-form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { UserFilled } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const registerFormRef = ref(null)
const loading = ref(false)
const error = ref('')

const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  name: '',
  phone: '',
  gender: 1
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      error.value = ''

      const userData = {
        user_name: registerForm.username,
        password: registerForm.password,
        name: registerForm.name,
        phone: registerForm.phone,
        gender: registerForm.gender
      }

      const result = await authStore.register(userData)

      if (result.success) {
        router.push('/dashboard')
      } else {
        error.value = result.message || '注册失败'
      }

      loading.value = false
    }
  })
}
</script>

<style scoped>
@import './auth.css';

.register-page .auth-card {
  max-height: calc(100vh - 64px);
  overflow-y: auto;
}

.register-card :deep(.el-form-item) {
  margin-bottom: 14px;
}

.register-card :deep(.el-form-item__label) {
  margin-bottom: 6px;
  color: var(--text-color-secondary);
  font-size: 13px;
  font-weight: 700;
}

.auth-footer-link {
  margin-top: 16px;
  text-align: center;
}
</style>
