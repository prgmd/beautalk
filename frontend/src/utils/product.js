// 백엔드 product(snake_case) → 프론트 UI 공통 형태(camelCase)로 정규화.
// 찜 스토어·추천 카드·히스토리·상세 모달이 모두 같은 형태를 쓰도록 한 곳에서 변환한다.
// ai_summary·평점·만족도 등 상세 필드와 추천 이유(reason)는 그대로 보존한다.
export function normalizeProduct(p) {
  return {
    id: p.id,
    brand: p.brand,
    name: p.name,
    price: p.price,
    image: p.image_url ?? p.image ?? null,
    oliveyoungUrl: p.oliveyoung_url ?? p.oliveyoungUrl ?? '#',
    category: p.category,
    ai_summary: p.ai_summary,
    average_rating: p.average_rating,
    review_count: p.review_count,
    satisfaction_by_type: p.satisfaction_by_type,
    reason: p.reason, // 추천 응답에만 존재(있으면 보존)
  }
}
