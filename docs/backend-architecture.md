# 백엔드 아키텍처 · 모델 · API · 흐름 (단일 레퍼런스)

> 코드 기준으로 정리한 백엔드 전체 지도. (검증: `backend/*/urls.py`·`models.py`·`chat/views.py` 실제 코드)
> 발표·인수인계·온보딩 시 "백엔드가 무엇으로 이뤄졌고 어떻게 도는가"를 이 문서 하나로 끝낸다.

---

## 1. 시스템 아키텍처

```
            사용자 브라우저 (Vue SPA)
                  │ HTTPS(443)
                  ▼
   ┌──────────── EC2 (t3.micro, Docker Compose) ────────────┐
   │  nginx        : Vue 정적(dist) 서빙 + /api·/admin 프록시  │
   │  backend      : Django + DRF + gunicorn                 │
   │  db           : PostgreSQL 16 + pgvector                │
   └─────────────────────────────────────────────────────────┘
              │                         │
       GMS(LLM·임베딩) API        카카오/구글 OAuth
```

- **컨테이너 3개**: nginx · backend(gunicorn) · db(postgres+pgvector). 상세 배포: [deployment.md](deployment.md).
- **외부 의존**: GMS(SSAFY OpenAI 프록시 — 대화·추천·요약·임베딩), 카카오·구글 OAuth.
- **앱 4개**: `accounts`(인증·프로필) · `products`(제품·찜) · `chat`(대화·추천) · `board`(커뮤니티).
- **공통 규약**: 모든 API는 `/api/v1/` 하위. 인증은 JWT(Bearer). 외부 식별 PK는 UUID(글 수·유저 수 추측 방지).

---

## 2. 데이터 모델 (ERD)

### accounts
| 모델 | 핵심 필드 | 관계 |
|------|-----------|------|
| **UserInfo** | `id`(UUID) · `email`(unique) · `auth_provider`(kakao/google) · `nickname` | Django `User`와 **1:1**. 모든 사용자 데이터의 주인 |
| **SkinProfile** | `skin_type`(건성/지성/복합성/민감성) · `concerns`(JSON) · `avoid_ingredients`(JSON) | UserInfo와 **1:1** |

### products
| 모델 | 핵심 필드 | 관계 |
|------|-----------|------|
| **Product** | `id`(UUID) · `brand` · `name` · `price` · `category` · **`form`**(ArrayField, 제형 enum 복수) · `ai_summary` · `satisfaction_by_type`(JSON) · **`embedding`**(Vector 1536) · `oliveyoung_url` · `image_url` | 여러 표가 이 표를 가리킴 |
| **Review** | `text` · `rating` · `skin_type` · `recommend_count` | Product와 **N:1** |
| **Like** | (찜) | UserInfo + Product, **unique(user,product)** |
| **InUseProduct** | (사용 중) | UserInfo + Product, **unique** |

> **제형 enum(`FORM_CHOICES`, 10종)**: toner·lotion·essence·serum·cream·mist·suncream·cleanser·pad·mask.
> 모델에 단일 출처로 두고 백필·시리얼라이저·필터가 공유. 한 제품이 복수 제형 가능(예: "스킨로션"=[toner,lotion])이라 ArrayField.

### chat (추천 기록)
| 모델 | 핵심 필드 | 관계 |
|------|-----------|------|
| **Recommendation** | `id`(UUID) · `title`(배치 요약) | UserInfo와 **N:1**. `/recommend/` 1회 = 1배치 |
| **RecommendedProduct** | `reason`(제품별 추천 이유) | Recommendation(부모) + Product. **unique 없음** → 같은 제품 재추천 허용(이벤트 로그 성격) |

### board (커뮤니티)
| 모델 | 핵심 필드 | 관계 |
|------|-----------|------|
| **Post** | `id`(UUID) · `category`(free/qna/sale) · `title` · `content` · **`products`(M2M)** | UserInfo와 N:1, Product와 **M:N**(제품 태그) |
| **Comment** | `content` | Post + UserInfo, N:1 |
| **PostLike** | (좋아요) | UserInfo + Post, **unique** |

---

## 3. API 엔드포인트 (22개, 전부 `/api/v1/`)

### accounts (9)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET/POST/PATCH | `/profile` | 피부 프로필 조회·생성·수정 |
| GET | `/auth/{kakao,google}/login/` | OAuth 인가 URL로 리다이렉트 |
| GET | `/auth/{kakao,google}/callback/` | 콜백(state 검증·토큰교환·유저정보) → 프론트로 리다이렉트 |
| GET | `/auth/exchange/` | 1회용 세션 → access 토큰 + refresh 쿠키 교환 |
| POST | `/auth/token/refresh` | refresh 쿠키로 access 재발급 |
| POST | `/auth/logout/` | refresh 블랙리스트 + 쿠키 삭제 |
| DELETE | `/account/` | 회원 탈퇴(토큰 무효화 + CASCADE) |

### products (5)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/products/` | 제품 목록(`?category=`, 페이지네이션) |
| GET | `/products/{id}/` | 제품 상세 |
| GET | `/products/{id}/posts/` | 그 제품이 태그된 글(역참조) |
| GET/POST | `/likes/` | 찜 목록 / 찜 추가 |
| DELETE | `/likes/{product_id}/` | 찜 해제 |

### chat (3)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/chat/` | **대화 단계**(자연어 ↔ `{content, ready}`) |
| POST | `/recommend/` | **추천 단계**(history → 제품 3개 배치 생성) |
| GET | `/recommendations/` | 내 추천 히스토리(배치 단위) |

### board (5)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET/POST | `/posts/` | 글 목록(`?category=`) / 작성 |
| GET/PATCH/DELETE | `/posts/{id}/` | 상세 / 수정·삭제(작성자만) |
| POST | `/posts/{id}/comments/` | 댓글 작성 |
| POST/DELETE | `/posts/{id}/like/` | 좋아요 토글 |
| DELETE | `/comments/{id}/` | 댓글 삭제(작성자만) |

> **RESTful**: 자원 중심 URL + 메서드별 의미 + 상태코드(201 생성·204 삭제·403 권한·404 없음·502/504 외부 LLM 실패).
> **권한**: 전부 `IsAuthenticated`. 수정·삭제는 `IsAuthorOrReadOnly`(작성자=`obj.user==request.user.userinfo`)로 IDOR 차단.

---

## 4. 핵심 흐름

### 4-1. OAuth 로그인 (비밀번호 미보관)
```
① FE → GET /auth/kakao/login/        → 백엔드가 카카오 인가 URL로 302
② 카카오 본인확인 → GET /auth/kakao/callback/?code&state
       · state 검증(CSRF)  · code→토큰 교환  · 유저정보 조회  · UserInfo upsert
       → FRONTEND_URL/auth/callback 로 302 (1회용 세션 키 동반)
③ FE → GET /auth/exchange/           → access 토큰(바디) + refresh(HttpOnly 쿠키) 발급
④ 이후 요청: Authorization: Bearer <access>.  만료 시 /auth/token/refresh 로 자동 갱신
```
- access 30분(메모리) / refresh 7일(HttpOnly 쿠키, 회전+블랙리스트). `secure=not DEBUG`(운영 HTTPS 전용).

### 4-2. 대화 단계 — `POST /chat/` (Stateless)
```
요청 { content, history[] }   ← history는 FE가 관리, 매 요청 전송(서버 무상태)
  → _availability_hint(history)  : 현재 제약의 실제 재고를 SQL로 읽어 주입(라이브 그라운딩)
  → _build_chat_prompt(grounding): 질문을 '쓰는 축'(제품군·제형 enum·가격·고민)에만 묶음
  → _call_gms(reasoning_effort='minimal')   : 대화는 단순 → 추론 최소(빠름)
  → JSON {content, ready} 파싱 (실패 시 raw 텍스트 + ready=false 안전 처리)
응답 { content, ready }
```

### 4-3. 추천 단계 — `POST /recommend/` (하이브리드 파이프라인 ⭐)
```
요청 { history[], filters? }
  ── _recommend_candidates ───────────────────────────────────────
  ① _resolve_constraints : 규칙 추출(가격 _extract_price · 제형 _extract_forms)
                           명시 filters 우선, 빈 축만 발화로 보강, enum/가격역전 검증
  ② base = Product.exclude(ai_summary='')        ← 요약 있는 제품만
  ③ _apply_degradation : 후보 < MIN_POOL(3) 이면 단계적 완화
                           가격 ±PRICE_RELAX → 제형 해제 → 카테고리 해제 (+ relaxed_axes 기록)
  ④ _rank_candidates : 걸러진 후보를 대화 임베딩 CosineDistance 정렬 top 15
                        (임베딩 없거나 실패 시 review_count순 폴백)
  ────────────────────────────────────────────────────────────────
  ⑤ _build_recommend_prompt(candidates) + history → _call_gms
  ⑥ LLM JSON {content, products:[{id, reason}]} 파싱
  ⑦ id를 Product.filter(id__in=...)로 **검증**(환각·오타 제거) → 최대 3개
  ⑧ transaction.atomic: Recommendation(배치) + RecommendedProduct(자식) 저장
응답 { id, content, products:[제품 전체 + reason + meets 배지], constraints(완화 note) }
```
- **하드 제약은 SQL(③④ 전의 ①②), 소프트 취향은 임베딩(④)** → LLM은 조건 위반 제품을 **볼 수조차 없음**("로션 요청에 크림" 구조적 불가).
- 완화가 일어나면 `constraints.note`로 "무엇을 풀었는지" + 제품별 `meets`(✓/✗) 정직하게 표기.

---

## 5. 모델·임베딩

| 용도 | 모델 | 비고 |
|------|------|------|
| 생성(대화·추천) | **gpt-4o** | 모델 5종 실측 비교로 선정(비추론형이 추론형보다 2~3배 빠름). [model-selection-report.md](model-selection-report.md) |
| 임베딩 | **text-embedding-3-small** (1536차원) | 제품 `ai_summary` 백필, 쿼리와 같은 모델이라야 코사인 유효 |

- `reasoning_effort`는 gpt-5/o 계열에만 적용(코드가 비추론 모델엔 자동 미전송). gpt-4o라 현재는 미사용.
- **데이터**: 제품 306종(중복 제거 후), 요약·임베딩 305/306(99.7%), 제형 281종.

---

## 6. 관측·테스트
- **LangSmith**: `@traceable`를 `_call_gms`·`_resolve_constraints`·`_recommend_candidates`에 부착. 미설정 시 no-op([observability.py](../backend/chat/observability.py)).
- **테스트 63개**(accounts·products·chat·board), GMS는 mock으로 빠르고 결정적.
