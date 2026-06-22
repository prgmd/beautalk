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
  <div class="layout">
    <GlobalSidebar />

    <nav class="sub-sidebar">
      <button
        v-for="tab in tabs"
        :key="tab.path"
        class="sub-tab"
        :class="{ active: route.path === tab.path }"
        @click="router.push(tab.path)"
      >
        {{ tab.label }}
      </button>
    </nav>

    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.layout { display: flex; height: 100vh; background: var(--bg); }

.sub-sidebar {
  width: 200px;
  min-width: 200px;
  border-right: 1px solid var(--border);
  padding: 24px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sub-tab {
  position: relative;
  width: 100%;
  padding: 10px 14px;
  border: none;
  background: transparent;
  text-align: left;
  font-size: 14px;
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--t-fast) var(--ease), color var(--t-fast) var(--ease), transform var(--t-fast) var(--ease);
  overflow: hidden;
}
.sub-tab::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%) scaleY(0);
  width: 3px;
  height: 56%;
  border-radius: 0 3px 3px 0;
  background: var(--gradient-brand);
  transition: transform var(--t) var(--ease-back);
}
.sub-tab:hover { background: var(--surface-hover); color: var(--text-primary); }
.sub-tab.active {
  background: var(--brand-soft);
  color: var(--brand);
  font-weight: 700;
  box-shadow: var(--shadow-sm);
}
.sub-tab.active::before { transform: translateY(-50%) scaleY(1); }

.content {
  flex: 1;
  overflow-y: auto;
  padding: 40px 48px;
  background: var(--surface);
}
</style>
