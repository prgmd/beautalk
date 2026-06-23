<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useLikesStore } from '@/stores/likes'
import { useProductDetailStore } from '@/stores/productDetail'
import GlobalSidebar from '@/components/GlobalSidebar.vue'
import DewyLoader from '@/components/DewyLoader.vue'

const chat = useChatStore()
const likes = useLikesStore()
const productDetail = useProductDetailStore()

const inputText = ref('')
const chatBody = ref(null)

const isEmpty = computed(() => chat.messages.length === 0)

const EXAMPLE_PROMPTS = [
  '여드름 자국에 좋은 토너 추천해줘',
  '건조한 피부에 맞는 크림이 필요해',
  '민감성 피부에 무난한 클렌저 있어?',
]

async function sendMessage(text) {
  const msg = text || inputText.value.trim()
  if (!msg || chat.isLoading) return

  // 사용량 제한은 백엔드 throttle(100/day)이 단일 기준. 초과 시 서버가 429를 주면
  // api.js가 페이월을 띄운다(프론트는 별도 카운팅하지 않는다).
  inputText.value = ''
  await chat.sendChat(msg)
}

// 한글 등 IME 조합 중의 Enter는 무시한다.
function onEnterKey(e) {
  if (e.isComposing) return
  sendMessage()
}

function getRecommendations() {
  chat.requestRecommend()
}

function newChat() {
  chat.clearMessages()
}

function scrollToBottom() {
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
}

watch(
  () => [chat.messages.length, chat.isLoading],
  () => nextTick(scrollToBottom),
)

function formatPrice(n) {
  return n?.toLocaleString('ko-KR') + '원'
}
</script>

<template>
  <div class="screen">
    <div class="main">
    <!-- 앱바 -->
    <header class="appbar">
      <span class="ab-brand serif">beau<span class="it">talk</span></span>
      <button class="ab-new" title="새 대화" @click="newChat">⟲</button>
    </header>

    <!-- 추천 결과 화면 -->
    <div v-if="chat.mode === 'result'" class="body result">
      <!-- 로딩 -->
      <div v-if="chat.isRecommending" class="result-loading">
        <DewyLoader
          text="대화 내역으로 고르는 중"
          subtitle="맑은 피부에 어울리는 제품을 찾고 있어요"
          :size="150"
        />
      </div>

      <!-- 에러 -->
      <div v-else-if="chat.recommendError" class="result-error">
        <p class="err-icon">🌿</p>
        <p class="err-text">{{ chat.recommendError }}</p>
        <div class="err-actions">
          <button class="ghost-btn" @click="chat.backToChat()">대화로 돌아가기</button>
          <button class="primary-btn" @click="getRecommendations()">다시 시도</button>
        </div>
      </div>

      <!-- 결과 -->
      <template v-else-if="chat.recommendBatch">
        <div class="result-head">
          <span class="eyebrow">your edit</span>
          <p class="result-summary serif">{{ chat.recommendBatch.content }}</p>
        </div>

        <div class="rec-list">
          <article v-for="product in chat.recommendBatch.products" :key="product.id" class="rec-card">
            <div class="rec-arch" @click="productDetail.open(product)">
              <img v-if="product.image" :src="product.image" :alt="product.name" />
              <span v-else class="rec-ph">🧴</span>
              <button
                class="rec-heart"
                :class="{ liked: likes.isLiked(product.id) }"
                @click.stop="likes.toggleLike(product)"
              >{{ likes.isLiked(product.id) ? '♥' : '♡' }}</button>
            </div>
            <div class="rec-meta" @click="productDetail.open(product)">
              <p class="rec-brand">{{ product.brand }}</p>
              <p class="rec-name">{{ product.name }}</p>
              <p class="rec-price serif">{{ formatPrice(product.price) }}</p>
            </div>
            <p v-if="product.reason" class="rec-reason">{{ product.reason }}</p>
            <a :href="product.oliveyoungUrl" target="_blank" class="rec-link">올리브영에서 보기 ↗</a>
          </article>
        </div>

        <button class="more-chat-btn" @click="chat.backToChat()">← 조금 더 대화할래요</button>
      </template>
    </div>

    <!-- 대화 화면 -->
    <template v-else>
      <div ref="chatBody" class="body chat">
        <!-- 빈 상태 -->
        <div v-if="isEmpty" class="empty">
          <div class="empty-orb">
            <DewyLoader :size="96" />
          </div>
          <span class="eyebrow">consultation</span>
          <h1 class="empty-title serif">맑게 비치는<br><em>당신의 피부</em></h1>
          <p class="empty-desc">피부 고민을 편하게 적어주세요. 저장된 프로필을 참고해 맞춤 추천을 드려요.</p>
          <div class="examples">
            <button
              v-for="p in EXAMPLE_PROMPTS" :key="p"
              class="example"
              @click="sendMessage(p)"
            >{{ p }}</button>
          </div>
        </div>

        <!-- 메시지 -->
        <template v-else>
          <div v-for="msg in chat.messages" :key="msg.id" class="msg" :class="msg.role">
            <div v-if="msg.role === 'assistant'" class="av">🌿</div>
            <div class="bubble-wrap">
              <div class="bubble" :class="[msg.role, { error: msg.error }]">{{ msg.text }}</div>
              <button
                v-if="msg.error && msg.id === chat.messages.at(-1)?.id"
                class="retry-btn"
                @click="chat.retryChat()"
              >다시 시도</button>
            </div>
          </div>

          <!-- 로딩 -->
          <div v-if="chat.isLoading" class="msg assistant">
            <div class="av">🌿</div>
            <div class="bubble assistant loading">
              <span class="dot" /><span class="dot" /><span class="dot" />
            </div>
          </div>
        </template>
      </div>

      <!-- 추천받기 -->
      <div v-if="!isEmpty" class="reco-bar">
        <button class="reco-btn" :class="{ ready: chat.ready }" @click="getRecommendations()">
          <span class="lf">✦</span> 추천 3개 받기{{ chat.ready ? ' · 준비됐어요' : '' }}
        </button>
      </div>

      <!-- 입력 -->
      <div class="composer">
        <input
          v-model="inputText"
          placeholder="피부 고민을 적어주세요"
          :disabled="chat.isLoading"
          @keydown.enter="onEnterKey"
        />
        <button class="go" :disabled="!inputText.trim() || chat.isLoading" @click="sendMessage()">↑</button>
      </div>
    </template>
    </div>

    <GlobalSidebar />
  </div>
</template>

<style scoped>
.screen { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.main { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

/* 앱바 */
.appbar {
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between;
  padding: calc(10px + env(safe-area-inset-top)) 20px 12px;
}
.ab-brand { font-size: 21px; font-weight: 500; letter-spacing: -.3px; }
.ab-brand .it { font-style: italic; color: var(--sage); }
.ab-new {
  width: 36px; height: 36px; border-radius: 50%;
  border: 1px solid var(--line); background: var(--sheet); color: var(--ink-soft);
  font-size: 16px; display: flex; align-items: center; justify-content: center; box-shadow: var(--sh-sm);
  transition: transform var(--t) var(--ease);
}
.ab-new:active { transform: rotate(-180deg); }

.body { flex: 1; min-height: 0; overflow-y: auto; }

/* ── 빈 상태 ── */
.chat { padding: 4px 20px 12px; }
.empty {
  min-height: 100%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 20px 8px 40px; gap: 14px;
}
.empty-orb { margin-bottom: 4px; }
.eyebrow { font-size: 10px; letter-spacing: 4px; text-transform: uppercase; color: var(--sage); }
.empty-title { font-size: 26px; font-weight: 400; line-height: 1.25; letter-spacing: -.3px; }
.empty-title em { font-style: italic; }
.empty-desc { font-size: 13.5px; color: var(--ink-soft); line-height: 1.7; max-width: 300px; }
.examples { display: flex; flex-direction: column; gap: 8px; width: 100%; margin-top: 8px; }
.example {
  padding: 13px 16px; background: var(--card); border: 1px solid var(--line-soft);
  border-radius: var(--radius); font-size: 14px; text-align: left; box-shadow: var(--sh-sm);
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease);
}
.example:active { transform: scale(.98); box-shadow: var(--sh-sm); }

/* ── 메시지 ── */
.msg { display: flex; gap: 9px; margin-bottom: 14px; align-items: flex-end; animation: bt-rise .35s var(--ease) both; }
.msg.user { flex-direction: row-reverse; }
.av {
  width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
  background: var(--sage-soft); border: 1px solid var(--line); box-shadow: var(--sh-sm);
  display: flex; align-items: center; justify-content: center; font-size: 14px;
}
.bubble-wrap { display: flex; flex-direction: column; gap: 7px; max-width: 80%; }
.msg.user .bubble-wrap { align-items: flex-end; }
.bubble {
  font-size: 14.5px; line-height: 1.6; padding: 11px 15px; border-radius: 17px; white-space: pre-wrap;
}
.bubble.assistant { background: var(--card); border: 1px solid var(--line-soft); border-bottom-left-radius: 5px; box-shadow: var(--sh-bub); }
.bubble.user { background: var(--ink); color: var(--canvas); border-bottom-right-radius: 5px; box-shadow: var(--sh-ink); }
.bubble.error { background: var(--danger-bg); color: var(--danger); border-color: var(--danger-border); }
.retry-btn {
  align-self: flex-start; padding: 6px 14px; border-radius: 99px;
  border: 1px solid var(--line); background: var(--sheet); font-size: 12.5px; box-shadow: var(--sh-sm);
}
.bubble.loading { display: flex; gap: 4px; align-items: center; padding: 13px 16px; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: var(--sage); opacity: .5; animation: bt-bounce 1.2s infinite; }
.dot:nth-child(2) { animation-delay: .2s; }
.dot:nth-child(3) { animation-delay: .4s; }

/* ── 추천받기 ── */
.reco-bar { flex-shrink: 0; padding: 8px 20px 4px; }
.reco-btn {
  width: 100%; display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  border: 1px solid var(--ink); background: var(--card); color: var(--ink);
  font-weight: 600; font-size: 14px; padding: 13px; border-radius: 99px; box-shadow: var(--sh-sm);
  transition: transform var(--t) var(--ease), background var(--t-fast), color var(--t-fast);
}
.reco-btn .lf { color: var(--sage); }
.reco-btn:active { transform: scale(.99); }
.reco-btn.ready {
  background: var(--ink); color: var(--canvas); border-color: var(--ink); box-shadow: var(--sh-ink);
}
.reco-btn.ready .lf { color: var(--sage-soft); }

/* ── 입력 ── */
.composer {
  flex-shrink: 0; display: flex; align-items: center; gap: 9px;
  padding: 8px 16px 10px;
}
.composer input {
  flex: 1; border: 1px solid var(--line); background: var(--card); border-radius: 16px;
  padding: 12px 16px; font-size: 14.5px; outline: none; color: var(--ink); box-shadow: var(--sh-sm);
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
}
.composer input:focus { border-color: var(--sage); box-shadow: 0 0 0 3px rgba(126,139,109,.15); }
.composer input:disabled { opacity: .6; }
.composer input::placeholder { color: var(--ink-faint); }
.composer .go {
  width: 44px; height: 44px; flex-shrink: 0; border-radius: 14px;
  background: var(--ink); color: var(--canvas); font-size: 18px; box-shadow: var(--sh-ink);
  display: flex; align-items: center; justify-content: center;
  transition: transform var(--t) var(--ease), opacity var(--t-fast);
}
.composer .go:disabled { opacity: .3; background: var(--ink-faint); box-shadow: none; }
.composer .go:not(:disabled):active { transform: scale(.94); }

/* ── 추천 결과 ── */
.result { padding: 8px 20px 24px; }
.result-loading { min-height: 70%; display: flex; align-items: center; justify-content: center; }
.result-error {
  min-height: 60%; display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; gap: 10px;
}
.err-icon { font-size: 34px; }
.err-text { font-size: 14px; color: var(--ink-soft); }
.err-actions { display: flex; gap: 8px; margin-top: 8px; }

.result-head { margin: 6px 2px 18px; animation: bt-rise .4s var(--ease) both; }
.result-summary { font-size: 19px; font-weight: 400; line-height: 1.4; margin-top: 8px; }

.rec-list { display: flex; flex-direction: column; gap: 16px; }
.rec-card {
  background: var(--card); border: 1px solid var(--line-soft); border-radius: var(--radius-lg);
  padding: 12px; box-shadow: var(--sh-sm); animation: bt-rise .5s var(--ease) both;
}
.rec-card:nth-child(2) { animation-delay: .07s; }
.rec-card:nth-child(3) { animation-delay: .14s; }
.rec-arch {
  position: relative; aspect-ratio: 16/10; border-radius: 90px 90px 12px 12px; overflow: hidden;
  background: linear-gradient(170deg,#EFE7DB,#E6E3D0 60%,#DEE7DF); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.rec-arch::before {
  content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: 46%;
  background: repeating-linear-gradient(180deg, transparent 0 9px, rgba(34,42,46,.05) 9px 10px);
}
.rec-arch img { width: 100%; height: 100%; object-fit: cover; }
.rec-ph { font-size: 40px; position: relative; }
.rec-heart {
  position: absolute; top: 10px; right: 10px; width: 32px; height: 32px; border-radius: 50%;
  background: rgba(255,255,255,.9); box-shadow: var(--sh-sm); font-size: 14px; color: var(--rose);
  display: flex; align-items: center; justify-content: center;
}
.rec-heart.liked { background: var(--rose); color: #fff; }
.rec-meta { padding: 12px 6px 0; cursor: pointer; }
.rec-brand { font-size: 10.5px; letter-spacing: 1.2px; text-transform: uppercase; color: var(--ink-faint); }
.rec-name { font-size: 15px; font-weight: 600; line-height: 1.35; margin: 4px 0 6px; }
.rec-price { font-size: 16px; }
.rec-reason {
  font-size: 12.5px; line-height: 1.6; color: var(--ink-soft);
  background: var(--panel); border-radius: 12px; padding: 11px 13px; margin: 12px 6px 0;
}
.rec-link {
  display: block; text-align: center; margin: 12px 6px 4px; padding: 10px;
  border: 1px solid var(--line); border-radius: 12px; font-size: 13px; font-weight: 500; color: var(--ink);
}

.more-chat-btn {
  display: block; margin: 24px auto 8px; padding: 11px 22px; border-radius: 99px;
  border: 1px solid var(--line); background: var(--sheet); font-size: 13.5px; box-shadow: var(--sh-sm);
}
.ghost-btn { padding: 10px 18px; border-radius: 99px; border: 1px solid var(--line); background: var(--sheet); font-size: 13px; }
.primary-btn { padding: 10px 18px; border-radius: 99px; border: none; background: var(--ink); color: var(--canvas); font-size: 13px; font-weight: 600; box-shadow: var(--sh-ink); }

/* ── 데스크탑(≥900px) ── */
@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .appbar { max-width: 900px; width: 100%; margin: 0 auto; padding: 22px 40px 10px; }
  .ab-brand { display: none; }
  .ab-new { margin-left: auto; }
  .chat, .result { max-width: 900px; width: 100%; margin: 0 auto; padding-left: 40px; padding-right: 40px; }
  .reco-bar, .composer { max-width: 900px; width: 100%; margin: 0 auto; padding-left: 40px; padding-right: 40px; }
  .composer { padding-bottom: 22px; }
  .empty-title { font-size: 32px; }
  .empty-desc { max-width: 400px; }
  .rec-list { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; }
  .more-chat-btn { grid-column: 1 / -1; }
}
</style>
