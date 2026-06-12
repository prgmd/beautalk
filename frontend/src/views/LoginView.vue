<script setup>
import { ref } from 'vue'
import TermsModal from '@/components/TermsModal.vue'

const activeModal = ref(null) // null | 'terms' | 'privacy'

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
    <div class="card">
      <div class="logo">beautalk</div>
      <h1 class="title">시작하기</h1>
      <p class="subtitle">챗봇이 내 피부에 맞는 화장품을 추천해드려요.</p>

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
  min-height: 100vh;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.card {
  background: var(--surface);
  border-radius: 16px;
  padding: 40px 32px;
  width: 100%;
  max-width: 380px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.logo {
  text-align: center;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: var(--text-muted);
}

.title {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.subtitle {
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 16px;
}

.oauth { display: flex; flex-direction: column; gap: 10px; }

.btn-oauth {
  width: 100%;
  padding: 13px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: background 0.15s;
}
.btn-oauth:hover { background: var(--bg); }
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
