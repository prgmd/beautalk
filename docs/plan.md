# Beautalk 서비스 취약점 분석 및 RAG 도입 계획

## 1. 현재 서비스 취약점

### 1-1. 백엔드 (Django)

---

#### [Critical] SECRET_KEY 하드코딩 ✅

**상태:** 수정 완료 (2026-06-22)

**변경 사항:**
- `.env` 파일 추가, `DJANGO_SECRET_KEY` 환경변수로 분리
- [config/settings.py:15](../backend/config/settings.py#L15): `SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')`
- 새 SECRET_KEY 발급 완료

---

#### [Critical] JWT 토큰을 URL 쿼리스트링으로 전달 ✅

**상태:** 수정 완료 (2026-06-22)

**변경 사항:**
- 콜백 후 토큰을 세션에 임시 저장 (`pending_access`, `pending_refresh`)
- `/api/v1/auth/exchange/` 엔드포인트 추가: access는 응답 바디, refresh는 HttpOnly 쿠키로 반환
- Access 토큰: 메모리(Pinia)에만 유지, refresh 토큰: HttpOnly; SameSite=Lax 쿠키로 백엔드 관리
- 토큰이 브라우저 히스토리/로그에 남지 않음

---

#### [Critical] OAuth CSRF 방어 누락 (state 파라미터 없음) ✅

**상태:** 수정 완료 (2026-06-22)

**변경 사항:**
- 로그인 시작 시 `secrets.token_urlsafe(16)` 로 state 생성, 세션 저장
- 카카오/구글 Auth URL에 `&state={state}` 파라미터 추가
- 콜백에서 반환된 state와 세션 state 비교, 불일치 시 `?error=csrf_detected` 리다이렉트
- [accounts/views.py:KakaoLoginView, GoogleLoginView, KakaoCallbackView, GoogleCallbackView]

---

#### [High] 이메일 중복 시 계정 탈취 버그 ✅

**상태:** 수정 완료 (2026-06-22)

**변경 사항:**
- `resolve_oauth_user()` 헬퍼 함수 추가: provider_id를 username으로 인코딩해 사용자 식별
- 신규 가입 시 이메일이 이미 선점돼 있으면 None 반환 → `?error=email_duplicated` 리다이렉트
- 기존 사용자는 동일 provider_id로 기존 계정 재사용
- [accounts/views.py:resolve_oauth_user(), KakaoCallbackView, GoogleCallbackView]

---

#### [High] DEBUG=True, ALLOWED_HOSTS 미설정

**상태:** 부분 완료 (배포 단계에서 최종 처리)

**현재:**
- 개발 환경: DEBUG=True (의도적, 로컬 개발용)
- 프로덕션 배포 시 수정 필요: 환경변수 분기 처리, DEBUG=False 설정

---

#### [High] Refresh Token을 localStorage에 저장 ✅

**상태:** 수정 완료 (2026-06-22)

**변경 사항:**
- localStorage: `{ hasProfile }` 정보만 저장 (토큰 제거)
- Access 토큰: Pinia 메모리에만 유지 (페이지 새로고침 시 App.vue startup refresh로 복원)
- Refresh 토큰: HttpOnly; SameSite=Lax 쿠키로 백엔드 관리
- [frontend/src/stores/auth.js, App.vue, services/api.js]

---

#### [Medium] OAuth 콜백 에러 처리 없음 ✅

**상태:** 수정 완료 (2026-06-22)

**변경 사항:**
- `code` 누락: `?error=missing_code` 리다이렉트
- Provider 에러 (`?error=`): `?error=oauth_failed` 리다이렉트
- 토큰 교환 실패: `?error=token_exchange_failed` 리다이렉트
- 사용자 정보 요청 실패: `?error=userinfo_failed` 리다이렉트
- 각 HTTP 요청에 10초 타임아웃 설정
- [accounts/views.py: KakaoCallbackView, GoogleCallbackView]

---

#### [Medium] API Rate Limiting 없음 ✅

**상태:** 수정 완료 (2026-06-22)

**변경 사항:**
- DRF throttling 전역 설정 추가 (장점: JWT 토큰 기반 사용자별 제한 가능)
- 비인증 사용자: 20 요청/시간
- 인증 사용자: 100 요청/시간
- [config/settings.py: REST_FRAMEWORK['DEFAULT_THROTTLE_*']]
- 429 Too Many Requests 에러 반환

---

#### [Medium] JWT 설정 미정의 (기본값 의존) ✅

**상태:** 수정 완료 (2026-06-22)

**변경 사항:**
- `SIMPLE_JWT` 설정 블록 명시 추가
  - Access 토큰: 30분 (기본값 5분에서 확대)
  - Refresh 토큰: 7일
  - `ROTATE_REFRESH_TOKENS=True`: 토큰 갱신 시 새 토큰 발급
  - `BLACKLIST_AFTER_ROTATION=True`: 회전된 토큰 자동 블랙리스트
- `rest_framework_simplejwt.token_blacklist` 앱 추가, 마이그레이션 실행
- 로그아웃 시 RefreshToken.blacklist() 호출 → DB에 기록
- [config/settings.py: SIMPLE_JWT 블록, accounts/views.py: LogoutView]

---

#### [Medium] SkinProfile JSONField 입력 검증 없음 ✅

**상태:** 수정 완료 (2026-06-22)

**변경 사항:**
- `SkinProfileSerializer` 클래스에 검증 메서드 추가
  - `validate_concerns()`: 리스트 타입 확인 + 각 항목 50자 이하 검증
  - `validate_avoid_ingredients()`: 리스트 타입 확인 + 각 항목 50자 이하 검증
- 검증 실패 시 400 Bad Request 반환
- [accounts/serializers.py: SkinProfileSerializer.validate_*]
- 테스트: test_rejects_non_list_concerns, test_accepts_valid_list

---

#### [Low] SQLite 사용

**상태:** 개발 단계 유지, 배포 시 전환

**현재:**
- 로컬 개발: SQLite 사용 (간편함)
- 배포 단계: PostgreSQL로 전환 계획
- 추가 고려사항: pgvector를 함께 도입해 RAG 벡터 검색 구현

---

### 1-2. 프론트엔드 (Vue 3)

---

#### [High] 사용량 제한이 클라이언트 사이드에서만 관리됨

**상태:** 부분 완료 (백엔드 Throttling 추가, 서버사이드 카운팅 미구현)

**현재:**
- DRF Throttling 전역 설정으로 인증 사용자 100/시간 제한
- 그러나 **사용자별 일별 사용 횟수 상세 카운팅은 아직 미구현**
  - Chat API에서 사용 횟수 로깅 필요
  - 별도 UsageLog 모델 추가 고려
- 프론트 localStorage 검증: 여전히 클라이언트에서만 관리 (보조 용도)

**수정 필요:**
- Chat API (`POST /api/v1/chat`) 요청마다 사용 횟수 기록
- 일일 한도(10회 예정) 초과 시 429 반환

---

#### [Medium] 찜/추천 기록이 서버와 미연동

**상태:** 미구현 (다음 단계)

**현재:** localStorage에서만 관리 (브라우저 캐시 삭제 시 초기화)

**구현 필요:**
- Like API: `POST /api/v1/likes/`, `DELETE /api/v1/likes/{product_id}/`
- Recommendation API: `GET /api/v1/recommendations/`
- 백엔드 모델 활성화: Like, InUseProduct, Recommendation (이미 models.py에 정의됨)
- 프론트 연동: stores/chat.js → api.js로 교체

---

#### [Medium] Access 토큰 자동 갱신 로직 없음 ✅

**상태:** 수정 완료 (2026-06-22)

**변경 사항:**
- `api.js`에 401 자동 갱신 인터셉터 추가
  - 401 응답 발생 시 `POST /api/v1/auth/token/refresh` 호출
  - HttpOnly 쿠키로 refresh 토큰 자동 전송 (credentials: 'include')
  - 새 access 토큰으로 auth store 갱신
  - 원본 요청 자동 재시도
  - 갱신 실패 시 로그아웃 처리
- [frontend/src/services/api.js: tryRefresh, request 함수]

---

#### [Low] Mock 데이터가 프로덕션 코드에 잔류

**상태:** 미구현 (AI 백엔드 연동 단계에서 처리)

**현재:** ChatView.vue에서 Mock 제품 목록 사용 (임시)

**제거 필요:**
- Chat API 구현 완료 후 Mock 제품 로직 삭제
- 실제 AI 응답 처리 로직으로 교체

---

#### [Low] `auth/callback` 라우트 CSRF 취약성 ✅

**상태:** 수정 완료 (2026-06-22)

**변경 사항:**
- 백엔드 OAuth CSRF 방어 (state 검증) 도입으로 자동 해결
- 콜백 라우트는 `?error=` 파라미터로 백엔드 에러 감지
- 프론트 측에서는 `/auth/exchange` 엔드포인트를 신뢰하고 토큰 교환
- [frontend/src/views/AuthCallbackView.vue]

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
