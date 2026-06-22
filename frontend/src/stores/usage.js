import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

// 무료 사용자가 하루에 보낼 수 있는 대화(메시지) 횟수
const FREE_DAILY_LIMIT = 500

function today() {
  return new Date().toISOString().slice(0, 10) // 'YYYY-MM-DD'
}

export const useUsageStore = defineStore('usage', () => {
  const limit = ref(FREE_DAILY_LIMIT)

  // localStorage에서 복원 ({ date, count } 형태)
  const stored = JSON.parse(localStorage.getItem('bt_usage') || 'null')
  const date = ref(stored?.date === today() ? stored.date : today())
  const count = ref(stored?.date === today() ? stored.count : 0)

  const remaining = computed(() => Math.max(0, limit.value - count.value))
  const canSend = computed(() => remaining.value > 0)

  function persist() {
    localStorage.setItem('bt_usage', JSON.stringify({ date: date.value, count: count.value }))
  }

  // 날짜가 바뀌었으면 카운트 초기화
  function rolloverIfNeeded() {
    if (date.value !== today()) {
      date.value = today()
      count.value = 0
      persist()
    }
  }

  // 메시지 1회 사용 기록. 한도 초과 시 false 반환
  function consume() {
    rolloverIfNeeded()
    if (!canSend.value) return false
    count.value += 1
    persist()
    return true
  }

  return { limit, count, remaining, canSend, rolloverIfNeeded, consume }
})
