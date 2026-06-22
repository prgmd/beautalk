import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

const SEED_RECOMMENDED = [
  { id: 'p1', brand: '코스알엑스', name: 'AHA/BHA 클래리파잉 토너', price: 12000, image: null, oliveyoungUrl: '#', recommendedAt: '2025-05-24T10:30:00' },
  { id: 'p2', brand: '바이오더마', name: '세비엄 H2O 미셀라 워터', price: 29800, image: null, oliveyoungUrl: '#', recommendedAt: '2025-05-21T14:20:00' },
  { id: 'p3', brand: '아누아', name: '어성초 77 토너', price: 15000, image: null, oliveyoungUrl: '#', recommendedAt: '2025-05-19T09:00:00' },
  { id: 'p5', brand: '에스트라', name: '아토베리어 365 크림', price: 35000, image: null, oliveyoungUrl: '#', recommendedAt: '2025-05-16T16:45:00' },
]

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const isLoading = ref(false)

  // 찜한 제품을 "객체"로 보관한다(예전에는 id만 저장해 찜 목록 페이지에서 제품 정보를 못 보여줬음).
  // 과거 데이터(id 문자열 배열)는 제품 정보를 복원할 수 없으므로 객체 형태만 살린다.
  const likedRaw = JSON.parse(localStorage.getItem('bt_liked') || '[]')
  const likedProducts = ref(Array.isArray(likedRaw) ? likedRaw.filter((p) => p && typeof p === 'object' && p.id) : [])
  const likedIds = computed(() => new Set(likedProducts.value.map((p) => p.id)))

  const stored = localStorage.getItem('bt_recommended')
  const recommendedProducts = ref(stored ? JSON.parse(stored) : SEED_RECOMMENDED)

  function persistRecommended() {
    localStorage.setItem('bt_recommended', JSON.stringify(recommendedProducts.value))
  }

  function addMessage(msg) {
    messages.value.push(msg)
    if (msg.products?.length) addRecommendations(msg.products)
  }

  function addRecommendations(products) {
    const now = new Date().toISOString()
    products.forEach((p) => {
      const exists = recommendedProducts.value.find((r) => r.id === p.id)
      if (exists) {
        exists.recommendedAt = now
      } else {
        recommendedProducts.value.unshift({ ...p, recommendedAt: now })
      }
    })
    recommendedProducts.value.sort((a, b) => new Date(b.recommendedAt) - new Date(a.recommendedAt))
    persistRecommended()
  }

  function clearMessages() {
    messages.value = []
  }

  function persistLiked() {
    localStorage.setItem('bt_liked', JSON.stringify(likedProducts.value))
  }

  // product 객체를 받아 찜 토글. 찜 해제만 하는 화면도 객체를 그대로 넘기면 된다.
  function toggleLike(product) {
    const id = product?.id
    if (!id) return
    const idx = likedProducts.value.findIndex((p) => p.id === id)
    if (idx >= 0) {
      likedProducts.value.splice(idx, 1)
    } else {
      likedProducts.value.unshift({
        id,
        brand: product.brand,
        name: product.name,
        price: product.price,
        image: product.image ?? null,
        oliveyoungUrl: product.oliveyoungUrl ?? '#',
        likedAt: new Date().toISOString(),
      })
    }
    persistLiked()
  }

  function isLiked(productId) {
    return likedIds.value.has(productId)
  }

  return {
    messages, isLoading, likedIds, likedProducts, recommendedProducts,
    addMessage, addRecommendations, clearMessages, toggleLike, isLiked,
  }
})
