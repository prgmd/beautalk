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
    <div class="blob blob-1" />
    <div class="blob blob-2" />
    <div class="blob blob-3" />

    <div class="card">
      <div class="logo">beautalk</div>
      <h1 class="title">시작하기</h1>
      <p class="subtitle">챗봇이 내 피부에 맞는 화장품을 추천해드려요.</p>

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
  min-height: 100vh;
  width: 100%;
  background: radial-gradient(140% 120% at 50% 0%, #FBF4EF 0%, var(--bg) 55%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  overflow: hidden;
}

/* Ambient floating blobs */
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(56px);
  opacity: 0.55;
  pointer-events: none;
  will-change: transform;
}
.blob-1 { width: 360px; height: 360px; background: #FFB7CE; top: -90px; left: -70px; animation: bt-float 11s var(--ease) infinite; }
.blob-2 { width: 320px; height: 320px; background: #D6BBFF; bottom: -100px; right: -60px; animation: bt-float 13s var(--ease) infinite reverse; }
.blob-3 { width: 240px; height: 240px; background: #FFD7B5; top: 40%; right: 18%; opacity: 0.4; animation: bt-float 16s var(--ease) infinite; }

.card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px) saturate(150%);
  -webkit-backdrop-filter: blur(20px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: 44px 34px;
  width: 100%;
  max-width: 390px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  animation: bt-pop 0.6s var(--ease-back) both;
}

.logo {
  text-align: center;
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.6px;
  background: var(--gradient-brand-rich);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 6px;
}

.title {
  text-align: center;
  font-size: 23px;
  font-weight: 800;
  letter-spacing: -0.5px;
}

.subtitle {
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 16px;
}

.error-banner {
  margin-bottom: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--danger-bg, #FEF2F2);
  border: 1px solid var(--danger-border, #FECACA);
  color: var(--danger, #DC2626);
  font-size: 13px;
  line-height: 1.5;
  text-align: center;
}

.oauth { display: flex; flex-direction: column; gap: 10px; }

.btn-oauth {
  width: 100%;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: var(--shadow-sm);
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease), background var(--t-fast);
}
.btn-oauth:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.btn-oauth:active { transform: translateY(0) scale(0.99); }
.btn-oauth.kakao { background: #FEE500; border-color: #FEE500; color: #191600; }
.btn-oauth.kakao:hover { box-shadow: 0 8px 20px rgba(254, 229, 0, 0.4); }
.oauth-icon { width: 20px; height: 20px; }

.terms-notice {
  margin-top: 12px;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.7;
}
.terms-notice a { color: var(--text-secondary); text-decoration: underline; }
.terms-notice a:hover { color: var(--text-primary); }
</style>
