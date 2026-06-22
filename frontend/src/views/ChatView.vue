<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useLikesStore } from '@/stores/likes'
import { useProductDetailStore } from '@/stores/productDetail'
import { useUsageStore } from '@/stores/usage'
import GlobalSidebar from '@/components/GlobalSidebar.vue'
import PaywallModal from '@/components/PaywallModal.vue'

const chat = useChatStore()
const likes = useLikesStore()
const productDetail = useProductDetailStore()
const usage = useUsageStore()

const inputText = ref('')
const chatBody = ref(null)
const showPaywall = ref(false)

const isEmpty = computed(() => chat.messages.length === 0)

const EXAMPLE_PROMPTS = [
  '여드름 자국에 좋은 토너 추천해줘',
  '건조한 피부에 맞는 크림이 필요해',
  '민감성 피부에 무난한 클렌저 있어?',
]

async function sendMessage(text) {
  const msg = text || inputText.value.trim()
  if (!msg || chat.isLoading) return

  // 무료 사용량 한도 체크 — 초과 시 결제 모달 노출
  if (!usage.consume()) {
    showPaywall.value = true
    return
  }

  inputText.value = ''
  await chat.sendChat(msg)
}

// 한글 등 IME 조합 중의 Enter는 무시한다.
// (조합 확정 Enter로 전송하면 마지막 글자가 입력칸에 다시 남는 버그 방지)
function onEnterKey(e) {
  if (e.isComposing) return
  sendMessage()
}

function getRecommendations() {
  chat.requestRecommend()
}

function scrollToBottom() {
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
}

// 메시지/로딩이 바뀔 때마다 맨 아래로 스크롤
watch(
  () => [chat.messages.length, chat.isLoading],
  () => nextTick(scrollToBottom),
)

function formatPrice(n) {
  return n?.toLocaleString('ko-KR') + '원'
}
</script>

<template>
  <div class="layout">
    <GlobalSidebar />

    <div class="main">
      <!-- 헤더 -->
      <div v-if="!isEmpty || chat.mode === 'result'" class="chat-header">
        <span class="chat-title">챗봇 추천</span>
        <button class="usage-pill" :class="{ depleted: usage.remaining === 0 }" @click="showPaywall = true">
          오늘 남은 대화 {{ usage.remaining }}/{{ usage.limit }}
        </button>
      </div>

      <!-- 추천 결과 화면 -->
      <div v-if="chat.mode === 'result'" class="result-body">
        <div class="result-inner">
          <!-- 로딩 -->
          <div v-if="chat.isRecommending" class="result-loading">
            <div class="spinner" />
            <p>대화 내역을 기반으로 화장품을 추천 중입니다...</p>
          </div>

          <!-- 에러 -->
          <div v-else-if="chat.recommendError" class="result-error">
            <p class="err-icon">⚠️</p>
            <p class="err-text">{{ chat.recommendError }}</p>
            <div class="err-actions">
              <button class="ghost-btn" @click="chat.backToChat()">대화로 돌아가기</button>
              <button class="primary-btn" @click="getRecommendations()">다시 시도</button>
            </div>
          </div>

          <!-- 결과 -->
          <template v-else-if="chat.recommendBatch">
            <p class="result-summary">{{ chat.recommendBatch.content }}</p>

            <div class="rec-list">
              <div v-for="product in chat.recommendBatch.products" :key="product.id" class="rec-card">
                <div class="rec-clickable" @click="productDetail.open(product)">
                  <div class="rec-image">
                    <img v-if="product.image" :src="product.image" :alt="product.name" />
                    <div v-else class="rec-img-placeholder">🧴</div>
                  </div>
                  <div class="rec-info">
                    <p class="rec-brand">{{ product.brand }}</p>
                    <p class="rec-name">{{ product.name }}</p>
                    <p class="rec-price">{{ formatPrice(product.price) }}</p>
                  </div>
                </div>
                <p v-if="product.reason" class="rec-reason">💡 {{ product.reason }}</p>
                <div class="rec-actions">
                  <button
                    class="action-btn"
                    :class="{ liked: likes.isLiked(product.id) }"
                    @click="likes.toggleLike(product)"
                  >{{ likes.isLiked(product.id) ? '♥ 찜함' : '♡ 찜하기' }}</button>
                  <a :href="product.oliveyoungUrl" target="_blank" class="action-btn link">올리브영에서 보기 ↗</a>
                </div>
              </div>
            </div>

            <button class="more-chat-btn" @click="chat.backToChat()">← 조금 더 대화할래요</button>
          </template>
        </div>
      </div>

      <!-- 대화 화면 -->
      <template v-else>
        <div ref="chatBody" class="chat-body">
          <div class="chat-inner">
            <!-- 빈 상태 -->
            <div v-if="isEmpty" class="empty-state">
              <div class="empty-avatar">💄</div>
              <h2 class="empty-title">어떤 화장품을 찾고 계세요?</h2>
              <p class="empty-desc">자연어로 자유롭게 물어보세요. 저장된 피부 프로필을 참고해 맞춤 추천을 드려요.</p>
              <div class="example-prompts">
                <button
                  v-for="p in EXAMPLE_PROMPTS" :key="p"
                  class="example-btn"
                  @click="sendMessage(p)"
                >{{ p }}</button>
              </div>
            </div>

            <!-- 메시지 목록 -->
            <template v-else>
              <div
                v-for="msg in chat.messages"
                :key="msg.id"
                class="msg-row"
                :class="msg.role"
              >
                <div v-if="msg.role === 'assistant'" class="ai-avatar">B</div>
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
              <div v-if="chat.isLoading" class="msg-row assistant">
                <div class="ai-avatar">B</div>
                <div class="bubble assistant loading">
                  <span class="dot" /><span class="dot" /><span class="dot" />
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 추천받기 바 -->
        <div v-if="!isEmpty" class="recommend-bar">
          <button
            class="recommend-btn"
            :class="{ ready: chat.ready }"
            @click="getRecommendations()"
          >
            ✨ 추천받기{{ chat.ready ? ' (준비됐어요!)' : '' }}
          </button>
        </div>

        <!-- 입력 영역 -->
        <div class="input-bar">
          <div v-if="usage.remaining === 0" class="limit-notice">
            오늘의 무료 대화를 모두 사용했어요.
            <button class="upgrade-link" @click="showPaywall = true">프리미엄으로 계속하기</button>
          </div>
          <div class="input-inner">
            <input
              v-model="inputText"
              :placeholder="usage.remaining === 0 ? '내일 다시 이용하거나 프리미엄으로 업그레이드하세요' : '메시지를 입력하세요'"
              :disabled="usage.remaining === 0 || chat.isLoading"
              @keydown.enter="onEnterKey"
            />
            <button class="send-btn" :disabled="!inputText.trim() || usage.remaining === 0 || chat.isLoading" @click="sendMessage()">
              ↑
            </button>
          </div>
        </div>
      </template>
    </div>

    <PaywallModal v-if="showPaywall" @close="showPaywall = false" />
  </div>
</template>

<style scoped>
.layout { display: flex; height: 100vh; background: var(--bg); }

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--surface);
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.usage-pill {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 5px 12px;
  cursor: pointer;
  transition: background 0.15s;
}
.usage-pill:hover { background: var(--surface-hover); }
.usage-pill.depleted { color: var(--danger); border-color: var(--danger-border); background: var(--danger-bg); }

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.chat-inner {
  width: 100%;
  max-width: 820px;
  margin: 0 auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Empty state */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 40px 24px;
  text-align: center;
}
.empty-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--ai-avatar);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
}
.empty-title { font-size: 20px; font-weight: 700; }
.empty-desc { font-size: 14px; color: var(--text-secondary); max-width: 360px; line-height: 1.7; }
.example-prompts { display: flex; flex-direction: column; gap: 8px; width: 100%; max-width: 420px; }
.example-btn {
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s;
}
.example-btn:hover { background: var(--bg); }

/* Messages */
.msg-row { display: flex; gap: 10px; align-items: flex-start; }
.msg-row.user { flex-direction: row-reverse; }

.ai-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--ai-avatar);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.bubble-wrap { display: flex; flex-direction: column; gap: 8px; max-width: 560px; }

.bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.bubble.assistant { background: var(--ai-bubble); border-top-left-radius: 4px; }
.bubble.user { background: var(--user-bubble); color: #fff; border-top-right-radius: 4px; }
.bubble.error { background: var(--danger-bg); color: var(--danger); }
.retry-btn {
  align-self: flex-start;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}
.retry-btn:hover { background: var(--bg); }

.bubble.loading { display: flex; gap: 4px; align-items: center; padding: 14px 18px; }
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: bounce 1.2s infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-6px); }
}

/* 추천받기 바 */
.recommend-bar {
  padding: 12px 24px;
  display: flex;
  justify-content: center;
  border-top: 1px solid var(--border);
}
.recommend-btn {
  width: 100%;
  max-width: 820px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.recommend-btn:hover { background: var(--bg); }
.recommend-btn.ready {
  background: var(--text-primary);
  color: #fff;
  border-color: var(--text-primary);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
}

/* 추천 결과 화면 */
.result-body { flex: 1; overflow-y: auto; padding: 24px; }
.result-inner { width: 100%; max-width: 720px; margin: 0 auto; }

.result-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 80px 0;
  color: var(--text-secondary);
  font-size: 14px;
}
.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--text-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.result-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 64px 0;
  text-align: center;
}
.err-icon { font-size: 32px; }
.err-text { font-size: 14px; color: var(--text-secondary); }
.err-actions { display: flex; gap: 8px; margin-top: 8px; }

.result-summary {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.6;
  margin-bottom: 20px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #F3EEFB 0%, #EDF3FB 100%);
  border-radius: 12px;
  color: #3A3A4A;
}

.rec-list { display: flex; flex-direction: column; gap: 14px; }
.rec-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.rec-clickable { display: flex; gap: 14px; cursor: pointer; }
.rec-clickable:hover .rec-name { text-decoration: underline; }
.rec-image {
  width: 64px;
  height: 64px;
  border-radius: 10px;
  background: var(--surface-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}
.rec-image img { width: 100%; height: 100%; object-fit: cover; }
.rec-img-placeholder { font-size: 28px; }
.rec-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.rec-brand { font-size: 12px; color: var(--text-muted); }
.rec-name { font-size: 15px; font-weight: 600; line-height: 1.4; }
.rec-price { font-size: 14px; color: var(--text-secondary); margin-top: 2px; }

.rec-reason {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  background: var(--surface);
  border-radius: 10px;
  padding: 10px 12px;
}

.rec-actions { display: flex; gap: 8px; }
.action-btn {
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
}
.action-btn:hover { background: var(--bg); color: var(--text-primary); }
.action-btn.liked { color: #E53935; border-color: #FECACA; background: #FFF5F5; }
.action-btn.link { color: var(--text-primary); }

.more-chat-btn {
  margin: 24px auto 8px;
  display: block;
  padding: 10px 20px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.more-chat-btn:hover { background: var(--bg); }

.ghost-btn {
  padding: 9px 18px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 13px;
  cursor: pointer;
}
.primary-btn {
  padding: 9px 18px;
  border-radius: 8px;
  border: none;
  background: var(--text-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

/* Input */
.input-bar { padding: 16px 24px; border-top: 1px solid var(--border); background: var(--surface); }
.limit-notice {
  max-width: 820px;
  margin: 0 auto 10px;
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
}
.upgrade-link {
  border: none;
  background: none;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
  padding: 0 2px;
}
.input-inner { display: flex; gap: 10px; width: 100%; max-width: 820px; margin: 0 auto; }
.input-bar input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 14px;
  outline: none;
  background: var(--bg);
  transition: border-color 0.15s;
}
.input-bar input:focus { border-color: var(--text-primary); background: var(--surface); }
.input-bar input:disabled { opacity: 0.6; cursor: not-allowed; }
.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  border: none;
  background: var(--text-primary);
  color: #fff;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.15s;
}
.send-btn:disabled { opacity: 0.3; cursor: default; }
</style>
