<script setup>
import { useRouter } from 'vue-router'
import GlobalSidebar from '@/components/GlobalSidebar.vue'

const router = useRouter()
function go(path) { router.push(path) }
</script>

<template>
  <div class="screen">
    <div class="main">
      <div class="page">
        <header class="head">
          <span class="eyebrow">상담</span>
          <h1 class="title serif">어떤 상담을<br><em>받아볼까요?</em></h1>
          <p class="sub">필요한 상담을 골라주세요. 대화하듯 편하게 진행돼요.</p>
        </header>

        <div class="cards">
          <button class="card" @click="go('/chat')">
            <span class="c-emoji">💌</span>
            <div class="c-body">
              <p class="c-title">화장품 추천</p>
              <p class="c-desc">피부 고민·원하는 제형·예산을 말씀하시면, 내 피부에 맞는 제품 3개를 이유와 함께 추천해 드려요.</p>
            </div>
            <span class="c-cta">시작하기 →</span>
          </button>

          <button class="card" @click="go('/consult/skin')">
            <span class="c-emoji">🧪</span>
            <div class="c-body">
              <p class="c-title">피부 타입 진단</p>
              <p class="c-desc">몇 가지 질문에 답하면 AI가 내 피부 타입(건성·지성·복합성·민감성)을 분석해 프로필에 저장해 드려요.</p>
            </div>
            <span class="c-cta">시작하기 →</span>
          </button>
        </div>
      </div>
    </div>

    <GlobalSidebar />
  </div>
</template>

<style scoped>
.screen { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.main { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow-y: auto; }
.page {
  width: 100%; max-width: 560px; margin: 0 auto;
  padding: calc(24px + env(safe-area-inset-top)) 20px 32px;
  display: flex; flex-direction: column; gap: 24px;
}

.head { animation: bt-rise .4s var(--ease) both; }
.eyebrow { font-size: 10px; letter-spacing: 4px; text-transform: uppercase; color: var(--sage); }
.title { font-size: 26px; font-weight: 400; line-height: 1.25; letter-spacing: -.3px; margin-top: 8px; }
.title em { font-style: italic; }
.sub { font-size: 13.5px; color: var(--ink-soft); margin-top: 10px; line-height: 1.6; }

.cards { display: flex; flex-direction: column; gap: 14px; }
.card {
  text-align: left; display: flex; align-items: center; gap: 16px;
  padding: 22px; border-radius: var(--radius-lg);
  background: var(--card); border: 1px solid var(--line-soft); box-shadow: var(--sh-soft);
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease), border-color var(--t-fast);
  animation: bt-rise .5s var(--ease) .06s both;
}
.card:hover { transform: translateY(-3px); box-shadow: var(--sh-hover); border-color: var(--sage); }
.c-emoji { font-size: 38px; line-height: 1; flex-shrink: 0; }
.c-body { flex: 1; min-width: 0; }
.c-title { font-size: 17px; font-weight: 700; color: var(--ink); }
.c-desc { font-size: 12.5px; color: var(--ink-soft); line-height: 1.55; margin-top: 6px; }
.c-cta { font-size: 13px; font-weight: 700; color: var(--sage-ink); flex-shrink: 0; align-self: flex-end; }

@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .page { max-width: 680px; padding: 48px 40px; }
  .title { font-size: 30px; }
}
</style>
