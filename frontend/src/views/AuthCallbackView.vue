<template>
  <div>로그인 처리 중...</div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const profile = useProfileStore()

onMounted(async () => {
  // 백엔드가 OAuth 에러 발생 시 ?error= 를 붙여 리다이렉트한다.
  if (route.query.error) {
    router.push('/login')
    return
  }

  // 백엔드가 세션에 저장한 JWT를 교환한다.
  // - access 토큰 → 응답 바디
  // - refresh 토큰 → HttpOnly 쿠키 (브라우저가 자동 관리)
  let access
  try {
    const res = await fetch('http://localhost:8000/api/v1/auth/exchange/', {
      method: 'GET',
      credentials: 'include',
    })
    if (!res.ok) throw new Error('exchange failed')
    const data = await res.json()
    access = data.access
  } catch {
    router.push('/login')
    return
  }

  // access 토큰은 메모리(Pinia)에만 저장
  auth.login({}, access)

  let data = null
  try {
    data = await profile.fetchProfile()
  } catch {
    data = null
  }

  if (data) auth.setProfileComplete()

  router.push(data ? '/chat' : '/onboarding')
})
</script>
