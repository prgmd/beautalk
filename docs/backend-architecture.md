# Django 백엔드 아키텍처

> **최종 정리본** — 2026-06-23
>
> **Beautalk**: AI 화장품 추천 챗봇 플랫폼
> 
> 사용자의 피부 타입과 고민을 대화로 수집한 후, LLM(GMS API)이 제품 목록에서 최적의 3개를 선택해 추천하는 서비스입니다.
> 
> 이 문서는 전체 백엔드 아키텍처, 각 파트의 작동 원리, 설계 결정사항을 포함합니다.

---

## 🎯 프로젝트 개요

### 핵심 가치
```
사용자 대화 → 피부 정보 수집 → AI 분석 → 개인맞춤 추천
```

### 아키텍처 특징

| 특징 | 설명 |
|------|------|
| **Stateless 챗봇** | 서버가 대화 히스토리를 저장하지 않음. 프론트가 관리해서 매 요청마다 전송 |
| **LLM 직접 호출** | 추천 로직을 DB 쿼리로 구현하지 않고 GMS API(GPT-5-nano)에 위임 |
| **배치 기반 추천** | 1회 추천 = 최대 3개 제품 + AI 생성 이유. 이벤트 로그로 모두 저장 |
| **무상태성** | 각 API 요청이 독립적. 동시성 문제 최소화 |
| **보안 우선** | OAuth + JWT + HttpOnly 쿠키, IDOR 방어, Throttling |

### 설계 철학

```
"복잡한 추천 로직 = LLM에 위임"

전통적 추천 시스템:
  사용자 입력 → 필터링 규칙 작성 → DB 쿼리 → 정렬
  (규칙 수정 시마다 코드 변경)

Beautalk:
  사용자 입력 → 프롬프트 작성 → GMS API 호출 → JSON 파싱 → DB 검증
  (규칙 수정 = 프롬프트 수정만. 코드 변경 최소)
```

---

## ✨ Beautalk만의 설계 특수성

일반적인 AI 추천 서비스와 달리, Beautalk이 차별화된 점들을 정리했습니다.

### 1. 프롬프트 엔지니어링으로 로직 단순화

```
일반적 추천 시스템:
  ├─ 사용자 선호도 학습 (ML 모델)
  ├─ 협력적 필터링 (유사 사용자 찾기)
  ├─ 규칙 추가 시 코드 수정
  └─ 운영 복잡도 높음

Beautalk:
  ├─ LLM에 프롬프트로 규칙 기술
  ├─ 규칙 변경 = 프롬프트 수정만
  ├─ 코드 변경 최소 (배포 불필요)
  └─ 운영 단순화
  
예: "여드름 & 건성 피부에는 순한 토너"
   → 프롬프트에만 작성 (코드 수정 없음)
```

**장점**:
- **빠른 반복**: 프롬프트 수정 → 즉시 반영
- **버전 관리**: 프롬프트 변경 히스토리 추적 가능
- **A/B 테스트**: 다른 프롬프트로 비교 실험 가능

---

### 2. 배치 기반 추천으로 이벤트 로그 구현

```
일반적 추천 시스템:
  └─ "좋아요" 정보만 저장 (Like 테이블)
     └─ "왜" 추천했는지 기록 안 됨

Beautalk:
  ├─ Recommendation (배치)
  │   └─ title = "당신의 피부를 위해..."
  └─ RecommendedProduct (제품 3개)
      ├─ product_id (실제 제품)
      └─ reason (추천 이유)

구조적 특징:
  ├─ 같은 제품이 다른 배치에서 또 추천될 수 있음
  │   └─ UniqueConstraint 없음 (의도적)
  └─ 각 추천 배치의 컨텍스트 완벽 보존
      └─ Phase 2: 추천 피드백 → 알고리즘 개선
```

**장점**:
- **투명성**: 왜 이 제품을 추천했는지 사용자에게 설명 가능
- **분석**: 어떤 추천이 사용자 만족도를 높이는지 분석
- **재학습**: 피드백을 통해 알고리즘 개선

---

### 3. 한글 처리 최적화

```
일반적 JSON 통신:
  POST /api/v1/...
  json={"content": "여드름"}
  └─ requests가 자동으로 \\uXXXX 인코딩 (환각 위험)

Beautalk의 처리:
  payload_json = json.dumps(payload, ensure_ascii=False).encode('utf-8')
  POST /api/v1/...
  data=payload_json
  headers={'Content-Type': 'application/json; charset=utf-8'}
  └─ 한글 "여드름"이 그대로 GMS API에 전달
```

**왜 중요한가?**
- GMS API는 UTF-8을 기대하지만, 잘못된 인코딩 → 400 에러
- 한글 기반 추천 시스템에서는 **필수** (타 영어 서비스에선 간과하기 쉬운 부분)

---

### 4. OAuth 콜백 보안: 토큰 노출 방지

```
일반적 OAuth 콜백:
  GET /auth/callback?access_token=...
  └─ ❌ 토큰이 URL에 노출
      ├─ 브라우저 히스토리 저장
      ├─ 프록시/CDN 로그 기록
      └─ 공유 시 토큰 탈취 위험

Beautalk의 처리:
  1. GET /auth/kakao/callback?code=...&state=...
     └─ 실제 code만 받음
  2. 백엔드에서 code → access_token 교환
  3. 세션에 임시 토큰 저장
  4. 프론트: /api/v1/auth/exchange (세션 토큰)
  5. 백엔드: access를 응답 바디로, refresh를 HttpOnly 쿠키로 반환
     └─ ✅ 토큰이 안전한 채널로만 전달
```

**결과**:
- 토큰이 URL/히스토리에 남지 않음
- refresh는 자동으로 쿠키에 포함 (JavaScript 접근 불가)
- OAuth 콜백 단계에서 최고 수준의 보안 확보

---

### 5. 401 자동 갱신으로 사용자 경험 개선

```
일반적 JWT 처리:
  401 Unauthorized 발생
  └─ 사용자가 수동으로 다시 로그인

Beautalk:
  1. API 요청 → 401 응답
  2. api.js 인터셉터가 자동 감지
  3. POST /api/v1/auth/token/refresh
     └─ 쿠키 자동 포함 (HttpOnly)
  4. 백엔드: 새 access 토큰 발급
  5. api.js: 메모리 업데이트 후 원래 요청 재시도
     └─ ✅ 사용자는 투명하게 경험 (끊김 없음)
```

**결과**:
- 토큰 만료 시에도 "다시 로그인" 화면 안 나타남
- 사용자: "아, 앱 끊겼나?" 없는 경험

---

### 6. 조건부 Throttling으로 개발 편의성 확보

```
일반적 설정:
  DEFAULT_THROTTLE_CLASSES = [AnonRateThrottle, UserRateThrottle]
  └─ 개발 중에도 제약 → 테스트 어려움

Beautalk:
  DEFAULT_THROTTLE_CLASSES = (
    [] if DEBUG else [AnonRateThrottle, UserRateThrottle]
  )
  └─ DEBUG=True: 제약 없음 (개발 쉬움)
  └─ DEBUG=False: 보안 유지 (프로덕션 안전)
```

**결과**:
- 로그인 테스트 10번 → 429 제약 안 생김
- 프로덕션에서도 보안 유지

---

### 7. JSON mode 미지원 극복: 프롬프트 강제

```
일반적 LLM 활용:
  messages=[...],
  response_format={"type": "json_object"}  # OpenAI의 JSON mode
  └─ 깔끔하게 JSON 보장

Beautalk (GMS API):
  └─ JSON mode 미지원
  └─ 프롬프트에 강제 JSON 형식 명시
  
프롬프트 예:
  """
  출력 형식은 반드시 JSON이어야 합니다:
  {
    "content": "...",
    "ready": true
  }
  다른 형식은 허용되지 않습니다.
  """
```

**처리**:
- 정규식이나 휴리스틱이 아닌 명확한 프롬프트
- json.loads()로 파싱 (환각 시 예외 처리)

---

### 8. LLM 환각 방지: 이중 검증

```
문제: GMS API가 존재하지 않는 제품 id 반환 가능
  "이 ID의 제품이 진짜 있나?"

일반적 대응:
  └─ 그냥 신뢰하고 추천

Beautalk의 이중 방어:
  1. 프롬프트 강제
     └─ "반드시 아래 목록의 id만 사용하세요"
  2. DB 검증 (최후의 방어)
     ├─ Product.objects.filter(id__in=[...])
     ├─ LLM이 선택한 id 확인
     ├─ 없는 id는 제외
     └─ 유효한 제품이 0개 → 502 반환 (사용자에게 재시도 요청)
```

**결과**:
- LLM이 아무리 환각해도 DB에 없는 제품 추천 불가
- "추천 실패" vs "틀린 추천" → 전자가 더 안전

---

### 9. Stateless 챗봇으로 멀티탭 동기화

```
일반적 챗봇 (Stateful):
  서버 DB:
    user_id=123 → [message1, message2, ...]
  문제:
    ├─ 탭 1에서 메시지 입력
    ├─ 탭 2에서는 여전히 이전 상태
    └─ 새로고침 필요

Beautalk (Stateless):
  프론트 (localStorage):
    [message1, message2, ...]
  요청:
    POST /api/v1/chat/ (history: [...])
  결과:
    ├─ 탭 1 메시지 입력 → history 업데이트
    ├─ 탭 2도 같은 localStorage 참고 → 자동 동기화
    └─ 새로고침 불필요
```

**장점**:
- 서버 상태 관리 최소화 (확장성 높음)
- 멀티탭 사용자 경험 최적화
- 새로고침 후에도 히스토리 복구 가능 (localStorage)

---

## 📊 전체 아키텍처 다이어그램

```
프론트 (Vue + Pinia)
    ↓
api.js (OAuth 토큰 관리 + 401 자동 갱신)
    ↓
config/urls.py (루트 라우팅)
    ├── accounts/ (인증 & 프로필)
    ├── products/ (제품 & 찜)
    └── chat/ (챗봇 & 추천)
```

---

---

## 🏗️ 전체 데이터 흐름

```
사용자 로그인
    ↓
피부 프로필 입력 (온보딩)
    ↓
챗봇 대화 시작
  ├─ 사용자: "여드름 피부인데 추천해줄 상품?"
  ├─ AI: "어떤 제품을 찾으세요?" (피부 정보 하나씩 수집)
  └─ ready=true → 추천 준비 완료
    ↓
추천 요청
  ├─ 대화 히스토리 전송
  ├─ GMS API가 전체 제품 분석
  ├─ 가장 적합한 3개 선택
  └─ 각각의 추천 이유 생성
    ↓
추천 배치 저장
  ├─ Recommendation (배치)
  └─ RecommendedProduct (3개 제품)
    ↓
사용자에게 표시
  ├─ 제품 카드 (이미지, 가격, AI 요약)
  ├─ 추천 이유 표시
  ├─ 찜하기 가능
  └─ 올리브영 링크 제공
```

---

## 🔐 인증 흐름 (Accounts)

### 왜 OAuth + JWT인가?

```
목표: 사용자 정보 관리 + 보안 + 편의성

선택사항:
1. Session (Cookie) → 서버가 상태 저장 (확장성 낮음)
2. JWT (Stateless) → 서버 상태 최소 (확장성 높음) ✓
3. OAuth (외부 인증) → 회원가입 간소화 ✓

결론: OAuth (가입) + JWT (인증) 조합
```

### 작동 방식

### 1. 로그인 (OAuth) - 작동 방식

```
프론트: LoginView 
  ↓
사용자 클릭 → "카카오로 로그인"
  ↓
프론트 리다이렉트
  GET /api/v1/auth/kakao/login
  → Kakao OAuth 서버로 리다이렉트
  (+ state 파라미터로 CSRF 토큰 생성)
  ↓
사용자가 Kakao에서 인증
  ↓
Kakao → 콜백 URL로 code 반환
  GET /api/v1/auth/kakao/callback?code=...&state=...
  ↓
백엔드 처리:

1. state 검증
   ├── 세션에서 저장된 state 확인
   ├── 일치하지 않으면 401 (CSRF 공격 방어)
   └── 일치하면 진행

2. code → access_token 교환
   └── Kakao OAuth 서버에 code 제출
       → access_token, refresh_token 획득

3. access_token으로 사용자 정보 조회
   ├── Kakao API: GET /v2/user/me
   └── { "id": "123456", "kakao_account": { "email": "..." } }

4. provider_id 기준 사용자 식별
   DB에서 조회:
   ├── UserInfo.objects.get(email='user@example.com')
   ├── 있으면 → 기존 사용자 (로그인)
   └── 없으면 → 새로운 UserInfo 생성 (가입)

5. Django JWT 토큰 발급
   ├── access 토큰 (15분 유효)
   ├── refresh 토큰 (7일 유효)
   └── 세션에 임시 저장

6. 응답
   └── 프론트로 세션 토큰만 반환
       (직접 토큰을 쿼리스트링으로 보내지 않음)
```

**왜 세션 토큰 방식인가?**
```
문제: 토큰을 직접 쿼리스트링으로 반환
  GET /auth/callback?access_token=...
  ├── 브라우저 히스토리에 남음 (보안 위험)
  ├── 프록시/CDN 로그에 기록될 수 있음
  └── URL이 공유될 수 있음

해결: 세션 토큰 + 교환 엔드포인트
  1. OAuth 콜백 → 세션 토큰만 반환
  2. AuthCallbackView에서 /auth/exchange 호출
  3. 백엔드가 실제 토큰 생성 & 반환
  4. 쿠키로 refresh 토큰 설정 (자동 관리)
```

### 2. 토큰 교환 (보안)

```
프론트: AuthCallbackView → /api/v1/auth/exchange (세션 토큰)

백엔드 처리:
├── 세션 토큰 검증
├── access를 응답 바디로 반환
├── refresh를 HttpOnly 쿠키로 설정
└── Secure + SameSite 속성 추가 (프로덕션)

프론트:
├── access를 메모리에만 저장 (XSS 방지)
├── refresh는 쿠키가 자동 관리 (CSRF 불가)
└── 이후 모든 요청에서 Authorization 헤더에 access 포함
```

### 3. 자동 갱신 (401)

```
요청 흐름:
1. 프론트가 API 요청
2. 401 응답 받음
3. api.js의 tryRefresh() 자동 호출
4. POST /api/v1/auth/token/refresh
   └── 쿠키 자동 전송 (HttpOnly)
5. 백엔드가 새 access 토큰 발급
6. 프론트가 메모리 업데이트
7. 원래 요청 재시도
```

### 4. 로그아웃

```
POST /api/v1/auth/logout

백엔드 처리:
├── 현재 refresh 토큰을 OutstandingToken 테이블에 등록
├── BlacklistedToken 추가 (이중 보안)
├── HttpOnly 쿠키 삭제 (Set-Cookie: max-age=0)
└── 그 이후 해당 토큰으로는 refresh 불가

결과:
└── 프론트의 access 메모리 삭제 → 로그인 페이지로 리다이렉트
```

---

## 🛍️ 제품 & 찜 흐름 (Products)

### 제품 목록 조회

```
GET /api/v1/products/?category=스킨케어&page=2

처리:
├── 카테고리 필터 (선택사항)
├── 페이지네이션 (PAGE_SIZE=10)
└── ProductSerializer로 직렬화

응답:
{
  "count": 156,
  "next": "http://localhost:8000/api/v1/products/?page=3",
  "previous": "http://localhost:8000/api/v1/products/?page=1",
  "results": [
    {
      "id": "uuid-...",
      "brand": "닥터지",
      "name": "레드블레미셔",
      "price": 27600,
      "category": "토너",
      "image_url": "...",
      "oliveyoung_url": "...",
      "ai_summary": "...",
      "average_rating": 4.5
    },
    ...
  ]
}
```

### 제품 상세

```
GET /api/v1/products/{uuid}/

응답:
{
  "id": "uuid",
  "brand": "...",
  "name": "...",
  "price": 27600,
  "category": "토너",
  "image_url": "...",
  "oliveyoung_url": "...",
  "ai_summary": "AI가 생성한 제품 요약",
  "average_rating": 4.5,
  "review_count": 120,
  "satisfaction_by_type": {
    "dry": 4.2,
    "oily": 3.8,
    "combination": 4.0,
    "sensitive": 4.3
  },
  "reviews": [
    {
      "id": "uuid",
      "text": "정말 좋아요!",
      "rating": 5,
      "skin_type": "건성",
      "user_name": "익명",
      "recommend_count": 15,
      "review_date": "2026-06-01",
      "created_at": "2026-06-01T10:00:00Z"
    }
  ]
}
```

### 찜 관리

```
1. 내 찜 목록 조회
   GET /api/v1/likes/
   
   응답:
   [
     {
       "id": "uuid",
       "product": { 제품 정보 },
       "created_at": "..."
     }
   ]

2. 찜 추가
   POST /api/v1/likes/
   요청: { "product_id": "uuid" }
   
   백엔드: Like 객체 생성 (unique 제약으로 중복 방지)

3. 찜 해제
   DELETE /api/v1/likes/{product_id}/
   
   백엔드: IDOR 방어 (현재 사용자의 찜만 삭제 가능)
```

---

## 🤖 챗봇 & 추천 흐름 (Chat)

### 1. 대화 (Stateless) - 작동 방식

**왜 Stateless인가?**

```
Stateful (서버가 히스토리 저장):
  요청 1: "안녕"
    ↓ 서버가 DB에 저장
  요청 2: "추천해줘"
    ↓ 서버가 이전 메시지 조회해서 컨텍스트 구성
  
장점: 간단함
단점: 
  ├─ 서버 메모리/DB 부하 증가
  ├─ 사용자별로 상태 관리해야 함
  ├─ 멀티 탭 사용 시 동기화 문제
  └─ 확장성 낮음

Stateless (프론트가 히스토리 관리):
  프론트: [ { role: "user", content: "안녕" }, ... ]
    ↓ 매 요청마다 전체 히스토리 전송
  요청 1: POST /api/v1/chat/ (history: [...])
    ↓ 서버가 받은 history만 사용
  요청 2: POST /api/v1/chat/ (history: [...])
    ↓ 서버가 받은 history만 사용 (이전 요청 불필요)

장점:
  ├─ 서버 상태 최소화 (확장성 높음)
  ├─ 멀티 탭 자동 동기화
  ├─ 히스토리 복구 용이 (localStorage)
  └─ 서버 단순화
단점: 네트워크 대역폭 (매번 전체 히스토리 전송)

Beautalk 선택: Stateless ✓
  이유: 확장성, 사용자 경험, 서버 관리 용이
```

### 대화 요청/응답

```
POST /api/v1/chat/

요청:
{
  "content": "여드름에 좋은 토너 추천해줘",
  "history": [
    { "role": "assistant", "content": "안녕하세요! Beautalk입니다." },
    { "role": "user", "content": "피부 타입을 알려주시겠어요?" }
  ]
}

백엔드 처리:

1. _build_chat_prompt() 생성
   ├── UserInfo.skinprofile 조회
   │   └── 없으면 "미입력 (일반 추천으로 대응)" 처리
   ├── 시스템 프롬프트 생성
   │   ├── "당신은 화장품 추천 AI 'Beautalk'입니다"
   │   ├── 사용자 피부 정보
   │   ├── 취급 제품군 (카테고리)
   │   └── 대화 규칙 (2문장 이내, 한 번에 한 가지만)
   └── JSON 포맷 강제

2. GMS API 호출
   POST https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions
   └── 모델: gpt-5-nano
   └── 타임아웃: 60초

3. JSON 파싱
   ├── content: 챗봇 답변
   └── ready: 추천 준비 완료 여부

응답:
{
  "content": "피부 타입이 건성이시군요. 지금까지 얘기해주신 내용을 바탕으로...",
  "ready": false
}
```

**특징**:
- **Stateless** — 서버가 대화 히스토리 저장 안 함
- 프론트가 `history[]` 전체를 매 요청마다 전송
- 프롬프트로 JSON 포맷 강제 (JSON mode 미지원)
- UTF-8 명시 필수 (한글 처리)

---

### 2. 추천 배치 생성

```
POST /api/v1/recommend/

요청:
{
  "history": [
    { "role": "assistant", "content": "..." },
    { "role": "user", "content": "..." }
  ]
}

백엔드 처리:

1. _build_recommend_prompt() 생성
   ├── 사용자 피부 프로필
   ├── 추천 가능한 제품 목록 (156개)
   │   └── id + brand + name + category + ai_summary
   ├── 규칙
   │   ├── "정확히 3개를 고르세요"
   │   ├── "목록에 없는 제품을 지어내지 마세요"
   │   └── "각 제품마다 추천 이유를 작성하세요"
   └── JSON 포맷 강제

2. GMS API 호출
   └── 동일한 엔드포인트, 동일한 모델

3. 응답 파싱
   {
     "content": "당신의 피부 타입과 고민을 고려하면...",
     "products": [
       { "id": "uuid-...", "reason": "피부 진정에 효과적" },
       { "id": "uuid-...", "reason": "보습력이 우수함" },
       { "id": "uuid-...", "reason": "자극 없는 공식" }
     ]
   }

4. DB 검증 (환각 제거)
   ├── 각 product id를 DB에서 확인
   ├── 일치하는 제품만 유지
   ├── LLM 선택 순서 보존
   ├── 중복 제거
   └── 유효한 제품이 0개면 502 반환

5. Recommendation 배치 생성
   └── transaction.atomic()으로 데이터 무결성 보장
   ├── Recommendation 생성 (title = content)
   └── RecommendedProduct 3개 일괄 생성 (bulk_create)

응답:
{
  "id": "batch-uuid",
  "content": "당신의 피부 타입과 고민을 고려하면...",
  "created_at": "2026-06-23T10:00:00Z",
  "products": [
    {
      "id": "uuid-...",
      "brand": "닥터지",
      "name": "레드블레미셔",
      "price": 27600,
      "category": "토너",
      "image_url": "...",
      "reason": "피부 진정에 효과적"
    },
    ...
  ]
}
```

---

### 3. 추천 히스토리

```
GET /api/v1/recommendations/

응답:
[
  {
    "id": "batch-uuid-1",
    "content": "당신의 피부 상태를 고려하면...",
    "created_at": "2026-06-23T10:00:00Z",
    "products": [ ... ]
  },
  {
    "id": "batch-uuid-2",
    "content": "건조한 피부를 위해 추천하는...",
    "created_at": "2026-06-22T15:30:00Z",
    "products": [ ... ]
  }
]

정렬: 최신순 (created_at DESC)
페이지네이션: PAGE_SIZE=10 (설정 가능)
```

---

## 📡 GMS API 통신

### 왜 LLM을 직접 호출하는가?

```
전통적 추천 시스템:
  카테고리 매칭 + 별점 + 리뷰 감정분석 + 규칙 기반 필터링
  
  문제점:
  ├─ 새로운 규칙 추가 → 코드 수정 필수
  ├─ 사용자 선호 변화 → 규칙 업데이트 어려움
  ├─ 컨텍스트 이해 부족 (예: "자극 없는" vs "보습력 좋은" 차이)
  └─ 추천 다양성 낮음

LLM 기반 추천 (Beautalk):
  사용자 대화 → 피부 정보 수집 → GMS API → 제품 목록 분석 → 3개 선택
  
  장점:
  ├─ 자연어 이해 (사용자 의도 파악)
  ├─ 유연한 규칙 (프롬프트 수정만으로 동작 변경)
  ├─ 개인맞춤성 높음 (대화 컨텍스트 활용)
  ├─ 확장성 (새 제품 자동 학습)
  └─ 추천 이유 설명 가능 (투명성)
  
  단점:
  ├─ 비용 (API 호출료)
  ├─ 응답 지연 (3~5초)
  ├─ 환각 가능성 (존재하지 않는 제품 추천)
  └─ 일관성 (같은 입력 ≠ 같은 출력)

Beautalk 대응:
  ├─ 환각 방지: DB 검증 (LLM이 선택한 id만 DB에서 확인)
  ├─ 속도 최적화: 타임아웃 60초, 비동기 처리
  └─ 비용 관리: Throttling (100 요청/day)
```

### 요청 형식

```python
payload = {
  "model": "gpt-5-nano",
  "messages": [
    {
      "role": "system",
      "content": "당신은 Beautalk AI입니다..."
    },
    {
      "role": "user",
      "content": "여드름에 좋은 토너는?"
    }
  ]
}

# UTF-8 명시적 인코딩
payload_json = json.dumps(payload, ensure_ascii=False).encode('utf-8')

# 요청
response = requests.post(
  GMS_API_URL,
  headers={
    'Authorization': f'Bearer {GMS_API_KEY}',
    'Content-Type': 'application/json; charset=utf-8',
  },
  data=payload_json,
  timeout=60,  # 긴 프롬프트 처리 고려
)
```

### 응답 형식

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1782117668,
  "model": "gpt-5-nano-2025-08-07",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "{\"content\": \"...\", \"ready\": true}"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 500,
    "completion_tokens": 200,
    "total_tokens": 700
  }
}
```

### 특징

- **Stateless** — 서버가 히스토리 추적 안 함
- **JSON mode 미지원** — 프롬프트로 강제 JSON 생성
- **UTF-8 필수** — 한글 처리를 위해 명시적 인코딩
- **타임아웃: 60초** — 긴 프롬프트(156개 제품) 처리 고려
- **에러 처리**:
  - 400 Bad Request → UTF-8 인코딩, Content-Type 확인
  - 504 Gateway Timeout → 타임아웃 증가
  - 429 Rate Limited → 백엔드 사용량 제한

### 프롬프트 엔지니어링

**Chat 단계 프롬프트**

```python
_build_chat_prompt():
  ├─ 역할 정의: "당신은 화장품 추천 AI 'Beautalk'입니다"
  ├─ 사용자 피부 정보: SkinProfile 데이터 (타입, 고민, 기피 성분)
  ├─ 제품 카테고리: 현재 DB의 모든 카테고리 (스킨케어, 클렌저 등)
  ├─ 행동 규칙:
  │   ├─ "최대 2문장으로 짧게"
  │   ├─ "한 번에 한 가지만 물어보기" (정보 수집)
  │   ├─ "제품 직접 나열하지 말기" (추천은 다음 단계)
  │   └─ "한국어로만 답변"
  ├─ 출력 형식: JSON { "content": "...", "ready": true/false }
  └─ ready 기준: 추천을 의미 있게 할 정보가 충분한가?
```

**Recommend 단계 프롬프트**

```python
_build_recommend_prompt():
  ├─ 역할 정의: "당신은 화장품 추천 AI 'Beautalk'입니다"
  ├─ 사용자 피부 정보: SkinProfile (Chat에서 수집한 데이터)
  ├─ 제품 목록: 
  │   ├─ ID (정확히 3개 선택 시 DB 검증용)
  │   ├─ 브랜드, 이름
  │   ├─ 카테고리
  │   └─ ai_summary (크롤링 시 Gemini로 생성한 요약)
  ├─ 규칙:
  │   ├─ "반드시 위 목록에 있는 id만 사용하세요"
  │   ├─ "정확히 3개를 고르세요" (상한선)
  │   ├─ "각 제품마다 추천 이유 작성"
  │   └─ "지어낸 제품 금지" (환각 방지)
  ├─ 출력 형식: JSON { "content": "...", "products": [{...}] }
  └─ 목표: LLM이 선택한 id는 반드시 DB에 존재해야 함
```

**프롬프트 설계의 핵심**

```
1. 정확성 (Accuracy)
   └─ id 기반 선택 → DB 검증으로 환각 제거

2. 일관성 (Consistency)
   └─ 같은 형식의 응답 강제 (JSON 구조)

3. 안전성 (Safety)
   ├─ "지어낸 제품 금지" 명시
   ├─ "목록에 없는 id는 무효"
   └─ DB 검증 (최후의 방어)

4. 효율성 (Efficiency)
   ├─ 제품 전체 목록 제시 (LLM이 모두 볼 수 있도록)
   ├─ ai_summary 포함 (제품 정보 풍부)
   └─ 3개 제한 (토큰 절약 + 사용자 선택 제한)
```

**트러블슈팅**

```
문제: GMS API가 400 Bad Request 반환
원인: 한글 프롬프트 UTF-8 인코딩 미흡

해결:
  ├─ json.dumps(payload, ensure_ascii=False)
  │   └─ ensure_ascii=False: 한글을 그대로 두기 (기본은 \\uXXXX로 인코딩)
  ├─ .encode('utf-8')
  │   └─ 바이트 문자열로 명시적 변환
  └─ Content-Type: 'application/json; charset=utf-8'
      └─ 헤더에 인코딩 명시
```

---

## 💾 DB 설계 철학

### 왜 이 스키마인가?

```
1. Recommendation (배치) ↔ RecommendedProduct (제품)

설계 선택: 1:N 관계 (배치 1개 당 최대 3개 제품)

이유:
├─ 추천의 컨텍스트 유지
│   └─ "언제" "왜" "어떤 이유"로 추천했는지 기록
├─ 그룹핑
│   └─ 사용자가 "지난 주 추천받은 상품"으로 조회 가능
├─ 히스토리 관리
│   └─ 같은 제품이 다른 배치에서 또 추천될 수 있음 (이벤트 로그)
└─ 분석 및 피드백
    └─ 어떤 추천에 만족했는지 추적 가능 (Phase 2: Feedback 모델)

다른 방식과의 비교:

❌ 추천 기록 없이 제품만 저장
  └─ 추천 이유 사라짐, 히스토리 불명확

✓ Recommendation + RecommendedProduct
  └─ 배치 단위로 컨텍스트 유지, 확장성 높음
```

```
2. SkinProfile (1:1 관계, UserInfo당 1개)

선택: OneToOneField
이유:
├─ 사용자당 정확히 1개의 피부 프로필 (중복 방지)
├─ 선택사항 (null 허용하지 않는 것이 설계 의도)
└─ 성능 (JOIN 1번으로 모든 정보 조회)

nullable 선택지:
├─ null=True: 프로필 미입력 사용자도 서비스 이용
│            (현재 방식 - _skin_block에서 "미입력" 처리)
├─ null=False: 프로필 입력 필수 (온보딩 강제)
└─ Beautalk 선택: null=True (높은 접근성)
```

```
3. Like + InUseProduct (같은 구조, 다른 의미)

Like:
├─ 사용자가 "찜한" 제품
├─ 관심 표시, 나중에 구매할 의향
└─ 추천과는 독립적

InUseProduct:
├─ 사용자가 "현재 사용 중인" 제품
├─ 피부 상태 기록 (향후 추천 참고)
└─ Phase 2: 사용 경험 기반 추천 개선

구조:
  Like(user, product) + unique 제약
  └─ 같은 제품을 여러 번 찜할 수 없음 (버튼 토글)
  
  InUseProduct(user, product) + unique 제약
  └─ 같은 제품을 여러 번 "사용 중"으로 표시 불가
```

---

## 💾 DB 구조

### Accounts

```python
class UserInfo(models.Model):
    id = UUIDField(PK)
    user = OneToOneField(Django User)  # user_id 자동 생성
    email = EmailField(unique=True)
    auth_provider = CharField(['kakao', 'google'])
    created_at = DateTimeField(auto_now_add=True)

class SkinProfile(models.Model):
    user = OneToOneField(UserInfo)
    skin_type = CharField(['dry', 'oily', 'combination', 'sensitive'])
    concerns = JSONField()  # ["여드름", "주름"]
    avoid_ingredients = JSONField()
    updated_at = DateTimeField(auto_now=True)
```

### Products

```python
class Product(models.Model):
    id = UUIDField(PK)
    brand = CharField(100)
    name = CharField(100)
    price = IntegerField()
    oliveyoung_url = URLField()
    image_url = URLField()
    category = CharField(50)
    ai_summary = TextField()  # Gemini로 생성
    average_rating = FloatField(nullable)
    review_count = IntegerField()
    satisfaction_by_type = JSONField()  # {"dry": 4.2, "oily": 3.8, ...}

class Review(models.Model):
    product = ForeignKey(Product, CASCADE)
    text = TextField()
    rating = IntegerField()
    skin_type = CharField(50, blank=True)
    user_name = CharField(100, blank=True)
    recommend_count = IntegerField()
    review_date = CharField(50, blank=True)  # "2026-06-22" 형식
    created_at = DateTimeField(auto_now_add=True)

class Like(models.Model):
    user = ForeignKey(UserInfo, CASCADE)
    product = ForeignKey(Product, CASCADE)
    created_at = DateTimeField(auto_now_add=True)
    # Constraint: unique(user, product)

class InUseProduct(models.Model):
    user = ForeignKey(UserInfo, CASCADE)
    product = ForeignKey(Product, CASCADE)
    created_at = DateTimeField(auto_now_add=True)
    # Constraint: unique(user, product)
```

### Chat

```python
class Recommendation(models.Model):
    id = UUIDField(PK)
    user = ForeignKey(UserInfo, CASCADE)
    title = TextField()  # 배치 요약 (LLM 생성)
    created_at = DateTimeField(auto_now_add=True)

class RecommendedProduct(models.Model):
    id = UUIDField(PK)
    recommendation = ForeignKey(Recommendation, CASCADE, related_name='products')
    product = ForeignKey(Product, CASCADE)
    reason = TextField()  # "피부 진정에 효과적"
    created_at = DateTimeField(auto_now_add=True)
    # 같은 제품이 다른 배치에서 또 추천될 수 있음 (이벤트 로그)
```

---

## 🛡️ 보안 & 제약

### 보안 설계 철학

```
목표: "프라이빗 데이터 보호 + 악의적 접근 차단"

계층별 방어:

1. 전송 계층 (HTTPS)
   └─ 중간자 공격 방지

2. 인증 계층 (OAuth + JWT)
   ├─ 누가인지 확인 (Are you who you claim to be?)
   └─ state 파라미터로 CSRF 방지

3. 인가 계층 (Permission + IDOR)
   ├─ 무엇을 할 수 있는지 확인 (What can you do?)
   └─ 다른 사용자 데이터 접근 차단

4. 데이터 계층 (암호화, SQL Injection 방지)
   └─ DB 쿼리 안전성

5. API 계층 (Rate Limiting, Input Validation)
   ├─ DoS 방지
   └─ 악의적 입력 차단
```

### 인증 & 인가

```
인증 (Authentication):
├── OAuth (Kakao, Google)
│   ├── state 파라미터로 CSRF 방어
│   └── code ↔ access_token 교환
├── JWT (SIMPLE_JWT)
│   ├── access 토큰: 15분 유효
│   ├── refresh 토큰: 7일 유효
│   └── 자동 갱신 (401 시)
└── 토큰 블랙리스트 (로그아웃 시)

인가 (Authorization):
├── IsAuthenticated (대부분의 API)
├── IDOR 방어 (찜, 계정)
│   └── DELETE /api/v1/likes/{product_id}/
│       ├── 현재 사용자 확인
│       └── 다른 사용자의 찜은 삭제 불가
└── ScopedRateThrottle (Phase 2 계획)
    └── /chat, /recommend에 별도 제한
```

### 사용량 제한 (Throttling)

```
설정:
├── 비인증 사용자: 20 요청/시간
├── 인증 사용자: 100 요청/일
└── DEBUG=True: 무제한 (개발 환경)

적용 대상:
├── 모든 APIView
├── GMS API 호출 (비용 발생)
└── OAuth 콜백 (brute force 방어)

제약 초과 시:
└── 429 Too Many Requests
    ├── Retry-After 헤더로 대기 시간 전달
    └── 프론트의 PaywallModal 표시
```

### 토큰 보안

```
Access Token (메모리):
├── 메모리에만 저장 (XSS 방지)
├── Authorization: Bearer <token> 헤더로 전송
└── 매 요청마다 포함

Refresh Token (HttpOnly 쿠키):
├── HttpOnly 속성으로 JavaScript 접근 불가
├── Secure 속성으로 HTTPS만 전송 (프로덕션)
├── SameSite=Lax으로 CSRF 방어
└── 자동으로 모든 요청에 포함 (credentials: 'include')

결과:
└── XSS 공격 → access 탈취 불가 (쿠키는 JS에서 보이지 않음)
└── CSRF 공격 → 쿠키는 SameSite로 방어, access는 Bearer로 방어
```

---

## 🔄 요청 흐름 예시

### 추천 요청 전체 흐름

```
1️⃣ 프론트 API 호출
   const response = await api.post('/api/v1/recommend/', {
     history: [...]
   })
   └── Authorization 헤더: "Bearer {accessToken}"
   └── Cookie: "refresh={refreshToken}"

2️⃣ Django 미들웨어 처리
   ├── CORSMiddleware (CORS 허용)
   ├── SessionMiddleware (세션 로드)
   ├── AuthenticationMiddleware
   └── JWTAuthentication (access 토큰 검증)

3️⃣ URL 라우팅
   config/urls.py
   ├── accounts/ 경로 확인 → ❌
   ├── products/ 경로 확인 → ❌
   └── chat/ 경로 확인 → ✓
       └── chat/urls.py
           └── POST /api/v1/recommend/ → RecommendView.post()

4️⃣ RecommendView.post() 실행
   ├── request.user 확인 (IsAuthenticated 권한)
   │   └── 없으면 401 반환
   ├── _clean_history(request.data['history'])
   │   └── role='user'/'assistant', content 있는 항목만 필터
   ├── _build_recommend_prompt(request.user)
   │   ├── SkinProfile 조회
   │   ├── Product 목록 조회 (ai_summary != '')
   │   └── 긴 프롬프트 생성
   ├── _call_gms(messages)
   │   ├── JSON 인코딩 (UTF-8)
   │   ├── GMS API POST (timeout=60)
   │   ├── 응답 파싱
   │   └── 에러 처리
   ├── JSON 파싱 & 검증
   │   ├── content, products 추출
   │   └── 예상외 형식 → 502 반환
   ├── DB 검증
   │   ├── 각 product_id 확인
   │   ├── 유효한 것만 유지
   │   └── 0개 → 502 반환
   ├── transaction.atomic()로 저장
   │   ├── Recommendation 생성
   │   └── RecommendedProduct bulk_create
   └── RecommendationSerializer 직렬화
       └── 응답 생성

5️⃣ 응답 전송
   {
     "id": "uuid",
     "content": "...",
     "created_at": "...",
     "products": [...]
   }
   └── 상태 코드: 201 Created

6️⃣ 프론트 처리
   ├── 응답 데이터 저장 (Pinia store)
   ├── 추천 카드 렌더링
   └── 찜하기, 올리브영 이동 등 기능 활성화
```

---

## ⚡ 성능 & 확장성

### Stateless의 이점

```
확장성 문제:
  Stateful (서버가 상태 저장)
    └─ 사용자 A의 세션이 서버 1에 저장됨
    └─ 로드 밸런싱 시 서버 2로 요청 → 세션 손실
    └─ 세션 DB 필요 (Redis, Memcached)
    └─ 복잡도 증가

Stateless (클라이언트가 상태 관리)
    ├─ 매 요청에 모든 필요한 정보 포함
    ├─ 어떤 서버든 처리 가능 (수평 확장 용이)
    ├─ 세션 동기화 불필요
    └─ 서버 부하 최소화
```

### 성능 최적화

```
1. API 설계
   ├─ 페이지네이션 (PAGE_SIZE=10)
   │   └─ 전체 156개 제품을 한 번에 로드하지 않음
   ├─ 선택적 필터 (?category=)
   │   └─ DB 쿼리 최소화
   └─ 중첩 Serializer
       └─ N+1 쿼리 문제 해결 (prefetch_related 사용)

2. GMS API
   ├─ 타임아웃 최적화 (60초)
   │   └─ 긴 프롬프트 처리 고려
   ├─ JSON 파싱 최소화
   │   └─ 정규식 대신 json.loads() 사용
   └─ 에러 처리 (fast-fail)
       └─ 잘못된 응답은 빨리 중단

3. DB 쿼리
   ├─ select_related (1:1 관계: UserInfo → User)
   ├─ prefetch_related (1:N 관계: Recommendation → RecommendedProduct)
   └─ 인덱스 (category, created_at 등)
```

### 확장 전략

```
현재 (Phase 1):
  ├─ SQLite (개발 용)
  ├─ Django 단일 서버
  └─ GMS API (비용: 연 수백만원)

Phase 2 (규모 확대):
  ├─ PostgreSQL (동시성, 트랜잭션)
  ├─ Redis (캐시, 세션)
  ├─ Celery (비동기 작업)
  │   └─ 긴 작업(크롤링, 임베딩)을 백그라운드에서 처리
  ├─ 로드 밸런싱 (Nginx)
  │   └─ 여러 서버로 분산
  └─ CDN (이미지 캐싱)

Phase 3 (RAG 도입):
  ├─ 벡터 DB (pgvector, Pinecone)
  ├─ 임베딩 모델 (OpenAI embeddings)
  └─ 추천 알고리즘 전환
      ├─ LLM 요약 → 임베딩 → 유사도 검색
      └─ 더 빠르고 정확한 추천
```

---

## 🚀 향후 개선 (Phase 2)

```
1. RAG 도입 (벡터 기반 추천)
   ├── 채팅 내역 → LLM 요약 → 임베딩
   ├── 벡터 DB (pgvector, Pinecone, ...)
   └── 유사도 기반 상위 3개 추천

2. 특화 엔드포인트 제한
   ├── /chat, /recommend에 ScopedRateThrottle
   └── GMS API 비용 관리

3. 채팅 히스토리 저장
   ├── ChatMessage 모델 추가
   ├── 새로고침 후 복구
   └── 분석용 데이터 수집

4. 기피 성분 필터링
   ├── ProductIngredient 모델
   ├── SkinProfile.avoid_ingredients와 매칭
   └── 추천에서 자동 제외

5. 피드백 수집
   ├── Feedback 모델
   ├── 추천에 대한 만족도 기록
   └── 알고리즘 개선 데이터
```

---

## 📝 환경 변수 설정

```env
# Django
DJANGO_SECRET_KEY=...
DEBUG=True  # 개발 환경

# OAuth
KAKAO_CLIENT_ID=...
KAKAO_CLIENT_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# GMS API
GMS_API_KEY=...
GMS_API_URL=https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions
GMS_MODEL=gpt-5-nano
```

---

## 🔧 개발 팁

```bash
# DB 초기화
python manage.py flush  # 모든 데이터 삭제

# 마이그레이션
python manage.py makemigrations
python manage.py migrate

# 개발 서버
python manage.py runserver 8000

# 셸에서 테스트
python manage.py shell
>>> from accounts.models import UserInfo
>>> UserInfo.objects.all()
```

---

## 🔍 실제 작동 사례

### 사용자 여정 (전체 흐름)

**Step 1: 로그인**
```
사용자 클릭 → "카카오로 로그인"
  ↓
state 생성 + 세션 저장
  ↓
Kakao OAuth 리다이렉트
  ↓
사용자가 Kakao에서 인증 (비밀번호 입력)
  ↓
콜백: GET /api/v1/auth/kakao/callback?code=...&state=...
  ↓
백엔드:
  ├─ state 검증
  ├─ code → access_token 교환
  ├─ 사용자 정보 조회
  ├─ UserInfo 생성 (또는 기존 조회)
  ├─ JWT 토큰 발급
  └─ 세션 토큰 반환
  ↓
프론트: AuthCallbackView → /api/v1/auth/exchange
  └─ access를 메모리에, refresh를 쿠키에 저장
```

**Step 2: 온보딩**
```
사용자 입력:
  ├─ 피부 타입: 건성
  ├─ 고민: ["여드름", "주름"]
  └─ 기피 성분: ["alcohol"]
  ↓
POST /api/v1/profile/
  ├─ JSONField 검증 (concerns, avoid_ingredients)
  ├─ SkinProfile 생성
  └─ 응답: 201 Created
  ↓
프론트: ChatView로 이동
```

**Step 3: 대화**
```
사용자 1: "여드름 피부인데 추천해줄 상품?"
  ↓
POST /api/v1/chat/
  요청:
  {
    "content": "여드름 피부인데 추천해줄 상품?",
    "history": []
  }
  
  백엔드:
  ├─ _build_chat_prompt() → "당신은 Beautalk AI입니다..."
  ├─ GMS API 호출
  ├─ 응답: {"content": "어떤 제품을 찾으세요?", "ready": false}
  └─ 응답: 200 OK
  
  AI: "어떤 제품을 찾으세요? (토너/에센스/크림 등)"
  ↓
사용자 2: "토너 추천해줘"
  ↓
POST /api/v1/chat/
  요청:
  {
    "content": "토너 추천해줘",
    "history": [
      {"role": "assistant", "content": "어떤 제품을..."},
      {"role": "user", "content": "여드름 피부인데..."}
    ]
  }
  
  백엔드:
  ├─ history 정제 (role & content 검증)
  ├─ 사용자 피부 정보 로드
  ├─ GMS API 호출
  ├─ 응답: {"content": "...추천이 가능합니다", "ready": true}
  └─ 응답: 200 OK
  
  AI: "충분한 정보를 수집했습니다. 추천하겠습니다."
  ↓
프론트: "추천하기" 버튼 활성화 (ready=true이므로)
```

**Step 4: 추천**
```
사용자 클릭: "추천하기"
  ↓
POST /api/v1/recommend/
  요청:
  {
    "history": [
      {"role": "assistant", "content": "어떤 제품..."},
      {"role": "user", "content": "여드름..."},
      {"role": "assistant", "content": "...추천이 가능합니다"},
      {"role": "user", "content": "토너"}
    ]
  }
  
  백엔드:
  ├─ _build_recommend_prompt()
  │   ├─ 피부 정보: "건성, 여드름 고민"
  │   ├─ 제품 목록: 156개 (id, name, category, ai_summary)
  │   └─ 규칙: "정확히 3개, 목록의 id만 사용"
  ├─ GMS API 호출 (타임아웃 60초)
  ├─ 응답:
  │   {
  │     "content": "당신의 피부를 위해...",
  │     "products": [
  │       {"id": "uuid-1", "reason": "여드름 진정"},
  │       {"id": "uuid-2", "reason": "보습 효과"},
  │       {"id": "uuid-3", "reason": "자극 없음"}
  │     ]
  │   }
  ├─ DB 검증
  │   └─ 각 id가 실제로 존재하는가? → 3개 모두 유효
  ├─ Transaction 시작
  │   ├─ Recommendation 생성 (title = content)
  │   └─ RecommendedProduct 3개 bulk_create
  ├─ Transaction 커밋
  └─ RecommendationSerializer 응답
  
  응답:
  {
    "id": "batch-uuid",
    "content": "당신의 피부를 위해...",
    "created_at": "2026-06-23T10:00:00Z",
    "products": [
      {
        "id": "product-uuid-1",
        "brand": "닥터지",
        "name": "레드블레미셔",
        "price": 27600,
        "image_url": "...",
        "reason": "여드름 진정에 효과적"
      },
      ...
    ]
  }
  ↓
프론트: 추천 카드 렌더링
  ├─ 이미지 + 가격 표시
  ├─ 추천 이유 표시
  ├─ 찜하기 버튼
  └─ "올리브영에서 보기" 링크
```

---

## 🐛 트러블슈팅 가이드

### 문제 1: GMS API 400 Bad Request

**증상**: 추천 요청 시 400 에러

**원인**: 한글 프롬프트 UTF-8 인코딩 실패

**해결**:
```python
# ❌ 잘못된 방식
res = requests.post(..., json=payload)  # requests가 자동 인코딩

# ✓ 올바른 방식
payload_json = json.dumps(payload, ensure_ascii=False).encode('utf-8')
res = requests.post(
    ..., 
    data=payload_json,
    headers={'Content-Type': 'application/json; charset=utf-8'}
)
```

### 문제 2: GMS API 504 Timeout

**증상**: 요청이 30초 이상 걸림

**원인**: 프롬프트가 길어서 처리 시간 초과 (156개 제품 나열)

**해결**:
```python
# 타임아웃 증가
res = requests.post(..., timeout=60)

# 또는 프롬프트 최적화
_build_recommend_prompt():
  ├─ ai_summary 길이 제한 ([:200])
  ├─ 제품 개수 제한 ([:50])
  └─ 불필요한 정보 제거
```

### 문제 3: LLM 환각 (존재하지 않는 제품)

**증상**: "제품 id가 DB에 없음" 에러

**원인**: GMS API가 존재하지 않는 id를 반환

**방어**:
```python
# 1. DB 검증
product_map = {str(prod.id): prod for prod in Product.objects.filter(...)}
matched = [(product_map[pid], reason) for pid, reason in id_to_reason.items() if pid in product_map]

# 2. 유효한 제품이 0개면 502 반환 (사용자에게 "다시 시도" 요청)
if not matched:
    return Response({'error': '...'}, status=HTTP_502_BAD_GATEWAY)
```

### 문제 4: Throttling 제약

**증상**: "429 Too Many Requests"

**원인**: 사용량 초과 (비인증: 20/h, 인증: 100/d)

**해결** (개발 환경):
```python
# settings.py
'DEFAULT_THROTTLE_CLASSES': (
    [] if DEBUG else [  # DEBUG=True면 비활성화
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ]
),
```

### 문제 5: IDOR (다른 사용자 데이터 접근)

**증상**: 다른 사용자의 찜을 삭제할 수 있음

**방어**:
```python
# DELETE /api/v1/likes/{product_id}/
like = Like.objects.get(product_id=product_id, user=request.user.userinfo)
# 현재 사용자의 찜만 조회 → 다른 사용자의 찜은 404
like.delete()
```

---

## 📚 추가 자료

- **설계 문서**: docs/chat-recommend-plan.md
- **프로젝트 구조**: docs/structure.md
- **진행 현황**: docs/progress.md
- **코드 리뷰**: docs/review-findings.md

---

**최종 수정**: 2026-06-23

**작성자**: Beautalk 팀

**라이센스**: MIT
