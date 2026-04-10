<template>
  <div class="register-container">
    <el-card class="register-card">
      <h2 class="login-title">
        <img src="../../assets/摄像头.png" alt="园区智能安防系统" class="login-logo">
        注册新账号
      </h2>
      <el-form :model="registerForm" :rules="rules" ref="registerFormRef" @submit.prevent="handleRegister">
        <el-form-item label="用户名" prop="username" :required="false">
          <el-input v-model="registerForm.username" placeholder="请输入用户名">
          </el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password" :required="false">
          <el-input v-model="registerForm.password" type="password" placeholder="请输入密码">
          </el-input>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword" :required="false">
          <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请确认密码">
          </el-input>
        </el-form-item>
        <el-form-item label="姓名" prop="name" :required="false">
          <el-input v-model="registerForm.name" placeholder="请输入姓名">
          </el-input>
        </el-form-item>
        <el-form-item label="手机号" prop="phone" :required="false">
          <el-input v-model="registerForm.phone" placeholder="请输入手机号">
          </el-input>
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
        <el-form-item>
          <el-button type="primary" native-type="submit" class="register-btn" :loading="loading">
            注册
          </el-button>
        </el-form-item>
        <el-form-item>
          <el-link type="primary" @click="$router.push('/login')">返回登录</el-link>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

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
.register-container {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-image: url('../../assets/背景图.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  position: relative;
  overflow: hidden;
}

.register-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(64, 158, 255, 0.05) 100%);
  z-index: 1;
}

.register-card {
  width: 400px;
  padding: 2.5rem;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 2;
  transform-style: preserve-3d;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.register-card:hover {
  transform: translateY(-5px) rotateX(2deg);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
}

.register-card .login-title {
  text-align: center;
  margin-bottom: 2.5rem;
  color: #303133;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  transform-style: preserve-3d;
  transition: all 0.3s ease;
}

.register-card:hover .login-title {
  transform: translateY(-3px) scale(1.02);
}

.login-logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
  transition: all 0.3s ease;
  transform-style: preserve-3d;
}

.register-card:hover .login-logo {
  transform: rotateY(360deg);
  transition-duration: 1s;
}

.register-btn {
  width: 100%;
  padding: 0.75rem;
  font-size: 1rem;
  transition: all 0.3s ease;
  transform-style: preserve-3d;
  position: relative;
  overflow: hidden;
}

.register-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(64, 158, 255, 0.4);
}

.register-btn:active {
  transform: translateY(0);
}

.error-message {
  margin-bottom: 1.5rem;
  animation: shake 0.5s ease;
}

/* 输入框样式优化 */
.register-card .el-input {
  transition: all 0.3s ease;
  transform-style: preserve-3d;
}

.register-card .el-input:focus-within {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(64, 158, 255, 0.2);
}

.register-card .el-input__wrapper {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.register-card .el-input__wrapper:focus-within {
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 表单项目样式 */
.register-card .el-form-item {
  display: flex;
  align-items: center;
  margin-bottom: 1.5rem;
}

/* 输入框标签样式 */
.register-card .el-form-item__label {
  color: #333333;
  width: 80px;
  text-align: right;
  margin-right: 10px;
  white-space: nowrap;
}

/* 确保表单项目内容区域填充剩余空间 */
.register-card .el-form-item__content {
  flex: 1;
  margin-left: 0 !important;
}

/* 确保所有输入框宽度一致 */
.register-card .el-input {
  width: 100% !important;
}

/* 确保性别选项区域与输入框对齐 */
.register-card .el-radio-group {
  display: flex;
  align-items: center;
}

/* 性别选项样式 */
.register-card .el-radio__label {
  color: #333333;
}

/* 登录链接样式 */
.register-card .el-link {
  transition: all 0.3s ease;
  display: inline-block;
  color: #333333;
}

.register-card .el-link:hover {
  transform: translateY(-2px);
  color: #000000;
}

/* 动画效果 */
@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-5px);
  }
  75% {
    transform: translateX(5px);
  }
}

/* 背景动画效果 */
.register-container::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(64, 158, 255, 0.1) 0%, transparent 70%);
  animation: pulse 8s ease-in-out infinite;
  z-index: 1;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.3;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.1;
  }
}

/* 响应式设计 */
@media (max-width: 480px) {
  .register-card {
    width: 90%;
    padding: 2rem;
  }
  
  .register-card:hover {
    transform: translateY(-3px);
  }
}
</style>
