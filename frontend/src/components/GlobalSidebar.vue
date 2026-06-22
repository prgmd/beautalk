<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const chat = useChatStore()

function goChat() {
  router.push('/chat')
}

function newChat() {
  chat.clearMessages()
  router.push('/chat')
}

async function logout() {
  await auth.serverLogout()
  router.push('/login')
}

function isActive(path) {
  return route.path.startsWith(path)
}
</script>

<template>
  <aside class="sidebar">
    <div class="top">
      <div class="logo">beautalk</div>

      <nav class="nav">
        <button class="nav-item" :class="{ active: route.path === '/chat' && !route.path.startsWith('/mypage') }" @click="goChat">
          <span class="nav-icon">💬</span>
          홈 / 챗봇
        </button>
        <button class="nav-item" @click="newChat">
          <span class="nav-icon">✏️</span>
          새 대화
        </button>
        <button class="nav-item" :class="{ active: isActive('/mypage') }" @click="router.push('/mypage')">
          <span class="nav-icon">👤</span>
          마이페이지
        </button>
      </nav>
    </div>

    <div class="bottom">
      <button class="nav-item logout" @click="logout">
        <span class="nav-icon">→</span>
        로그아웃
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 208px;
  min-width: 208px;
  background: linear-gradient(180deg, #F7F1EB 0%, var(--bg) 100%);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 24px 12px;
  height: 100vh;
}

.top { display: flex; flex-direction: column; gap: 30px; }

.logo {
  font-size: 21px;
  font-weight: 800;
  letter-spacing: -0.5px;
  padding: 4px 8px;
  background: var(--gradient-brand-rich);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  width: fit-content;
}

.nav { display: flex; flex-direction: column; gap: 3px; }

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 11px;
  width: 100%;
  padding: 11px 14px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  text-align: left;
  transition: background var(--t-fast), color var(--t-fast), transform var(--t-fast) var(--ease);
}

.nav-item:hover {
  background: var(--surface-hover);
  color: var(--text-primary);
  transform: translateX(3px);
}

.nav-item.active {
  background: var(--surface);
  color: var(--text-primary);
  font-weight: 700;
  box-shadow: var(--shadow-sm);
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 5px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 18px;
  border-radius: 999px;
  background: var(--gradient-brand);
}

.nav-icon { font-size: 16px; width: 20px; transition: transform var(--t) var(--ease-back); }
.nav-item:hover .nav-icon { transform: scale(1.18); }

.logout { color: var(--text-muted); }
.logout:hover { color: var(--text-primary); }
</style>
