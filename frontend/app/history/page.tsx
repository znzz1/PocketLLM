'use client'

import { useEffect, useState } from 'react'
import { useAuthContext } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'

/**
 * History Page - View Chat Sessions
 *
 * Architecture Reference: HW3 Section 3.1.3 Component Design
 * - Displays list of chat sessions
 * - Allows viewing session details
 * - Allows deleting sessions
 */

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  tokens_used?: number
}

interface ChatSession {
  session_id: string
  user_id: string
  messages: ChatMessage[]
  created_at: string
  updated_at: string
}

export default function HistoryPage() {
  const { isAuthenticated, token, isLoading: authLoading } = useAuthContext()
  const router = useRouter()
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, authLoading, router])

  useEffect(() => {
    if (isAuthenticated && token) {
      fetchSessions()
    }
  }, [isAuthenticated, token])

  const fetchSessions = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch('/api/history', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch sessions')
      }

      const data = await response.json()
      setSessions(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchSessionDetails = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/history/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch session details')
      }

      const data = await response.json()
      setSelectedSession(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    }
  }

  const deleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this session?')) {
      return
    }

    try {
      const response = await fetch(`/api/history/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to delete session')
      }

      // Refresh sessions list
      await fetchSessions()
      setSelectedSession(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    }
  }

  if (authLoading || !isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Chat History
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            View and manage your conversation history
          </p>
          <button
            onClick={() => router.push('/')}
            className="mt-4 text-blue-600 dark:text-blue-400 hover:underline"
          >
            ← Back to Chat
          </button>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-400 rounded-lg">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-gray-600 dark:text-gray-400">Loading sessions...</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Sessions List */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Sessions ({sessions.length})
              </h2>

              {sessions.length === 0 ? (
                <p className="text-gray-600 dark:text-gray-400">
                  No chat sessions yet. Start a conversation to create your first session!
                </p>
              ) : (
                <div className="space-y-3">
                  {sessions.map((session) => (
                    <div
                      key={session.session_id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedSession?.session_id === session.session_id
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                      onClick={() => fetchSessionDetails(session.session_id)}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <p className="font-medium text-gray-900 dark:text-white">
                            Session {session.session_id.slice(0, 8)}...
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {session.messages.length} messages
                          </p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteSession(session.session_id)
                          }}
                          className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 text-sm"
                        >
                          Delete
                        </button>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-500">
                        Created: {new Date(session.created_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Session Details */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Session Details
              </h2>

              {!selectedSession ? (
                <p className="text-gray-600 dark:text-gray-400">
                  Select a session to view details
                </p>
              ) : (
                <div className="space-y-4">
                  <div className="border-b border-gray-200 dark:border-gray-700 pb-4">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Session ID: {selectedSession.session_id}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Created: {new Date(selectedSession.created_at).toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Updated: {new Date(selectedSession.updated_at).toLocaleString()}
                    </p>
                  </div>

                  <div className="space-y-3 max-h-[600px] overflow-y-auto">
                    {selectedSession.messages.map((message, index) => (
                      <div
                        key={index}
                        className={`p-4 rounded-lg ${
                          message.role === 'user'
                            ? 'bg-blue-100 dark:bg-blue-900/20 ml-8'
                            : 'bg-gray-100 dark:bg-gray-700 mr-8'
                        }`}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <p className="font-medium text-sm text-gray-900 dark:text-white">
                            {message.role === 'user' ? 'You' : 'Assistant'}
                          </p>
                          {message.tokens_used && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {message.tokens_used} tokens
                            </span>
                          )}
                        </div>
                        <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
                          {message.content}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                          {new Date(message.timestamp).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
