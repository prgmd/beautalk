import { ref } from 'vue'
import { defineStore } from 'pinia'

// 선택한 프로필 사진(아바타) 키. 백엔드에 아바타 필드가 없어 로컬에 저장(기기 단위).
// 백엔드가 avatar 필드를 제공하면 그 값을 우선 쓰도록 확장 가능.
export const useAvatarStore = defineStore('avatar', () => {
  const selected = ref(localStorage.getItem('bt_avatar') || '')

  function set(key) {
    selected.value = key
    localStorage.setItem('bt_avatar', key)
  }

  return { selected, set }
})
