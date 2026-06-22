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
.view { max-width: 560px; width: 100%; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }

.page-title { font-size: 20px; font-weight: 800; letter-spacing: -0.4px; }

.account-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 18px 22px;
  box-shadow: var(--shadow-sm);
  animation: bt-rise 0.5s var(--ease) both;
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
.email { font-size: 15px; font-weight: 700; }
.join-date { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.section { display: flex; flex-direction: column; gap: 8px; }
.section:nth-of-type(2) { animation: bt-rise 0.5s var(--ease) 0.06s both; }
.danger-section { animation: bt-rise 0.5s var(--ease) 0.12s both; }
.section-title { font-size: 13px; font-weight: 600; color: var(--text-secondary); }

.action-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--surface);
  border-radius: var(--radius);
  padding: 15px 18px;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: transform var(--t-fast) var(--ease), box-shadow var(--t-fast) var(--ease), background var(--t-fast) var(--ease);
}
.action-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }

.action-left { display: flex; align-items: center; gap: 12px; }
.action-icon { font-size: 18px; width: 24px; text-align: center; }
.action-label { font-size: 14px; font-weight: 600; }
.action-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.chevron { font-size: 18px; color: var(--text-muted); transition: transform var(--t-fast) var(--ease); }
.action-card:hover .chevron { transform: translateX(3px); }

/* Danger zone */
.danger-title { color: var(--danger); }
.danger-card {
  border: 1px solid var(--danger-border);
  background: var(--danger-bg);
}
.danger-card:hover { background: #FEE2E2; box-shadow: var(--shadow-md); }
.danger-label { color: var(--danger); }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(40,28,22,0.42);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  animation: bt-rise 0.25s var(--ease) both;
}
.modal {
  background: var(--surface);
  border-radius: var(--radius-xl);
  padding: 28px;
  width: 340px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: var(--shadow-lg);
  animation: bt-pop 0.3s var(--ease-back) both;
}
.modal h3 { font-size: 16px; font-weight: 800; letter-spacing: -0.3px; }
.modal p { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }
.modal-error { color: var(--danger); }
.modal-confirm:disabled, .modal-cancel:disabled { opacity: 0.5; cursor: default; }
.modal-actions { display: flex; gap: 8px; margin-top: 8px; }
.modal-cancel {
  flex: 1;
  padding: 11px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: transform var(--t-fast) var(--ease), box-shadow var(--t-fast) var(--ease);
}
.modal-cancel:hover:not(:disabled) { transform: translateY(-1px); box-shadow: var(--shadow-md); }
.modal-confirm {
  flex: 1;
  padding: 11px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--danger);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: transform var(--t-fast) var(--ease), box-shadow var(--t-fast) var(--ease), filter var(--t-fast) var(--ease);
}
.modal-confirm:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 10px 30px rgba(220,38,38,0.28); filter: brightness(1.05); }
</style>
