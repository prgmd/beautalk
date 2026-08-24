<script setup>
import { useRoute, useRouter } from 'vue-router'
import GlobalSidebar from '@/components/GlobalSidebar.vue'

const route = useRoute()
const router = useRouter()

// 내 정보 = 두 섹션. '나의 화장대'를 내 정보 안으로 편입.
const SECTIONS = [
  {
    label: '나의 화장대',
    tabs: [
      { label: '찜한 제품', path: '/mypage/liked' },
      { label: '추천받은 제품', path: '/mypage/recommended' },
    ],
  },
  {
    label: '프로필',
    tabs: [
      { label: '피부 프로필', path: '/mypage/profile' },
      { label: '계정', path: '/mypage/account' },
    ],
  },
]
</script>

<template>
  <div class="screen">
    <div class="main">
      <div class="subnav">
        <header class="appbar">
          <span class="ab-title serif">내 정보</span>
        </header>
        <nav class="tabstrip">
          <template v-for="sec in SECTIONS" :key="sec.label">
            <span class="sec-label">{{ sec.label }}</span>
            <button
              v-for="tab in sec.tabs"
              :key="tab.path"
              class="tab"
              :class="{ active: route.path === tab.path }"
              :aria-current="route.path === tab.path ? 'page' : undefined"
              @click="router.push(tab.path)"
            >{{ tab.label }}</button>
          </template>
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
/* 모바일: 섹션 라벨을 탭 사이 작은 구분자로 */
.sec-label {
  display: inline-flex; align-items: center; flex-shrink: 0;
  font-size: 10px; letter-spacing: 1px; color: var(--ink-faint); font-weight: 700;
  padding: 0 2px 0 6px;
}
.sec-label:first-child { padding-left: 0; }
.tab {
  flex-shrink: 0;
  padding: 8px 16px; border-radius: 99px; font-size: 13px; font-weight: 600;
  color: var(--ink-soft); background: var(--sheet); border: 1px solid var(--line);
  transition: all var(--t-fast);
}
.tab:active { transform: scale(.97); }
.tab.active { background: var(--ink); color: var(--canvas); border-color: var(--ink); box-shadow: var(--sh-sm); }

.content { flex: 1; min-height: 0; overflow-y: auto; padding: 8px 20px 24px; }

/* ── 데스크탑(≥900px): 글로벌 사이드바 + 세로 서브 사이드바(섹션 구분) ── */
@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .main { flex-direction: row; }
  .subnav {
    width: 220px; height: 100%;
    border-right: 1px solid var(--line);
    padding: 32px 18px;
    display: flex; flex-direction: column; gap: 14px;
    overflow-y: auto;
  }
  .appbar { padding: 0 8px 4px; }
  .ab-title { font-size: 21px; }
  .tabstrip { flex-direction: column; gap: 3px; overflow: visible; padding: 0; }
  .sec-label {
    display: block; font-size: 10px; letter-spacing: 2px; text-transform: uppercase;
    color: var(--ink-faint); font-weight: 600; padding: 12px 12px 4px;
  }
  .sec-label:first-child { padding-top: 4px; }
  .tab {
    width: 100%; text-align: left; border-radius: var(--radius);
    background: transparent; border-color: transparent; color: var(--ink-soft);
  }
  .tab:hover { background: rgba(255, 255, 255, .5); color: var(--ink); }
  .tab.active { background: var(--sage-soft); color: var(--ink); border-color: transparent; box-shadow: none; }
  .content { padding: 40px 48px; }
}
</style>
