<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useAvatarStore } from '@/stores/avatar'
import { avatarSrc } from '@/utils/avatars'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const ui = useUiStore()
const avatar = useAvatarStore()

// 상단 메뉴(이모지 없음). '내 정보'는 하단 프로필로 따로 둔다.
const MENU = [
  { key: 'chat', label: '상담', path: '/chat' },
  { key: 'community', label: '커뮤니티', path: '/community' },
  { key: 'catalog', label: '둘러보기', path: '/catalog' },
]

function isActive(key) {
  const p = route.path
  if (key === 'chat') return p === '/chat'
  if (key === 'community') return p.startsWith('/community')
  if (key === 'catalog') return p.startsWith('/catalog')
  return false
}
// 내 정보 = 마이페이지 전체(나의 화장대 + 프로필 + 계정)
const infoActive = computed(() => route.path.startsWith('/mypage'))

function go(path) {
  if (route.path !== path) router.push(path)
}
function goInfo() {
  go('/mypage/profile')
}

async function logout() {
  await auth.serverLogout()
  router.push('/login')
}

const displayName = computed(() => auth.user?.nickname || (auth.user?.email ? auth.user.email.split('@')[0] : '게스트'))
const avatarChar = computed(() => displayName.value.charAt(0).toUpperCase() || '?')

onMounted(() => {
  // 하단 프로필에 표시할 이메일이 아직 없으면 한 번 가져온다.
  if (auth.isLoggedIn && !auth.user?.email) auth.fetchAccount().catch(() => {})
})
</script>

<template>
  <nav class="appnav" :class="{ collapsed: ui.sidebarCollapsed }">
    <!-- 모바일: 하단 탭바 -->
    <div class="mtabs">
      <button v-for="t in MENU" :key="t.key" class="mtab" :class="{ on: isActive(t.key) }" @click="go(t.path)">
        <span class="mlb">{{ t.label }}</span>
      </button>
      <button class="mtab" :class="{ on: infoActive }" @click="goInfo">
        <span class="mlb">내 정보</span>
      </button>
    </div>

    <!-- 데스크탑: 햄버거 사이드바 -->
    <div class="dnav">
      <div class="nav-head">
        <button class="burger" :aria-label="ui.sidebarCollapsed ? '메뉴 펼치기' : '메뉴 접기'" @click="ui.toggleSidebar()">
          <span /><span /><span />
        </button>
        <span class="brand serif">beau<span class="it">talk</span></span>
      </div>

      <div class="nav-body">
        <span class="sec-label">메뉴</span>
        <button
          v-for="t in MENU" :key="t.key"
          class="item" :class="{ on: isActive(t.key) }"
          @click="go(t.path)"
        >{{ t.label }}</button>
      </div>

      <div class="nav-foot">
        <span class="sec-label foot-label">내 정보</span>
        <button class="profile" :class="{ on: infoActive }" @click="goInfo">
          <span class="avatar">
            <img v-if="avatar.selected" :src="avatarSrc(avatar.selected)" alt="" />
            <template v-else>{{ avatarChar }}</template>
          </span>
          <span class="p-meta">
            <span class="p-name">{{ displayName }}</span>
            <span class="p-sub">찜·추천·프로필·계정</span>
          </span>
        </button>
        <button class="logout" @click="logout">로그아웃</button>
      </div>
    </div>
  </nav>
</template>

<style scoped>
/* ── 모바일 기본: 하단 탭바(텍스트, 이모지 없음) ── */
.appnav {
  flex-shrink: 0;
  background: var(--sheet);
  border-top: 1px solid var(--line-soft);
  box-shadow: 0 -4px 18px rgba(60, 48, 30, .05);
  z-index: 5;
}
.dnav { display: none; }
.mtabs {
  display: flex;
  justify-content: space-around;
  padding: 9px 8px calc(9px + env(safe-area-inset-bottom));
}
.mtab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 6px 4px 4px;
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-faint);
  transition: color var(--t-fast);
}
.mtab .mlb { line-height: 1; }
.mtab::after {
  content: '';
  width: 4px; height: 4px; border-radius: 50%;
  background: transparent; transition: background var(--t-fast);
}
.mtab.on { color: var(--ink); font-weight: 700; }
.mtab.on::after { background: var(--sage); }

/* ── 데스크탑(≥900px): 햄버거 사이드바 ── */
@media (min-width: 900px) {
  .mtabs { display: none; }
  .appnav {
    order: -1;
    height: 100%;
    flex-shrink: 0;
    background: transparent;
    border-top: none;
    box-shadow: none;
  }
  .dnav {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 244px;
    padding: 26px 14px;
    background: var(--sheet);
    border-right: 1px solid var(--line);
    box-shadow: 8px 0 30px rgba(50, 40, 24, .07);
    transition: width var(--t) var(--ease), padding var(--t) var(--ease);
    overflow: hidden;
  }
  .appnav.collapsed .dnav { width: 66px; padding: 26px 12px; }

  /* 헤더: 햄버거 + 브랜드 */
  .nav-head { display: flex; align-items: center; gap: 12px; padding: 0 8px; margin-bottom: 22px; }
  .burger {
    width: 36px; height: 36px; flex-shrink: 0;
    display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 4px;
    border-radius: 10px; transition: background var(--t-fast);
  }
  .burger:hover { background: rgba(255, 255, 255, .55); }
  .burger span { display: block; width: 18px; height: 2px; border-radius: 2px; background: var(--ink-soft); }
  .brand { font-size: 23px; font-weight: 500; letter-spacing: -.3px; white-space: nowrap; color: var(--ink); }
  .brand .it { font-style: italic; color: var(--sage); }
  .appnav.collapsed .brand { display: none; }

  /* 메뉴 섹션 */
  .nav-body { display: flex; flex-direction: column; gap: 4px; }
  .sec-label {
    font-size: 10px; letter-spacing: 2px; text-transform: uppercase;
    color: var(--ink-faint); font-weight: 600; padding: 6px 14px 6px;
  }
  .item {
    display: flex; align-items: center;
    padding: 12px 14px; border-radius: var(--radius);
    font-size: 14px; font-weight: 500; color: var(--ink-soft);
    white-space: nowrap; overflow: hidden; text-align: left;
    transition: background var(--t-fast), color var(--t-fast);
  }
  .item:hover { background: rgba(255, 255, 255, .5); color: var(--ink); }
  .item.on { background: var(--sage-soft); color: var(--ink); font-weight: 600; }
  /* 접으면 메뉴 항목은 숨기고 햄버거로 펼친다 */
  .appnav.collapsed .nav-body { display: none; }

  /* 하단: 내 정보(간략 프로필) + 로그아웃 */
  .nav-foot { margin-top: auto; display: flex; flex-direction: column; gap: 8px; }
  .foot-label { padding-top: 0; }
  .appnav.collapsed .foot-label { display: none; }
  .profile {
    display: flex; align-items: center; gap: 11px;
    padding: 9px 10px; border-radius: var(--radius);
    border: 1px solid var(--line); background: var(--card); box-shadow: var(--sh-sm);
    transition: box-shadow var(--t-fast), border-color var(--t-fast), background var(--t-fast);
  }
  .profile:hover { box-shadow: var(--sh-md); }
  .profile.on { border-color: transparent; background: var(--sage-soft); }
  .avatar {
    width: 36px; height: 36px; flex-shrink: 0; border-radius: 50%; overflow: hidden;
    background: var(--sage); color: #fff; font-weight: 700; font-size: 15px;
    display: flex; align-items: center; justify-content: center;
  }
  .avatar img { width: 100%; height: 100%; object-fit: cover; }
  .p-meta { display: flex; flex-direction: column; gap: 2px; min-width: 0; text-align: left; }
  .p-name { font-size: 13.5px; font-weight: 600; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .p-sub { font-size: 10.5px; color: var(--ink-faint); white-space: nowrap; }
  .appnav.collapsed .p-meta { display: none; }
  .appnav.collapsed .profile { justify-content: center; padding: 8px; }

  .logout {
    padding: 10px; border-radius: var(--radius); font-size: 12.5px; font-weight: 600;
    color: var(--ink-soft); background: var(--card); border: 1px solid var(--line); box-shadow: var(--sh-sm);
    transition: color var(--t-fast), border-color var(--t-fast), background var(--t-fast);
  }
  .logout:hover { color: var(--danger); border-color: var(--danger-border); background: var(--danger-bg); }
  .appnav.collapsed .logout { display: none; }
}
</style>
