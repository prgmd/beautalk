// 제형(form) enum — 백엔드 Product.FORM_CHOICES 와 키·라벨 일치
// (docs/recommend-hybrid-contract.md §4). 추천 조건 칩 + 결과 배지에서 공용.
export const FORM_OPTIONS = [
  { key: 'toner', label: '스킨/토너' },
  { key: 'lotion', label: '로션/에멀전' },
  { key: 'essence', label: '에센스' },
  { key: 'serum', label: '세럼/앰플' },
  { key: 'cream', label: '크림' },
  { key: 'mist', label: '미스트' },
  { key: 'suncream', label: '선크림' },
  { key: 'cleanser', label: '클렌저' },
  { key: 'pad', label: '패드' },
  { key: 'mask', label: '마스크/팩' },
]

const FORM_LABEL = Object.fromEntries(FORM_OPTIONS.map((o) => [o.key, o.label]))
export function formLabel(key) {
  return FORM_LABEL[key] || key
}

// 가격대 프리셋 → price_min/price_max(원). 단일 선택. null=경계 없음.
export const PRICE_BANDS = [
  { key: 'u10', label: '~1만원', min: null, max: 10000 },
  { key: '10_20', label: '1~2만원', min: 10000, max: 20000 },
  { key: '20_30', label: '2~3만원', min: 20000, max: 30000 },
  { key: '30_50', label: '3~5만원', min: 30000, max: 50000 },
  { key: 'o50', label: '5만원~', min: 50000, max: null },
]
