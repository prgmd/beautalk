import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/services/api'
import { normalizeProduct } from '@/utils/product'

// 챗봇은 "대화 단계"와 "추천 단계"로 분리돼 있다(docs/chat-recommend-plan.md).
// - 대화: POST /chat/  → { content, ready }
// - 추천: POST /recommend/ → { id, content, created_at, products[] } (서버가 저장까지 완료)
export const useChatStore = defineStore('chat', () => {
  // messages: { id, role: 'user' | 'assistant', text, error? }
  const messages = ref([])
  const isLoading = ref(false) // 대화 응답 대기
  const ready = ref(false) // 추천 준비 — sticky(한 대화에서 한 번 true면 유지)

  const mode = ref('chat') // 'chat' | 'result'
  const isRecommending = ref(false) // 추천 응답 대기
  const recommendBatch = ref(null) // { id, content, products: [정규화된 product] }
  const recommendError = ref('')

  const lastUserContent = ref('') // 대화 에러 시 재시도용

  let seq = 0
  function nextId() {
    seq += 1
    return `${Date.now()}-${seq}`
  }

  // 백엔드로 보낼 대화 내역. 에러 말풍선(UI 전용)은 제외한다.
  const history = computed(() =>
    messages.value
      .filter((m) => !m.error && m.text)
      .map((m) => ({ role: m.role, content: m.text })),
  )

  function push(role, text, extra = {}) {
    messages.value.push({ id: nextId(), role, text, ...extra })
  }

  // POST /chat/ — 사용자 메시지 전송 → AI 답변/ready 수신
  async function sendChat(content) {
    lastUserContent.value = content
    const priorHistory = history.value // 새 user 메시지를 넣기 전 내역(백엔드가 content를 따로 붙임)
    push('user', content)
    isLoading.value = true
    try {
      const { data } = await api.post('/chat/', { content, history: priorHistory })
      push('assistant', data?.content || '...')
      if (data?.ready) ready.value = true // sticky
    } catch (e) {
      push('assistant', e?.data?.error || 'AI 응답을 받지 못했어요. 잠시 후 다시 시도해 주세요.', { error: true })
    } finally {
      isLoading.value = false
    }
  }

  // 대화 에러 후 재시도 — 마지막 에러 말풍선과 직전 user 메시지를 걷어내고 다시 전송한다.
  async function retryChat() {
    if (isLoading.value || !lastUserContent.value) return
    if (messages.value.at(-1)?.error) messages.value.pop()
    if (messages.value.at(-1)?.role === 'user') messages.value.pop()
    await sendChat(lastUserContent.value)
  }

  // POST /recommend/ — 지금까지의 대화로 제품 추천(배치 저장은 서버가 처리)
  async function requestRecommend() {
    mode.value = 'result'
    isRecommending.value = true
    recommendError.value = ''
    recommendBatch.value = null
    try {
      const { data } = await api.post('/recommend/', { history: history.value })
      recommendBatch.value = {
        id: data.id,
        content: data.content,
        products: (data.products || []).map(normalizeProduct),
      }
    } catch (e) {
      recommendError.value = e?.data?.error || '추천을 받지 못했어요. 잠시 후 다시 시도해 주세요.'
    } finally {
      isRecommending.value = false
    }
  }

  // 추천 화면 → 대화 화면 복귀 ("조금 더 대화할래요")
  function backToChat() {
    mode.value = 'chat'
    recommendBatch.value = null
    recommendError.value = ''
  }

  // 새 대화 (사이드바 "새 대화"). ready/모드/추천 결과까지 모두 리셋한다.
  function clearMessages() {
    messages.value = []
    ready.value = false
    mode.value = 'chat'
    recommendBatch.value = null
    recommendError.value = ''
    isLoading.value = false
    isRecommending.value = false
  }

  return {
    messages, isLoading, ready, mode, isRecommending, recommendBatch, recommendError,
    history, sendChat, retryChat, requestRecommend, backToChat, clearMessages,
  }
})
