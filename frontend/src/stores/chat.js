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

  // 오늘 남은 대화 횟수(표시용). 서버가 단일 기준 — 응답의 quota로 갱신한다.
  const quota = ref(null) // { limit, used, remaining } | null

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

  // 사전 선택 조건을 첫 봇 인사말로 심는다. history에 포함되어 대화 단계 AI도
  // 이 조건을 인지하고(텍스트로), 추천 단계는 filters로 다시 한 번 보장한다.
  function seedAssistant(text) {
    push('assistant', text)
    ready.value = true // 조건이 정해졌으니 바로 추천 가능 상태로
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
      if (data?.quota) quota.value = data.quota
    } catch (e) {
      // 429(사용 한도 초과)는 api.js가 페이월을 띄우므로 에러 말풍선은 생략
      if (e?.status !== 429) {
        push('assistant', e?.data?.error || 'AI 응답을 받지 못했어요. 잠시 후 다시 시도해 주세요.', { error: true })
      }
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
  // filters(선택): { forms[], price_min, price_max, categories[] } — 하이브리드 SQL 필터.
  // 없으면 백엔드가 대화에서 추출/폴백(가산적이라 기존 동작 유지).
  async function requestRecommend(filters) {
    mode.value = 'result'
    isRecommending.value = true
    recommendError.value = ''
    recommendBatch.value = null
    try {
      const body = { history: history.value }
      if (filters && Object.keys(filters).length) body.filters = filters
      const { data } = await api.post('/recommend/', body)
      recommendBatch.value = {
        id: data.id,
        content: data.content,
        constraints: data.constraints || null, // { requested, applied, relaxed, relaxed_axes, note }
        products: (data.products || []).map(normalizeProduct),
      }
    } catch (e) {
      // 429는 api.js가 페이월을 띄우므로 결과 화면 대신 대화로 복귀
      if (e?.status === 429) {
        mode.value = 'chat'
      } else {
        recommendError.value = e?.data?.error || '추천을 받지 못했어요. 잠시 후 다시 시도해 주세요.'
      }
    } finally {
      isRecommending.value = false
    }
  }

  // 오늘 남은 대화 횟수 조회 (초기 로드용)
  async function fetchQuota() {
    try {
      const { data } = await api.get('/chat/quota/')
      if (data) quota.value = data
    } catch {
      // 실패 시 표시만 생략 (대화 기능에는 영향 없음)
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
    messages, isLoading, ready, mode, isRecommending, recommendBatch, recommendError, quota,
    history, sendChat, seedAssistant, retryChat, requestRecommend, fetchQuota, backToChat, clearMessages,
  }
})
