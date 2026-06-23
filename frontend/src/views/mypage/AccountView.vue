<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const showWithdrawModal = ref(false)
const withdrawing = ref(false)
const errorMsg = ref('')

// 진입 시 백엔드에서 최신 계정 정보를 불러온다(실패해도 기존 표시 유지).
onMounted(() => {
  auth.fetchAccount().catch(() => {})
})

async function logout() {
  await auth.serverLogout()
  router.push('/login')
}

function openWithdraw() {
  errorMsg.value = ''
  showWithdrawModal.value = true
}
function closeWithdraw() {
  if (withdrawing.value) return
  showWithdrawModal.value = false
}

async function doWithdraw() {
  if (withdrawing.value) return
  withdrawing.value = true
  errorMsg.value = ''
  try {
    await auth.withdraw()
    router.push('/login')
  } catch {
    errorMsg.value = '탈퇴 처리에 실패했어요. 잠시 후 다시 시도해 주세요.'
    withdrawing.value = false
  }
}

const PROVIDER_LABEL = { kakao: '카카오', google: '구글' }

function formatJoinDate() {
  const raw = auth.user?.joinedAt
  const provider = PROVIDER_LABEL[auth.user?.authProvider] || '이메일'
  if (!raw) return `${provider} 가입`
  const d = new Date(raw)
  return `${provider} 가입 · ${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일`
}

function getInitials(email) {
  return email ? email.slice(0, 2).toUpperCase() : 'ME'
}
</script>

<template>
  <div class="view">
    <header class="page-header">
      <p class="eyebrow">Account · 내 계정</p>
      <h2 class="page-title serif">계정</h2>
    </header>

    <!-- 계정 정보 카드 -->
    <div class="account-card">
      <span class="leaf" aria-hidden="true">❋</span>
      <div class="avatar">{{ getInitials(auth.user?.email) }}</div>
      <div class="account-info">
        <p class="email serif">{{ auth.user?.email || 'demo@example.com' }}</p>
        <p class="join-date">{{ formatJoinDate() }}</p>
      </div>
    </div>

    <!-- 계정 관리 -->
    <section class="section">
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
    </section>

    <!-- 위험 영역 -->
    <section class="section danger-section">
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
    </section>

    <!-- 탈퇴 확인 모달 (모바일 바텀 시트) -->
    <div v-if="showWithdrawModal" class="modal-overlay" @click="closeWithdraw">
      <div class="modal" @click.stop>
        <span class="grab-handle" aria-hidden="true"></span>
        <p class="modal-eyebrow">Danger Zone</p>
        <h3 class="serif">정말 탈퇴하시겠어요?</h3>
        <p>프로필, 추천 기록, 찜한 제품 등 모든 데이터가 영구 삭제됩니다. 이 작업은 되돌릴 수 없어요.</p>
        <p v-if="errorMsg" class="modal-error">{{ errorMsg }}</p>
        <div class="modal-actions">
          <button class="modal-cancel" :disabled="withdrawing" @click="closeWithdraw">취소</button>
          <button class="modal-confirm" :disabled="withdrawing" @click="doWithdraw">
            {{ withdrawing ? '처리 중...' : '탈퇴하기' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.view { display: flex; flex-direction: column; gap: 24px; }

/* Header */
.page-header { animation: bt-rise 0.4s var(--ease) both; }
.eyebrow {
  font-size: 11px; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase;
  color: var(--sage-ink); margin-bottom: 6px;
}
.page-title { font-size: 26px; font-weight: 500; letter-spacing: -0.4px; line-height: 1.15; }

/* Account identity card */
.account-card {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--card);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  padding: 20px 22px;
  box-shadow: var(--sh-sm);
  animation: bt-rise 0.45s var(--ease) 0.04s both;
}
.leaf {
  position: absolute;
  top: -12px; right: -8px;
  font-size: 60px;
  line-height: 1;
  color: var(--sage-soft);
  pointer-events: none;
  user-select: none;
}
.avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--sage-soft);
  border: 1px solid var(--line-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
  color: var(--sage-ink);
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}
.account-info { position: relative; z-index: 1; min-width: 0; }
.email { font-size: 17px; font-weight: 500; color: var(--ink); overflow-wrap: anywhere; }
.join-date { font-size: 12px; color: var(--ink-faint); margin-top: 3px; }

/* Sections */
.section { display: flex; flex-direction: column; gap: 10px; }
.section:nth-of-type(2) { animation: bt-rise 0.45s var(--ease) 0.1s both; }
.danger-section { animation: bt-rise 0.45s var(--ease) 0.16s both; }
.section-title {
  font-size: 10px; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase;
  color: var(--sage-ink);
}

.action-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--card);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  padding: 16px 18px;
  cursor: pointer;
  box-shadow: var(--sh-sm);
  transition: transform var(--t-fast) var(--ease), box-shadow var(--t-fast) var(--ease), background var(--t-fast) var(--ease);
}
.action-card:hover { transform: translateY(-2px); box-shadow: var(--sh-md); }
.action-card:active { transform: scale(.99); }

.action-left { display: flex; align-items: center; gap: 12px; }
.action-icon { font-size: 17px; width: 24px; text-align: center; color: var(--ink-soft); }
.action-label { font-size: 15px; font-weight: 500; color: var(--ink); }
.action-desc { font-size: 12px; color: var(--ink-faint); margin-top: 2px; }
.chevron { font-size: 20px; color: var(--ink-faint); transition: transform var(--t-fast) var(--ease); }
.action-card:hover .chevron { transform: translateX(3px); }

/* Danger zone */
.danger-title { color: var(--danger); }
.danger-card {
  border: 1px solid var(--danger-border);
  background: var(--danger-bg);
}
.danger-card .action-icon { color: var(--danger); }
.danger-card:hover { background: var(--danger-bg); box-shadow: var(--sh-md); }
.danger-label { color: var(--danger); }

/* Modal — mobile bottom sheet */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(34,28,22,0.42);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  align-items: flex-end;
  z-index: 100;
  animation: bt-rise 0.25s var(--ease) both;
}
.modal {
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
  background: var(--card);
  border-radius: 26px 26px 0 0;
  padding: 12px 26px calc(26px + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: var(--sh-lg);
  animation: sheet-up 0.34s var(--ease) both;
}
@keyframes sheet-up {
  from { opacity: 0; transform: translateY(100%); }
  to { opacity: 1; transform: translateY(0); }
}
.grab-handle {
  width: 40px; height: 4px;
  border-radius: 99px;
  background: var(--line-strong);
  margin: 0 auto 12px;
}
.modal-eyebrow {
  font-size: 10px; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase;
  color: var(--danger);
}
.modal h3 { font-size: 21px; font-weight: 500; letter-spacing: -0.3px; color: var(--ink); }
.modal p { font-size: 13px; color: var(--ink-soft); line-height: 1.6; }
.modal-error { color: var(--danger); }
.modal-confirm:disabled, .modal-cancel:disabled { opacity: 0.5; cursor: default; }
.modal-actions { display: flex; gap: 8px; margin-top: 14px; }
.modal-cancel {
  flex: 1;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 99px;
  background: var(--sheet);
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  cursor: pointer;
  box-shadow: var(--sh-sm);
  transition: transform var(--t-fast) var(--ease);
}
.modal-cancel:active:not(:disabled) { transform: scale(.98); }
.modal-confirm {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 99px;
  background: var(--danger);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: transform var(--t-fast) var(--ease), filter var(--t-fast) var(--ease);
}
.modal-confirm:active:not(:disabled) { transform: scale(.98); filter: brightness(1.05); }
</style>
