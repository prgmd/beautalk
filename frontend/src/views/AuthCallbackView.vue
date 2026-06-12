<template>
  <div>로그인 처리 중...</div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'

const router = useRouter()
const route = useRoute()   // 현재 URL 정보 접근용 (쿼리스트링 포함)
const auth = useAuthStore()
const profile = useProfileStore()

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

  // 먼저 토큰을 store에 저장해야 이후 API 호출에 자동 첨부됨 (api.js 참고)
  auth.login({ access, refresh, hasProfile: false })

  // 프로필 조회로 온보딩 완료 여부 확인 (없으면 204 → null)
  // 동시에 profile store에 채워둬서 마이페이지에서 재호출 안 하도록 함
  let data = null
  try {
    data = await profile.fetchProfile()
  } catch {
    data = null
  }

  if (data) auth.setProfileComplete()

  // 프로필 존재 여부로 이동 경로 분기
  router.push(data ? '/chat' : '/onboarding')
})
</script>
