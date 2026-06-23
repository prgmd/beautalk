<template>
  <div class="callback">
    <DewyLoader
      text="로그인하는 중"
      subtitle="잠시만 기다려 주세요"
      :size="140"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import DewyLoader from '@/components/DewyLoader.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const profile = useProfileStore()

onMounted(async () => {
  // 백엔드가 OAuth 에러 발생 시 ?error= 를 붙여 리다이렉트한다.
  // 에러 사유를 LoginView로 그대로 전달해 안내 메시지를 띄운다.
  if (route.query.error) {
    router.push({ path: '/login', query: { error: route.query.error } })
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
    router.push({ path: '/login', query: { error: 'token_exchange_failed' } })
    return
  }

  // access 토큰은 메모리(Pinia)에만 저장
  auth.login({}, access)

  let data
  try {
    data = await profile.fetchProfile()
  } catch {
    data = null
  }

  if (data) auth.setProfileComplete()

  router.push(data ? '/chat' : '/onboarding')
})
</script>

<style scoped>
.callback {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding:
    calc(env(safe-area-inset-top) + 24px) 24px
    calc(env(safe-area-inset-bottom) + 24px);
  background: var(--canvas);
  animation: bt-rise var(--t-slow) var(--ease) both;
}
</style>
