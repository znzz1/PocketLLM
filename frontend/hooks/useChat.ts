import { useChatContext } from '@/contexts/ChatContext'

/**
 * useChat Hook with Stop Functionality
 *
 * Architecture Reference: HW3 Class Diagram - useChat
 * - Custom React Hook for chat functionality
 * - Manages chat state and streaming connection
 * - Provides message sending and stopping operations
 *
 * Attributes:
 * - abortController: AbortController (for canceling requests)
 *
 * Methods:
 * - sendMessage(text): Promise<void>
 * - stopGenerating(): void
 * - subscribeToMessages(callback): void
 * - disconnect(): void
 */

export function useChat() {
  const {
    messages,
    sessionId,
    isLoading,
    sendMessage,
    stopGenerating,
    addMessage,
    clearMessages,
  } = useChatContext()

  return {
    messages,
    sessionId,
    isLoading,
    sendMessage: async (text: string) => {
      await sendMessage(text)
    },
    stopGenerating: () => {
      stopGenerating()
    },
    addMessage,
    clearMessages,
  }
}