# Beautalk — 보안 점검 · RAG 도입 · 잔여 작업 계획

> 작성일 2026-06-22. 전체 코드 리뷰 기반 취약점 진단 + 해결 방안 + RAG 가능성 + 잔여 작업 로드맵.

---

## 1. 보안 취약점 진단 및 해결 방안

심각도: 🔴 치명적 · 🟠 높음 · 🟡 중간 · ⚪ 낮음/하드닝

### 🔴 V1. SECRET_KEY 하드코딩 + git 노출
- **위치**: [backend/config/settings.py:27](../backend/config/settings.py#L27)
- **문제**: `SECRET_KEY`가 소스에 하드코딩되어 첫 커밋(2026-05-21)부터 공개 git 히스토리에 존재. SimpleJWT 서명이 `SECRET_KEY`에서 파생되므로, 키가 노출되면 **임의 사용자의 JWT를 위조**해 계정 탈취 가능.
- **해결**:
  1. `.env`로 이동: `SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')`
  2. **키 재발급**(rotate) — 이미 노출된 키는 폐기. `get_random_secret_key()`로 신규 생성.
  3. `.env.example`에 플레이스홀더만 추가.
  4. (선택) git 히스토리에서 제거하려면 `git filter-repo`. 단, 협업 중이면 강제 푸시 영향 고려 → 최소한 키 재발급은 필수.

### 🔴 V2. OAuth 계정 연동 로직 버그 (이메일 충돌 → 로그인 불가/계정 혼선)
- **위치**: [backend/accounts/views.py:116-120](../backend/accounts/views.py#L116), [google:169-173](../backend/accounts/views.py#L169)
- **문제**: `UserInfo.objects.get_or_create(email=email, defaults={'user': django_user, ...})` 구조에서, 동일 이메일이 **이미 다른 provider로 가입**되어 있으면:
  - `get_or_create`는 기존 `UserInfo`(다른 `django_user`에 연결됨)를 반환하고 `defaults`는 무시됨.
  - 그런데 JWT는 방금 만든 신규 `django_user`로 발급 → 이 신규 user는 `userinfo` 역참조가 없음.
  - 결과: 프로필 API 진입 시 `request.user.userinfo`에서 `RelatedObjectDoesNotExist` 예외. 즉 **로그인은 되는데 모든 인증 API가 깨짐.**
- **해결**: provider+provider_id를 키로 사용하도록 변경. `UserInfo`에 `provider_id` 필드 추가 후:
  ```python
  user_info, created = UserInfo.objects.get_or_create(
      auth_provider='kakao', provider_id=str(kakao_id),
      defaults={'user': django_user, 'email': email},
  )
  ```
  이메일은 식별자가 아닌 부가정보로. (이메일 unique 제약도 재검토 — 동일인이 두 provider 가입 가능하게 하려면 제거.)

### 🔴 V3. OAuth `state` 파라미터 부재 (CSRF)
- **위치**: [KakaoLoginView:60](../backend/accounts/views.py#L60), [GoogleLoginView:73](../backend/accounts/views.py#L73)
- **문제**: 인증 요청에 `state` 미생성·미검증. 공격자가 자신의 `code`를 피해자 브라우저에 주입(로그인 CSRF)해 **피해자를 공격자 계정으로 로그인**시킬 수 있음.
- **해결**: 로그인 진입 시 랜덤 `state` 생성 → 세션 저장 → 인증 URL에 `&state=`. 콜백에서 `request.GET['state']`와 세션값 비교, 불일치 시 400.

### 🟠 V4. JWT를 URL 쿼리스트링으로 전달
- **위치**: [callback redirect:135](../backend/accounts/views.py#L135), [google:177](../backend/accounts/views.py#L177), [AuthCallbackView.vue:17](../frontend/src/views/AuthCallbackView.vue#L17)
- **문제**: `?access=...&refresh=...` 형태 → 브라우저 히스토리, 서버 access 로그, Referer 헤더에 토큰 평문 잔존.
- **해결**:
  - 최소: 프론트에서 토큰 읽은 직후 `window.history.replaceState({}, '', '/auth/callback')`로 URL 청소.
  - 정석: refresh 토큰은 백엔드가 `httpOnly`·`Secure`·`SameSite` 쿠키로 내려주고, access만 응답 바디로. OAuth 콜백 흐름 일부 재작성 필요.

### 🟠 V5. JWT를 localStorage에 저장
- **위치**: [frontend/src/stores/auth.js:11](../frontend/src/stores/auth.js#L11)
- **문제**: access·refresh 토큰이 `localStorage`(`bt_user`)에 저장 → **XSS 1회로 토큰 탈취**. 특히 refresh 토큰 탈취 시 장기 세션 장악.
- **해결**: access 토큰은 메모리(Pinia state)만, refresh는 httpOnly 쿠키(V4와 동일 방향). 차선책으로라도 refresh는 localStorage에서 빼기.

### 🟠 V6. SIMPLE_JWT 미설정 + 토큰 무효화(로그아웃) 불가
- **위치**: [settings.py](../backend/config/settings.py) (`SIMPLE_JWT` 블록 없음)
- **문제**: 기본값 사용(access 5분·refresh 1일·rotation 없음·blacklist 없음). **로그아웃해도 refresh 토큰이 만료 전까지 유효** → 서버측 무효화 수단 전무.
- **해결**:
  ```python
  from datetime import timedelta
  SIMPLE_JWT = {
      'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
      'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
      'ROTATE_REFRESH_TOKENS': True,
      'BLACKLIST_AFTER_ROTATION': True,
  }
  ```
  `INSTALLED_APPS`에 `'rest_framework_simplejwt.token_blacklist'` 추가 + 마이그레이션 → 로그아웃 시 refresh 블랙리스트 처리.

### 🟠 V7. OAuth 콜백 에러 핸들링 부재
- **위치**: [KakaoCallbackView:89-107](../backend/accounts/views.py#L89), google 동일
- **문제**: 토큰 교환 실패 시 `token_response.json().get('access_token')`가 `None`이어도 그대로 진행 → 사용자 정보 요청 실패 → 빈 `id`로 `get_or_create` → 쓰레기 계정 생성/500. `code` 누락·만료에도 무방비.
- **해결**: `code` 존재 확인, `token_response.status_code`·`access_token` 유효성 검사, 실패 시 프론트 에러 페이지로 리다이렉트. `try/except`로 외부 호출 감싸기.

### 🟡 V8. DEBUG=True / ALLOWED_HOSTS=[] (배포 시 정보 노출)
- **위치**: [settings.py:30,32](../backend/config/settings.py#L30)
- **문제**: `DEBUG=True` 운영 시 예외 페이지에 settings·쿼리·트레이스백 노출.
- **해결**: 환경변수로 분기 — `DEBUG = os.environ.get('DEBUG', 'False') == 'True'`, 운영은 `ALLOWED_HOSTS` 명시.

### 🟡 V9. 챗봇 API 비용 남용 위험 (throttling 부재)
- **위치**: 미구현 [chat/views.py](../backend/chat/views.py)
- **문제**: LLM 호출 엔드포인트는 인증 사용자라도 무제한 호출 시 토큰 비용 폭증. (이미 프론트엔드 사용량 제한 UI는 있으나 클라이언트 측이라 우회 가능.)
- **해결**: DRF `throttle_classes` + `ScopedRateThrottle`로 사용자당 일/분 한도. 서버측 카운팅이 정답.

### ⚪ V10. 운영 하드닝 (배포 전 일괄)
- HTTPS 강제: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`.
- SQLite → PostgreSQL (동시성·확장성, RAG의 pgvector 전제이기도 함).
- CORS: 운영 도메인으로 교체([settings.py:63](../backend/config/settings.py#L63)).
- `python manage.py check --deploy`로 일괄 점검.

### 우선순위 요약
| 순위 | 항목 | 시점 |
|---|---|---|
| 1 | V1 SECRET_KEY 재발급+이동 | 즉시 |
| 2 | V2 OAuth 계정 연동 버그 | 즉시(기능 깨짐) |
| 3 | V6 SIMPLE_JWT+로그아웃, V3 state | 인증 마무리 단계 |
| 4 | V4/V5 토큰 전달·저장 | 배포 전 |
| 5 | V7 콜백 에러처리, V9 throttle | 해당 기능 구현 시 |
| 6 | V8/V10 하드닝 | 배포 직전 |

---

## 2. 문서 점검 결과

- 🔴 **[docs/API.md](API.md) 프로필 응답 예시 오류**: GET `/profile` 응답에 `"id"`, `"user"` 필드가 적혀 있으나, [SkinProfileSerializer](../backend/accounts/serializers.py#L10) `fields`는 `skin_type, concerns, avoid_ingredients, updated_at` 4개뿐. 실제 응답엔 `id`·`user` 없음 → **본 작업에서 수정 완료.**
- ✅ [docs/structure.md](structure.md): models·views 구성 실제 코드와 일치.
- ✅ [docs/progress.md](progress.md): 완료/예정 체크 상태 코드와 일치.
- ⚠️ 정합성 메모: `path('profile', ...)`는 trailing slash 없음. 프론트도 `/api/v1/profile`로 호출 중이라 동작하나, 나머지 라우트(`/callback/` 등)는 slash 있음 → 컨벤션 통일 권장(기능 영향 없어 문서 메모만).

---

## 3. RAG 도입 가능성

### 결론: **도입 가치 높음. 단, 현재 SQLite에서는 pgvector 불가 → PostgreSQL 전환이 선행 조건.**

### 왜 필요한가
챗봇은 `프로필 + 제품 ai_summary`를 LLM 컨텍스트로 주입(progress.md 아키텍처). 제품 수가 늘면 전체 `ai_summary` 주입은 **토큰 한도 초과·비용 폭증**. 질문과 무관한 제품까지 매번 전송하는 낭비도 큼.

### 구조 (Retrieval-Augmented Generation)
```
유저 질문 + 프로필
   → (임베딩) 질문을 벡터화
   → (검색) 벡터 DB에서 유사 제품 top-k(5~10)만 조회
   → (필터) 기피 성분 제외 등 메타 필터
   → (생성) 해당 제품 ai_summary만 LLM 컨텍스트로 주입
   → 추천 답변
```
효과: 컨텍스트 토큰 최대 ~95% 절감, 추천 정확도(질문 관련성) 향상.

### 기술 선택지
| 구성 | 임베딩 | 벡터 저장 | 적합도 |
|---|---|---|---|
| A | Gemini Embedding API | **pgvector**(PostgreSQL 확장) | 운영 권장. DB 일원화, V10의 PG 전환과 시너지 |
| B | Gemini Embedding API | **Chroma**(로컬) | 빠른 프로토타이핑. 별도 인프라 불필요 |
| C | sentence-transformers(로컬) | pgvector/Chroma | 외부 임베딩 비용 0, 단 한국어 품질·서버 메모리 트레이드오프 |

→ **데모/3일 일정**: B(Chroma)로 빠르게 검증 → 배포 시 A(pgvector) 이관.

### 구현 단계
1. PostgreSQL 전환(또는 Chroma 로컬 기동).
2. 적재 스크립트: 전 제품 `ai_summary` 임베딩 → 벡터 저장(제품 `id` 메타데이터 포함). 크롤링/요약 파이프라인 뒤에 1회 배치.
3. 신규/수정 제품 임베딩 갱신 훅.
4. `chat/views.py`: 질문 임베딩 → top-k 검색 → 기피성분 필터 → GMS 호출.
5. (확장) LangGraph로 `질문분석 → 검색 → 필터 → 생성 → 검증` 노드 그래프화. 현재 단일 호출엔 과설계이나, 후속 질문 맥락/멀티스텝 추천에서 이점.

### 리스크
- 임베딩 비용/레이트리밋(Gemini) → 적재는 배치, 질문 임베딩은 캐시 고려.
- 한국어 임베딩 품질 검증 필요(소량 샘플 A/B).
- 데이터 적어 RAG 이점이 작으면, 초기엔 카테고리 필터 + 전체주입으로 시작하고 제품 증가 시 RAG 전환하는 단계적 접근도 유효.

---

## 4. 잔여 작업 로드맵 (progress.md 기반)

남은 핵심은 **온보딩→프로필 연동 / 챗봇 API / UI 완성**. 의존성 순서로 정렬.

### Phase 0 — 보안·인증 마무리 (반나절)
- [ ] V1 SECRET_KEY 재발급+`.env` 이동
- [ ] V2 OAuth 계정 연동 버그 수정 (provider_id 키) — **인증 깨짐, 최우선**
- [ ] V7 콜백 에러 핸들링
- [ ] V6 SIMPLE_JWT 설정 + 로그아웃(블랙리스트)

### Phase 1 — 온보딩·프로필 연결 (0.5일)
선행: 프로필 API는 이미 구현됨. 프론트 연결만 남음.
- [ ] `OnboardingView` `finishOnboarding()` → `POST /api/v1/profile` 호출 + `auth.setProfileComplete()`
- [ ] 마이페이지 `SkinProfileView` → GET/PATCH `/profile` 연동
- [ ] 온보딩 스킵 시 챗봇 진입 처리 (progress 미완 항목)

### Phase 2 — 챗봇 API (1~1.5일, 최대 리스크)
- [ ] `chat/views.py`: `POST /api/v1/chat` — `content` + `history[]` 수신
- [ ] GMS 연동: 프로필 + 제품 컨텍스트 구성 (초기엔 카테고리 필터 전체주입, 시간 남으면 RAG)
- [ ] 기피 성분 필터링, 화장품 외 질문 범위 제한
- [ ] `history[]` 기반 후속 질문, 응답 실패 에러 핸들링
- [ ] V9 throttle 적용
- [ ] 프론트 `ChatView`/`stores/chat.js`: MOCK 제거 → 실제 API 연결

### Phase 3 — 제품·찜·추천 API (0.5일)
- [ ] `products/views.py`: `GET /api/v1/products` (검색/카테고리)
- [ ] `POST /api/v1/likes` 찜 토글 — 프론트 localStorage(`bt_liked`) → 백엔드 `Like` 동기화
- [ ] `GET /api/v1/recommendations` 추천 히스토리(`Recommendation`)

### Phase 4 — UI 완성 (잔여)
- [ ] 추천 카드(이미지/이름/가격, 3~5개+이유), 올리브영 새 탭
- [ ] 찜하기 인라인, 추천 히스토리, 제품 상세
- [ ] 챗봇 말풍선·로딩 인디케이터

### Phase 5 — 배포·QA (시간 허용 시)
- [ ] Docker 컨테이너화 + PostgreSQL 전환 (RAG 전제와 동일)
- [ ] V4/V5 토큰 전달·저장 개선, V8/V10 하드닝, `check --deploy`
- [ ] AWS·Nginx, 전체 QA, 발표 준비

### 3일 현실 배분 (제안)
| Day | 내용 |
|---|---|
| D1 | Phase 0 + Phase 1 (인증 안정화 + 온보딩/프로필 연결) |
| D2 | Phase 2 (챗봇 API — 핵심 기능, RAG 없이 동작 우선) |
| D3 | Phase 3 핵심(찜·제품) + Phase 4 챗봇/추천 카드 UI, 데모 시나리오 점검 |

> RAG·Docker·LangGraph·V4/V5 정석 대응은 **데모 필수 경로 밖** → 시간 남을 때만. "동작하는 데모 우선, 하드닝 후순위" 원칙.
