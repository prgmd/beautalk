import { ref } from 'vue'
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

  // 찜 관련 상태/액션은 백엔드 연동 스토어(useLikesStore)로 분리됐다.

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

  return {
    messages, isLoading, recommendedProducts,
    addMessage, addRecommendations, clearMessages,
  }
})
