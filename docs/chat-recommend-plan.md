# 챗봇 대화 → 추천 분리 설계 (프론트/백엔드 공유용)

> 작성일: 2026-06-22
> 목적: 챗봇을 **"대화 단계"와 "추천 단계"로 분리**하는 설계 합의 문서.
> 상태: **✅ 계약 확정(lock).** §4 API 계약 + §5 모델 + §7 결정 모두 합의 완료.
> 프론트/백엔드는 이 문서 기준으로 §6 분담대로 **병렬 착수**한다.

> ⚠️ **이 문서의 §4 API 계약은 기존 챗봇 구현(커밋 `d87e50d`, `POST /chat/` → `{content}`)을 대체한다.**
> 프론트는 옛 응답 형식에 붙이지 말고 이 확정본 기준으로 작업할 것. (헛수고 방지)

---

## 1. 배경 — 왜 나누는가

기존 `POST /api/v1/chat/`는 대화 응답과 제품 추천을 한 번에 처리하려다 보니
LLM이 JSON으로 답하면 **그 JSON이 채팅 말풍선에 그대로 노출되는** 문제가 있다.

해법: **단계를 분리한다.**
- **대화 단계**: 자연어 텍스트만 주고받는다. (채팅 경험)
- **추천 단계**: 사용자가 추천을 트리거하면, 그 시점까지의 대화 내역으로 제품 3개를 구조화해 반환한다.

이렇게 하면 채팅창에는 자연어만, 추천 카드는 추천 단계에서만 나온다.

---

## 2. 전체 흐름

```
[대화 화면]
 ┌─────────────────────────────────────┐
 │ 🤖 어떤 제품군을 찾으세요?           │
 │ 🙋 여드름 자국용 토너요              │
 │ 🤖 향에 민감하신 편인가요?           │
 │                                     │
 │        [✨ 추천받기]  ← 항상 클릭 가능. ready=true면 강조(반짝)
 └─────────────────────────────────────┘
            │ 버튼 클릭
            ▼
[추천 화면] "대화 내역을 기반으로 화장품을 추천 중입니다..." (로딩)
            ▼
       추천 제품 3개 + 추천 이유
       [조금 더 대화할래요]  ← 다시 대화 화면으로 복귀
```

핵심 규칙:
- **추천 트리거 = AI 자동 판단 + 사용자 수동.** AI가 "이제 추천 가능"이라고 판단하면(`ready=true`)
  프론트가 추천 버튼을 강조한다. 단, 사용자는 `ready`와 무관하게 언제든 추천을 누를 수 있다(중간 추천).
- **"조금 더 대화할래요"**는 추천 화면 → 대화 화면 복귀일 뿐이라 **백엔드 추가 작업 없음**(프론트 라우팅).

> 📌 **progress 게이지(readiness 숫자)는 폐기됐다.** LLM 자율 점수라 요동쳐서 UI에 그리면
> 디버깅·UX 둘 다 손해. 추천 트리거는 `ready` **불리언 하나로만** 표현한다(§3).

---

## 3. 추천 트리거 `ready` (불리언)

- LLM이 매 대화 턴마다 "추천을 의미 있게 할 만큼 정보가 모였나"를 판단해 `ready`(true/false)를 반환한다.
  - 판단 근거(정보 슬롯): 피부 타입·고민(**SkinProfile에서 이미 채워짐**) + 원하는 제품군·향/가격대 선호(**대화로 채움**).
  - `ready=true` 기준: 제품군이 특정되는 등 추천이 유의미해지는 시점. 임계값 개념상 **readiness ≥ 70** 수준에 해당하지만, 숫자는 외부로 노출하지 않고 백엔드 내부 판단으로만 쓴다.
- **백엔드**: 매 턴 **솔직한 `ready` 값만** 반환한다. 단조 증가/sticky 처리 안 함(`max()` 안 함).
- **프론트(표시 책임)**:
  - `ready`는 **sticky** — 한 대화에서 한 번 true가 되면 버튼 강조를 유지한다(중간에 false로 떨어져도 강조 유지).
  - **새 대화 시작 시 리셋**(false로). 대화 경계는 history를 들고 있는 프론트만 알기 때문에 리셋 책임도 프론트에 둔다.

---

## 4. API 계약 (확정)

> 공통:
> - 응답은 **snake_case**. 인증 **JWT 필수**(`Authorization: Bearer <access>`). base `/api/v1/`.
> - 어시스턴트/요약 텍스트 키는 대화·추천·히스토리 **전부 `content`로 통일**한다. (모델 내부 컬럼명이 `title`이어도 시리얼라이저에서 `content`로 내보낸다.)
> - 에러는 **공통 포맷**: 상태코드 + `{ "error": "..." }`.

### 4-1. 대화 — `POST /api/v1/chat/` (기존 수정)

**Request**
```json
{
  "content": "여드름 자국용 토너 찾아요",
  "history": [
    { "role": "user",      "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

**200 Response**
```json
{
  "content": "향에 민감한 편이신가요?",   // 채팅 버블에 표시 (자연어만)
  "ready": false                          // true면 프론트가 추천 버튼 강조(sticky)
}
```

**에러 Response (공통 포맷)**
```json
// 502 (AI 서버 연결 실패) / 504 (타임아웃) / 400 (content 누락)
{ "error": "AI 서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요." }
```

- `history`는 프론트가 관리하고 매 요청마다 전송한다(백엔드 Stateless).
- 프론트는 `content`만 말풍선에 그린다. `ready`는 버튼 강조 상태에만 쓴다(§3, sticky·리셋은 프론트 처리).

### 4-2. 추천 — `POST /api/v1/recommend/` (신설)

**Request**
```json
{
  "history": [
    { "role": "user",      "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

**200 Response**
```json
{
  "content": "여드름 자국 + 민감성을 고려해 3가지를 골랐어요.",
  "products": [
    {
      "id": "product-uuid",
      "brand": "코스알엑스",
      "name": "AHA/BHA 클래리파잉 토너",
      "price": 12000,
      "oliveyoung_url": "https://...",
      "image_url": "https://...",
      "category": "토너",
      "ai_summary": "...",
      "average_rating": 4.6,
      "review_count": 1284,
      "satisfaction_by_type": { "건성": 72, "지성": 91, "복합성": 88, "민감성": 64 },
      "reason": "여드름 자국 진정에 호평이 많고 민감성에도 무난해요."
    }
    // 최대 3개
  ]
}
```

- **product 객체 = 기존 `ProductSerializer` 전체 필드 + `reason`.** (트림하지 않는다.)
  → 추천/히스토리 카드에서 제품 상세 모달을 열 때 실제 `ai_summary`·평점·만족도를 바로 보여줄 수 있다(목업 fallback 제거).
- 백엔드 처리: 대화 내역 + 피부 프로필 + 제품 목록 → LLM이 **제품 목록의 정확한 id 3개**를 고르도록 강제.
  → 백엔드가 그 id로 DB 조회 → 실제 제품만 반환(환각 방지) → §5 모델에 저장.
- 기피 성분 포함 제품은 후보에서 제외(후처리 필터).
  - **유효 제품이 3개 미만이면 채워진 만큼만 반환**(1~3개). 프론트는 개수에 무관하게 렌더한다.
- **실패 시**: §4-1과 동일 포맷(502/504 등). 프론트는 에러 안내 후 "다시 시도".

### 4-3. 추천 히스토리 — `GET /api/v1/recommendations/` (기존 수정)

**배치(추천 1회) 단위 타임라인**, 최신순. 각 배치는 그 안의 제품들을 중첩한다.

```json
[
  {
    "id": "rec-uuid",                       // 배치(Recommendation) id
    "content": "여드름 자국 + 민감성을 고려해 3가지를 골랐어요.",  // 배치 요약(= /recommend 응답 content)
    "created_at": "2026-06-22T10:30:00Z",
    "products": [
      {
        "id": "product-uuid",
        "brand": "코스알엑스",
        "name": "...",
        "price": 12000,
        "oliveyoung_url": "https://...",
        "image_url": "https://...",
        "category": "토너",
        "ai_summary": "...",
        "average_rating": 4.6,
        "review_count": 1284,
        "satisfaction_by_type": { "건성": 72, "지성": 91, "복합성": 88, "민감성": 64 },
        "reason": "여드름 자국 진정에 호평이 많고..."
      }
      // 그 배치에서 추천된 제품들 (최대 3)
    ]
  }
]
```

- product 객체는 §4-2와 **동일하게 `ProductSerializer` 전체 + `reason`**.
- 같은 제품이 다른 날 또 추천돼도 **배치(부모)가 다르므로** 각각 별도로 남는다(이벤트 로그).
- 프론트 `:key`는 **배치 `id` / 제품 조합**으로 잡는다 → key 충돌 없음.

---

## 5. 추천 기록 모델 (확정: 배치 부모 + 제품 자식)

기존 `chat.Recommendation`을 **"추천 1회(배치)"의 부모**로 재활용한다.
이 한 수로 ① 추천 묶음 식별(batch) ② 같은 제품 반복 추천 ③ 배치 요약 보존이 한 번에 풀린다.

```python
# chat/models.py
class Recommendation(models.Model):                  # 추천 1회 = 배치(부모)
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey('accounts.UserInfo', on_delete=models.CASCADE)
    title      = models.TextField()                  # /recommend 응답 요약 → 시리얼라이저에서 content로 노출
    created_at = models.DateTimeField(auto_now_add=True)


class RecommendedProduct(models.Model):              # 배치에 묶인 제품(자식)
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, related_name='products')
    product        = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    reason         = models.TextField(blank=True)    # 제품별 추천 이유 (쟁점1=A: 저장)
    created_at     = models.DateTimeField(auto_now_add=True)
    # UniqueConstraint 없음 — 이벤트 로그(쟁점2=B). 같은 제품도 배치마다 새 행.
```

- `/recommend/` 한 번 = `Recommendation` 1개 생성 + 그 밑에 `RecommendedProduct` 최대 3개.
  - `Recommendation.title` ← 그 호출의 응답 `content`(배치 요약) 저장.
  - 각 `RecommendedProduct.reason` ← 제품별 이유 저장.
- 히스토리(§4-3)는 `Recommendation`을 최신순으로, 자식 `products`를 중첩해 반환.
- 시리얼라이저에서 `title` → 외부 키 **`content`**로 매핑(§4 통일 규칙).

---

## 6. 책임 분담

| 구분 | 백엔드 | 프론트 |
|------|--------|--------|
| 대화 | LLM 호출, `content`/`ready` 분리 반환(매 턴 솔직한 `ready`) | `content`만 말풍선, `ready`로 버튼 강조(**sticky·새 대화 리셋**) |
| 추천 트리거 | `ready` 판단 | `ready=true`면 버튼 강조, 클릭 시 `/recommend/` 호출(항상 가능) |
| 추천 | id 추출 → DB 조회 → 배치 저장 → 제품(전체 필드+reason) 반환 | "추천 중..." 로딩 → 제품 카드 렌더(1~3개) |
| 더 대화하기 | (없음) | 추천 화면 → 대화 화면 라우팅 |
| 히스토리 | 배치 단위 중첩 응답 반환 | **배치 타임라인** 렌더(요약+날짜+제품 카드) |

---

## 7. 확정된 결정

- [x] **§4 계약이 기존 챗봇 구현(d87e50d)을 대체함** — 양 팀 확인.
- [x] **progress 게이지·readiness 숫자 = 삭제.** `ready` 불리언만 유지(프론트 sticky·리셋).
- [x] **`ready` 임계값 70** (백엔드 내부 판단, 숫자 미노출).
- [x] **reason 저장 = A** (모델 `RecommendedProduct.reason`).
- [x] **dedup = B (이벤트 로그)** — 배치 부모(`Recommendation`) + 자식(`RecommendedProduct`)로 구현. UniqueConstraint 없음.
- [x] **어시스턴트/요약 텍스트 키 `content`로 통일** (모델 `title` → 시리얼라이저 `content`).
- [x] **중첩 product = `ProductSerializer` 전체 필드 + `reason`** (상세 모달 실데이터 표시).
- [x] **추천 개수 3개 고정**, 단 기피 성분 필터로 부족하면 있는 만큼(1~3개).
- [x] **히스토리 = 배치 단위 타임라인** — `RecommendedProductsView`는 "찜 후보 그리드"가 아니라 "추천 받은 내역 로그" 성격. (프론트 수용 확정)
- [x] **readiness 산출 = LLM 자율 판단**(1차). 불안정 시 슬롯 채움률 규칙으로 보강.

### 추후(이번 범위 밖)
- [ ] **사용량 제한 위치**: 현재 프론트에 로컬 usage 카운터 + 페이월 목업 존재.
      서버사이드(`ScopedRateThrottle`) 이전이 정석이나 이번 범위 밖 — **언제 이전할지**만 추후 합의.
- [ ] 진짜 벡터 검색(RAG, pgvector)은 Phase 2.

---

## 8. 작업 순서

### 백엔드
1. `Recommendation`(배치 부모) 보강 + `RecommendedProduct`(자식) 신규 모델 + 마이그레이션 (§5).
2. `POST /api/v1/chat/` 수정 — LLM 구조화 출력(JSON 모드) → `content`/`ready` 분리 + 공통 에러 포맷.
3. `POST /api/v1/recommend/` 신설 — history → 제품 id 추출 → DB 조회 → 배치 저장 → `content`+`products`(전체 필드+reason) 반환.
4. `GET /api/v1/recommendations/` 수정 — 배치 단위 중첩 응답(§4-3).
5. 테스트 (LLM 호출은 mock).

### 프론트 (§6 기준 병렬)
1. 챗봇 API 연동 — `POST /chat/`(content/ready), `ready` sticky·새 대화 리셋, 공통 에러 처리.
2. 추천 흐름 — `[추천받기]` → `POST /recommend/` 로딩 → 제품 카드(1~3개) 렌더.
3. `RecommendedProductsView` — `GET /recommendations/` 배치 타임라인으로 재구성(`:key`=배치 id/제품).
4. 추천/히스토리 카드의 찜·상세 모달 연동(이미 만든 `likes` 스토어 + 실제 UUID로 자동 동작).
