/**
 * WebSocket Client for Real-Time Chat
 *
 * Architecture Reference: HW3 Section 3.2.2 - WebSocket Support
 */

export interface WebSocketMessage {
  type: 'start' | 'token' | 'done' | 'error' | 'ping' | 'pong'
  content?: string
  session_id?: string
  message_id?: string
  message?: string
  timestamp?: string
}

export interface ChatMessage {
  type: 'chat'
  prompt: string
  session_id?: string
  max_tokens?: number
  temperature?: number
}

type MessageHandler = (message: WebSocketMessage) => void
type ErrorHandler = (error: Error) => void
type CloseHandler = () => void

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private token: string
  private messageHandlers: Set<MessageHandler> = new Set()
  private errorHandlers: Set<ErrorHandler> = new Set()
  private closeHandlers: Set<CloseHandler> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isManualClose = false

  constructor(url: string, token: string) {
    this.url = url
    this.token = token
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.url + '?token=' + encodeURIComponent(this.token)
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.messageHandlers.forEach(handler => handler(message))
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onerror = (event) => {
          console.error('WebSocket error:', event)
          const error = new Error('WebSocket error')
          this.errorHandlers.forEach(handler => handler(error))
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket closed')
          this.closeHandlers.forEach(handler => handler())

          if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++
            setTimeout(() => {
              this.connect().catch(err => console.error('Reconnect failed:', err))
            }, this.reconnectDelay * this.reconnectAttempts)
          }
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  sendMessage(message: ChatMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected')
    }
    this.ws.send(JSON.stringify(message))
  }

  ping(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return
    this.ws.send(JSON.stringify({ type: 'ping' }))
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler)
    return () => this.messageHandlers.delete(handler)
  }

  onError(handler: ErrorHandler): () => void {
    this.errorHandlers.add(handler)
    return () => this.errorHandlers.delete(handler)
  }

  onClose(handler: CloseHandler): () => void {
    this.closeHandlers.add(handler)
    return () => this.closeHandlers.delete(handler)
  }

  close(): void {
    this.isManualClose = true
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }
}
