'use client'

import { useAuth } from '@/hooks/useAuth'

export default function DebugPage() {
  const { user, token, isAuthenticated } = useAuth()

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Debug User Info</h1>

      <div className="bg-gray-100 p-4 rounded-lg mb-4">
        <h2 className="font-semibold mb-2">Authentication Status:</h2>
        <p>isAuthenticated: {isAuthenticated ? 'true' : 'false'}</p>
      </div>

      <div className="bg-gray-100 p-4 rounded-lg mb-4">
        <h2 className="font-semibold mb-2">User Object:</h2>
        <pre className="text-xs overflow-auto">
          {JSON.stringify(user, null, 2)}
        </pre>
      </div>

      <div className="bg-gray-100 p-4 rounded-lg mb-4">
        <h2 className="font-semibold mb-2">User Fields:</h2>
        <p>user?.username: {user?.username || 'undefined'}</p>
        <p>user?.is_admin: {user?.is_admin !== undefined ? String(user.is_admin) : 'undefined'}</p>
        <p>user?.is_admin type: {typeof user?.is_admin}</p>
      </div>

      <div className="bg-gray-100 p-4 rounded-lg mb-4">
        <h2 className="font-semibold mb-2">Token (first 50 chars):</h2>
        <p className="text-xs break-all">{token?.substring(0, 50) || 'No token'}</p>
      </div>

      <div className="bg-gray-100 p-4 rounded-lg">
        <h2 className="font-semibold mb-2">LocalStorage Data:</h2>
        <button
          onClick={() => {
            const storedUser = localStorage.getItem('user')
            const storedToken = localStorage.getItem('auth_token')
            alert(`User: ${storedUser}\n\nToken: ${storedToken?.substring(0, 50)}`)
          }}
          className="px-4 py-2 bg-blue-500 text-white rounded"
        >
          Show LocalStorage
        </button>
      </div>
    </div>
  )
}
