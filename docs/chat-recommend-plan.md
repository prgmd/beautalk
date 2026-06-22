# 챗봇 대화 → 추천 분리 설계 (프론트/백엔드 공유용)

> 작성일: 2026-06-22
> 목적: 챗봇을 **"대화 단계"와 "추천 단계"로 분리**하는 설계를 프론트/백엔드가 함께 합의하기 위함
> 상태: **설계 합의 단계** (구현 전). 이 문서로 API 계약을 먼저 확정한 뒤 양쪽이 병렬 작업한다.

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
 │ 추천 준비도 ▓▓▓▓▓▓░░░░ 60%          │ ← progress 바 (readiness)
 ├─────────────────────────────────────┤
 │ 🤖 어떤 제품군을 찾으세요?           │
 │ 🙋 여드름 자국용 토너요              │
 │ 🤖 향에 민감하신 편인가요?           │
 │                                     │
 │        [✨ 추천받기]  ← 준비도와 무관하게 항상 클릭 가능 (중간 추천)
 └─────────────────────────────────────┘
            │ 버튼 클릭
            ▼
[추천 화면] "대화 내역을 기반으로 화장품을 추천 중입니다..." (로딩)
            ▼
       추천 제품 3개 + 추천 이유
       [조금 더 대화할래요]  ← 다시 대화 화면으로 복귀, 준비도 더 채우기
```

핵심 규칙:
- **추천 트리거 = AI 자동 판단 + 사용자 수동**. AI가 "이제 추천 가능"이라고 판단하면(`ready=true`)
  프론트가 추천 버튼을 강조한다. 단, 사용자는 준비도가 낮아도 언제든 추천을 누를 수 있다(중간 추천).
- **"조금 더 대화할래요"**는 추천 화면 → 대화 화면 복귀일 뿐이라 **백엔드 추가 작업 없음**(프론트 라우팅).

---

## 3. "추천 준비도(readiness)" 개념

> ⚠️ 용어 정리: 여기서 말하는 준비도는 **임베딩 벡터가 아니다.**
> 진짜 벡터 검색(RAG)은 Phase 2(pgvector)이고, 지금은
> **"AI가 추천에 필요한 정보를 얼마나 모았는가"를 나타내는 0~100 점수**다.

- LLM이 매 대화 턴마다 "내가 추천에 필요한 정보를 얼마나 모았나"를 스스로 판단해 숫자로 반환한다.
- 백엔드는 LLM의 구조화 응답을 파싱해 `content`(자연어)와 `readiness`(숫자)를 **분리**한다.
  → 사용자는 JSON을 절대 보지 않는다.
- 정보 슬롯 예시:
  - 피부 타입 · 피부 고민 → **SkinProfile에서 이미 채워짐** (시작부터 어느 정도 준비됨)
  - 원하는 제품군(토너/세럼/클렌저 등) · 향/가격대 선호 → **대화로 채움**
- `ready=true` 기준: 추천을 의미 있게 할 만큼 정보가 모인 상태(예: 제품군이 특정됨).

---

## 4. API 계약

> 공통: 응답은 **snake_case**. 인증 **JWT 필수**(`Authorization: Bearer <access>`). base `/api/v1/`.

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
  "readiness": 60,                        // 0~100, 상단 progress 바
  "ready": false                          // true면 "추천 준비 완료" 강조
}
```

- `history`는 프론트가 관리하고 매 요청마다 전송한다(백엔드 Stateless).
- 프론트는 `content`만 말풍선에 그린다. `readiness`/`ready`는 UI 상태(progress, 버튼 강조)에만 쓴다.

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
  "reply": "여드름 자국 + 민감성을 고려해 3가지를 골랐어요.",
  "products": [
    {
      "id": "product-uuid",
      "brand": "코스알엑스",
      "name": "AHA/BHA 클래리파잉 토너",
      "price": 12000,
      "image_url": "https://...",
      "oliveyoung_url": "https://...",
      "reason": "여드름 자국 진정에 호평이 많고 민감성에도 무난해요."
    }
    // 최대 3개
  ]
}
```

- 백엔드 처리: 대화 내역 + 피부 프로필 + 제품 목록 → LLM이 **제품 목록의 정확한 id 3개**를 고르도록 강제.
  → 백엔드가 그 id로 DB 조회 → 실제 제품만 반환(환각 방지). + `RecommendedProduct`에 저장.
- 기피 성분 포함 제품은 후보에서 제외(후처리 필터).
- **실패 시**: 502/504 + `{ "error": "..." }`. 프론트는 에러 안내 후 "다시 시도".

### 4-3. 추천 히스토리 — `GET /api/v1/recommendations/` (기존 수정)

나에게 추천된 제품 목록(최신순, 중복 제품은 최신 1건).
```json
[
  {
    "id": "product-uuid",
    "brand": "코스알엑스",
    "name": "...",
    "price": 12000,
    "image_url": "https://...",
    "oliveyoung_url": "https://...",
    "recommended_at": "2026-06-22T10:30:00Z"
  }
]
```

---

## 5. 모델 변경

> ⚠️ 현재 `chat.Recommendation`은 `{ user, title(TextField), created_at }`라 **제품을 가리키지 않는다.**
> 추천된 "제품"을 기록하려면 제품 FK가 필요하다.

신규 모델 (`products` 또는 `chat`):
```python
class RecommendedProduct(models.Model):
    user    = models.ForeignKey('accounts.UserInfo', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_recommendation')
        ]
        # 같은 제품이 여러 번 추천되면 upsert(최신 created_at 갱신) — 중복 행을 만들지 않는다.
```
- 기존 `Recommendation` 모델은 (유지/삭제) 추후 논의. 당장은 `RecommendedProduct`로 제품 추천 기록을 담는다.

---

## 6. 책임 분담

| 구분 | 백엔드 | 프론트 |
|------|--------|--------|
| 대화 | LLM 호출, `content`/`readiness` 분리 반환 | `content`만 말풍선, `readiness`로 progress 바 |
| 추천 트리거 | `ready` 플래그 계산 | `ready=true`면 버튼 강조, 클릭 시 `/recommend/` 호출 |
| 추천 | id 추출 → DB 조회 → 저장 → 제품 반환 | "추천 중..." 로딩 → 제품 3개 카드 렌더 |
| 더 대화하기 | (없음) | 추천 화면 → 대화 화면 라우팅 |
| 히스토리 | `RecommendedProduct` 조회 반환 | 마이페이지 추천 히스토리 렌더 |

---

## 7. 논의 필요 / 미확정

- [ ] `readiness` 산출을 LLM 자율 판단으로 둘지, 슬롯(피부타입·고민·제품군) 채움률 규칙으로 둘지
      → 1차는 **LLM 자율 판단**으로 가고, 불안정하면 규칙 보강 제안.
- [ ] 추천 개수 고정 3개 vs 가변(최대 5개). → 1차 **3개 고정**.
- [ ] `ready` 임계값(예: readiness ≥ 70). → 프론트와 수치 합의 필요.
- [ ] 기존 `chat.Recommendation` 모델 처리(유지/마이그레이션).
- [ ] 사용량 제한(일 N회)은 이 작업과 별개로 추후(`ScopedRateThrottle`).

---

## 8. 작업 순서 (백엔드)

1. `RecommendedProduct` 모델 + 마이그레이션
2. `POST /api/v1/chat/` 수정 — LLM 구조화 출력(JSON 모드) → `content`/`readiness`/`ready` 분리
3. `POST /api/v1/recommend/` 신설 — history → 제품 id 추출 → DB 조회 → 저장 → 반환
4. `GET /api/v1/recommendations/` 수정 — 제품 정보 포함 반환
5. 테스트 (LLM 호출은 mock)

> 이 문서의 API 계약(§4)이 확정되면 프론트는 §6 기준으로 병렬 작업 가능.
