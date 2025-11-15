'use client'

import { createContext, useContext, useState, ReactNode } from 'react'

/**
 * ChatContext - Global Chat State
 *
 * Architecture Reference: HW3 Section 3.1.2 State Management
 * - React Context API for chat state
 * - Manages messages and session
 * - Provides chat operations
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

  const sendMessage = async (content: string) => {
    if (!content.trim()) return

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
      // Call Next.js API Route (BFF pattern)
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          prompt: content,
          session_id: sessionId || undefined,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const data = await response.json()

      // Add assistant response
      const assistantMessage: Message = {
        id: data.message_id,
        role: 'assistant',
        content: data.response,
        timestamp: new Date(data.timestamp),
      }

      setMessages((prev) => [...prev, assistantMessage])

      // Update session ID if new
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id)
      }
    } catch (error) {
      console.error('Send message error:', error)

      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
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
