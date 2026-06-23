# 추천 하이브리드 검색 — API 계약 초안 (FE → BE)

> 추천 실패 분석([recommend-failure-report.md](recommend-failure-report.md)) 후속.
> **정형 제약(제형·가격)을 SQL로 먼저 거른 뒤 임베딩 정렬**하는 하이브리드 구조로
> 가기 위한 프론트/백엔드 **인터페이스 합의안**이다. 이 계약대로 FE는 구조화
> 입력을 보내고 충족 배지·완화 배너를 그리며, BE는 필터·응답 필드를 붙인다.
>
> 상태: **초안(논의용)**. "확인 필요" 표시 항목은 BE 합의 후 확정.

---

## 0. 합의된 전제 (보고서 + 논의 반영)

1. **A/B 분리** — 실패를 두 유형으로 나눠 우선순위를 정한다.
   - **유형 A**: 조건 맞는 데이터가 있는데 못 지킴(예: 2~3만원 59건인데 5,700원 추천). → 로직/필터로 해결. **1차 목표.**
   - **유형 B**: 조건 맞는 데이터가 아예 없음(예: 로션/스킨 0건). → 데이터(크롤링)·정직한 실패로 대응. 그다음 단계.
2. **진짜 방어선은 SQL 필터** — 프롬프트의 `{price}원`은 보조일 뿐, LLM은 언제든 어긴다. 후보를 `WHERE price BETWEEN .. AND form IN (..)`로 먼저 걸러 **LLM이 위반 제품을 볼 수조차 없게** 한다.
3. **정직한 실패(graceful degradation)** — 필터 결과가 부족하면 단계적으로 완화하되, **무엇을 완화했는지 응답에 표기**해 신뢰를 유지한다(말없이 위반 제품 X).
4. **제형 칩(FE)은 form 필드(BE)가 선행** — FE가 `form=lotion`을 보내도 BE에 `form` 컬럼이 없으면 못 거른다. form 백필(규칙 파싱)이 하이브리드의 1번 작업.

---

## 1. 요청 — `POST /api/v1/recommend/`

기존 `history`에 **선택적 `filters`** 를 추가한다. 하위호환: `filters`가 없으면
지금과 동일 동작(BE가 history에서 추출하거나 필터 없이 진행).

```jsonc
{
  "history": [ { "role": "user", "content": "지성 피부인데 2~3만원대 로션 추천" }, ... ],

  "filters": {                      // 선택. 없으면 제약 없음(또는 BE가 history에서 추출)
    "forms": ["lotion", "toner"],   // 제형 키 배열(OR 매칭). §4 enum 참고. [] / 생략 = 제형 무관
    "price_min": 20000,             // 원, 포함(inclusive). 생략 = 하한 없음
    "price_max": 35000,             // 원, 포함(inclusive). 생략 = 상한 없음
    "categories": ["스킨케어"]       // 선택. 대분류 필터(있으면). 생략 = 무관
  }
}
```

- 모든 `filters` 하위 키는 **선택**. 보낸 축만 제약으로 적용한다.
- 가격은 **원 단위 정수**. "2~3만원대"는 FE가 `20000~35000`으로 변환해 보낸다(슬라이더/칩).
- `forms`는 **키(영문 enum)** 로 보낸다. 한글 라벨↔키 매핑은 §4. FE가 키로 변환 책임.

---

## 2. 응답 — `POST /api/v1/recommend/` (확장)

기존 `RecommendationSerializer`(`id`, `content`, `created_at`, `products[]`)에
**`constraints`(완화 메타) 추가** + **product마다 `form`·`meets` 추가**. 전부 **가산적(추가만)** 이라
기존 화면은 그대로 동작한다.

```jsonc
{
  "id": "…",
  "content": "지성 피부에 맞춘 진정·피지 케어 3종이에요.",
  "created_at": "2026-06-23T…",

  "constraints": {                         // 신규(선택). 없으면 FE는 배너 미표시
    "requested": { "forms": ["lotion","toner"], "price_min": 20000, "price_max": 35000 },
    "applied":   { "forms": [], "price_min": 20000, "price_max": 35000 },  // 실제 적용(완화 후)
    "relaxed": true,
    "relaxed_axes": ["form"],              // 완화한 축: "form" | "price" | "category"
    "note": "요청하신 2~3만원대 로션/스킨은 없어, 가격대를 맞춘 비슷한 기초 제품으로 추천드려요."
  },

  "products": [
    {
      "id": "…", "brand": "닥터지", "name": "레드블레미쉬 수딩크림",
      "price": 27600, "image_url": "…", "category": "스킨케어",
      "ai_summary": "…", "average_rating": 4.6, "review_count": 1284,
      "satisfaction_by_type": { "지성": 91, … },
      "reason": "지성 피부의 피지·진정에 맞춰…",

      "form": "cream",                     // 신규: 구조화된 제형 키(§4). 미분류면 null
      "meets": { "price": true, "form": false }  // 신규: 사용자가 건 제약별 충족 여부
    }
  ]
}
```

### `meets` 규칙
- **사용자가 건 축만** 키로 포함한다(가격 안 보냈으면 `price` 키 없음).
- 값은 `true`/`false`. FE는 충족=초록 배지, 미충족=회색/경고 배지로 표시.
- `applied` 필터가 완화돼 통과한 제품이라도, `meets`는 **원본 요청(`requested`) 기준**으로 평가한다.
  → "가격은 지켰지만 제형은 미충족" 같은 정직한 표시가 가능.

---

## 3. 동작 규약 (BE) — 필터 → 임베딩 → LLM

```
history + filters
   │  ① 의도 보강: filters 없으면 history에서 form·price 추출(선택)
   ▼
SQL 후보 필터:  Product.exclude(ai_summary='')
                .filter(price 범위) .filter(form in forms) .filter(category in …)
   │  ② 결과 수가 충분(≥ MIN_POOL)?  ── 예 ──┐
   │                                         │
   │  아니오 → ③ 단계적 완화(아래 순서)        │
   ▼                                         ▼
완화된 후보 ─────────────► 임베딩 코사인 정렬 top-N ─► LLM이 N개 중 3개 선택 ─► 검증·저장
```

- **핵심**: 필터는 임베딩 **앞**에서 SQL로. LLM에는 **걸러진 후보만** 들어가 위반 추천이 구조적으로 불가.
- 프롬프트에 `{price}원`·`{form}` 노출은 **보조**(LLM이 이유 작성·동률 선택에 활용).

### 완화(degradation) 순서 — *확인 필요*
후보가 `MIN_POOL` 미만이면 아래 순으로 완화하고, 완화한 축을 `relaxed_axes`·`note`에 기록:

1. **가격대 ± 한 단계 확장**(예: ±10,000 또는 한 가격밴드) — 예산은 최대한 존중.
2. 그래도 부족하면 **제형(form) 제약 해제** — 가격은 유지(유형 B 흔한 경로).
3. 그래도 부족하면 **카테고리까지 해제** → 일반 추천 + `note` 명시.

> 기본값 제안: 가격을 제형보다 **나중에** 풀지(예산 존중) vs 먼저 풀지는 BE와 확정.
> 어떤 순서든 `relaxed_axes`/`note`만 정확하면 FE는 그대로 표시(순서 무관).

---

## 4. 제형(form) enum — FE 칩 ↔ BE form 필드 *확인 필요*

FE 칩과 BE `form` 백필이 **같은 키**를 써야 매칭된다. 제안 키셋(한글 라벨 → 키):

| 칩 라벨 | 키 | 제품명 매칭 키워드(BE 파싱 참고) |
|---|---|---|
| 스킨/토너 | `toner` | 스킨, 토너 |
| 로션/에멀전 | `lotion` | 로션, 에멀전, 유액 |
| 에센스 | `essence` | 에센스 |
| 세럼/앰플 | `serum` | 세럼, 앰플 |
| 크림 | `cream` | 크림 |
| 미스트 | `mist` | 미스트 |
| 선크림 | `suncream` | 선크림, 선세럼, 선블록 |
| 클렌저 | `cleanser` | 클렌저, 클렌징, 폼 |
| 패드 | `pad` | 패드, 토너패드 |
| 마스크/팩 | `mask` | 마스크, 팩, 시트 |

- **예외 우선순위**(보고서의 가짜매칭): `선크림/선세럼`은 `suncream`이 **스킨/토너보다 우선**.
  `스킨핏`(피부밀착)·`스킨1004`(브랜드)는 토너로 보지 않음 → 키워드 경계·브랜드 예외 처리.
- FE는 위 라벨로 칩을 노출하고 **키로 변환해** `forms`에 담는다. enum 확정 후 양쪽 고정.

---

## 5. 책임 분담 & 점진 적용

| | FE (내가) | BE (팀원) |
|---|---|---|
| 입력 | 제형 칩 + 가격대 UI → `filters` 전송 | (선택) history에서 form·price 추출 폴백 |
| 필터 | — | `_recommend_candidates`에 price/form **SQL 필터** |
| 데이터 | — | `form` 필드 + **규칙 파싱 백필**(§4) |
| 프롬프트 | — | 후보 줄에 `{price}원`·`{form}` 추가 |
| 완화 | `note` 배너 + `relaxed` 표시 | 완화 로직 + `constraints` 응답 |
| 표시 | product `meets`→ 충족 배지, `form` 표시 | product에 `form`·`meets` 직렬화 |

### 하위호환(점진 적용) 규칙
- FE가 보내는 `filters`는 **추가 키** → 구버전 BE는 무시(안전).
- BE 신규 응답 필드(`constraints`·`meets`·`form`)는 **모두 선택** → FE는 **있으면 표시, 없으면 생략**.
  → 양쪽이 서로를 기다리지 않고 **독립 배포** 가능. 둘 다 붙으면 자동으로 완전 동작.

---

## 6. 예시

### (성공) 제약 충족
요청 `filters: {forms:["cream"], price_min:20000, price_max:35000}`
→ `applied == requested`, `relaxed:false`, 모든 product `meets:{price:true,form:true}`.

### (유형 A — 가격 박멸 목표) 가격은 지켜짐
요청 `price_min:20000, price_max:35000` (forms 없음)
→ SQL이 59건 후보를 가격대 안으로 한정 → LLM은 그 안에서만 선택 →
모든 product `meets:{price:true}`. **5,700원 추천 불가.**

### (유형 B — 정직한 실패) 로션 0건
요청 `filters:{forms:["lotion","toner"], price_min:20000, price_max:35000}`
→ 제형 후보 0 → 완화 2단계(제형 해제, 가격 유지) →
`constraints.relaxed:true, relaxed_axes:["form"], note:"요청하신 … 없어 …"`,
product `meets:{price:true, form:false}`. FE는 상단 배너 + 카드에 "제형 미충족" 배지.

---

## 7. 미해결/합의 필요
- [ ] 완화 순서 기본값(가격 먼저 vs 제형 먼저) — §3
- [ ] form enum 키셋 최종 확정 — §4
- [ ] `MIN_POOL`(완화 트리거 최소 후보 수) 값
- [ ] 가격 입력 UI 형태(슬라이더 vs 가격밴드 칩) — FE 결정, BE는 min/max만 받으면 무관
