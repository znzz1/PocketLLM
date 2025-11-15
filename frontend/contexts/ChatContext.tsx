'use client'

import { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react'
import { WebSocketClient, WebSocketMessage } from '@/lib/wsClient'

/**
 * ChatContext - Global Chat State
 *
 * Architecture Reference: HW3 Section 3.1.2 State Management
 * Architecture Reference: HW3 Section 3.2.2 WebSocket Support
 * - React Context API for chat state
 * - Manages messages and session via WebSocket
 * - Provides real-time chat operations
 */

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatContextType {
  messages: Message[]
  sessionId: string | null
  isLoading: boolean
  isConnected: boolean
  sendMessage: (content: string) => Promise<void>
  addMessage: (message: Message) => void
  clearMessages: () => void
  setSessionId: (id: string) => void
}

const ChatContext = createContext<ChatContextType | undefined>(undefined)

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const wsClientRef = useRef<WebSocketClient | null>(null)
  const currentMessageIdRef = useRef<string | null>(null)

  // Initialize WebSocket connection
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (!token) return

    // Get WebSocket URL from environment
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/chat/ws'

    const wsClient = new WebSocketClient(wsUrl, token)
    wsClientRef.current = wsClient

    // Connect to WebSocket
    wsClient.connect().then(() => {
      setIsConnected(true)
      console.log('WebSocket connected')
    }).catch((error) => {
      console.error('WebSocket connection failed:', error)
      setIsConnected(false)
    })

    // Handle incoming messages
    const unsubscribe = wsClient.onMessage((message: WebSocketMessage) => {
      if (message.type === 'start') {
        // Update session ID
        if (message.session_id && !sessionId) {
          setSessionId(message.session_id)
        }
      } else if (message.type === 'token') {
        // Append token to current message
        if (message.content && currentMessageIdRef.current) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === currentMessageIdRef.current
                ? { ...msg, content: msg.content + message.content }
                : msg
            )
          )
        }
      } else if (message.type === 'done') {
        // Message complete
        setIsLoading(false)
        currentMessageIdRef.current = null
      } else if (message.type === 'error') {
        // Handle error
        console.error('WebSocket error:', message.message)
        setMessages((prev) => {
          const lastMessage = prev[prev.length - 1]
          if (lastMessage && lastMessage.role === 'assistant' && !lastMessage.content) {
            return prev.slice(0, -1).concat({
              ...lastMessage,
              content: `Error: ${message.message || 'Unknown error'}`,
            })
          }
          return prev
        })
        setIsLoading(false)
        currentMessageIdRef.current = null
      }
    })

    // Handle connection close
    const unsubscribeClose = wsClient.onClose(() => {
      setIsConnected(false)
      console.log('WebSocket disconnected')
    })

    // Cleanup on unmount
    return () => {
      unsubscribe()
      unsubscribeClose()
      wsClient.close()
    }
  }, []) // Empty dependency array - only run once on mount

  const sendMessage = async (content: string) => {
    if (!content.trim()) return
    if (!wsClientRef.current || !wsClientRef.current.isConnected()) {
      console.error('WebSocket is not connected')
      return
    }

    // Add user message immediately
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      // Create placeholder for assistant message
      const assistantMessageId = `msg-${Date.now()}`
      currentMessageIdRef.current = assistantMessageId
      const assistantMessage: Message = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])

      // Send message via WebSocket
      wsClientRef.current.sendMessage({
        type: 'chat',
        prompt: content,
        session_id: sessionId || undefined,
        max_tokens: 512,
        temperature: 0.7,
      })
    } catch (error) {
      console.error('Send message error:', error)
      setMessages((prev) => {
        const lastMessage = prev[prev.length - 1]
        if (lastMessage && lastMessage.role === 'assistant' && !lastMessage.content) {
          return prev.slice(0, -1).concat({
            ...lastMessage,
            content: 'Sorry, I encountered an error. Please try again.',
          })
        }
        return prev
      })
      setIsLoading(false)
      currentMessageIdRef.current = null
    }
  }

  const addMessage = (message: Message) => {
    setMessages((prev) => [...prev, message])
  }

  const clearMessages = () => {
    setMessages([])
    setSessionId(null)
  }

  const value: ChatContextType = {
    messages,
    sessionId,
    isLoading,
    isConnected,
    sendMessage,
    addMessage,
    clearMessages,
    setSessionId,
  }

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

export function useChatContext() {
  const context = useContext(ChatContext)
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider')
  }
  return context
}
