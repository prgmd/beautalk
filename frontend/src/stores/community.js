import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/services/api'

// 게시판 카테고리 (백엔드 Post.CATEGORY_CHOICES 와 일치)
export const CATEGORIES = [
  { key: 'free', label: '자유' },
  { key: 'qna', label: 'Q&A·팁' },
  { key: 'sale', label: '세일 정보' },
]

export function categoryLabel(key) {
  return CATEGORIES.find((c) => c.key === key)?.label || key
}

export const useCommunityStore = defineStore('community', () => {
  // ── 목록 상태 (카테고리 필터 + 더보기 페이지네이션) ──
  const posts = ref([])
  const count = ref(0)
  const page = ref(1)
  const category = ref('') // '' = 전체
  const loading = ref(false)
  const error = ref('')
  const hasNext = ref(false)

  async function fetchPosts({ append = false } = {}) {
    loading.value = true
    error.value = ''
    try {
      const qs = new URLSearchParams()
      qs.set('page', String(page.value))
      if (category.value) qs.set('category', category.value)
      const { data } = await api.get(`/posts/?${qs.toString()}`)
      const results = data?.results || []
      posts.value = append ? [...posts.value, ...results] : results
      count.value = data?.count || 0
      hasNext.value = !!data?.next
    } catch {
      error.value = '게시글을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.'
    } finally {
      loading.value = false
    }
  }

  // 카테고리 전환 → 1페이지부터 새로 조회
  function setCategory(cat) {
    if (category.value === cat) return Promise.resolve()
    category.value = cat
    page.value = 1
    return fetchPosts()
  }

  function loadMore() {
    if (loading.value || !hasNext.value) return Promise.resolve()
    page.value += 1
    return fetchPosts({ append: true })
  }

  // ── 단건 ──
  async function fetchPost(id) {
    const { data } = await api.get(`/posts/${id}/`)
    return data
  }

  async function createPost(payload) {
    const { data } = await api.post('/posts/', payload)
    return data
  }

  async function updatePost(id, payload) {
    const { data } = await api.patch(`/posts/${id}/`, payload)
    return data
  }

  async function deletePost(id) {
    await api.del(`/posts/${id}/`)
  }

  // ── 댓글 ──
  async function addComment(postId, content) {
    const { data } = await api.post(`/posts/${postId}/comments/`, { content })
    return data
  }

  async function deleteComment(commentId) {
    await api.del(`/comments/${commentId}/`)
  }

  // ── 좋아요(토글) → { liked, like_count } ──
  async function like(postId) {
    const { data } = await api.post(`/posts/${postId}/like/`)
    return data
  }

  async function unlike(postId) {
    const { data } = await api.del(`/posts/${postId}/like/`)
    return data
  }

  return {
    posts, count, page, category, loading, error, hasNext,
    fetchPosts, setCategory, loadMore,
    fetchPost, createPost, updatePost, deletePost,
    addComment, deleteComment, like, unlike,
  }
})
