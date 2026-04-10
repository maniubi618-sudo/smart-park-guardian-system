<template>
  <div class="login-container">
    <!-- 3D等待动画 -->
    <div v-if="showLoading" class="loading-container">
      <div class="loading-3d">
        <div class="loading-cubes">
          <!-- 外层立方体 -->
          <div class="loading-cube cube-1">
            <div class="cube-face front"></div>
            <div class="cube-face back"></div>
            <div class="cube-face right"></div>
            <div class="cube-face left"></div>
            <div class="cube-face top"></div>
            <div class="cube-face bottom"></div>
          </div>
          <div class="loading-cube cube-2">
            <div class="cube-face front"></div>
            <div class="cube-face back"></div>
            <div class="cube-face right"></div>
            <div class="cube-face left"></div>
            <div class="cube-face top"></div>
            <div class="cube-face bottom"></div>
          </div>
          <!-- 中层立方体 -->
          <div class="loading-cube cube-3">
            <div class="cube-face front"></div>
            <div class="cube-face back"></div>
            <div class="cube-face right"></div>
            <div class="cube-face left"></div>
            <div class="cube-face top"></div>
            <div class="cube-face bottom"></div>
          </div>
          <div class="loading-cube cube-4">
            <div class="cube-face front"></div>
            <div class="cube-face back"></div>
            <div class="cube-face right"></div>
            <div class="cube-face left"></div>
            <div class="cube-face top"></div>
            <div class="cube-face bottom"></div>
          </div>
          <!-- 内层立方体 -->
          <div class="loading-cube cube-5">
            <div class="cube-face front"></div>
            <div class="cube-face back"></div>
            <div class="cube-face right"></div>
            <div class="cube-face left"></div>
            <div class="cube-face top"></div>
            <div class="cube-face bottom"></div>
          </div>
          <div class="loading-cube cube-6">
            <div class="cube-face front"></div>
            <div class="cube-face back"></div>
            <div class="cube-face right"></div>
            <div class="cube-face left"></div>
            <div class="cube-face top"></div>
            <div class="cube-face bottom"></div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="login-content">
      <!-- 左侧GIF图片 -->
      <div class="login-gif">
        <img src="../../assets/制作园区安防系统 3D 视频-ezremove 00_00_00-00_00_30.gif" alt="园区智能安防系统" class="gif-image">
      </div>
      
      <!-- 右侧登录卡片 -->
      <el-card class="login-card">
        <h2 class="login-title">
          <img src="../../assets/摄像头.png" alt="园区智能安防系统" class="login-logo">
          园区智能安防系统
        </h2>
        <el-form :model="loginForm" :rules="rules" ref="loginFormRef" @submit.prevent="handleLogin">
          <el-form-item prop="username" :required="false">
            <div class="input-with-icon">
              <div class="input-icon-wrapper">
                <el-icon class="input-icon"><User /></el-icon>
              </div>
              <el-input v-model="loginForm.username" placeholder="请输入用户名">
              </el-input>
            </div>
          </el-form-item>
          <el-form-item prop="password" :required="false">
            <div class="input-with-icon">
              <div class="input-icon-wrapper">
                <el-icon class="input-icon"><Lock /></el-icon>
              </div>
              <el-input 
                v-model="loginForm.password" 
                :type="showPassword ? 'text' : 'password'" 
                placeholder="请输入密码"
              >
                <template #suffix>
                  <el-icon @click="togglePasswordVisibility" class="password-toggle-icon">
                    <View v-if="!showPassword" />
                    <Hide v-else />
                  </el-icon>
                </template>
              </el-input>
            </div>
          </el-form-item>
          <el-form-item v-if="error" class="error-message">
            <el-alert :title="error" type="error" show-icon :closable="false" />
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="loginForm.rememberMe">记住我</el-checkbox>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" native-type="submit" class="login-btn" :loading="loading">
              登录
            </el-button>
          </el-form-item>
          <el-form-item>
            <el-link type="primary" @click="$router.push('/register')">注册新账号</el-link>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { View, Hide, User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref(null)
const loading = ref(false)
const error = ref('')
const showLoading = ref(true)
const showPassword = ref(false)

// 模拟加载过程
setTimeout(() => {
  showLoading.value = false
}, 2000)

const loginForm = reactive({
  username: localStorage.getItem('rememberedUsername') || '',
  password: '',
  rememberMe: localStorage.getItem('rememberMe') === 'true'
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      error.value = ''
      
      const result = await authStore.login(loginForm.username, loginForm.password)
      
      if (result.success) {
        // 处理记住我功能
        if (loginForm.rememberMe) {
          localStorage.setItem('rememberedUsername', loginForm.username)
          localStorage.setItem('rememberMe', 'true')
        } else {
          localStorage.removeItem('rememberedUsername')
          localStorage.removeItem('rememberMe')
        }
        router.push('/dashboard')
      } else {
        error.value = result.message || '登录失败'
      }
      
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  background-image: url('../../assets/背景图.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-content {
  display: flex;
  width: 90%;
  max-width: 1200px;
  height: 80vh;
  max-height: 600px;
  position: relative;
  z-index: 2;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  border-radius: 16px;
  overflow: hidden;
}

.login-gif {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2.5rem;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 12px 0 0 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 2;
  transform-style: preserve-3d;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-right: none;
  display: flex;
  flex-direction: column;
  justify-content: center;
  opacity: 0.9;
}

.login-gif:hover {
  transform: translateY(-5px) rotateX(2deg);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
}
.gif-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.login-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(64, 158, 255, 0.05) 100%);
  z-index: 1;
}

.login-card {
  width: 450px;
  padding: 2.5rem;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 0 12px 12px 0;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 2;
  transform-style: preserve-3d;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-left: none;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-card:hover {
  transform: translateY(-5px) rotateX(2deg);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
}

.login-card .login-title {
  text-align: center;
  margin-bottom: 2.5rem;
  color: #303133;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  transform-style: preserve-3d;
  transition: all 0.3s ease;
  opacity: 1;
}

.login-card:hover .login-title {
  transform: translateY(-3px) scale(1.02);
}

.login-logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
  transition: all 0.3s ease;
  transform-style: preserve-3d;
}

.login-card:hover .login-logo {
  transform: rotateY(360deg);
  transition-duration: 1s;
}

/* 表单样式优化 */
.login-card .el-form {
  width: 100%;
}

.login-card .el-form-item {
  margin-bottom: 1.25rem;
}

.login-card .el-form-item__label {
  font-size: 1rem;
  color: #606266;
  font-weight: 500;
}

/* 输入框样式优化 */
.login-card .el-input {
  transition: all 0.3s ease;
  transform-style: preserve-3d;
}

.login-card .el-input:focus-within {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(64, 158, 255, 0.2);
}

.login-card .el-input__wrapper {
  border-radius: 8px;
  transition: all 0.3s ease;
}

/* 密码切换图标样式 */
.password-toggle-icon {
  cursor: pointer;
  color: #333333;
  transition: all 0.3s ease;
  font-size: 18px;
}

.password-toggle-icon:hover {
  color: #000000;
  transform: scale(1.1);
}

/* 输入框左侧图标样式 */
.input-with-icon {
  display: flex !important;
  align-items: center !important;
  gap: 12px !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  width: 100% !important;
}

.input-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.input-icon {
  color: #333333;
  transition: all 0.3s ease;
  font-size: 18px;
}

.input-with-icon:focus-within .input-icon-wrapper {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(64, 158, 255, 0.2);
}

.input-with-icon:focus-within .input-icon {
  color: #000000;
  transform: scale(1.1);
}

/* 确保输入框高度与图标容器一致 */
.input-with-icon .el-input {
  height: 40px !important;
  flex: 1 !important;
  min-width: 0 !important;
}

.input-with-icon .el-input__wrapper {
  height: 100% !important;
  width: 100% !important;
}

/* 确保表单项目内容区域填充整个宽度 */
.input-with-icon + .el-form-item__error {
  margin-left: 52px !important;
}

.login-card .el-input__wrapper:focus-within {
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 记住我样式 */
.login-card .el-checkbox {
  font-size: 0.9rem;
  color: #606266;
}

.login-card .el-checkbox__label {
  margin-left: 0.5rem;
}

/* 确保记住我按钮点击后不变色 */
.login-card :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #f0f0f0 !important;
  border-color: #dcdfe6 !important;
}

.login-card :deep(.el-checkbox__input.is-checked .el-checkbox__inner::after) {
  border-color: #909399 !important;
}

.login-card :deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: #606266 !important;
}

/* 确保鼠标悬停时也不变色 */
.login-card :deep(.el-checkbox__input:hover .el-checkbox__inner) {
  border-color: #dcdfe6 !important;
}

.login-card :deep(.el-checkbox__input.is-checked:hover .el-checkbox__inner) {
  background-color: #f0f0f0 !important;
  border-color: #dcdfe6 !important;
}

/* 确保点击时也不变色 */
.login-card :deep(.el-checkbox__input.is-checked.is-focus .el-checkbox__inner) {
  background-color: #f0f0f0 !important;
  border-color: #dcdfe6 !important;
}

/* 确保复选框默认样式 */
.login-card :deep(.el-checkbox__input .el-checkbox__inner) {
  background-color: #f0f0f0 !important;
  border-color: #dcdfe6 !important;
}

/* 登录按钮样式 */
.login-btn {
  width: 100%;
  padding: 0.75rem;
  font-size: 1rem;
  transition: all 0.3s ease;
  transform-style: preserve-3d;
  position: relative;
  overflow: hidden;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(64, 158, 255, 0.4);
}

.login-btn:active {
  transform: translateY(0);
}

/* 错误信息样式 */
.error-message {
  margin-bottom: 1.5rem;
  animation: shake 0.5s ease;
}

.error-message .el-alert {
  border-radius: 8px;
}

/* 注册链接样式 */
.login-card .el-link {
  transition: all 0.3s ease;
  display: inline-block;
  color: #333333;
}

.login-card .el-link:hover {
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
.login-container::after {
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

/* 3D等待动画样式 */
.loading-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  z-index: 1000;
}

.loading-3d {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-cubes {
  position: relative;
  width: 400px;
  height: 400px;
  margin-bottom: 20px;
}

.loading-cube {
  position: absolute;
  top: 50%;
  left: 50%;
  transform-style: preserve-3d;
  animation: rotate 3s linear infinite;
}

/* 外层立方体 */
.cube-1 {
  width: 240px;
  height: 240px;
  margin-top: -120px;
  margin-left: -120px;
  animation-delay: 0s;
}

.cube-2 {
  width: 192px;
  height: 192px;
  margin-top: -96px;
  margin-left: -96px;
  animation-delay: -1.5s;
}

/* 中层立方体 */
.cube-3 {
  width: 144px;
  height: 144px;
  margin-top: -72px;
  margin-left: -72px;
  animation-delay: -0.75s;
}

.cube-4 {
  width: 108px;
  height: 108px;
  margin-top: -54px;
  margin-left: -54px;
  animation-delay: -2.25s;
}

/* 内层立方体 */
.cube-5 {
  width: 72px;
  height: 72px;
  margin-top: -36px;
  margin-left: -36px;
  animation-delay: -1.125s;
}

.cube-6 {
  width: 48px;
  height: 48px;
  margin-top: -24px;
  margin-left: -24px;
  animation-delay: -2.625s;
}

.cube-face {
  position: absolute;
  border: 2px solid var(--primary-color);
  opacity: 0.7;
  background-color: rgba(64, 158, 255, 0.2);
}

/* 第一个立方体的面 - 外层 */
.cube-1 .cube-face {
  width: 240px;
  height: 240px;
}

.cube-1 .cube-face.front {
  transform: translateZ(120px);
}

.cube-1 .cube-face.back {
  transform: rotateY(180deg) translateZ(120px);
}

.cube-1 .cube-face.right {
  transform: rotateY(90deg) translateZ(120px);
}

.cube-1 .cube-face.left {
  transform: rotateY(-90deg) translateZ(120px);
}

.cube-1 .cube-face.top {
  transform: rotateX(90deg) translateZ(120px);
}

.cube-1 .cube-face.bottom {
  transform: rotateX(-90deg) translateZ(120px);
}

/* 第二个立方体的面 - 外层 */
.cube-2 .cube-face {
  width: 192px;
  height: 192px;
}

.cube-2 .cube-face.front {
  transform: translateZ(96px);
}

.cube-2 .cube-face.back {
  transform: rotateY(180deg) translateZ(96px);
}

.cube-2 .cube-face.right {
  transform: rotateY(90deg) translateZ(96px);
}

.cube-2 .cube-face.left {
  transform: rotateY(-90deg) translateZ(96px);
}

.cube-2 .cube-face.top {
  transform: rotateX(90deg) translateZ(96px);
}

.cube-2 .cube-face.bottom {
  transform: rotateX(-90deg) translateZ(96px);
}

/* 第三个立方体的面 - 中层 */
.cube-3 .cube-face {
  width: 144px;
  height: 144px;
}

.cube-3 .cube-face.front {
  transform: translateZ(72px);
}

.cube-3 .cube-face.back {
  transform: rotateY(180deg) translateZ(72px);
}

.cube-3 .cube-face.right {
  transform: rotateY(90deg) translateZ(72px);
}

.cube-3 .cube-face.left {
  transform: rotateY(-90deg) translateZ(72px);
}

.cube-3 .cube-face.top {
  transform: rotateX(90deg) translateZ(72px);
}

.cube-3 .cube-face.bottom {
  transform: rotateX(-90deg) translateZ(72px);
}

/* 第四个立方体的面 - 中层 */
.cube-4 .cube-face {
  width: 108px;
  height: 108px;
}

.cube-4 .cube-face.front {
  transform: translateZ(54px);
}

.cube-4 .cube-face.back {
  transform: rotateY(180deg) translateZ(54px);
}

.cube-4 .cube-face.right {
  transform: rotateY(90deg) translateZ(54px);
}

.cube-4 .cube-face.left {
  transform: rotateY(-90deg) translateZ(54px);
}

.cube-4 .cube-face.top {
  transform: rotateX(90deg) translateZ(54px);
}

.cube-4 .cube-face.bottom {
  transform: rotateX(-90deg) translateZ(54px);
}

/* 第五个立方体的面 - 内层 */
.cube-5 .cube-face {
  width: 72px;
  height: 72px;
}

.cube-5 .cube-face.front {
  transform: translateZ(36px);
}

.cube-5 .cube-face.back {
  transform: rotateY(180deg) translateZ(36px);
}

.cube-5 .cube-face.right {
  transform: rotateY(90deg) translateZ(36px);
}

.cube-5 .cube-face.left {
  transform: rotateY(-90deg) translateZ(36px);
}

.cube-5 .cube-face.top {
  transform: rotateX(90deg) translateZ(36px);
}

.cube-5 .cube-face.bottom {
  transform: rotateX(-90deg) translateZ(36px);
}

/* 第六个立方体的面 - 内层 */
.cube-6 .cube-face {
  width: 48px;
  height: 48px;
}

.cube-6 .cube-face.front {
  transform: translateZ(24px);
}

.cube-6 .cube-face.back {
  transform: rotateY(180deg) translateZ(24px);
}

.cube-6 .cube-face.right {
  transform: rotateY(90deg) translateZ(24px);
}

.cube-6 .cube-face.left {
  transform: rotateY(-90deg) translateZ(24px);
}

.cube-6 .cube-face.top {
  transform: rotateX(90deg) translateZ(24px);
}

.cube-6 .cube-face.bottom {
  transform: rotateX(-90deg) translateZ(24px);
}

@keyframes rotate {
  0% {
    transform: rotateX(0deg) rotateY(0deg);
  }
  100% {
    transform: rotateX(360deg) rotateY(360deg);
  }
}

.loading-text {
  color: var(--text-color);
  font-size: 1rem;
  margin-top: 1rem;
  animation: pulse-text 1.5s ease-in-out infinite;
}

@keyframes pulse-text {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-content {
    flex-direction: column;
    width: 95%;
    height: 90vh;
  }
  
  .login-gif {
    flex: 1;
    min-height: 30vh;
  }
  
  .login-card {
    flex: 1;
    width: 100%;
    padding: 2rem;
  }
  
  .login-card:hover {
    transform: translateY(-2px);
  }
}

@media (max-width: 480px) {
  .login-content {
    width: 98%;
    height: 95vh;
  }
  
  .login-gif {
    padding: 1rem;
  }
  
  .login-card {
    padding: 1.5rem;
  }
  
  .login-card .login-title {
    margin-bottom: 2rem;
  }
  
  .loading-cubes {
    width: 300px;
    height: 300px;
  }
  
  /* 外层立方体 */
  .cube-1 {
    width: 180px;
    height: 180px;
    margin-top: -90px;
    margin-left: -90px;
  }
  
  .cube-2 {
    width: 144px;
    height: 144px;
    margin-top: -72px;
    margin-left: -72px;
  }
  
  /* 中层立方体 */
  .cube-3 {
    width: 108px;
    height: 108px;
    margin-top: -54px;
    margin-left: -54px;
  }
  
  .cube-4 {
    width: 81px;
    height: 81px;
    margin-top: -40.5px;
    margin-left: -40.5px;
  }
  
  /* 内层立方体 */
  .cube-5 {
    width: 54px;
    height: 54px;
    margin-top: -27px;
    margin-left: -27px;
  }
  
  .cube-6 {
    width: 36px;
    height: 36px;
    margin-top: -18px;
    margin-left: -18px;
  }
  
  /* 第一个立方体的面 - 外层 */
  .cube-1 .cube-face {
    width: 180px;
    height: 180px;
  }
  
  .cube-1 .cube-face.front {
    transform: translateZ(90px);
  }
  
  .cube-1 .cube-face.back {
    transform: rotateY(180deg) translateZ(90px);
  }
  
  .cube-1 .cube-face.right {
    transform: rotateY(90deg) translateZ(90px);
  }
  
  .cube-1 .cube-face.left {
    transform: rotateY(-90deg) translateZ(90px);
  }
  
  .cube-1 .cube-face.top {
    transform: rotateX(90deg) translateZ(90px);
  }
  
  .cube-1 .cube-face.bottom {
    transform: rotateX(-90deg) translateZ(90px);
  }
  
  /* 第二个立方体的面 - 外层 */
  .cube-2 .cube-face {
    width: 144px;
    height: 144px;
  }
  
  .cube-2 .cube-face.front {
    transform: translateZ(72px);
  }
  
  .cube-2 .cube-face.back {
    transform: rotateY(180deg) translateZ(72px);
  }
  
  .cube-2 .cube-face.right {
    transform: rotateY(90deg) translateZ(72px);
  }
  
  .cube-2 .cube-face.left {
    transform: rotateY(-90deg) translateZ(72px);
  }
  
  .cube-2 .cube-face.top {
    transform: rotateX(90deg) translateZ(72px);
  }
  
  .cube-2 .cube-face.bottom {
    transform: rotateX(-90deg) translateZ(72px);
  }
  
  /* 第三个立方体的面 - 中层 */
  .cube-3 .cube-face {
    width: 108px;
    height: 108px;
  }
  
  .cube-3 .cube-face.front {
    transform: translateZ(54px);
  }
  
  .cube-3 .cube-face.back {
    transform: rotateY(180deg) translateZ(54px);
  }
  
  .cube-3 .cube-face.right {
    transform: rotateY(90deg) translateZ(54px);
  }
  
  .cube-3 .cube-face.left {
    transform: rotateY(-90deg) translateZ(54px);
  }
  
  .cube-3 .cube-face.top {
    transform: rotateX(90deg) translateZ(54px);
  }
  
  .cube-3 .cube-face.bottom {
    transform: rotateX(-90deg) translateZ(54px);
  }
  
  /* 第四个立方体的面 - 中层 */
  .cube-4 .cube-face {
    width: 81px;
    height: 81px;
  }
  
  .cube-4 .cube-face.front {
    transform: translateZ(40.5px);
  }
  
  .cube-4 .cube-face.back {
    transform: rotateY(180deg) translateZ(40.5px);
  }
  
  .cube-4 .cube-face.right {
    transform: rotateY(90deg) translateZ(40.5px);
  }
  
  .cube-4 .cube-face.left {
    transform: rotateY(-90deg) translateZ(40.5px);
  }
  
  .cube-4 .cube-face.top {
    transform: rotateX(90deg) translateZ(40.5px);
  }
  
  .cube-4 .cube-face.bottom {
    transform: rotateX(-90deg) translateZ(40.5px);
  }
  
  /* 第五个立方体的面 - 内层 */
  .cube-5 .cube-face {
    width: 54px;
    height: 54px;
  }
  
  .cube-5 .cube-face.front {
    transform: translateZ(27px);
  }
  
  .cube-5 .cube-face.back {
    transform: rotateY(180deg) translateZ(27px);
  }
  
  .cube-5 .cube-face.right {
    transform: rotateY(90deg) translateZ(27px);
  }
  
  .cube-5 .cube-face.left {
    transform: rotateY(-90deg) translateZ(27px);
  }
  
  .cube-5 .cube-face.top {
    transform: rotateX(90deg) translateZ(27px);
  }
  
  .cube-5 .cube-face.bottom {
    transform: rotateX(-90deg) translateZ(27px);
  }
  
  /* 第六个立方体的面 - 内层 */
  .cube-6 .cube-face {
    width: 36px;
    height: 36px;
  }
  
  .cube-6 .cube-face.front {
    transform: translateZ(18px);
  }
  
  .cube-6 .cube-face.back {
    transform: rotateY(180deg) translateZ(18px);
  }
  
  .cube-6 .cube-face.right {
    transform: rotateY(90deg) translateZ(18px);
  }
  
  .cube-6 .cube-face.left {
    transform: rotateY(-90deg) translateZ(18px);
  }
  
  .cube-6 .cube-face.top {
    transform: rotateX(90deg) translateZ(18px);
  }
  
  .cube-6 .cube-face.bottom {
    transform: rotateX(-90deg) translateZ(18px);
  }
}
</style>
