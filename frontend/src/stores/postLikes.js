import { ref } from 'vue'
import { defineStore } from 'pinia'

// 게시글 좋아요 상태를 로컬에 기억한다.
// 백엔드 게시글 응답에 'is_liked'가 없어, 상세 재진입 시 하트 상태가 풀리는 문제 보완.
// 서버가 is_liked를 제공하면 그 값을 우선 쓰고(이 스토어는 폴백), 토글 결과는 항상 여기 반영한다.
export const usePostLikesStore = defineStore('postLikes', () => {
  const cached = JSON.parse(localStorage.getItem('bt_post_likes') || '[]')
  const ids = ref(new Set(Array.isArray(cached) ? cached : []))

  function isLiked(id) {
    return ids.value.has(id)
  }
  function set(id, liked) {
    if (liked) ids.value.add(id)
    else ids.value.delete(id)
    localStorage.setItem('bt_post_likes', JSON.stringify([...ids.value]))
  }
  return { isLiked, set }
})
