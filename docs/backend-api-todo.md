# 백엔드 개발 필요 목록 (찜 / 추천 기록 / 챗봇 / 사용량)

> 작성 배경: 프론트는 현재 찜·추천·챗봇·사용량을 모두 **localStorage / Mock**으로만 처리 중.
> `Product`, `Review`, `Like`, `InUseProduct`, `Recommendation` 모델은 있으나 **API(뷰·시리얼라이저·URL)가 전혀 없음**
> (`products/views.py`, `chat/views.py`는 빈 스텁, `config/urls.py`는 `accounts.urls`만 include).
> 아래 엔드포인트가 생기면 프론트가 바로 연동한다.

## 공통 규칙
- 모든 응답은 **snake_case** (기존 `profile` API와 동일). 프론트가 camelCase로 매핑한다.
- 인증: 별도 표기 없으면 **JWT 필수** (`IsAuthenticated`). `Authorization: Bearer <access>`.
- 사용자 식별: `request.user.userinfo` (기존 `ProfileView`와 동일 패턴).
- base: `/api/v1/`

---

## 1. 제품 상세 — `products`
프론트 [productDetail.js](../frontend/src/stores/productDetail.js)의 `MOCK_DETAIL`을 대체한다.

### `GET /api/v1/products/{id}/`  *(인증 불필요해도 됨)*
제품 1건 + 대표 리뷰. `id`는 `Product.id`(UUID).

**200 Response**
```json
{
  "id": "uuid",
  "brand": "코스알엑스",
  "name": "AHA/BHA 클래리파잉 토너",
  "price": 12000,
  "oliveyoung_url": "https://...",
  "image_url": "https://...",
  "category": "토너",
  "ai_summary": "여드름성·복합성 피부에 호평...",
  "average_rating": 4.6,
  "review_count": 1284,
  "satisfaction_by_type": { "건성": 72, "지성": 91, "복합성": 88, "민감성": 64 },
  "reviews": [
    { "id": 1, "user_name": "뷰티***", "rating": 5, "skin_type": "복합성",
      "recommend_count": 42, "review_date": "2025.05.18", "text": "..." }
  ]
}
```
- `reviews`는 추천수 상위 N개(예: 5개)만. `Review`에서 `product` 기준 정렬.
- **404**: 해당 id 없음.

> (선택) `GET /api/v1/products/?search=&category=&page=` 목록 API — 현재 프론트는 추천 카드로만 제품을 받으므로 필수 아님. 추후 검색/탐색 화면 추가 시 필요.

---

## 2. 찜 — `likes` (모델: `products.Like`)
프론트 [LikedProductsView.vue](../frontend/src/views/mypage/LikedProductsView.vue) (찜 목록) + 챗봇/추천 카드의 ♡ 토글.

### `GET /api/v1/likes/`
내가 찜한 제품 목록(최신순). 각 항목은 **제품 정보 + 찜한 시각**.
```json
[
  { "id": "product-uuid", "brand": "아누아", "name": "어성초 77 토너",
    "price": 15000, "image_url": "https://...", "oliveyoung_url": "https://...",
    "liked_at": "2025-05-24T10:30:00Z" }
]
```

### `POST /api/v1/likes/`  body `{ "product_id": "uuid" }`
- **201**: 찜 생성. 이미 있으면 **200**(멱등) 또는 그대로 200 반환.
- **404**: product_id 없음. **400**: product_id 누락.
- `Like`의 `unique_together(user, product)` 활용 → `get_or_create`.

### `DELETE /api/v1/likes/{product_id}/`
- **204**: 찜 해제. 없어도 204(멱등) 권장.

---

## 3. 추천 기록 — `recommendations`
프론트 [RecommendedProductsView.vue](../frontend/src/views/mypage/RecommendedProductsView.vue) + [chat.js](../frontend/src/stores/chat.js)의 `recommendedProducts`.

> ⚠️ **모델 불일치 주의**: 현재 `chat.Recommendation`은 `{ user, title(TextField), created_at }`라 **제품을 가리키지 않는다.**
> 프론트가 필요한 건 "유저에게 추천된 **제품 목록**(추천 시각 포함)"이므로 스키마 보강이 필요하다.
> 권장: `Like`/`InUseProduct`처럼 `RecommendedProduct(user FK, product FK, created_at)` 형태의 M2M 기록 테이블 추가,
> 또는 `Recommendation`에 `product FK` 추가.

### `GET /api/v1/recommendations/`
나에게 추천된 제품 목록(최신순, 중복 제품은 최신 1건).
```json
[
  { "id": "product-uuid", "brand": "코스알엑스", "name": "...",
    "price": 12000, "image_url": "https://...", "oliveyoung_url": "https://...",
    "recommended_at": "2025-05-24T10:30:00Z" }
]
```

### 추천 기록 생성
- **권장**: 아래 `POST /api/v1/chat` 응답에 제품이 포함될 때 **백엔드가 자동으로** 추천 기록을 저장(upsert: 이미 있으면 `created_at` 갱신).
- 프론트가 별도 POST를 호출하지 않아도 되게 하는 편이 깔끔함.

---

## 4. 챗봇 — `chat` (progress.md 결정 사항 기준)
프론트 [ChatView.vue](../frontend/src/views/ChatView.vue)의 `MOCK_PRODUCTS` + `setTimeout` Mock 응답 대체.
아키텍처: **GMS 직접 호출, 백엔드 stateless, 프론트가 `history[]` 관리** (progress.md 참고).

### `POST /api/v1/chat`
**Request**
```json
{
  "content": "여드름 자국에 좋은 토너 추천해줘",
  "history": [ { "role": "user", "text": "..." }, { "role": "ai", "text": "..." } ]
}
```
**200 Response**
```json
{
  "reply": "민감성 + 여드름 고민 프로필을 참고해 3가지를 골랐어요.",
  "products": [
    { "id": "uuid", "brand": "...", "name": "...", "price": 12000,
      "image_url": "https://...", "oliveyoung_url": "https://..." }
  ]
}
```
- 유저 `SkinProfile`(피부타입/고민/기피성분)을 컨텍스트로 자동 주입.
- 기피 성분 포함 제품은 결과에서 제외(후처리 필터).
- 화장품 외 질문은 범위 제한 답변.
- 응답에 포함된 제품은 **추천 기록으로 저장**(위 3번).
- **실패 시**: 502 등 + `{ "error": "..." }`. 프론트가 에러 말풍선 처리.

---

## 5. 사용량 제한 (보안 [High] — 서버 권위)
프론트 [usage.js](../frontend/src/stores/usage.js)는 localStorage 기반이라 우회 가능. 서버가 카운트해야 함.

### 적용
- `POST /api/v1/chat` 호출 시 **사용자별 일일 횟수 카운트**(무료 10회/일).
- 초과 시 **429** + body:
```json
{ "error": "daily_limit_exceeded", "limit": 10, "remaining": 0 }
```
- DRF `ScopedRateThrottle`(scope `chat`, rate `10/day`) 또는 별도 카운트 모델.
  (settings.py에 이미 `DEFAULT_THROTTLE_*` 있음 — scope 추가만 하면 됨.)

### `GET /api/v1/usage/`  *(표시용)*
```json
{ "limit": 10, "used": 3, "remaining": 7, "date": "2025-06-22" }
```
- 프론트가 "오늘 남은 대화 N/10" 표시에 사용.

---

## 6. URL 등록
`config/urls.py`에 products/chat 라우팅 추가 필요:
```python
path('api/v1/', include('products.urls')),
path('api/v1/', include('chat.urls')),
```
(현재 `accounts.urls`만 include됨. `products/urls.py`, `chat/urls.py` 신규 생성 필요.)

---

## 관련 이슈 (PR #16에서 별도 보고됨)
- `bt_refresh` 쿠키 path가 `/api/v1/auth/token/refresh`로 한정되어 `/auth/logout/`에 전송되지 않음 → 로그아웃 시 refresh 토큰 블랙리스트 미동작.
- 이메일 중복 케이스에서 `?error=email_duplicated` 미전송 (프론트는 메시지 매핑 준비 완료).
