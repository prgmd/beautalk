import { ref } from 'vue'
import { defineStore } from 'pinia'

// 가벼운 전역 토스트. 저장 성공/실패 등 일시적 피드백에 사용.
let seq = 0
export const useToastStore = defineStore('toast', () => {
  const items = ref([]) // { id, message, type: 'success'|'error'|'info' }

  function dismiss(id) {
    items.value = items.value.filter((t) => t.id !== id)
  }
  function show(message, type = 'info', ms = 2200) {
    const id = ++seq
    items.value.push({ id, message, type })
    setTimeout(() => dismiss(id), ms)
    return id
  }
  const success = (m) => show(m, 'success')
  const error = (m) => show(m, 'error', 3200)

  return { items, show, dismiss, success, error }
})
