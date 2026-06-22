import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/services/api'

// 백엔드 product(snake_case) → 프론트 UI가 쓰는 형태(camelCase)로 정규화.
// ai_summary 등 상세 필드는 제품 상세 모달에서 재사용하므로 그대로 보존한다.
function normalize(p) {
  return {
    id: p.id,
    brand: p.brand,
    name: p.name,
    price: p.price,
    image: p.image_url ?? p.image ?? null,
    oliveyoungUrl: p.oliveyoung_url ?? p.oliveyoungUrl ?? '#',
    ai_summary: p.ai_summary,
    average_rating: p.average_rating,
    review_count: p.review_count,
    satisfaction_by_type: p.satisfaction_by_type,
  }
}

// 진짜 백엔드 제품(UUID)인지 판별. 챗봇이 아직 목업 제품(p1 등)을 내려주는 단계라,
// UUID가 아닌 제품은 서버에 저장하지 않고 로컬에만 둔다(챗봇 Phase 2부터 완전 동작).
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export const useLikesStore = defineStore('likes', () => {
  // localStorage는 캐시 역할. 서버 응답이 오면 source of truth로 덮어쓴다.
  const cached = JSON.parse(localStorage.getItem('bt_liked') || '[]')
  const items = ref(Array.isArray(cached) ? cached.filter((p) => p && typeof p === 'object' && p.id) : [])
  const loaded = ref(false)

  const likedIds = computed(() => new Set(items.value.map((p) => p.id)))
  function isLiked(id) {
    return likedIds.value.has(id)
  }

  function persist() {
    localStorage.setItem('bt_liked', JSON.stringify(items.value))
  }

  // GET /likes/ — 서버 찜을 source of truth로 반영.
  // 서버에 없는 로컬 목업 찜(UUID 아님)은 데모 연속성을 위해 병합 유지한다.
  async function fetchLikes() {
    const { data } = await api.get('/likes/')
    const serverItems = (data || []).map((like) => normalize(like.product))
    const serverIds = new Set(serverItems.map((p) => p.id))
    const localMockOnly = items.value.filter((p) => !UUID_RE.test(p.id) && !serverIds.has(p.id))
    items.value = [...serverItems, ...localMockOnly]
    loaded.value = true
    persist()
  }

  // 낙관적 추가 → 서버 반영. 실패 시 롤백.
  async function add(product) {
    const norm = normalize(product)
    if (!isLiked(norm.id)) {
      items.value.unshift(norm)
      persist()
    }
    if (!UUID_RE.test(norm.id)) return // 목업 제품은 서버 저장 생략
    try {
      await api.post('/likes/', { product_id: norm.id })
    } catch (e) {
      items.value = items.value.filter((p) => p.id !== norm.id)
      persist()
      throw e
    }
  }

  // 낙관적 제거 → 서버 반영. 실패 시 롤백(단, 404는 '이미 없음'이므로 성공으로 간주).
  async function remove(productId) {
    const prev = [...items.value]
    items.value = items.value.filter((p) => p.id !== productId)
    persist()
    if (!UUID_RE.test(productId)) return // 목업 제품은 서버 호출 생략
    try {
      await api.del(`/likes/${productId}/`)
    } catch (e) {
      if (e?.status === 404) return // 서버에 이미 없음 → 삭제 목적 달성
      items.value = prev
      persist()
      throw e
    }
  }

  // 토글. 비동기지만 호출부는 await하지 않아도 되도록 에러를 내부에서 흡수한다.
  async function toggleLike(product) {
    const id = product?.id
    if (!id) return
    try {
      if (isLiked(id)) await remove(id)
      else await add(product)
    } catch (e) {
      console.warn('찜 동기화 실패:', e)
    }
  }

  return { items, loaded, likedIds, isLiked, fetchLikes, toggleLike }
})
