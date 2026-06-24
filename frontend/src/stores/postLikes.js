import { defineStore } from 'pinia'
import { useAuthStore } from '@/stores/auth'

// 게시글 좋아요 상태를 로컬에 기억(백엔드 is_liked 부재 보완).
// 사용자별로 분리 저장 — 같은 브라우저에서 계정이 달라도 하트가 섞이지 않는다.
// (서버가 is_liked를 제공하면 그 값을 우선 쓰고 이 스토어는 폴백)
function storageKey() {
  const auth = useAuthStore()
  return `bt_post_likes:${auth.user?.email || 'guest'}`
}
function read() {
  try {
    const c = JSON.parse(localStorage.getItem(storageKey()) || '[]')
    return new Set(Array.isArray(c) ? c : [])
  } catch {
    return new Set()
  }
}

export const usePostLikesStore = defineStore('postLikes', () => {
  function isLiked(id) {
    return read().has(id)
  }
  function set(id, liked) {
    const s = read()
    if (liked) s.add(id)
    else s.delete(id)
    localStorage.setItem(storageKey(), JSON.stringify([...s]))
  }
  return { isLiked, set }
})
