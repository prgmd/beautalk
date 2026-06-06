import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('bt_user') || 'null'))

  const isLoggedIn = computed(() => !!user.value)
  const hasProfile = computed(() => !!user.value?.hasProfile)

  function login(userData) {
    user.value = userData
    localStorage.setItem('bt_user', JSON.stringify(userData))
  }

  function logout() {
    user.value = null
    localStorage.removeItem('bt_user')
  }

  function setProfileComplete() {
    if (user.value) {
      user.value = { ...user.value, hasProfile: true }
      localStorage.setItem('bt_user', JSON.stringify(user.value))
    }
  }

  return { user, isLoggedIn, hasProfile, login, logout, setProfileComplete }
})
