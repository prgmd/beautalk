import { useAuthStore } from '@/stores/auth'

const BASE_URL = 'http://localhost:8000/api/v1'

// JWT 토큰을 자동으로 첨부하는 fetch 래퍼
// path 예: '/profile' → http://localhost:8000/api/v1/profile
async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }

  if (auth) {
    const authStore = useAuthStore()
    const token = authStore.user?.access
    if (token) headers.Authorization = `Bearer ${token}`
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  // 204 No Content → 본문 없음
  if (res.status === 204) return { status: 204, data: null }

  let data = null
  try {
    data = await res.json()
  } catch {
    data = null
  }

  if (!res.ok) {
    const err = new Error(`API ${method} ${path} 실패 (${res.status})`)
    err.status = res.status
    err.data = data
    throw err
  }

  return { status: res.status, data }
}

export const api = {
  get: (path, opts) => request(path, { ...opts, method: 'GET' }),
  post: (path, body, opts) => request(path, { ...opts, method: 'POST', body }),
  patch: (path, body, opts) => request(path, { ...opts, method: 'PATCH', body }),
  del: (path, opts) => request(path, { ...opts, method: 'DELETE' }),
}
