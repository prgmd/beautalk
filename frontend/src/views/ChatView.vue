<script setup>
import { ref, computed, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useLikesStore } from '@/stores/likes'
import { useProfileStore } from '@/stores/profile'
import { useProductDetailStore } from '@/stores/productDetail'
import { useUsageStore } from '@/stores/usage'
import GlobalSidebar from '@/components/GlobalSidebar.vue'
import PaywallModal from '@/components/PaywallModal.vue'

const chat = useChatStore()
const likes = useLikesStore()
const profile = useProfileStore()
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

// Mock products for demo
const MOCK_PRODUCTS = [
  { id: 'p1', brand: '코스알엑스', name: 'AHA/BHA 클래리파잉 토너', price: 12000, image: null, oliveyoungUrl: '#' },
  { id: 'p2', brand: '바이오더마', name: '세비엄 H2O 미셀라 워터', price: 29800, image: null, oliveyoungUrl: '#' },
  { id: 'p3', brand: '아누아', name: '어성초 77 토너', price: 15000, image: null, oliveyoungUrl: '#' },
]

async function sendMessage(text) {
  const msg = text || inputText.value.trim()
  if (!msg) return

  // 무료 사용량 한도 체크 — 초과 시 결제 모달 노출
  if (!usage.consume()) {
    showPaywall.value = true
    return
  }

  inputText.value = ''

  chat.addMessage({ id: Date.now(), role: 'user', text: msg })
  chat.isLoading = true
  await nextTick()
  scrollToBottom()

  // Mock AI response after delay
  setTimeout(async () => {
    chat.isLoading = false
    chat.addMessage({
      id: Date.now() + 1,
      role: 'ai',
      text: `${profile.skinType} + ${profile.concerns.join(', ')} 고민 프로필을 참고해서 3가지를 골라봤어요.`,
      products: MOCK_PRODUCTS,
    })
    chat.addMessage({
      id: Date.now() + 2,
      role: 'ai',
      text: '더 저렴한 옵션이나 향이 없는 제품으로 좁혀볼 수도 있어요. 편하게 말씀해 주세요.',
    })
    await nextTick()
    scrollToBottom()
  }, 1200)
}

function scrollToBottom() {
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
}

function formatPrice(n) {
  return n.toLocaleString('ko-KR') + '원'
}

function askWhy(product) {
  sendMessage(`${product.name}를 추천한 이유가 뭐야?`)
}
</script>

<template>
  <div class="layout">
    <GlobalSidebar />

    <div class="main">
      <!-- 채팅 헤더 (활성 상태) -->
      <div v-if="!isEmpty" class="chat-header">
        <span class="chat-title">챗봇 추천</span>
        <button class="usage-pill" :class="{ depleted: usage.remaining === 0 }" @click="showPaywall = true">
          오늘 남은 대화 {{ usage.remaining }}/{{ usage.limit }}
        </button>
      </div>

      <!-- 채팅 영역 -->
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
          <button class="start-btn" @click="sendMessage(EXAMPLE_PROMPTS[0])">추천 받기 시작</button>
        </div>

        <!-- 메시지 목록 -->
        <template v-else>
          <div
            v-for="msg in chat.messages"
            :key="msg.id"
            class="msg-row"
            :class="msg.role"
          >
            <div v-if="msg.role === 'ai'" class="ai-avatar">B</div>

            <div class="bubble-wrap">
              <div v-if="msg.text" class="bubble" :class="msg.role">{{ msg.text }}</div>

              <!-- 제품 카드 목록 -->
              <div v-if="msg.products" class="product-list">
                <div v-for="product in msg.products" :key="product.id" class="product-card">
                  <div class="product-clickable" @click="productDetail.open(product)">
                    <div class="product-image">
                      <div class="product-img-placeholder">🧴</div>
                    </div>
                    <div class="product-info">
                      <p class="product-brand">{{ product.brand }}</p>
                      <p class="product-name">{{ product.name }}</p>
                      <p class="product-price">{{ formatPrice(product.price) }}</p>
                    </div>
                  </div>
                  <div class="product-actions">
                    <button class="action-btn why" @click="askWhy(product)">왜 이 제품?</button>
                    <button
                      class="action-btn icon"
                      :class="{ liked: likes.isLiked(product.id) }"
                      @click="likes.toggleLike(product)"
                      title="찜하기"
                    >{{ likes.isLiked(product.id) ? '♥' : '♡' }}</button>
                    <a :href="product.oliveyoungUrl" target="_blank" class="action-btn icon" title="올리브영">↗</a>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 로딩 -->
          <div v-if="chat.isLoading" class="msg-row ai">
            <div class="ai-avatar">B</div>
            <div class="bubble ai loading">
              <span class="dot" /><span class="dot" /><span class="dot" />
            </div>
          </div>
        </template>
       </div>
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
            :disabled="usage.remaining === 0"
            @keyup.enter="sendMessage()"
          />
          <button class="send-btn" :disabled="!inputText.trim() || usage.remaining === 0" @click="sendMessage()">
            ↑
          </button>
        </div>
      </div>
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

.start-btn {
  padding: 14px 32px;
  background: var(--text-primary);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
}

/* Messages */
.msg-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
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
}
.bubble.ai { background: var(--ai-bubble); border-top-left-radius: 4px; }
.bubble.user { background: var(--user-bubble); color: #fff; border-top-right-radius: 4px; }

.bubble.loading {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 14px 18px;
}
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

/* Product cards */
.product-list { display: flex; flex-direction: column; gap: 8px; }

.product-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 14px;
}

.product-clickable {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
  cursor: pointer;
  border-radius: 8px;
  transition: opacity 0.15s;
}
.product-clickable:hover { opacity: 0.7; }

.product-image {
  width: 52px;
  height: 52px;
  border-radius: 8px;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}
.product-img-placeholder { font-size: 24px; }
.product-image img { width: 100%; height: 100%; object-fit: cover; }

.product-info { flex: 1; min-width: 0; }
.product-brand { font-size: 11px; color: var(--text-muted); }
.product-name { font-size: 14px; font-weight: 500; }
.product-price { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }

.product-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.action-btn {
  padding: 5px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
}
.action-btn:hover { background: var(--bg); color: var(--text-primary); }
.action-btn.why { font-size: 11px; color: var(--text-secondary); }
.action-btn.icon { font-size: 14px; padding: 5px 8px; }
.action-btn.liked { color: #E53935; border-color: #FECACA; }

/* Input */
.input-bar {
  padding: 16px 24px;
  border-top: 1px solid var(--border);
  background: var(--surface);
}

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

.input-inner {
  display: flex;
  gap: 10px;
  width: 100%;
  max-width: 820px;
  margin: 0 auto;
}

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
