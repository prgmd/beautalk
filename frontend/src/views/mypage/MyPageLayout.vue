<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GlobalSidebar from '@/components/GlobalSidebar.vue'

const route = useRoute()
const router = useRouter()

// 마이(설정) 영역 서브탭 — 프로필/계정만.
// 찜·추천은 글로벌 내비(상담/추천/찜/MY)에 있으므로 여기서 중복으로 넣지 않는다.
const tabs = [
  { label: '피부 프로필', path: '/mypage/profile' },
  { label: '계정', path: '/mypage/account' },
]

// 프로필/계정에서만 서브탭(섹션 내비)을 보여준다.
// 찜/추천은 글로벌 내비로 진입하는 독립 화면이라 서브탭 없이 콘텐츠만 보인다.
const isSettings = computed(
  () => route.path === '/mypage/profile' || route.path === '/mypage/account' || route.path === '/mypage',
)
</script>

<template>
  <div class="screen">
    <div class="main">
      <div v-if="isSettings" class="subnav">
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
      </div>

      <main class="content">
        <RouterView />
      </main>
    </div>

    <GlobalSidebar />
  </div>
</template>

<style scoped>
.screen { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.main { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.subnav { flex-shrink: 0; }

.appbar { padding: calc(12px + env(safe-area-inset-top)) 20px 8px; }
.ab-title { font-size: 24px; font-weight: 500; letter-spacing: -.3px; }

.tabstrip {
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
.tab.active { background: var(--ink); color: var(--canvas); border-color: var(--ink); box-shadow: var(--sh-sm); }

.content { flex: 1; min-height: 0; overflow-y: auto; padding: 8px 20px 24px; }

/* ── 데스크탑(≥900px): 글로벌 사이드바 + (설정일 때) 세로 서브 사이드바 ── */
@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .main { flex-direction: row; }
  .subnav {
    width: 210px; height: 100%;
    border-right: 1px solid var(--line);
    padding: 32px 18px;
    display: flex; flex-direction: column; gap: 18px;
  }
  .appbar { padding: 0 8px; }
  .ab-title { font-size: 21px; }
  .tabstrip { flex-direction: column; gap: 4px; overflow: visible; padding: 0; }
  .tab {
    width: 100%; text-align: left; border-radius: var(--radius);
    background: transparent; border-color: transparent; color: var(--ink-soft);
  }
  .tab:hover { background: rgba(255,255,255,.5); color: var(--ink); }
  .tab.active { background: var(--sage-soft); color: var(--ink); border-color: transparent; box-shadow: none; }
  .content { padding: 40px 48px; }
}
</style>
