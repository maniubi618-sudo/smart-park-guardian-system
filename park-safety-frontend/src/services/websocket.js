class WebSocketService {
  constructor() {
    this.socket = null
    this.callbacks = []
    this.reconnectInterval = 5000
    this.voiceEnabled = true
  }

  connect() {
    const token = localStorage.getItem('token')
    if (!token) {
      console.warn('No token found, WebSocket connection skipped')
      return
    }

    try {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://'
      this.socket = new WebSocket(`${wsProtocol}${window.location.host}/api/v1/safety_analysis/ws?token=${token}`)

      this.socket.onopen = () => {
        console.log('WebSocket connected')
      }

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.callbacks.forEach(callback => callback(data))
          
          if (this.voiceEnabled && data.alarm_type !== undefined) {
            this.speakAlarm(data)
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.socket.onclose = () => {
        console.log('WebSocket disconnected')
        setTimeout(() => this.connect(), this.reconnectInterval)
      }

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }

  speakAlarm(data) {
    const alarmTypeMap = {
      0: '未戴安全帽或未穿反光衣',
      1: '区域入侵',
      2: '火焰或烟雾'
    }
    
    const alarmDesc = alarmTypeMap[data.alarm_type] || '异常情况'
    const voiceText = `警告！检测到${alarmDesc}！请立即处理！`
    
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(voiceText)
      utterance.lang = 'zh-CN'
      utterance.rate = 0.9
      utterance.pitch = 1
      utterance.volume = 1
      speechSynthesis.speak(utterance)
    } else {
      console.warn('浏览器不支持语音合成')
    }
  }

  enableVoice(enabled) {
    this.voiceEnabled = enabled
  }

  subscribe(callback) {
    this.callbacks.push(callback)
  }

  unsubscribe(callback) {
    this.callbacks = this.callbacks.filter(cb => cb !== callback)
  }

  disconnect() {
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.callbacks = []
  }
}

export default new WebSocketService()