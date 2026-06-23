<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

async function logout() {
  await auth.serverLogout()
  router.push('/login')
}

// 반응형 내비: 모바일=하단 탭바 / 데스크탑=왼쪽 사이드바. (파일명은 기존 import 호환을 위해 유지)
const TABS = [
  { key: 'chat', label: '상담', icon: '🌿', path: '/chat' },
  { key: 'community', label: '커뮤니티', icon: '💬', path: '/community' },
  { key: 'catalog', label: '둘러보기', icon: '🔎', path: '/catalog' },
  { key: 'vanity', label: '나의 화장대', icon: '💄', path: '/mypage/liked' },
  { key: 'info', label: '내 정보', icon: '👤', path: '/mypage/profile' },
]

function isActive(tab) {
  const p = route.path
  if (tab.key === 'chat') return p === '/chat'
  if (tab.key === 'community') return p.startsWith('/community')
  if (tab.key === 'catalog') return p.startsWith('/catalog')
  // 나의 화장대 = 찜한 제품 + 추천받은 제품
  if (tab.key === 'vanity') return p.startsWith('/mypage/liked') || p.startsWith('/mypage/recommended')
  // 내 정보 = 피부 프로필 + 계정
  if (tab.key === 'info') return p === '/mypage/profile' || p === '/mypage/account' || p === '/mypage'
  return false
}

function go(tab) {
  if (route.path !== tab.path) router.push(tab.path)
}
</script>

<template>
  <nav class="appnav">
    <div class="brand serif">beau<span class="it">talk</span></div>
    <div class="tabs">
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
    </div>
    <div class="navfoot">
      <svg class="sprig" width="64" height="96" viewBox="0 0 80 120" fill="none" aria-hidden="true">
        <g stroke="#7E8B6D" stroke-width="1.1">
          <path d="M40 118 C40 88 36 64 46 26" />
          <ellipse cx="31" cy="92" rx="5.5" ry="14" transform="rotate(38 31 92)" />
          <ellipse cx="52" cy="70" rx="5.5" ry="14" transform="rotate(-38 52 70)" />
          <ellipse cx="33" cy="52" rx="5" ry="12" transform="rotate(34 33 52)" />
          <ellipse cx="49" cy="36" rx="5" ry="11" transform="rotate(-34 49 36)" />
        </g>
      </svg>
      <button class="logout" @click="logout"><span class="lg-ic">→</span> 로그아웃</button>
    </div>
  </nav>
</template>


<style scoped>
/* ── 모바일 기본: 하단 탭바 ── */
.appnav {
  flex-shrink: 0;
  background: var(--sheet);
  border-top: 1px solid var(--line-soft);
  box-shadow: 0 -4px 18px rgba(60,48,30,.05);
  z-index: 5;
}
.appnav .brand { display: none; }
.navfoot { display: none; }
.tabs {
  display: flex;
  justify-content: space-around;
  align-items: stretch;
  padding: 8px 10px calc(8px + env(safe-area-inset-bottom));
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
.tab .dot { width: 4px; height: 4px; border-radius: 50%; background: transparent; transition: background var(--t-fast); }
.tab:hover { color: var(--ink-soft); }
.tab.on { color: var(--ink); font-weight: 700; }
.tab.on .ic { filter: none; opacity: 1; transform: translateY(-1px) scale(1.08); }
.tab.on .dot { background: var(--sage); }

/* ── 데스크탑(≥900px): 왼쪽 사이드바 ── */
@media (min-width: 900px) {
  .appnav {
    order: -1;
    width: 240px;
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 28px;
    padding: 32px 18px;
    background: var(--sheet);
    border-top: none;
    border-right: 1px solid var(--line);
    box-shadow: 8px 0 30px rgba(50, 40, 24, .07);
  }
  .navfoot { display: flex; flex-direction: column; align-items: center; gap: 14px; margin-top: auto; }
  .sprig { opacity: .55; }
  .logout {
    width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px;
    padding: 11px 14px; border-radius: var(--radius); font-size: 13.5px; font-weight: 600;
    color: var(--ink-soft); background: var(--card); border: 1px solid var(--line); box-shadow: var(--sh-sm);
    transition: all var(--t-fast);
  }
  .logout:hover { color: var(--danger); border-color: var(--danger-border); background: var(--danger-bg); }
  .logout .lg-ic { font-size: 15px; }
  .appnav .brand {
    display: block;
    font-size: 25px;
    font-weight: 500;
    letter-spacing: -.3px;
    padding: 4px 12px;
  }
  .appnav .brand .it { font-style: italic; color: var(--sage); }
  .tabs {
    flex-direction: column;
    gap: 4px;
    padding: 0;
  }
  .tab {
    flex: initial;
    flex-direction: row;
    justify-content: flex-start;
    gap: 12px;
    padding: 12px 14px;
    border-radius: var(--radius);
    font-size: 14px;
    color: var(--ink-soft);
  }
  .tab .ic { font-size: 18px; filter: none; opacity: .85; }
  .tab .lb { line-height: 1; }
  .tab .dot { display: none; }
  .tab:hover { background: rgba(255,255,255,.5); color: var(--ink); }
  .tab.on { background: var(--sage-soft); color: var(--ink); }
  .tab.on .ic { transform: none; opacity: 1; }
}
</style>
