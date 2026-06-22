import { ref } from 'vue'
import { defineStore } from 'pinia'

// 사용량 제한은 백엔드 throttle(인증 100/day)이 단일 기준이다.
// 서버가 429를 주면 api.js가 이 스토어를 열어 프리미엄 안내(페이월)를 띄운다.
export const usePaywallStore = defineStore('paywall', () => {
  const isOpen = ref(false)
  function open() {
    isOpen.value = true
  }
  function close() {
    isOpen.value = false
  }
  return { isOpen, open, close }
})
