<template>
  <div>로그인 처리 중...</div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()   // 현재 URL 정보 접근용 (쿼리스트링 포함)
const auth = useAuthStore()

onMounted(async () => {
  // 카카오 콜백 URL: /auth/callback?access=eyJ...&refresh=eyJ...
  // route.query로 쿼리스트링 파라미터를 객체로 접근 가능
  const access = route.query.access
  const refresh = route.query.refresh

  // 토큰이 없으면 비정상 접근 → 로그인 페이지로 튕겨냄
  if (!access || !refresh) {
    router.push('/login')
    return
  }

  // 프로필 API 호출로 온보딩 완료 여부 확인
  // Authorization 헤더에 방금 받은 access 토큰 첨부
  const res = await fetch('http://localhost:8000/api/v1/profile', {
    headers: { Authorization: `Bearer ${access}` }
  })
  const data = res.status === 204 ? null : await res.json()
  // 프로필 없으면 Django가 204 반환 → data = null → !!null = false
  // 프로필 있으면 객체 반환 → !!{} = true

  // Pinia store에 저장 → localStorage에도 자동 반영 (auth.js 참고)
  auth.login({ access, refresh, hasProfile: !!data })

  // 프로필 존재 여부로 이동 경로 분기
  router.push(data ? '/chat' : '/onboarding')
})
</script>
