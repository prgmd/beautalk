<script setup>
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// 모바일 하단 탭바. (파일명은 기존 import 호환을 위해 유지)
const TABS = [
  { key: 'chat', label: '상담', icon: '🌿', path: '/chat' },
  { key: 'recommended', label: '추천', icon: '✦', path: '/mypage/recommended' },
  { key: 'liked', label: '찜', icon: '💧', path: '/mypage/liked' },
  { key: 'my', label: 'MY', icon: '🪞', path: '/mypage/profile' },
]

function isActive(tab) {
  const p = route.path
  if (tab.key === 'chat') return p === '/chat'
  if (tab.key === 'recommended') return p.startsWith('/mypage/recommended')
  if (tab.key === 'liked') return p.startsWith('/mypage/liked')
  if (tab.key === 'my') return p === '/mypage/profile' || p === '/mypage/account' || p === '/mypage'
  return false
}

function go(tab) {
  if (route.path !== tab.path) router.push(tab.path)
}
</script>

<template>
  <nav class="bottomnav">
    <button
      v-for="tab in TABS"
      :key="tab.key"
      class="tab"
      :class="{ on: isActive(tab) }"
      @click="go(tab)"
    >
      <span class="ic">{{ tab.icon }}</span>
      <span class="lb">{{ tab.label }}</span>
      <span class="dot" />
    </button>
  </nav>
</template>

<style scoped>
.bottomnav {
  flex-shrink: 0;
  display: flex;
  justify-content: space-around;
  align-items: stretch;
  padding: 8px 10px calc(8px + env(safe-area-inset-bottom));
  background: var(--sheet);
  border-top: 1px solid var(--line-soft);
  box-shadow: 0 -4px 18px rgba(60,48,30,.05);
  z-index: 5;
}
.tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 4px;
  font-size: 10.5px;
  font-weight: 500;
  color: var(--ink-faint);
  transition: color var(--t-fast);
}
.tab .ic { font-size: 19px; filter: grayscale(.45); opacity: .6; transition: all var(--t) var(--ease-back); }
.tab .lb { transition: color var(--t-fast); }
.tab .dot { width: 4px; height: 4px; border-radius: 50%; background: transparent; transition: background var(--t-fast); }
.tab:hover { color: var(--ink-soft); }
.tab.on { color: var(--ink); font-weight: 700; }
.tab.on .ic { filter: none; opacity: 1; transform: translateY(-1px) scale(1.08); }
.tab.on .dot { background: var(--sage); }
</style>
