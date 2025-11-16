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
    <div className="min-h-screen" style={{ backgroundColor: '#F9FAFB' }}>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold" style={{ color: '#1E293B' }}>
            Chat History
          </h1>
          <p className="mt-2" style={{ color: '#64748B' }}>
            View and manage your conversation history
          </p>
          <button
            onClick={() => router.push('/')}
            className="mt-4 hover:underline"
            style={{ color: '#4A90E2' }}
          >
            ← Back to Chat
          </button>
        </div>

        {error && (
          <div className="mb-4 p-4 rounded-lg" style={{ backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', color: '#DC2626' }}>
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div style={{ color: '#64748B' }}>Loading sessions...</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Sessions List */}
            <div className="rounded-lg shadow-md p-6" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0' }}>
              <h2 className="text-xl font-semibold mb-4" style={{ color: '#1E293B' }}>
                Sessions ({sessions.length})
              </h2>

              {sessions.length === 0 ? (
                <p style={{ color: '#64748B' }}>
                  No chat sessions yet. Start a conversation to create your first session!
                </p>
              ) : (
                <div className="space-y-3">
                  {sessions.map((session) => {
                    // Get first user message as title
                    const firstUserMessage = session.messages.find(msg => msg.role === 'user')
                    const title = firstUserMessage
                      ? firstUserMessage.content.slice(0, 60) + (firstUserMessage.content.length > 60 ? '...' : '')
                      : 'New Conversation'

                    // Format time
                    const timeAgo = new Date(session.updated_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })

                    return (
                      <div
                        key={session.session_id}
                        className="p-4 rounded-lg cursor-pointer transition-colors"
                        style={selectedSession?.session_id === session.session_id
                          ? { border: '1px solid #4A90E2', backgroundColor: '#EAF3FF' }
                          : { border: '1px solid #E2E8F0', backgroundColor: '#FFFFFF' }
                        }
                        onClick={() => fetchSessionDetails(session.session_id)}
                        onMouseEnter={(e) => {
                          if (selectedSession?.session_id !== session.session_id) {
                            e.currentTarget.style.borderColor = '#CBD5E1'
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (selectedSession?.session_id !== session.session_id) {
                            e.currentTarget.style.borderColor = '#E2E8F0'
                          }
                        }}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1 min-w-0 pr-2">
                            <p className="font-medium truncate" style={{ color: '#1E293B' }}>
                              {title}
                            </p>
                            <p className="text-sm" style={{ color: '#64748B' }}>
                              {session.messages.length} messages • {timeAgo}
                            </p>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteSession(session.session_id)
                            }}
                            className="text-sm flex-shrink-0 hover:opacity-80"
                            style={{ color: '#DC2626' }}
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Session Details */}
            <div className="rounded-lg shadow-md p-6" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0' }}>
              <h2 className="text-xl font-semibold mb-4" style={{ color: '#1E293B' }}>
                Session Details
              </h2>

              {!selectedSession ? (
                <p style={{ color: '#64748B' }}>
                  Select a session to view details
                </p>
              ) : (
                <div className="space-y-4">
                  <div className="pb-4" style={{ borderBottom: '1px solid #E2E8F0' }}>
                    <p className="text-sm" style={{ color: '#64748B' }}>
                      Session ID: {selectedSession.session_id}
                    </p>
                    <p className="text-sm" style={{ color: '#64748B' }}>
                      Created: {new Date(selectedSession.created_at).toLocaleString()}
                    </p>
                    <p className="text-sm" style={{ color: '#64748B' }}>
                      Updated: {new Date(selectedSession.updated_at).toLocaleString()}
                    </p>
                  </div>

                  <div className="space-y-3 max-h-[600px] overflow-y-auto">
                    {selectedSession.messages.map((message, index) => (
                      <div
                        key={index}
                        className={`p-4 rounded-lg ${message.role === 'user' ? 'ml-8' : 'mr-8'}`}
                        style={message.role === 'user'
                          ? { backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0' }
                          : { backgroundColor: '#F1F6FF', border: '1px solid #D4E8FF' }
                        }
                      >
                        <div className="flex justify-between items-start mb-2">
                          <p className="font-medium text-sm" style={{ color: '#1E293B' }}>
                            {message.role === 'user' ? 'You' : 'Assistant'}
                          </p>
                          {message.tokens_used && (
                            <span className="text-xs" style={{ color: '#64748B' }}>
                              {message.tokens_used} tokens
                            </span>
                          )}
                        </div>
                        <p className="whitespace-pre-wrap" style={{ color: '#1E293B' }}>
                          {message.content}
                        </p>
                        <p className="text-xs mt-2" style={{ color: '#64748B' }}>
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
