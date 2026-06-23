<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import TermsModal from '@/components/TermsModal.vue'

const route = useRoute()
const activeModal = ref(null) // null | 'terms' | 'privacy'

// 백엔드 OAuth 콜백이 실패하면 /login?error=<사유> 로 리다이렉트한다.
// (backend/accounts/views.py 의 KakaoCallbackView/GoogleCallbackView 참고)
const ERROR_MESSAGES = {
  csrf_detected: '보안 인증에 실패했습니다. 다시 시도해 주세요.',
  email_duplicated: '이미 다른 소셜 계정으로 가입된 이메일입니다. 기존에 사용하던 플랫폼으로 로그인해 주세요.',
  oauth_failed: '소셜 로그인이 취소되었거나 실패했습니다. 다시 시도해 주세요.',
  missing_code: '로그인 정보가 올바르지 않습니다. 다시 시도해 주세요.',
  token_exchange_failed: '로그인 처리 중 오류가 발생했습니다. 다시 시도해 주세요.',
  userinfo_failed: '사용자 정보를 가져오지 못했습니다. 다시 시도해 주세요.',
}

const errorMessage = computed(() => {
  const code = route.query.error
  if (!code) return ''
  return ERROR_MESSAGES[code] || '로그인 중 오류가 발생했습니다. 다시 시도해 주세요.'
})

function handleOAuth(provider) {
  // 백엔드 로그인 시작 endpoint로 이동
  // 백엔드가 카카오/구글 인증 URL 조립 후 해당 로그인 페이지로 리다이렉트
  // Vue Router 아닌 window.location.href 사용 — 외부 사이트로 완전히 이동해야 하기 때문
  const urls = {
    kakao: 'http://localhost:8000/api/v1/auth/kakao/login/',
    google: 'http://localhost:8000/api/v1/auth/google/login/',
  }
  window.location.href = urls[provider]
}
</script>

<template>
  <div class="page">
    <!-- 식물 라인 장식 -->
    <svg class="sprig sprig-top" viewBox="0 0 80 120" fill="none" aria-hidden="true">
      <path d="M40 118 C40 80 40 40 40 6" stroke="var(--sage)" stroke-width="1.2" stroke-linecap="round"/>
      <path d="M40 30 C24 24 16 30 12 18" stroke="var(--sage)" stroke-width="1.2" stroke-linecap="round"/>
      <path d="M40 52 C56 46 64 52 68 40" stroke="var(--sage)" stroke-width="1.2" stroke-linecap="round"/>
      <path d="M40 74 C24 68 16 74 12 62" stroke="var(--sage)" stroke-width="1.2" stroke-linecap="round"/>
    </svg>
    <svg class="sprig sprig-bottom" viewBox="0 0 80 120" fill="none" aria-hidden="true">
      <path d="M40 2 C40 40 40 80 40 114" stroke="var(--rose)" stroke-width="1.2" stroke-linecap="round"/>
      <path d="M40 44 C56 38 64 44 68 32" stroke="var(--rose)" stroke-width="1.2" stroke-linecap="round"/>
      <path d="M40 70 C24 64 16 70 12 58" stroke="var(--rose)" stroke-width="1.2" stroke-linecap="round"/>
    </svg>

    <div class="card">
      <header class="masthead">
        <p class="eyebrow">Botanical Beauty Lab</p>
        <div class="logo serif">beaut<em>alk</em></div>
      </header>

      <div class="headline-block">
        <h1 class="title serif">내 피부를 위한<br /><em>섬세한</em> 시작</h1>
        <p class="subtitle">챗봇이 내 피부에 맞는 화장품을 다정하게 추천해 드려요.</p>
      </div>

      <p v-if="errorMessage" class="error-banner" role="alert">{{ errorMessage }}</p>

      <div class="oauth">
        <button class="btn-oauth kakao" @click="handleOAuth('kakao')">
          <img src="@/assets/kakao.svg" alt="" class="oauth-icon" />
          카카오톡으로 시작
        </button>
        <button class="btn-oauth google" @click="handleOAuth('google')">
          <img src="@/assets/google.svg" alt="" class="oauth-icon" />
          구글로 시작
        </button>
      </div>

      <p class="terms-notice">
        시작하면
        <a href="#" @click.prevent="activeModal = 'terms'">이용약관</a> 및
        <a href="#" @click.prevent="activeModal = 'privacy'">개인정보처리방침</a>에
        동의하는 것으로 간주됩니다.
      </p>
    </div>

    <TermsModal v-if="activeModal" :type="activeModal" @close="activeModal = null" />
  </div>
</template>

<style scoped>
.page {
  position: relative;
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding:
    calc(env(safe-area-inset-top) + 32px) 24px
    calc(env(safe-area-inset-bottom) + 32px);
  overflow: hidden;
}

/* 식물 라인 장식 — 모서리에 은은하게 */
.sprig {
  position: absolute;
  width: 56px;
  height: 84px;
  opacity: 0.5;
  pointer-events: none;
}
.sprig-top { top: calc(env(safe-area-inset-top) + 8px); left: 14px; transform: rotate(-12deg); }
.sprig-bottom { bottom: calc(env(safe-area-inset-bottom) + 8px); right: 14px; transform: rotate(8deg); }

.card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: bt-rise var(--t-slow) var(--ease) both;
}

.masthead { text-align: center; }

.eyebrow {
  font-size: 10px;
  letter-spacing: 4px;
  text-transform: uppercase;
  color: var(--sage);
  font-weight: 600;
  margin-bottom: 10px;
}

.logo {
  font-size: 34px;
  font-weight: 500;
  letter-spacing: -0.4px;
  color: var(--ink);
}
.logo em { font-style: italic; color: var(--sage-ink); }

.headline-block { text-align: center; }

.title {
  font-size: 26px;
  font-weight: 400;
  line-height: 1.32;
  letter-spacing: -0.3px;
  color: var(--ink);
}
.title em { font-style: italic; color: var(--rose-ink); }

.subtitle {
  margin-top: 12px;
  font-size: 13.5px;
  color: var(--ink-soft);
  line-height: 1.7;
}

.error-banner {
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
  color: var(--danger);
  font-size: 13px;
  line-height: 1.5;
  text-align: center;
  animation: bt-pop var(--t) var(--ease-back) both;
}

.oauth { display: flex; flex-direction: column; gap: 11px; margin-top: 4px; }

.btn-oauth {
  width: 100%;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 99px;
  background: var(--card);
  font-size: 14.5px;
  font-weight: 600;
  color: var(--ink);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: var(--sh-sm);
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease), background var(--t-fast);
}
.btn-oauth:hover { transform: translateY(-2px); box-shadow: var(--sh-md); }
.btn-oauth:active { transform: scale(0.98); box-shadow: var(--sh-sm); }
.btn-oauth.kakao { background: #FEE500; border-color: #FEE500; color: #191600; }
.btn-oauth.kakao:hover { box-shadow: 0 10px 24px rgba(254, 229, 0, 0.35); }
.oauth-icon { width: 20px; height: 20px; }

.terms-notice {
  margin-top: 10px;
  text-align: center;
  font-size: 12px;
  color: var(--ink-faint);
  line-height: 1.7;
}
.terms-notice a { color: var(--ink-soft); text-decoration: underline; text-underline-offset: 2px; }
.terms-notice a:hover { color: var(--ink); }

/* ── 데스크톱 ≥900px ── */
@media (min-width: 900px) {
  .page {
    padding: 48px 24px;
  }

  /* 식물 장식을 넓은 화면에 맞춰 확대 */
  .sprig {
    width: 88px;
    height: 132px;
    opacity: 0.55;
  }
  .sprig-top { top: 40px; left: 56px; }
  .sprig-bottom { bottom: 40px; right: 56px; }

  .card {
    max-width: 420px;
    gap: 24px;
  }

  .logo { font-size: 40px; }

  .title { font-size: 32px; }

  .subtitle { font-size: 14.5px; }
}
</style>
