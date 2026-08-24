import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/services/api'
import { API_BASE } from '@/services/config'

export const useAuthStore = defineStore('auth', () => {
  // 로그인 상태(hasProfile)만 localStorage에 유지 — 토큰은 저장하지 않는다.
  // access 토큰은 메모리(이 ref)에만 보관. XSS로 localStorage를 뒤져도 토큰을 얻을 수 없다.
  // refresh 토큰은 백엔드가 HttpOnly 쿠키로 관리하므로 프론트는 건드리지 않는다.
  const user = ref(JSON.parse(localStorage.getItem('bt_user') || 'null'))
  const accessToken = ref(null)

  // localStorage에 user 정보가 있으면 로그인 상태로 판단한다.
  // accessToken은 메모리에만 있으므로 페이지 새로고침 시 null이 되지만,
  // App.vue에서 startup refresh로 복원된다.
  const isLoggedIn = computed(() => !!user.value)
  const hasProfile = computed(() => !!user.value?.hasProfile)
  // 프리미엄 여부(목업 결제). 실제 결제 연동 전까지 로컬 상태로만 관리한다.
  const isPremium = computed(() => !!user.value?.isPremium)

  // 결제 성공을 가정하고 프리미엄으로 전환/해지한다(목업).
  function setPremium(value = true) {
    if (!user.value) return
    user.value = { ...user.value, isPremium: value }
    localStorage.setItem('bt_user', JSON.stringify(user.value))
  }

  function login(userData, token) {
    accessToken.value = token
    // 기존 프리미엄 상태(목업)는 재로그인 시에도 유지한다.
    user.value = { hasProfile: userData.hasProfile ?? false, isPremium: !!user.value?.isPremium }
    localStorage.setItem('bt_user', JSON.stringify(user.value))
  }

  function setAccessToken(token) {
    accessToken.value = token
  }

  // 로컬 상태만 정리 (api.js의 refresh 실패 등 세션이 이미 죽은 경우에 사용)
  function logout() {
    accessToken.value = null
    user.value = null
    localStorage.removeItem('bt_user')
  }

  // 사용자가 직접 로그아웃: 백엔드에 알려 refresh 토큰 블랙리스트 + HttpOnly 쿠키 삭제 후 로컬 정리
  async function serverLogout() {
    try {
      await fetch(`${API_BASE}/auth/logout/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...(accessToken.value ? { Authorization: `Bearer ${accessToken.value}` } : {}),
        },
      })
    } catch {
      // 네트워크 오류여도 클라이언트 상태는 정리한다
    }
    logout()
  }

  function setProfileComplete() {
    if (user.value) {
      user.value = { ...user.value, hasProfile: true }
      localStorage.setItem('bt_user', JSON.stringify(user.value))
    }
  }

  // GET /account/ — 계정 정보(이메일·가입경로·가입일)를 받아 user에 병합한다.
  async function fetchAccount() {
    const { data } = await api.get('/account/')
    if (data) {
      user.value = {
        ...user.value,
        email: data.email,
        authProvider: data.auth_provider,
        nickname: data.nickname || '',
        joinedAt: data.created_at,
      }
      localStorage.setItem('bt_user', JSON.stringify(user.value))
    }
    return data
  }

  // PATCH /account/ — 닉네임 수정. 성공 시 로컬 user에 반영.
  async function saveNickname(nickname) {
    const { data } = await api.patch('/account/', { nickname })
    if (data) {
      user.value = { ...user.value, nickname: data.nickname || '' }
      localStorage.setItem('bt_user', JSON.stringify(user.value))
    }
    return data
  }

  // DELETE /account/ — 회원 탈퇴. 서버가 데이터 연쇄 삭제 + 토큰 무효화 후 로컬 상태 정리.
  async function withdraw() {
    await api.del('/account/')
    logout()
  }

  return {
    user, accessToken, isLoggedIn, hasProfile, isPremium,
    login, setPremium, setAccessToken, logout, serverLogout, setProfileComplete,
    fetchAccount, saveNickname, withdraw,
  }
})
