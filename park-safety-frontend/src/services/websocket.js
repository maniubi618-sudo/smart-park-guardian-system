class WebSocketService {
  constructor() {
    this.socket = null
    this.callbacks = []
    this.reconnectInterval = 5000
  }

  connect() {
    const token = localStorage.getItem('token')
    if (!token) {
      console.warn('No token found, WebSocket connection skipped')
      return
    }

    try {
      this.socket = new WebSocket(`ws://localhost:8089/api/v1/safety_analysis/ws?token=${token}`)

      this.socket.onopen = () => {
        console.log('WebSocket connected')
      }

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.callbacks.forEach(callback => callback(data))
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.socket.onclose = () => {
        console.log('WebSocket disconnected')
        // 重连逻辑
        setTimeout(() => this.connect(), this.reconnectInterval)
      }

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
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