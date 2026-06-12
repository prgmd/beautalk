<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import TermsModal from '@/components/TermsModal.vue'

const router = useRouter()
const auth = useAuthStore()

const tab = ref('login') // 'login' | 'signup'
const email = ref('')
const password = ref('')
const agreeTerms = ref(false)
const agreePrivacy = ref(false)
const error = ref('')
const activeModal = ref(null) // null | 'terms' | 'privacy'

function handleSubmit() {
  error.value = ''
  if (!email.value || !password.value) {
    error.value = '이메일과 비밀번호를 입력해주세요.'
    return
  }
  if (tab.value === 'signup' && (!agreeTerms.value || !agreePrivacy.value)) {
    error.value = '필수 약관에 동의해주세요.'
    return
  }
  // TODO: API 연결
  auth.login({ email: email.value, hasProfile: false })
  router.push('/onboarding')
}

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

      <div class="tabs">
        <button class="tab" :class="{ active: tab === 'signup' }" @click="tab = 'signup'">가입</button>
        <button class="tab" :class="{ active: tab === 'login' }" @click="tab = 'login'">로그인</button>
      </div>

      <form class="form" @submit.prevent="handleSubmit">
        <div class="field">
          <label>이메일</label>
          <input v-model="email" type="email" placeholder="name@example.com" />
        </div>
        <div class="field">
          <label>비밀번호</label>
          <input v-model="password" type="password" placeholder="••••••••" />
        </div>

        <div v-if="tab === 'signup'" class="agreements">
          <label class="checkbox-row">
            <input v-model="agreeTerms" type="checkbox" />
            <span>(필수) 이용약관 동의 <a href="#" @click.prevent="activeModal = 'terms'">보기</a></span>
          </label>
          <label class="checkbox-row">
            <input v-model="agreePrivacy" type="checkbox" />
            <span>(필수) 개인정보처리방침 동의 <a href="#" @click.prevent="activeModal = 'privacy'">보기</a></span>
          </label>
        </div>

        <p v-if="error" class="error">{{ error }}</p>

        <button type="submit" class="btn-primary">
          {{ tab === 'signup' ? '가입하기' : '로그인' }}
        </button>
      </form>

      <div class="divider"><span>또는</span></div>

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
  gap: 20px;
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

.tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
}

.tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: transparent;
  font-size: 15px;
  color: var(--text-muted);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s, border-color 0.15s;
}

.tab.active {
  color: var(--text-primary);
  border-bottom-color: var(--text-primary);
  font-weight: 500;
}

.form { display: flex; flex-direction: column; gap: 14px; }

.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 13px; color: var(--text-secondary); }
.field input {
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  background: var(--surface);
  outline: none;
  transition: border-color 0.15s;
}
.field input:focus { border-color: var(--text-primary); }

.agreements {
  background: var(--bg);
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  cursor: pointer;
}
.checkbox-row a { color: #4A90D9; }

.error {
  font-size: 13px;
  color: var(--danger);
}

.btn-primary {
  width: 100%;
  padding: 14px;
  background: var(--btn-primary);
  color: var(--btn-primary-fg);
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  transition: opacity 0.15s;
}
.btn-primary:hover { opacity: 0.85; }

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-muted);
  font-size: 13px;
}
.divider::before, .divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
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
</style>
