<template>
  <div class="ai-assistant">
    <div class="assistant-header" @click="togglePanel">
      <el-icon class="ai-icon" :class="{ pulse: !isExpanded }"><ChatDotRound /></el-icon>
      <span class="ai-text">AI助手</span>
      <el-badge :value="unreadCount" :hidden="unreadCount === 0 || isExpanded" class="badge" />
    </div>

    <Transition name="assistant-panel-motion">
    <div v-show="isExpanded" class="assistant-panel">
      <div class="panel-header">
        <div class="header-title">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI智能问答助手</span>
        </div>
        <el-button size="small" @click="showHelp">使用指南</el-button>
      </div>

      <div class="chat-messages" ref="messagesContainer">
        <div v-for="(msg, index) in messages" :key="index" class="message" :class="msg.role">
          <div class="message-content">
            <div v-html="formatMessage(msg.content)" class="message-text"></div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>

        <div v-if="isLoading" class="message assistant">
          <div class="message-content">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <span>AI思考中...</span>
          </div>
        </div>
      </div>

      <div class="quick-questions">
        <el-button size="small" round @click="askQuestion('今天有多少告警？')">今日告警</el-button>
        <el-button size="small" round @click="askQuestion('哪个区域最危险？')">高风险区域</el-button>
        <el-button size="small" round @click="askQuestion('摄像头状态如何？')">设备状态</el-button>
        <el-button size="small" round @click="askQuestion('今日安全评分是多少？')">安全评分</el-button>
        <el-button size="small" round @click="askQuestion('有什么优化建议？')">优化建议</el-button>
      </div>

      <div class="input-area">
        <el-input
          v-model="userInput"
          placeholder="向AI助手提问..."
          @keyup.enter="sendMessage"
          :disabled="isLoading"
        >
          <template #append>
            <el-button @click="sendMessage" :disabled="isLoading || !userInput.trim()">
              <el-icon><Promotion /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>
    </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { ChatDotRound, Loading, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { aiApi } from '../services/api'

const isExpanded = ref(false)
const userInput = ref('')
const messages = ref([
  {
    role: 'assistant',
    content: '👋 你好！我是园区智能安防AI助手。我可以帮你查询告警统计、分析区域风险、查看设备状态等。请随时提问！',
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
])
const isLoading = ref(false)
const unreadCount = ref(0)
const messagesContainer = ref(null)

const togglePanel = () => {
  isExpanded.value = !isExpanded.value
  if (isExpanded.value) {
    unreadCount.value = 0
    nextTick(() => scrollToBottom())
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatMessage = (content) => {
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

const askQuestion = (question) => {
  userInput.value = question
  sendMessage()
}

const sendMessage = async () => {
  const question = userInput.value.trim()
  if (!question || isLoading.value) return

  messages.value.push({
    role: 'user',
    content: question,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })

  userInput.value = ''
  isLoading.value = true
  nextTick(() => scrollToBottom())

  try {
    const response = await aiApi.aiQuestion(question)
    
    if (response.code === 1 && response.data) {
      messages.value.push({
        role: 'assistant',
        content: response.data.answer || '抱歉，暂时无法回答这个问题。',
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      })
    } else {
      messages.value.push({
        role: 'assistant',
        content: '抱歉，查询失败，请稍后重试。',
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      })
    }
  } catch (error) {
    console.error('AI问答请求失败:', error)
    messages.value.push({
      role: 'assistant',
      content: '网络连接失败，请检查后端服务是否正常运行。',
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })
  } finally {
    isLoading.value = false
    nextTick(() => scrollToBottom())
  }
}

const showHelp = () => {
  askQuestion('你好，请介绍一下你能做什么？')
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.ai-assistant {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 2000;
}

.assistant-header {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #344e66 0%, #536f88 100%);
  color: #fbfaf7;
  padding: 11px 18px;
  border-radius: 999px;
  cursor: pointer;
  border: 1px solid rgba(216, 224, 231, 0.34);
  box-shadow: 0 16px 36px rgba(47, 57, 66, 0.22);
  animation: assistantFloatIn var(--motion-page) var(--motion-ease) both;
  transition: transform var(--motion-base) var(--motion-ease), box-shadow var(--motion-base) var(--motion-ease), filter var(--motion-base) var(--motion-ease);
  user-select: none;
}

@keyframes assistantFloatIn {
  from {
    opacity: 0;
    transform: translateY(18px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.assistant-header:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 42px rgba(47, 57, 66, 0.28);
  filter: saturate(1.06);
}

.ai-icon {
  font-size: 20px;
}

.ai-icon.pulse {
  animation: assistantBreath 2.8s var(--motion-ease) infinite;
}

@keyframes assistantBreath {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.72;
    transform: scale(1.12);
  }
}

.ai-text {
  font-weight: 500;
}

.badge {
  position: absolute;
  top: -5px;
  right: -5px;
}

.assistant-panel {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 400px;
  height: 600px;
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: var(--shadow-strong);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform-origin: 100% 100%;
}

.assistant-panel-motion-enter-active {
  transition: opacity var(--motion-slow) var(--motion-ease), transform var(--motion-slow) var(--motion-ease), filter var(--motion-slow) var(--motion-ease);
}

.assistant-panel-motion-leave-active {
  transition: opacity var(--motion-fast) var(--motion-exit), transform var(--motion-fast) var(--motion-exit), filter var(--motion-fast) var(--motion-exit);
}

.assistant-panel-motion-enter-from,
.assistant-panel-motion-leave-to {
  opacity: 0;
  transform: translateY(18px) scale(0.96);
  filter: blur(8px);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: linear-gradient(135deg, #20262a 0%, #344e66 100%);
  color: #fbfaf7;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f7f4ed;
}

.message {
  margin-bottom: 15px;
  display: flex;
  animation: messageBubbleIn 320ms var(--motion-ease) both;
}

@keyframes messageBubbleIn {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: var(--shadow-sm);
  transition: transform var(--motion-fast) var(--motion-ease), box-shadow var(--motion-base) var(--motion-ease);
}

.message-content:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(47, 57, 66, 0.10);
}

.message.user .message-content {
  background: var(--primary-color);
  color: #ffffff;
}

.message.assistant .message-content {
  background: white;
  color: var(--text-color);
  border: 1px solid var(--border-color);
}

.message-text {
  line-height: 1.6;
  font-size: 14px;
}

.message-time {
  font-size: 11px;
  opacity: 0.6;
  margin-top: 5px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.quick-questions {
  padding: 10px 20px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  background: white;
  border-top: 1px solid var(--border-color);
}

.input-area {
  padding: 15px 20px;
  background: white;
  border-top: 1px solid var(--border-color);
}

@media (max-width: 768px) {
  .assistant-panel {
    width: calc(100vw - 40px);
    height: 70vh;
  }
}

@media (prefers-reduced-motion: reduce) {
  .assistant-header,
  .ai-icon.pulse,
  .message,
  .loading-icon {
    animation: none !important;
  }
}
</style>
