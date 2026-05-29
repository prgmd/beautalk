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

function logout() {
  auth.logout()
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
  width: 200px;
  min-width: 200px;
  background: var(--bg);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 24px 12px;
  height: 100vh;
}

.top { display: flex; flex-direction: column; gap: 32px; }

.logo {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.5px;
  padding: 0 8px;
  color: var(--text-primary);
}

.nav { display: flex; flex-direction: column; gap: 2px; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  text-align: left;
  transition: background 0.15s, color 0.15s;
}

.nav-item:hover {
  background: var(--surface-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--sidebar-active);
  color: var(--text-primary);
  font-weight: 500;
}

.nav-icon { font-size: 16px; width: 20px; }

.logout { color: var(--text-muted); }
.logout:hover { color: var(--text-primary); }
</style>
