import { useAuthStore } from '@/stores/auth'

const BASE_URL = 'http://localhost:8000/api/v1'

// 동시에 여러 요청이 401을 맞아도 refresh는 한 번만 수행한다.
// (각 호출자는 같은 Promise를 공유해 결과를 함께 받는다 → 중복 갱신/오인 로그아웃 방지)
let refreshPromise = null

function tryRefresh() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${BASE_URL}/auth/token/refresh`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
        if (!res.ok) return false
        const data = await res.json()
        useAuthStore().setAccessToken(data.access)
        return true
      } catch {
        return false
      } finally {
        refreshPromise = null
      }
    })()
  }
  return refreshPromise
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }

  if (auth) {
    const token = useAuthStore().accessToken
    if (token) headers.Authorization = `Bearer ${token}`
  }

  const options = { method, headers, credentials: 'include' }
  if (body !== undefined) options.body = JSON.stringify(body)

  const res = await fetch(`${BASE_URL}${path}`, options)

  // access 토큰 만료 → refresh 시도 후 재요청 (무한 루프 방지: refresh 경로 제외)
  if (res.status === 401 && path !== '/auth/token/refresh') {
    const refreshed = await tryRefresh()
    if (refreshed) return request(path, { method, body, auth })
    useAuthStore().logout()
    window.location.href = '/login'
    return { status: 401, data: null }
  }

  // Rate Limiting 초과 → 사용자에게 안내 (백엔드 throttle: anon 20/h, user 100/h)
  if (res.status === 429) {
    window.alert('요청이 너무 잦습니다. 잠시 후 다시 시도해 주세요.')
  }

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
