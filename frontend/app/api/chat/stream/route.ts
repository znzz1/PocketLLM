/**
 * Chat Stream API Route (BFF Layer)
 *
 * Proxies streaming chat requests to the FastAPI backend.
 * Returns Server-Sent Events (SSE) stream.
 */
import { NextRequest } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    // Get authorization header
    const authHeader = request.headers.get('authorization')

    if (!authHeader) {
      return new Response(
        JSON.stringify({ detail: 'Not authenticated' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      )
    }

    const body = await request.json()

    // Forward request to FastAPI backend
    const response = await fetch(`${BACKEND_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const error = await response.json()
      return new Response(
        JSON.stringify(error),
        { status: response.status, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Return the streaming response
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no', // Disable buffering for nginx/proxies
      },
    })
  } catch (error) {
    console.error('Chat stream API error:', error)
    return new Response(
      JSON.stringify({ detail: 'Internal server error' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
}
