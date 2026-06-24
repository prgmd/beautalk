import { ref } from 'vue'
import { defineStore } from 'pinia'

// 전역 UI 상태. 데스크탑 사이드바 접힘 여부를 기억(라우트 이동·새로고침에도 유지).
export const useUiStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(localStorage.getItem('bt_sidebar_collapsed') === '1')

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem('bt_sidebar_collapsed', sidebarCollapsed.value ? '1' : '0')
  }

  return { sidebarCollapsed, toggleSidebar }
})
