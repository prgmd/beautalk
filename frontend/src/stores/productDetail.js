import { ref } from 'vue'
import { defineStore } from 'pinia'

// 백엔드 연결 전 임시 상세 데이터. API 연동 시 product id로 fetch하도록 교체.
const MOCK_DETAIL = {
  ai_summary:
    '여드름성·복합성 피부 사용자에게 특히 호평이 많아요. 각질 정리와 피지 조절 효과를 언급한 리뷰가 많고, 자극이 적어 데일리로 쓰기 좋다는 평이 주를 이룹니다. 다만 건성 피부는 사용 후 보습제를 충분히 덧바르는 것을 추천해요.',
  average_rating: 4.6,
  review_count: 1284,
  satisfaction_by_type: {
    건성: 72,
    지성: 91,
    복합성: 88,
    민감성: 64,
  },
  reviews: [
    { id: 1, user_name: '뷰티***', rating: 5, skin_type: '복합성', recommend_count: 42, review_date: '2025.05.18', text: '여드름 자국이 확실히 옅어졌어요. 자극 없이 매일 쓰기 좋습니다.' },
    { id: 2, user_name: '코덕***', rating: 4, skin_type: '지성', recommend_count: 17, review_date: '2025.05.10', text: '피지 조절은 만족스러운데 향이 살짝 있는 편이에요.' },
    { id: 3, user_name: '민감***', rating: 4, skin_type: '민감성', recommend_count: 9, review_date: '2025.04.29', text: '걱정했는데 따갑지 않았어요. 보습제랑 같이 쓰면 좋아요.' },
  ],
}

export const useProductDetailStore = defineStore('productDetail', () => {
  const product = ref(null)
  const detail = ref(null)
  const isOpen = ref(false)

  function open(p) {
    product.value = p
    detail.value = MOCK_DETAIL
    isOpen.value = true
  }

  function close() {
    isOpen.value = false
    product.value = null
    detail.value = null
  }

  return { product, detail, isOpen, open, close }
})
