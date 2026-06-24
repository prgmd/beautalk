import { ref } from 'vue'
import { defineStore } from 'pinia'

// 전역 확인 다이얼로그. native confirm() 대체 + 파괴적 동작 확인.
// 사용: const ok = await confirm.ask({ title, message, confirmText, danger: true })
export const useConfirmStore = defineStore('confirm', () => {
  const open = ref(false)
  const opts = ref({})
  let resolver = null

  function ask(o = {}) {
    opts.value = {
      title: '확인',
      message: '',
      confirmText: '확인',
      cancelText: '취소',
      danger: false,
      ...o,
    }
    open.value = true
    return new Promise((res) => { resolver = res })
  }
  function settle(value) {
    open.value = false
    if (resolver) { resolver(value); resolver = null }
  }

  return { open, opts, ask, settle }
})
