<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useLikesStore } from '@/stores/likes'
import { usePaywallStore } from '@/stores/paywall'
import ProductDetailModal from '@/components/ProductDetailModal.vue'
import PaywallModal from '@/components/PaywallModal.vue'

const auth = useAuthStore()
const likes = useLikesStore()
const paywall = usePaywallStore()

onMounted(async () => {
  // 페이지 새로고침 시 메모리의 accessToken이 사라진다.
  // localStorage에 user 정보가 남아있으면 HttpOnly 쿠키로 조용히 토큰을 복원한다.
  if (auth.user && !auth.accessToken) {
    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/token/refresh', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      })
      if (res.ok) {
        const data = await res.json()
        auth.setAccessToken(data.access)
      } else {
        auth.logout()
      }
    } catch {
      auth.logout()
    }
  }

  // 로그인 상태면 찜 목록을 미리 동기화해 앱 전역의 ♥ 표시를 맞춘다.
  if (auth.isLoggedIn) {
    likes.fetchLikes().catch(() => {})
  }
})
</script>

<template>
  <RouterView />
  <ProductDetailModal />
  <PaywallModal v-if="paywall.isOpen" @close="paywall.close()" />
</template>
