# Beautalk 서비스 취약점 분석 및 RAG 도입 계획

## 1. 현재 서비스 취약점

### 1-1. 백엔드 (Django)

---

#### [Critical] SECRET_KEY 하드코딩
**위치:** [config/settings.py:27](../backend/config/settings.py#L27)

```python
SECRET_KEY = 'django-insecure-k#7o(uz1nc^xr04)ks@g8$uq7)#vwe+9$td)iwygji+_u=&*i3'
```

`.env` 로드 로직이 이미 있음에도 SECRET_KEY는 코드에 하드코딩되어 있다. SECRET_KEY가 노출되면 Django 서명 기반 보안(세션, CSRF 토큰, JWT 서명 등) 전체가 무력화된다.

**수정 방향:** `SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')`

---

#### [Critical] JWT 토큰을 URL 쿼리스트링으로 전달
**위치:** [accounts/views.py:135-138](../backend/accounts/views.py#L135) / [views.py:177-180](../backend/accounts/views.py#L177)

```python
return redirect(
    f'http://localhost:5173/auth/callback'
    f'?access={str(refresh.access_token)}'
    f'&refresh={str(refresh)}'
)
```

OAuth 콜백 후 JWT access + refresh 토큰 둘 다를 URL 쿼리스트링으로 프론트엔드에 전달한다. 이 토큰은 브라우저 히스토리, Nginx/서버 액세스 로그, HTTP Referrer 헤더에 평문으로 기록되어 토큰 탈취로 이어질 수 있다.

**수정 방향:** 임시 일회용 코드(short-lived code)를 URL에 담고, 프론트엔드가 해당 코드를 백엔드에 POST로 교환하는 방식으로 전환. 또는 HttpOnly 쿠키 사용.

---

#### [Critical] OAuth CSRF 방어 누락 (state 파라미터 없음)
**위치:** [accounts/views.py:60-66](../backend/accounts/views.py#L60) / [views.py:73-80](../backend/accounts/views.py#L73)

카카오, 구글 OAuth 요청 URL에 `state` 파라미터가 없다. 공격자가 자신의 OAuth 인가 코드를 피해자의 브라우저에서 사용하게 만드는 OAuth CSRF 공격이 가능하다. 예를 들어 공격자가 자신의 계정으로 시작한 OAuth 흐름의 콜백 URL을 피해자가 열도록 유도하면, 피해자 세션에 공격자 계정이 연결된다.

**수정 방향:** 로그인 시작 시 서버에서 random state를 생성해 세션에 저장하고, 콜백에서 비교 검증.

---

#### [High] 이메일 중복 시 계정 탈취 버그
**위치:** [accounts/views.py:116-120](../backend/accounts/views.py#L116)

```python
django_user, _ = User.objects.get_or_create(username=f'kakao_{kakao_id}')
user_info, _ = UserInfo.objects.get_or_create(
    email=email,
    defaults={'user': django_user, 'auth_provider': 'kakao'}
)
```

이미 구글로 가입한 이메일과 동일한 이메일을 가진 카카오 계정으로 로그인하면:
- `django_user`는 새로 만들어진 카카오 유저
- `user_info`는 기존 구글 유저가 반환됨 (`get_or_create`에서 이미 존재하므로)
- JWT는 새 `django_user` 기준으로 발급되나, SkinProfile 등 데이터는 `user_info`(구글 유저)에 연결되어 있음

결과적으로 인증 주체와 데이터 소유자가 불일치하여 다른 사용자 데이터에 접근하는 버그가 발생한다. 구글의 경우도 동일한 패턴이다.

**수정 방향:** `UserInfo`를 email이 아닌 `auth_provider + provider_id` 조합으로 식별하거나, 이메일 중복 시 명시적 오류 반환.

---

#### [High] DEBUG=True, ALLOWED_HOSTS 미설정
**위치:** [config/settings.py:29](../backend/config/settings.py#L29), [settings.py:32](../backend/config/settings.py#L32)

```python
DEBUG = True
ALLOWED_HOSTS = []
```

프로덕션 배포 시 `DEBUG=True`이면 500 에러 발생 시 스택 트레이스, 로컬 변수, 설정값이 브라우저에 그대로 출력된다. `ALLOWED_HOSTS = []`는 Django 개발 서버에서는 모든 호스트를 허용하는 기본 동작을 한다.

**수정 방향:** 환경변수로 분기 처리, 프로덕션에서 `DEBUG=False` + `ALLOWED_HOSTS=['yourdomain.com']` 명시.

---

#### [High] Refresh Token을 localStorage에 저장
**위치:** [frontend/src/stores/auth.js:5](../frontend/src/stores/auth.js#L5), [auth.js:12](../frontend/src/stores/auth.js#L12)

```js
const user = ref(JSON.parse(localStorage.getItem('bt_user') || 'null'))
// ...
localStorage.setItem('bt_user', JSON.stringify(userData))
```

`bt_user` 객체에 access와 refresh 토큰이 함께 저장된다. localStorage는 동일 출처의 JavaScript에서 접근 가능하므로 XSS 취약점이 하나라도 있으면 두 토큰 모두 즉시 탈취된다. Refresh 토큰은 수명이 길어 특히 위험하다.

**수정 방향:** Refresh 토큰은 HttpOnly 쿠키로 저장하고, Access 토큰은 메모리(Pinia 상태)에만 유지.

---

#### [Medium] OAuth 콜백 에러 처리 없음
**위치:** [accounts/views.py:86](../backend/accounts/views.py#L86), [views.py:101](../backend/accounts/views.py#L101)

```python
code = request.GET.get('code')
# code가 None인 경우 바로 카카오 API 요청 → 500 에러
access_token = token_response.json().get('access_token')
# access_token이 None이면 이후 Authorization 헤더가 'Bearer None'이 됨
```

`code`가 없거나, OAuth 제공자가 에러를 반환하거나(`?error=access_denied`), 토큰 교환이 실패해도 예외 처리 없이 None이 전파되어 500 Internal Server Error가 발생한다.

**수정 방향:** 각 단계에서 명시적 검증 및 400/502 에러 반환.

---

#### [Medium] API Rate Limiting 없음
**위치:** [accounts/urls.py](../backend/accounts/urls.py), [config/urls.py](../backend/config/urls.py)

OAuth 콜백, 프로필 API, 토큰 갱신 엔드포인트에 Rate Limiting이 없다. 토큰 무차별 대입이나 스팸 계정 생성에 취약하다.

**수정 방향:** `django-ratelimit` 또는 DRF throttling 적용.

---

#### [Medium] JWT 설정 미정의 (기본값 의존)
**위치:** [config/settings.py](../backend/config/settings.py)

`SIMPLE_JWT` 설정 블록이 없어 simplejwt 기본값에 의존한다. 기본값은 Access 5분, Refresh 1일이고 Refresh 토큰 블랙리스트도 비활성화 상태다. 로그아웃 후에도 탈취된 Refresh 토큰을 재사용할 수 있다.

**수정 방향:** `SIMPLE_JWT` 설정 명시, `'BLACKLIST_AFTER_ROTATION': True`, `'rest_framework_simplejwt.token_blacklist'` 앱 추가.

---

#### [Medium] SkinProfile JSONField 입력 검증 없음
**위치:** [accounts/serializers.py:10](../backend/accounts/serializers.py#L10)

`concerns`와 `avoid_ingredients` 필드가 JSONField이지만 Serializer에서 형식 검증이 없다. 클라이언트가 배열 대신 임의의 JSON 객체나 중첩 구조를 전송해도 그대로 저장된다.

**수정 방향:** `validate_concerns`, `validate_avoid_ingredients` 메서드로 리스트 타입 + 항목 길이 검증 추가.

---

#### [Low] SQLite 사용
**위치:** [config/settings.py:101-106](../backend/config/settings.py#L101)

프로덕션 배포 시 SQLite는 동시 쓰기 처리에 한계가 있고, Docker 재기동 시 볼륨 마운트 누락으로 데이터 유실 위험이 있다.

**수정 방향:** PostgreSQL로 전환.

---

### 1-2. 프론트엔드 (Vue 3)

---

#### [High] 사용량 제한이 클라이언트 사이드에서만 관리됨
**위치:** [frontend/src/stores/usage.js](../frontend/src/stores/usage.js), [views/ChatView.vue:41-44](../frontend/src/views/ChatView.vue#L41)

```js
if (!usage.consume()) {
  showPaywall.value = true
  return
}
```

하루 10회 무료 사용 제한(`bt_usage`)이 localStorage 기반으로만 관리된다. 브라우저 개발자 도구에서 `localStorage.removeItem('bt_usage')` 한 줄로 무한 사용이 가능하다. 과금 모델이 있다면 비즈니스 직접 피해로 이어진다.

**수정 방향:** 서버 사이드에서 사용자별 일별 사용 횟수를 카운트하고 초과 시 429 반환.

---

#### [Medium] 찜/추천 기록이 서버와 미연동
**위치:** [frontend/src/stores/chat.js:15](../frontend/src/stores/chat.js#L15), [chat.js:17-18](../frontend/src/stores/chat.js#L17)

```js
const likedIds = ref(new Set(JSON.parse(localStorage.getItem('bt_liked') || '[]')))
const recommendedProducts = ref(stored ? JSON.parse(stored) : SEED_RECOMMENDED)
```

찜 목록과 추천 기록이 localStorage에만 저장된다. 브라우저 캐시 삭제나 기기 변경 시 데이터가 모두 사라진다. `Like`, `InUseProduct`, `Recommendation` 모델이 백엔드에 이미 정의되어 있으나 연동이 없다.

**수정 방향:** Like, Recommendation 관련 API 엔드포인트 구현 및 프론트엔드 연동.

---

#### [Medium] Access 토큰 자동 갱신 로직 없음
**위치:** [frontend/src/services/api.js](../frontend/src/services/api.js)

API 호출 래퍼에서 401 응답 시 Refresh 토큰으로 Access 토큰을 갱신하는 로직이 없다. Access 토큰 만료(기본 5분) 후 모든 API 호출이 401로 실패하고 사용자가 재로그인해야 한다.

**수정 방향:** `api.js`의 `request` 함수에서 401 응답 시 `/api/v1/token/refresh/`를 호출하고 재시도하는 인터셉터 패턴 적용.

---

#### [Low] Mock 데이터가 프로덕션 코드에 잔류
**위치:** [frontend/src/views/ChatView.vue:30-34](../frontend/src/views/ChatView.vue#L30), [ChatView.vue:53-69](../frontend/src/views/ChatView.vue#L53)

```js
const MOCK_PRODUCTS = [ ... ]
// setTimeout으로 Mock 응답 반환
```

실제 AI 응답 대신 하드코딩된 Mock 제품 목록을 반환하는 코드가 남아 있다. AI 백엔드 연동 전 임시 코드이나 배포 시 서비스 신뢰도를 해친다.

---

#### [Low] `auth/callback` 라우트 CSRF 취약성
**위치:** [frontend/src/router/index.js:42-46](../frontend/src/router/index.py#L42)

콜백 라우트에 추가 검증이 없고, 백엔드에서 state 검증도 없으므로(앞서 언급) URL을 직접 조작해 임의의 토큰을 삽입하는 시도가 가능하다. 백엔드 state 검증 도입과 함께 해결된다.

---

## 2. RAG(Retrieval-Augmented Generation) 도입 가능성

### 2-1. 현재 데이터 구조

크롤링으로 수집된 데이터:
- `Product`: 브랜드, 이름, 가격, 카테고리, AI 요약(`ai_summary`), 평균 평점, 리뷰 수, 피부 타입별 만족도(`satisfaction_by_type`)
- `Review`: 리뷰 본문(`text`), 별점, 피부 타입, 추천 수
- `SkinProfile`: 사용자 피부 타입, 피부 고민(`concerns`), 기피 성분(`avoid_ingredients`)

이 데이터는 RAG 파이프라인의 Knowledge Base로 사용하기에 적합한 구조다.

### 2-2. 왜 RAG가 필요한가

**현재 구조의 한계 (Mock 기반):**
- ChatView가 고정된 Mock 제품을 반환함
- 사용자 피부 프로필이 실제 추천에 반영되지 않음
- 리뷰 데이터가 있어도 LLM이 참조하지 못함

**RAG 도입 시 해결되는 것:**
- "민감성 피부에 향 없는 클렌저"처럼 복합 조건 자연어 쿼리를 실제 제품과 리뷰로 답변
- LLM이 학습하지 않은 올리브영 최신 제품 정보를 실시간 컨텍스트로 활용
- 리뷰 기반 근거 제시 ("이 제품은 건성 피부 리뷰에서 보습력을 많이 언급합니다")

### 2-3. 권장 RAG 아키텍처

```
사용자 질의 + 피부 프로필
        ↓
[검색 쿼리 구성]
  피부 타입 필터 + 자연어 쿼리 벡터화
        ↓
[벡터 DB 검색]  ←  임베딩된 제품 설명 + 리뷰
  상위 K개 관련 문서 반환
        ↓
[LLM 추론]
  컨텍스트(제품정보+리뷰) + 사용자 프로필 → 추천 응답
        ↓
사용자에게 추천 제품 + 이유 반환
```

### 2-4. 임베딩 대상 데이터

| 데이터 | 임베딩 단위 | 활용 목적 |
|--------|-------------|-----------|
| `Product.ai_summary` | 제품 1건 | 제품 특성 검색 |
| `Review.text` (피부 타입별 상위 10개) | 리뷰 묶음 | 실 사용 경험 검색 |
| `Product.satisfaction_by_type` | 제품 1건 | 피부 타입 매칭 |

**인덱싱 전략:** 제품 단위로 `ai_summary + 피부타입별 만족도 요약 + 대표 리뷰 3~5개`를 하나의 청크로 구성하면 검색 정밀도와 컨텍스트 품질을 동시에 확보할 수 있다.

### 2-5. 구현 난이도와 선택지

| 옵션 | 난이도 | 특징 |
|------|--------|------|
| **pgvector (PostgreSQL 확장)** | 낮음 | DB를 SQLite→PostgreSQL 전환과 동시에 도입. 별도 벡터 DB 불필요. 현 Django 스택과 친화적. |
| **ChromaDB** | 중간 | 로컬 개발에 편리. 프로덕션 확장성은 pgvector보다 제한적. |
| **Pinecone / Weaviate** | 높음 | 관리형 서비스. 운영 비용 발생하나 대규모 확장 가능. |

SQLite→PostgreSQL 전환(취약점 항목과 연계)을 하면서 `pgvector`를 함께 도입하는 것이 가장 자연스러운 경로다.

### 2-6. 도입 단계

**Phase 1 (기반 구축):**
- PostgreSQL + pgvector 전환
- 제품/리뷰 임베딩 생성 스크립트 작성 (`crawling.py` 확장)
- 기본 벡터 검색 API 엔드포인트 구현

**Phase 2 (챗봇 연동):**
- `chat/views.py`에 RAG 파이프라인 구현
- 사용자 SkinProfile을 필터 조건으로 전처리 (피부 타입 하드 필터 → 벡터 검색)
- LLM API 연동 (Claude API 권장: `claude-sonnet-4-6`)

**Phase 3 (품질 개선):**
- 사용자 찜/추천 기록을 피드백으로 활용한 재랭킹
- 기피 성분이 포함된 제품을 검색 결과에서 제외하는 후처리 필터
- 추천 이유 인용 (어떤 리뷰를 근거로 추천했는지 출처 제시)
