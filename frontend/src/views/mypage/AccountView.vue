<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const showWithdrawModal = ref(false)

function logout() {
  auth.logout()
  router.push('/login')
}

function openWithdraw() { showWithdrawModal.value = true }
function closeWithdraw() { showWithdrawModal.value = false }

function doWithdraw() {
  // TODO: API
  auth.logout()
  router.push('/login')
}

function formatJoinDate() {
  const raw = auth.user?.joinedAt || '2025-05-01'
  const [y, m, d] = raw.split('-')
  return `이메일 가입 · ${y}년 ${parseInt(m)}월 ${parseInt(d)}일`
}

function getInitials(email) {
  return email ? email.slice(0, 2).toUpperCase() : 'ME'
}
</script>

<template>
  <div class="view">
    <h2 class="page-title">계정</h2>

    <!-- 계정 정보 카드 -->
    <div class="account-card">
      <div class="avatar">{{ getInitials(auth.user?.email) }}</div>
      <div class="account-info">
        <p class="email">{{ auth.user?.email || 'demo@example.com' }}</p>
        <p class="join-date">{{ formatJoinDate() }}</p>
      </div>
    </div>

    <!-- 계정 관리 -->
    <div class="section">
      <p class="section-title">계정 관리</p>
      <div class="action-card" @click="logout">
        <div class="action-left">
          <span class="action-icon">→</span>
          <div>
            <p class="action-label">로그아웃</p>
            <p class="action-desc">이 기기에서 로그아웃합니다</p>
          </div>
        </div>
        <span class="chevron">›</span>
      </div>
    </div>

    <!-- 위험 영역 -->
    <div class="section danger-section">
      <p class="section-title danger-title">위험 영역</p>
      <div class="action-card danger-card" @click="openWithdraw">
        <div class="action-left">
          <span class="action-icon">⚠️</span>
          <div>
            <p class="action-label danger-label">회원 탈퇴</p>
            <p class="action-desc">프로필 · 추천 기록 · 찜 등 모든 데이터 삭제</p>
          </div>
        </div>
        <span class="chevron">›</span>
      </div>
    </div>

    <!-- 탈퇴 확인 모달 -->
    <div v-if="showWithdrawModal" class="modal-overlay" @click="closeWithdraw">
      <div class="modal" @click.stop>
        <h3>정말 탈퇴하시겠어요?</h3>
        <p>프로필, 추천 기록, 찜한 제품 등 모든 데이터가 영구 삭제됩니다. 이 작업은 되돌릴 수 없어요.</p>
        <div class="modal-actions">
          <button class="modal-cancel" @click="closeWithdraw">취소</button>
          <button class="modal-confirm" @click="doWithdraw">탈퇴하기</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.view { max-width: 560px; width: 100%; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }

.page-title { font-size: 20px; font-weight: 700; }

.account-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--bg);
  border-radius: 14px;
  padding: 16px 20px;
}
.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--ai-avatar);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: #3A5F80;
  flex-shrink: 0;
}
.email { font-size: 15px; font-weight: 600; }
.join-date { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.section { display: flex; flex-direction: column; gap: 8px; }
.section-title { font-size: 13px; font-weight: 500; color: var(--text-secondary); }

.action-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg);
  border-radius: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.15s;
}
.action-card:hover { background: var(--surface-hover); }

.action-left { display: flex; align-items: center; gap: 12px; }
.action-icon { font-size: 18px; width: 24px; text-align: center; }
.action-label { font-size: 14px; font-weight: 500; }
.action-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.chevron { font-size: 18px; color: var(--text-muted); }

/* Danger zone */
.danger-title { color: var(--danger); }
.danger-card {
  border: 1px solid var(--danger-border);
  background: var(--danger-bg);
}
.danger-card:hover { background: #FEE2E2; }
.danger-label { color: var(--danger); }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal {
  background: var(--surface);
  border-radius: 16px;
  padding: 28px;
  width: 340px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.modal h3 { font-size: 16px; font-weight: 700; }
.modal p { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }
.modal-actions { display: flex; gap: 8px; margin-top: 8px; }
.modal-cancel {
  flex: 1;
  padding: 11px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  font-size: 14px;
  cursor: pointer;
}
.modal-confirm {
  flex: 1;
  padding: 11px;
  border: none;
  border-radius: 8px;
  background: var(--danger);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
</style>
