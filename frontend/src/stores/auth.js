import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

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

  function login(userData, token) {
    accessToken.value = token
    user.value = { hasProfile: userData.hasProfile ?? false }
    localStorage.setItem('bt_user', JSON.stringify(user.value))
  }

  function setAccessToken(token) {
    accessToken.value = token
  }

  function logout() {
    accessToken.value = null
    user.value = null
    localStorage.removeItem('bt_user')
  }

  function setProfileComplete() {
    if (user.value) {
      user.value = { ...user.value, hasProfile: true }
      localStorage.setItem('bt_user', JSON.stringify(user.value))
    }
  }

  return { user, accessToken, isLoggedIn, hasProfile, login, setAccessToken, logout, setProfileComplete }
})
