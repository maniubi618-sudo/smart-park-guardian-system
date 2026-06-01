<template>
  <div class="auth-page">
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
        <span>SMART PARK SECURITY</span>
        <h1>园区智能安防系统</h1>
        <p>实时告警、设备巡检、区域态势与 AI 辅助处置统一入口</p>
      </div>
    </section>

    <section class="auth-panel">
      <div class="auth-card">
        <div class="auth-title">
          <div class="auth-logo">
            <el-icon><Monitor /></el-icon>
          </div>
          <div>
            <span>Command Center</span>
            <h2>登录控制台</h2>
          </div>
        </div>

        <el-form :model="loginForm" :rules="rules" ref="loginFormRef" @submit.prevent="handleLogin">
          <el-form-item prop="username" :required="false">
            <el-input v-model="loginForm.username" placeholder="请输入用户名" size="large">
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item prop="password" :required="false">
            <el-input
              v-model="loginForm.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请输入密码"
              size="large"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
              <template #suffix>
                <el-icon @click="togglePasswordVisibility" class="password-toggle-icon">
                  <View v-if="!showPassword" />
                  <Hide v-else />
                </el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item v-if="error" class="error-message">
            <el-alert :title="error" type="error" show-icon :closable="false" />
          </el-form-item>
          <div class="auth-options">
            <el-checkbox v-model="loginForm.rememberMe">记住账号</el-checkbox>
            <el-link type="primary" @click="$router.push('/register')">注册新账号</el-link>
          </div>
          <el-button type="primary" native-type="submit" class="auth-submit" size="large" :loading="loading">
            登录
          </el-button>
        </el-form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { View, Hide, User, Lock, Monitor } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref(null)
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

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
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 460px;
  background:
    radial-gradient(circle at 14% 18%, rgba(83, 111, 136, 0.24), transparent 28rem),
    radial-gradient(circle at 62% 78%, rgba(197, 138, 69, 0.18), transparent 24rem),
    linear-gradient(135deg, #20262a 0%, #344e66 45%, #eef2f5 45.1%, #fbfaf7 100%);
}

.auth-visual {
  position: relative;
  min-height: 100vh;
  padding: 56px;
  overflow: hidden;
  color: #fbfaf7;
  animation: authVisualIn var(--motion-page) var(--motion-ease) both;
}

@keyframes authVisualIn {
  from { opacity: 0; transform: translateX(-16px); }
  to { opacity: 1; transform: translateX(0); }
}

.auth-asset {
  position: absolute;
  right: 5%;
  bottom: 5%;
  width: min(58vw, 720px);
  max-height: 72vh;
  object-fit: contain;
  opacity: 0.58;
  filter: drop-shadow(0 28px 60px rgba(0, 0, 0, 0.36));
  animation: authAssetDrift 7s var(--motion-ease) infinite alternate;
}

@keyframes authAssetDrift {
  from { transform: translate3d(0, 0, 0) scale(1); }
  to { transform: translate3d(-12px, -10px, 0) scale(1.02); }
}

.auth-visual::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(216, 224, 231, 0.10) 1px, transparent 1px),
    linear-gradient(90deg, rgba(216, 224, 231, 0.10) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(120deg, #000 0%, transparent 74%);
}

.radar-panel {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(54vw, 620px);
  aspect-ratio: 1;
  border: 1px solid rgba(216, 224, 231, 0.26);
  border-radius: 50%;
  transform: translate(-50%, -45%);
  background: radial-gradient(circle, rgba(83, 111, 136, 0.14), transparent 62%);
  box-shadow: inset 0 0 90px rgba(83, 111, 136, 0.18);
}

.radar-grid {
  position: absolute;
  inset: 12%;
  border: 1px solid rgba(216, 224, 231, 0.22);
  border-radius: 50%;
}

.radar-grid::before,
.radar-grid::after {
  content: "";
  position: absolute;
  inset: 23%;
  border: 1px solid rgba(216, 224, 231, 0.18);
  border-radius: 50%;
}

.radar-grid::after {
  inset: 46%;
}

.radar-sweep {
  position: absolute;
  inset: 50% 50% 0 50%;
  width: 48%;
  height: 1px;
  transform-origin: 0 0;
  transform: rotate(-24deg);
  background: linear-gradient(90deg, rgba(216, 224, 231, 0.95), transparent);
  animation: authRadarSweep 4.8s linear infinite;
}

@keyframes authRadarSweep {
  from { transform: rotate(-24deg); }
  to { transform: rotate(336deg); }
}

.radar-point {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #f59e0b;
  box-shadow: 0 0 0 7px rgba(245, 158, 11, 0.18);
}

.point-a { left: 32%; top: 28%; }
.point-b { right: 24%; top: 42%; background: #536f88; box-shadow: 0 0 0 7px rgba(83, 111, 136, 0.16); }
.point-c { left: 50%; bottom: 24%; background: #ef4444; box-shadow: 0 0 0 7px rgba(239, 68, 68, 0.16); }

.visual-copy {
  position: relative;
  z-index: 1;
  max-width: 560px;
}

.visual-copy span,
.auth-title span {
  color: #c8d3dc;
  font-size: 12px;
  font-weight: 850;
  letter-spacing: 0.12em;
}

.visual-copy h1 {
  margin: 18px 0 14px;
  font-size: 48px;
  line-height: 1.08;
  letter-spacing: 0;
}

.visual-copy p {
  margin: 0;
  max-width: 440px;
  color: rgba(251, 250, 247, 0.72);
  font-size: 16px;
}

.auth-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 32px;
}

.auth-card {
  width: 100%;
  padding: 34px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: var(--shadow-strong);
  animation: authCardIn var(--motion-slow) var(--motion-ease) 120ms both;
}

@keyframes authCardIn {
  from { opacity: 0; transform: translateY(18px) scale(0.985); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.auth-title {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.auth-logo {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  color: #fbfaf7;
  background: linear-gradient(135deg, #344e66, #536f88);
  border-radius: 8px;
  font-size: 24px;
}

.auth-title h2 {
  margin: 4px 0 0;
  color: var(--text-color);
  font-size: 24px;
  font-weight: 850;
}

.password-toggle-icon {
  cursor: pointer;
  color: var(--text-color-muted);
}

.auth-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 4px 0 20px;
}

.auth-submit {
  width: 100%;
}

.error-message {
  margin-bottom: 14px;
}

@media (max-width: 920px) {
  .auth-page {
    display: flex;
    min-height: 100vh;
    background:
      radial-gradient(circle at 18% 12%, rgba(83, 111, 136, 0.22), transparent 22rem),
      linear-gradient(135deg, #20262a 0%, #344e66 100%);
  }

  .auth-visual {
    display: none;
  }

  .auth-panel {
    width: 100%;
    padding: 20px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .auth-visual,
  .auth-asset,
  .radar-sweep,
  .auth-card {
    animation: none !important;
  }
}
</style>
