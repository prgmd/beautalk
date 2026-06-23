<script setup>
import { useRoute, useRouter } from 'vue-router'
import GlobalSidebar from '@/components/GlobalSidebar.vue'

const route = useRoute()
const router = useRouter()

const tabs = [
  { label: '피부 프로필', path: '/mypage/profile' },
  { label: '찜한 제품', path: '/mypage/liked' },
  { label: '추천받은 제품', path: '/mypage/recommended' },
  { label: '계정', path: '/mypage/account' },
]
</script>

<template>
  <div class="screen">
    <header class="appbar">
      <span class="ab-title serif">마이페이지</span>
    </header>

    <nav class="tabstrip">
      <button
        v-for="tab in tabs"
        :key="tab.path"
        class="tab"
        :class="{ active: route.path === tab.path }"
        @click="router.push(tab.path)"
      >{{ tab.label }}</button>
    </nav>

    <main class="content">
      <RouterView />
    </main>

    <GlobalSidebar />
  </div>
</template>

<style scoped>
.screen { height: 100%; display: flex; flex-direction: column; overflow: hidden; }

.appbar {
  flex-shrink: 0;
  padding: calc(12px + env(safe-area-inset-top)) 20px 8px;
}
.ab-title { font-size: 24px; font-weight: 500; letter-spacing: -.3px; }

.tabstrip {
  flex-shrink: 0;
  display: flex; gap: 8px; overflow-x: auto;
  padding: 8px 20px 12px;
  -ms-overflow-style: none; scrollbar-width: none;
}
.tabstrip::-webkit-scrollbar { display: none; }
.tab {
  flex-shrink: 0;
  padding: 8px 16px; border-radius: 99px; font-size: 13px; font-weight: 600;
  color: var(--ink-soft); background: var(--sheet); border: 1px solid var(--line);
  transition: all var(--t-fast);
}
.tab:active { transform: scale(.97); }
.tab.active {
  background: var(--ink); color: var(--canvas); border-color: var(--ink); box-shadow: var(--sh-sm);
}

.content {
  flex: 1; min-height: 0; overflow-y: auto;
  padding: 8px 20px 24px;
}
</style>
