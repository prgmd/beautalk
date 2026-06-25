import { ref } from 'vue'
import { defineStore } from 'pinia'

// 실제 데이터 없는 필드의 폴백값.
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
}

export const useProductDetailStore = defineStore('productDetail', () => {
  const product = ref(null)
  const detail = ref(null)
  const isOpen = ref(false)

  function open(p) {
    product.value = p
    // 제품 객체가 백엔드 실데이터(ai_summary·평점·만족도)를 들고 있으면 그대로 쓰고,
    // 없으면 목업으로 채운다. 리뷰 목록은 아직 API 미제공이라 목업을 유지한다.
    const hasReal =
      p && (p.ai_summary || p.average_rating != null || (p.satisfaction_by_type && Object.keys(p.satisfaction_by_type).length))
    detail.value = hasReal
      ? {
          ai_summary: p.ai_summary || MOCK_DETAIL.ai_summary,
          average_rating: p.average_rating ?? MOCK_DETAIL.average_rating,
          review_count: p.review_count ?? MOCK_DETAIL.review_count,
          satisfaction_by_type:
            p.satisfaction_by_type && Object.keys(p.satisfaction_by_type).length
              ? p.satisfaction_by_type
              : MOCK_DETAIL.satisfaction_by_type,
        }
      : MOCK_DETAIL
    isOpen.value = true
  }

  function close() {
    isOpen.value = false
    product.value = null
    detail.value = null
  }

  return { product, detail, isOpen, open, close }
})
